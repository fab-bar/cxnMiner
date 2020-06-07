import collections
import collections.abc
import functools
import itertools
import json
import logging
import logging.config
import math
import multiprocessing
import pickle

import click
import conllu

from cxnminer.extractor import SyntacticNGramExtractor
from cxnminer.pattern import SNGram
from cxnminer.pattern_encoder import PatternEncoder, Base64Encoder, HuffmanEncoder
from cxnminer.utils.helpers import open_file

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


def conversion_function(tree, tags):

    if tree.token['upostag'] in tags:
        return SNGram.Tree(dict({'np_function': tree.token['deprel'], 'id': tree.token['id']}), [])
    else:
        return None


def encode_pattern(pattern):

    current_pattern = b''
    for element in pattern.get_element_list():
        encoded_element = Base64Encoder.b64decode(str(element))
        current_pattern = HuffmanEncoder.combine(current_pattern, encoded_element)

    return Base64Encoder.b64encode(current_pattern, binary=False)

def pattern_extraction(sentence_tuple, extractor, word_level, logger, unknown=None, known=None):

    sentence_nr, sentence = sentence_tuple

    pattern_list = []

    logger.info("Extract patterns from sentence {}, {}".format(
        str(sentence_nr + 1), sentence.metadata.get('sent_id', "no id")))

    sentence_base_patterns = collections.defaultdict(list)
    tpatterns = extractor.extract_patterns(sentence)

    for tpattern in tpatterns:

        this_pattern_list = []

        base_pattern = tpattern.get_base_pattern(word_level)

        base_pattern_encoded = None

        for pattern in tpattern.get_pattern_list(frozenset(['lemma', 'upostag', 'np_function'])):

            if pattern != base_pattern:
                ### only keep patterns that consist of given vocabulary entries
                if unknown is None or not any((unknown == getattr(element, "form", None) for element in pattern.get_element_list())):
                    if known is None or all(
                            (getattr(element, "form", element) in known.get(
                                getattr(element, "level", "__special__"), {})
                             for element in pattern.get_element_list())):
                        if base_pattern_encoded is None:
                            base_pattern_encoded = encode_pattern(base_pattern)
                        this_pattern_list.append((False, encode_pattern(pattern), base_pattern_encoded))

        if this_pattern_list:
            base_pattern_positions = ",".join(
                [str(element) for element in tpattern.get_base_pattern('id').get_element_list()])
            sentence_base_patterns[base_pattern_encoded].append(base_pattern_positions)
            pattern_list.extend(this_pattern_list)

    for encoded_base_pattern, positions in sentence_base_patterns.items():
        for _, _ in itertools.groupby(sorted(positions)):
            pattern_list.append((True, encoded_base_pattern, sentence_nr + 1))

    return pattern_list

@main.command()
@click.pass_context
@click.argument('infile')
@click.argument('outfile_patterns')
@click.argument('outfile_base')
@click.argument('word_level', type=str)
@click.argument('phrase_tags', type=str, nargs=-1)
@click.option('--encoded_dictionaries', type=str, default="{}")
@click.option('--max_pattern_size', type=int, default=4)
@click.option('--keep_only_dict_words', is_flag=True)
@click.option('--skip_unknown', is_flag=True)
@click.option('--only_base', is_flag=True)
def extract_patterns(ctx, infile, outfile_patterns, outfile_base,
                     word_level, phrase_tags, encoded_dictionaries, max_pattern_size,
                     keep_only_dict_words, skip_unknown, only_base):

    try:
        encoded_dict = json.loads(encoded_dictionaries)
    except json.JSONDecodeError:
        with open_file(encoded_dictionaries) as dict_file:
            encoded_dict = json.load(dict_file)

    meta_symbols = encoded_dict.get("__special__", {})

    if skip_unknown:
        unknown = encoded_dict.get('__unknown__', '__unknown__')
    else:
        unknown = None

    if keep_only_dict_words:
        known = {level: set(vocab.values()) for level, vocab in encoded_dict.items() if isinstance(vocab, collections.abc.Mapping)}
    else:
        known = None

    if phrase_tags:
        phrase_tags = [encoded_dict.get("upostag", {}).get(element, element) for element in phrase_tags]
        special_node_conversion = functools.partial(conversion_function, tags=phrase_tags)
    else:
        special_node_conversion = None

    del encoded_dict

    extractor = SyntacticNGramExtractor(
        max_size=max_pattern_size,
        special_node_conversion=special_node_conversion,
        left_bracket=meta_symbols.get("[", None),
        right_bracket=meta_symbols.get("]", None),
        comma=meta_symbols.get(",", None))

    with open_file(infile) as infile:
        with open_file(outfile_patterns, 'w') as outfile_patterns:
            with open_file(outfile_base, 'w') as outfile_base:

                for sentence_patterns in map(
                        functools.partial(
                            pattern_extraction, extractor=extractor, word_level=word_level, logger=ctx.obj['logger'],
                            unknown=unknown, known=known),
                        enumerate(conllu.parse_incr(infile))):

                    for is_base_pattern, pattern, content in sentence_patterns:
                        if not is_base_pattern:
                            if not only_base:
                                print("\t".join([pattern, str(content)]), file=outfile_patterns)
                        else:
                            print("\t".join([pattern, str(content)]), file=outfile_base)


