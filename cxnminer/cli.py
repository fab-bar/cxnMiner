import base64
import binascii
import collections
import collections.abc
import functools
import itertools
import json
import logging
import logging.config
import operator
import math
import os
import os.path
import pickle

import click
import conllu

from cxnminer.pattern import SNGram, PatternElement
from cxnminer.pattern_collection import PatternCollection
from cxnminer.pattern_encoder import PatternEncoder, Base64Encoder, HuffmanEncoder
from cxnminer.utils.helpers import factories, open_file, open_json_config, MultiprocessMap

@click.group()
@click.pass_context
@click.option('--logging_config', default=None)
def main(ctx, logging_config):

    ctx.ensure_object(dict)

    loggingConfig = dict(
            version = 1,
            formatters = {
                'f': {'format':
                      '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
            },
            handlers = {
                'h': {'class': 'logging.StreamHandler',
                      'formatter': 'f',
                      'level': logging.DEBUG},
            },
            root = {
                'handlers': ['h'],
                'level': logging.DEBUG,
            }
        )

    if logging_config is not None:

        try:
            logging_config = json.loads(logging_config)
        except json.JSONDecodeError:
            with open(logging_config) as config_file:
                logging_config = json.load(config_file)

        loggingConfig.update(logging_config)

    logging.config.dictConfig(loggingConfig)
    logger = logging.getLogger(__name__)

    ctx.obj['logger'] = logger

@main.command()
@click.pass_context
@click.argument('infile')
@click.argument('outdir')
@click.option('--example_ids')
def corpus2sentences(ctx, infile, outdir, example_ids):


    try:
        os.mkdir(outdir)
    except OSError:
        print ("Creation of the directory %s failed" % outdir)

    if example_ids is not None:
        example_ids = set(json.load(open_file(example_ids)))

    with open_file(infile) as corpusfile:

        for sent_id, sentence in enumerate(conllu.parse_incr(corpusfile)):
             print(sent_id)
             if example_ids is None or sent_id in example_ids:
                 print(sentence.serialize(), file=open(os.path.join(outdir, str(sent_id)), 'w'))


def conversion_function(tree, tags):

    if tree.token['upos'] in tags:
        return SNGram.Tree(dict({'np_function': tree.token['deprel'], 'id': tree.token['id']}), [])
    else:
        return None


def encode_pattern(pattern, token_start, token_end, unknowns):

    current_pattern = b''
    for element in pattern.get_element_list():
        if not hasattr(element, 'items'):
            ## can be special element (string), or a PatternElement
            current_list = [(str(element), getattr(element, 'get', lambda x, y: None)('level', None))]
        else:
            current_list = [(token_start, None)] + [(word, level) for level, word in element.items() if level in {'lemma', 'upos', 'deprel'}] + [(token_end, None)]

        for element, level in current_list:
            ## just a quick fix - np_function needs to be handled differently
            if level == 'deprel':
                level = 'np_function'
            try:
                encoded_element = Base64Encoder.b64decode(element)
            except binascii.Error:
                ## set encoded_element to unknown
                encoded_element = Base64Encoder.b64decode(unknowns[level])

            current_pattern = HuffmanEncoder.combine(current_pattern, encoded_element)

    return Base64Encoder.b64encode(current_pattern, binary=False)

def pattern_extraction(sentence_tuple, extractor, word_level, token_start, token_end, keep_only_word,
                       logger, skip_unknown, unknowns={}, known=None):

    sentence_nr, sentence = sentence_tuple

    pattern_list = []

    logger.info("Extract patterns from sentence {}, {}".format(
        str(sentence_nr + 1), sentence.metadata.get('sent_id', "no id")))

    sentence_base_patterns = collections.defaultdict(list)
    tpatterns = extractor.extract_patterns(sentence)

    if skip_unknown:
        unknown = unknowns.values()
    else:
        unknown = []

    for tpattern in tpatterns:

        this_pattern_list = []

        base_level_pattern = tpattern.get_base_pattern(word_level)

        base_pattern_encoded = None

        if keep_only_word is None or any([getattr(element, "get", lambda x, y: None)(word_level, None) == keep_only_word for element in tpattern.get_full_pattern().get_element_list()]):
            for pattern in tpattern.get_pattern_list(frozenset(['lemma', 'upos', 'np_function'])):

                if pattern != base_level_pattern:
                    ### only keep patterns that consist of given vocabulary entries
                    if not unknown or not any((getattr(element, "form", None) in unknown for element in pattern.get_element_list())):
                        if known is None or all(
                                (getattr(element, "form", element) in known.get(
                                    getattr(element, "level", "__special__"), {})
                                 for element in pattern.get_element_list())):
                            if base_pattern_encoded is None:
                                base_pattern_encoded = encode_pattern(tpattern.get_full_pattern(), token_start, token_end, unknowns)
                            this_pattern_list.append((False, encode_pattern(pattern, token_start, token_end, unknowns), base_pattern_encoded))


        if this_pattern_list:
            base_pattern_positions = [int(str(element)) for element in tpattern.get_base_pattern('id').get_element_list() if isinstance(element, PatternElement)]
            sentence_base_patterns[base_pattern_encoded].append(base_pattern_positions)
            pattern_list.extend(this_pattern_list)

    for encoded_base_pattern, positions in sentence_base_patterns.items():
        for key, _ in itertools.groupby(sorted(positions, key=lambda x: ",".join(str(x)))):
            pattern_list.append((True, encoded_base_pattern, [sentence_nr + 1, key]))

    return pattern_list

@main.command()
@click.pass_context
@click.argument('infile')
@click.argument('outfile_patterns')
@click.argument('outfile_base')
@click.argument('encoded_dictionaries', type=str)
@click.argument('config')
@click.option('--keep_only_word', type=str)
@click.option('--keep_only_dict_words', is_flag=True)
@click.option('--skip_unknown', is_flag=True)
@click.option('--only_base', is_flag=True)
def extract_patterns(ctx, infile, outfile_patterns, outfile_base, encoded_dictionaries,
                     config, keep_only_word, keep_only_dict_words, skip_unknown, only_base):

    config = open_json_config(config)
    word_level = config["word_level"]
    phrase_tags = config["phrase_tags"]
    unknown_type = config["unknown"]

    try:
        encoded_dict = json.loads(encoded_dictionaries)
    except json.JSONDecodeError:
        with open_file(encoded_dictionaries) as dict_file:
            encoded_dict = json.load(dict_file)

    meta_symbols = encoded_dict.get("__special__", {})
    token_start = meta_symbols.get("__TOKEN_START__", "__TOKEN_START__")
    token_end = meta_symbols.get("__TOKEN_END__", "__TOKEN_END__")

    unknown = {}
    for level in encoded_dict.keys():
        if level != "__special__":
            unknown[level] = encoded_dict[level].get(unknown_type, unknown_type)

    if keep_only_dict_words:
        known = {level: set(vocab.values()) for level, vocab in encoded_dict.items() if isinstance(vocab, collections.abc.Mapping)}
    else:
        known = None

    if phrase_tags:
        phrase_tags = [encoded_dict.get("upos", {}).get(element, element) for element in phrase_tags]
        special_node_conversion = functools.partial(conversion_function, tags=phrase_tags)
    else:
        special_node_conversion = None

    if keep_only_word is not None:
        keep_only_word = encoded_dict["lemma"][keep_only_word]

    del encoded_dict

    extractor_config = config["extractor"]
    extractor_config['options']['special_node_conversion'] = special_node_conversion
    extractor_config['options']['left_bracket'] = meta_symbols.get(extractor_config['options']['left_bracket'])
    extractor_config['options']['right_bracket'] = meta_symbols.get(extractor_config['options']['right_bracket'])
    extractor_config['options']['comma'] = meta_symbols.get(extractor_config['options']['comma'])


    extractor = factories.create_from_name('extractor', extractor_config)

    with open_file(infile) as infile:
        with open_file(outfile_patterns, 'w') as outfile_patterns:
            with open_file(outfile_base, 'w') as outfile_base:

                for sentence_patterns in map(
                        functools.partial(
                            pattern_extraction, extractor=extractor, word_level=word_level,
                            token_start=token_start, token_end=token_end, keep_only_word=keep_only_word,
                            logger=ctx.obj['logger'],
                            skip_unknown=skip_unknown,
                            unknowns=unknown, known=known),
                        enumerate(conllu.parse_incr(infile))):

                    for is_base_pattern, pattern, content in sentence_patterns:
                        if not is_base_pattern:
                            if not only_base:
                                print("\t".join([pattern, str(content)]), file=outfile_patterns)
                        else:
                            print("\t".join([pattern, json.dumps(content)]), file=outfile_base)


@main.group()
@click.pass_context
def utils(ctx):
    pass

### extract features from tokens
def get_feature_extractors(phrase_tags):

    return {
        "form": lambda token: token['form'],
        "lemma": lambda token: token['lemma'],
        "upos": lambda token: token['upos'],
        "xpos": lambda token: token['xpos'],
        "np_function": lambda token: token['deprel'] if token['upos'] in phrase_tags else None,
    }

@utils.command()
@click.argument('infile')
@click.argument('outfile')
@click.argument('config')
@click.option('--drop_frequencies', is_flag=True)
@click.pass_context
def extract_vocabulary(ctx, infile, outfile, config, drop_frequencies):

    config = open_json_config(config)
    levels = [config.get("word_level")] + config.get("levels")
    feature_extractors = get_feature_extractors(config.get("phrase_tags"))

    vocabulary = {}
    for level in levels:

        vocabulary[level] = collections.defaultdict(int)

    for sentence in conllu.parse_incr(open_file(infile)):

        for token in sentence:

            for level in vocabulary.keys():

                value = feature_extractors[level](token)
                if value is not None:
                    vocabulary[level][value] += 1

    if drop_frequencies:
        for level in vocabulary:

            vocabulary[level] = list(vocabulary[level].keys())


    with open_file(outfile, 'w') as outfile:
        print(json.dumps(vocabulary), file=outfile)


@utils.command()
@click.argument('dictionaries')
@click.argument('outfile')
@click.argument('config')
@click.pass_context
def create_encoder(ctx, dictionaries, outfile, config):

  with open_file(dictionaries) as dict_file:
    vocabularies = json.load(dict_file)

  config = open_json_config(config)

  extractor = factories.create_from_name('extractor', config['extractor'])
  unknown = config["unknown"]

  pattern_encoder = HuffmanEncoder(vocabularies,
                                   extractor.get_pattern_type(),
                                   unknown=unknown)


  with open_file(outfile, 'wb') as outfile:
    pattern_encoder.save(outfile)


@utils.command()
@click.argument('vocabulary')
@click.argument('outfile')
@click.argument('encoder')
@click.argument('config')
@click.option('--no_frequencies', is_flag=True)
@click.pass_context
def encode_vocabulary(ctx, vocabulary, outfile, encoder, config, no_frequencies):

  logger = ctx.obj['logger']

  config = open_json_config(config)

  try:
    vocabularies = json.loads(vocabulary)
  except json.JSONDecodeError:
    with open_file(vocabulary) as dict_file:
      vocabularies = json.load(dict_file)

  logger.info("Read vocabulary.")

  with open_file(encoder, 'rb') as encoder_file:
    encoder = Base64Encoder(PatternEncoder.load(encoder_file), binary=False)

  encoded_vocabularies = collections.defaultdict(dict)
  levels = set(vocabularies.keys())
  levels.update(encoder.get_levels())

  for level in levels:
    if not no_frequencies:
      items = vocabularies.get(level, {}).keys()
    else:
      items = vocabularies.get(level, [])

    logger.info("Start encoding level " + level + " with " + str(len(items)) + " elements.")

    for word in items:
      logger.info("Encoding word " + word + ".")
      encoded_vocabularies[level][word] = encoder.encode_item(PatternElement(word, level))

    logger.info("Encoding unknown element.")
    encoded_vocabularies[level][config["unknown"]] = encoder.encode_item(PatternElement(config["unknown"], level))


  logger.info("Encoding special elements.")
  for word in encoder.get_pattern_type().specialElements():
    encoded_vocabularies["__special__"][word] = encoder.encode_item(word)

  encoded_vocabularies["__special__"][encoder.token_start] = encoder.encode_item(encoder.token_start)
  encoded_vocabularies["__special__"][encoder.token_end] = encoder.encode_item(encoder.token_end)

  logger.info("Finished encoding.")

  with open_file(outfile, 'w') as outfile:
    json.dump(encoded_vocabularies, outfile)


level_dict = {
    'np_function': 'deprel'
}

def encode_item(level, level_name, token, vocabulary, unknown=None, logger=None):

    encoded = vocabulary.get(level).get(token[level_name], vocabulary.get(level).get(unknown, None))

    if encoded is None:

        if logger is not None:
            logger.warning(str(PatternElement(token[level_name], level)) + " was not encoded.")
        encoded = token[level_name]

    return encoded


@utils.command()
@click.argument('infile')
@click.argument('outfile')
@click.argument('dictionary')
@click.argument('config')
@click.option('--processes', type=int, default=4)
@click.pass_context
def encode_corpus(ctx, infile, outfile, dictionary, config, processes):

    global encode_sentence

    logger = ctx.obj['logger']

    config = open_json_config(config)
    levels = [config.get("word_level")] + config.get("levels")

    with open_file(dictionary) as dict_file:
        vocabulary = json.load(dict_file)

    def encode_sentence(sentence):

        for token in sentence:

            for level in levels:

                ## get name of level, if it is an alias
                level_name = level_dict.get(level, level)

                ## write encoded data into token
                token[level_name] = encode_item(level, level_name, token, vocabulary, config['unknown'], logger)

        logger.info("Encoded sentence " + sentence.metadata.get('sent_id', sentence.metadata.get('text', '')))
        return sentence

    with open_file(outfile, 'w') as outfile:

        with MultiprocessMap(processes) as m:

            for sentence in m(encode_sentence, conllu.parse_incr(open_file(infile))):

                print(sentence.serialize(), file=outfile)


@utils.command()
@click.argument('infile')
@click.argument('outfile')
@click.option('--remove_hapax', is_flag=True)
@click.pass_context
def convert_pattern_list(ctx, infile, outfile, remove_hapax):

    def write_pattern(pattern, contents, outfile):
        json.dump((pattern, contents), outfile)
        outfile.write("\n")

    with open_file(infile) as infile:
        with open_file(outfile, 'w') as outfile:

            current_pattern = None
            contents = []

            for line in infile:
                pattern, content = line.rstrip().split("\t")

                if pattern != current_pattern:

                    if current_pattern is not None:
                        if not remove_hapax or len(contents) > 1:
                            write_pattern(current_pattern, contents, outfile)

                    current_pattern = pattern
                    contents = []

                contents.append(content)

            if not remove_hapax or len(contents) > 1:
                write_pattern(current_pattern, contents, outfile)


@utils.command()
@click.pass_context
@click.argument('vocabulary')
@click.argument('outfile')
@click.option('--add_smoothing', type=float, default=1, show_default=True)
def get_vocabulary_probs(ctx, vocabulary, outfile, add_smoothing):


    try:
        vocabularies = json.loads(vocabulary)
    except json.JSONDecodeError:
        with open_file(vocabulary) as dict_file:
            vocabularies = json.load(dict_file)

    vocabularies_probs = {}

    for level in vocabularies:

        freq = 0
        entries = len(vocabularies[level])

        probs = {}

        for entry in vocabularies[level]:

            freq += vocabularies[level][entry]

        for entry in vocabularies[level]:

            probs[entry] = (vocabularies[level][entry] + add_smoothing)/(freq + add_smoothing*entries)

        vocabularies_probs[level] = (probs, add_smoothing/(freq + add_smoothing*entries))

    with open_file(outfile, 'w') as o:
        json.dump(vocabularies_probs, o)



@utils.command()
@click.pass_context
@click.argument('infile_patterns')
@click.argument('frequency_stats')
@click.argument('outfile')
def get_pattern_type_freq(ctx, infile_patterns, frequency_stats, outfile):

    pattern_types = collections.defaultdict(int)

    number = 0

    stats = {}

    with open_file(frequency_stats) as infile:

        for line in infile:
            pattern, pstats = json.loads(line)
            stats[pattern] = pstats

    with open_file(infile_patterns, 'rb') as infile:

        while True:
            try:
                pattern, decoded_pattern = pickle.load(infile)

                number += 1
                ctx.obj['logger'].info("Pattern " + str(number))
                pattern_type = decoded_pattern.get_pattern_profile()

                pattern_types[pattern_type] += stats.get(pattern, {}).get('frequency', 1)
            except EOFError:
                break


    print(len(pattern_types))
    with open_file(outfile, 'w') as o:
        json.dump(pattern_types, o)


def get_stats(line, decoded_patterns, known_stats, base_patterns, base_level, pattern_profile_frequency, vocabulary_probs):

    pattern, base_ids = json.loads(line)
    base_ids = set(base_ids)

    stats = {}
    if known_stats is not None:
        stats = known_stats.get(pattern)

    if base_patterns is not None:
        frequency = 0
        base_hapax = 0

        for base_id in base_ids:

            base_freq = base_patterns[base_id]
            frequency += base_freq
            if base_freq == 1:
                base_hapax += 1
        stats['frequency'] = frequency
        stats['uif'] = base_hapax

    decoded_pattern = None
    if decoded_patterns is not None:
        decoded_pattern = decoded_patterns.get(pattern, None)

    if decoded_pattern is not None:

        stats['length'] = decoded_pattern.length

        if base_level is not None:

            base_elements = 0
            non_base_elements = 0

            for element in decoded_pattern.get_element_list():
                ## skip meta elements
                if hasattr(element, "level"):
                    if element.level == base_level:
                        base_elements += 1
                    else:
                        non_base_elements += 1

            stats['schematicity'] = non_base_elements/(base_elements + non_base_elements)

        pattern_type = decoded_pattern.get_pattern_profile()
        stats["pattern_profile"] = pattern_type

        if vocabulary_probs is not None:

            prob = 0

            for element in decoded_pattern.get_element_list():
                ## skip meta elements (and unknown?)
                if hasattr(element, "level"):
                    level_probs = vocabulary_probs[element.level]
                    prob += math.log(level_probs[0].get(element.form, level_probs[1]))

            stats["log_unigram_probability"] = prob

    if pattern_profile_frequency is not None and "pattern_profile" in stats and "frequency" in stats:
        stats["log_pattern_probability"] = math.log(stats["frequency"]/pattern_profile_frequency[stats["pattern_profile"]])

    if "log_pattern_probability" in stats and "log_unigram_probability" in stats:
        stats["pmi"] = stats["log_pattern_probability"] - stats["log_unigram_probability"]

    if "pmi" in stats and "uif" in stats:
        stats["uif-pmi"] = stats["uif"]*stats["pmi"]

    return pattern, stats

@utils.command()
@click.pass_context
@click.argument('infile_patterns')
@click.argument('outfile')
@click.option('--known_stats')
@click.option('--base_patterns')
@click.option('--decoded_patterns')
@click.option('--config')
@click.option('--vocabulary_probs')
@click.option('--pattern_profile_frequency')
def add_pattern_stats(ctx, infile_patterns, outfile, known_stats, base_patterns, decoded_patterns, config,
                      vocabulary_probs, pattern_profile_frequency):

    base_level = None
    if config is not None:
        base_level = open_json_config(config)['word_level']

    if decoded_patterns is not None:
        with open_file(decoded_patterns, 'rb') as infile:

            decoded_patterns = {}

            while True:
                try:
                    pattern, decoded_pattern = pickle.load(infile)
                    decoded_patterns[pattern] = decoded_pattern
                except EOFError:
                    break

    if base_patterns is not None:
        with open_file(base_patterns) as infile:

            base_patterns = {}

            for line in infile:
                pattern, sentences = json.loads(line)
                base_patterns[pattern] = len(sentences)

    if pattern_profile_frequency is not None:
        with open_file(pattern_profile_frequency, 'r') as infile:
            pattern_profile_frequency = json.load(infile)

    if vocabulary_probs is not None:
        with open_file(vocabulary_probs, 'r') as infile:
            vocabulary_probs = json.load(infile)

    if known_stats is not None:

        with open_file(known_stats) as infile:

            known_stats = {}

            for line in infile:
                pattern, stats = json.loads(line)
                known_stats[pattern] = stats

    number = 0
    with open_file(infile_patterns) as infile:
        with open_file(outfile, 'w') as o:

            for pattern, stats in map(
                    functools.partial(get_stats,
                                      decoded_patterns=decoded_patterns,
                                      known_stats=known_stats,
                                      base_patterns=base_patterns,
                                      base_level=base_level,
                                      pattern_profile_frequency=pattern_profile_frequency,
                                      vocabulary_probs=vocabulary_probs
                    ),
                    infile):

                number += 1
                ctx.obj['logger'].info("Pattern " + str(number))

                json.dump((pattern, stats), o)
                o.write("\n")

filter_ops = {
    "==": operator.eq,
    ">=": operator.ge,
    "<": operator.lt
}

@utils.command()
@click.pass_context
@click.argument('patterns')
@click.argument('stats')
@click.argument('feature')
@click.argument('threshold', type=int)
@click.argument('outfile')
@click.option('--operator', 'op', type=click.Choice(tuple(filter_ops.keys())), default=">=")
def filter_patterns(ctx, patterns, stats, feature, threshold, outfile, op):


    keep = set()
    with open_file(stats) as infile:
        for line in infile:
            pattern, stats = json.loads(line)
            if filter_ops[op](stats.get(feature, 0), threshold):
                keep.add(pattern)


    with open_file(patterns) as infile:
        with open_file(outfile, 'w') as o:

            for line in infile:

                pattern, _ = json.loads(line)

                if pattern in keep:
                    o.write(line)

def decode_pattern(line, pattern_encoder):

    pattern, _ = json.loads(line)
    return pattern, pattern_encoder.decode(pattern)

@utils.command()
@click.pass_context
@click.argument('infile')
@click.argument('encoder')
@click.argument('outfile')
@click.option('--processes', type=int, default=1)
def decode_patterns(ctx, infile, encoder, outfile, processes):

    with open_file(encoder, 'rb') as encoder_file:
        pattern_encoder = Base64Encoder(PatternEncoder.load(encoder_file), binary=False)

    with open_file(infile) as infile:
        with open_file(outfile, 'wb') as o:

            with MultiprocessMap(processes, chunksize=1000) as m:

                for pattern, decoded_pattern in m(
                        functools.partial(decode_pattern,
                                          pattern_encoder=pattern_encoder
                        ),
                        infile):

                    ctx.obj['logger'].info("Pattern")
                    pickle.dump((pattern, decoded_pattern), o)


@utils.command()
@click.pass_context
@click.argument('patterns_file')
@click.argument('pattern_stats_file')
@click.argument('stat')
@click.argument('n', type=int)
@click.argument('outfile')
def get_top_n(ctx, patterns_file, pattern_stats_file, stat, n, outfile):

    pattern_stats = {}

    ## collect patterns that are in the pattern_file
    with open_file(patterns_file) as infile:

            for line in infile:

                pattern, _ = json.loads(line)
                pattern_stats[pattern] = []

    ## get statistics for these patterns
    with open_file(pattern_stats_file) as infile:

        for line in infile:
            pattern, stats = json.loads(line)
            if pattern in pattern_stats:
                pattern_stats[pattern] = stats

    ## get top n patterns
    patterns = sorted(pattern_stats.items(), key=lambda item: item[1][stat], reverse=True)
    patterns = {pattern[0]: [rank] for rank, pattern in enumerate(patterns[:n])}

    ## add content to the top patterns
    with open_file(patterns_file) as infile:

            for line in infile:

                pattern, content = json.loads(line)

                if pattern in patterns:
                    patterns[pattern].append(content)

    with open_file(outfile, 'w') as o:
        for pattern, value in sorted(patterns.items(), key=lambda item: item[1][0]):
            json.dump([pattern, {'stats': pattern_stats[pattern], 'base_patterns': value[1]}], o)
            o.write("\n")


@utils.command()
@click.pass_context
@click.argument('patterns_file')
@click.argument('base_patterns_file')
@click.argument('n', type=int)
@click.argument('outfile')
@click.option('--example_ids')
def get_top_n_base_patterns(ctx, patterns_file, base_patterns_file, n, outfile, example_ids):

    with open_file(base_patterns_file) as infile:

        base_patterns = {}

        for line in infile:
            pattern, sentences = json.loads(line)
            base_patterns[pattern] = len(sentences)

    bp_example_ids = set()
    with open_file(patterns_file) as infile:
        with open_file(outfile, 'w') as o:

            for line in infile:

                pattern, content = json.loads(line)
                bp = content['base_patterns']

                if len(bp) > n:
                    bp = sorted(bp, key=lambda pattern: base_patterns[pattern], reverse=True)[:n]

                bp_set = set(bp)
                bp_with_examples = []
                with open_file(base_patterns_file) as basefile:

                    for baseline in basefile:
                        bpattern, sentences = json.loads(baseline)
                        if bpattern in bp_set:
                            examples = [json.loads(sentence) for sentence in sentences]
                            # I have added 1 to the id
                            for example in examples:
                                example[0] = example[0] - 1
                            bp_with_examples.append((bpattern, examples))
                            bp_example_ids.update(set([sentence[0] for sentence in examples]))

                            ## stop sanning base pattern file if I have all base patterns
                            bp_set.remove(bpattern)
                            if not bp_set:
                                break


                bp = bp_with_examples

                ## add frequency to bp
                bp = list(map(lambda pattern: pattern + (base_patterns[pattern[0]],), bp))

                content['base_patterns'] = bp

                json.dump([pattern, content], o)
                o.write("\n")

        if example_ids is not None:
            with open_file(example_ids, 'w') as o:
                json.dump(list(bp_example_ids), o)


@utils.command()
@click.pass_context
@click.argument('infile')
@click.argument('encoder')
@click.argument('outfile')
@click.argument('config')
@click.option('--string', is_flag=True)
@click.option('--skip_unknown', is_flag=True)
def decode_pattern_collection(ctx, infile, encoder, outfile, config, string, skip_unknown):

    config = open_json_config(config)
    word_level = config["word_level"]
    unknown = config["unknown"]

    with open_file(encoder, 'rb') as encoder_file:
        pattern_encoder = Base64Encoder(PatternEncoder.load(encoder_file), binary=False)

    with open_file(infile) as infile:
        with open_file(outfile, 'w') as o:

            for line in infile:

                pattern, content = json.loads(line)
                decoded_pattern = pattern_encoder.decode(pattern)

                if string:
                    out_pattern = str(decoded_pattern)
                else:
                    out_pattern = base64.b64encode(pickle.dumps(decoded_pattern)).decode('ascii')

                base_patterns = content.get('base_patterns', [])
                decoded_base_patterns = []
                for base_pattern in base_patterns:

                    try:
                        frequency = None
                        if len(base_pattern) > 2:
                            frequency = base_pattern[2]

                        examples = []
                        if len(base_pattern) > 1:
                            examples = base_pattern[1]
                            base_pattern = base_pattern[0]

                        decoded_pattern = pattern_encoder.decode(base_pattern)

                        if (not skip_unknown) or (all([element != unknown for element in decoded_pattern.get_element_list()])):
                            if string:
                                cout_pattern = str(decoded_pattern)
                            else:
                                cout_pattern = base64.b64encode(pickle.dumps(decoded_pattern)).decode('ascii')

                            decoded_base_patterns.append([cout_pattern, examples, decoded_pattern.get_brat_docdata(word_level), frequency])
                    except:
                        ctx.obj['logger'].warning("Could not test pattern for unknown, skipping.")

                content['base_patterns'] = decoded_base_patterns


                json.dump((out_pattern, content), o)
                o.write("\n")


@utils.command()
@click.pass_context
@click.argument('pattern_file')
def get_schematization_relation(ctx, pattern_file):

    pattern_set = PatternCollection(pattern_file)
    pattern_set.loadSchematisationRelation()
    pattern_set.save()