@main.group()
@click.pass_context
def utils(ctx):
    pass


@utils.command()
@click.argument('infile')
@click.argument('outfile')
@click.option('--is_int', is_flag=True)
@click.option('--remove_hapax', is_flag=True)
@click.pass_context
def convert_pattern_list(ctx, infile, outfile, is_int, remove_hapax):

    def write_pattern(pattern, contents, outfile):
        json.dump((pattern, contents), outfile)
        outfile.write("\n")

    with open_file(infile) as infile:
        with open_file(outfile, 'w') as outfile:

            current_pattern = None
            contents = []

            for line in infile:
                pattern, content = line.rstrip().split("\t")
                if is_int:
                    content = int(content)

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
@click.option('--base_level')
@click.option('--vocabulary_probs')
@click.option('--pattern_profile_frequency')
def add_pattern_stats(ctx, infile_patterns, outfile, known_stats, base_patterns, decoded_patterns, base_level,
                      vocabulary_probs, pattern_profile_frequency):


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


@utils.command()
@click.pass_context
@click.argument('patterns')
@click.argument('stats')
@click.argument('feature')
@click.argument('threshold', type=int)
@click.argument('outfile')
def filter_patterns(ctx, patterns, stats, feature, threshold, outfile):

    keep = set()
    with open_file(stats) as infile:
        for line in infile:
            pattern, stats = json.loads(line)
            if stats.get(feature, 0) >= threshold:
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

            with multiprocessing.Pool(processes) as p:

                for pattern, decoded_pattern in p.imap(
                        functools.partial(decode_pattern,
                                          pattern_encoder=pattern_encoder
                        ),
                        infile, chunksize=1000):

                    ctx.obj['logger'].info("Pattern")
                    pickle.dump((pattern, decoded_pattern), o)


@utils.command()
@click.pass_context
@click.argument('patterns_file')
@click.argument('pattern_stats')
@click.argument('stat')
@click.argument('n', type=int)
@click.argument('outfile')
def get_top_n(ctx, patterns_file, pattern_stats, stat, n, outfile):

    with open_file(pattern_stats) as infile:

        pattern_stats = {}

        for line in infile:
            pattern, stats = json.loads(line)
            pattern_stats[pattern] = stats

    patterns = sorted(pattern_stats.items(), key=lambda item: item[1][stat], reverse=True)
    patterns = {pattern[0]: [rank] for rank, pattern in enumerate(patterns[:n])}

    with open_file(patterns_file) as infile:

            for line in infile:

                pattern, content = json.loads(line)

                if pattern in patterns:
                    patterns[pattern].append(content)

    with open_file(outfile, 'w') as o:
        for pattern, value in sorted(patterns.items(), key=lambda item: item[1][0]):
            json.dump([pattern, value[1]], o)
            o.write("\n")


@utils.command()
@click.pass_context
@click.argument('infile')
@click.argument('encoder')
@click.argument('outfile')
def decode_pattern_collection(ctx, infile, encoder, outfile):

    with open_file(encoder, 'rb') as encoder_file:
        pattern_encoder = Base64Encoder(PatternEncoder.load(encoder_file), binary=False)

    with open_file(infile) as infile:
        with open_file(outfile, 'w') as o:

            for line in infile:

                pattern, content = json.loads(line)
                decoded_pattern = pattern_encoder.decode(pattern)

                json.dump((str(decoded_pattern), content), o)
                o.write("\n")

