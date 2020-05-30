import collections
import collections.abc
import functools
import itertools
import json
import logging
import logging.config

import click
import conllu

from cxnminer.extractor import SyntacticNGramExtractor
from cxnminer.pattern import SNGram
from cxnminer.pattern_encoder import Base64Encoder, HuffmanEncoder
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

        base_pattern_encoded = encode_pattern(base_pattern)

        base_pattern_positions = ",".join(
            [str(element) for element in tpattern.get_base_pattern('id').get_element_list()])

        for pattern in tpattern.get_pattern_list(frozenset(['lemma', 'upostag', 'np_function'])):

            ### only keep patterns that consist of given vocabulary entries
            if known is None or all(
                    [getattr(element, "form", element) in known.get(
                        getattr(element, "level", "__special__"), {})
                     for element in pattern.get_element_list()]):
                if unknown is None or not any((unknown == getattr(element, "form", None) for element in pattern.get_element_list())):
                    if pattern != base_pattern:
                        this_pattern_list.append((False, encode_pattern(pattern), base_pattern_encoded))

        if this_pattern_list:
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
def extract_patterns(ctx, infile, outfile_patterns, outfile_base,
                     word_level, phrase_tags, encoded_dictionaries, max_pattern_size, keep_only_dict_words, skip_unknown):

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

    patterns = collections.defaultdict(set)
    base_patterns = collections.defaultdict(list)


    with open_file(infile) as infile:

        for sentence_patterns in map(
                functools.partial(
                    pattern_extraction, extractor=extractor, word_level=word_level, logger=ctx.obj['logger'],
                    unknown=unknown, known=known),
                enumerate(conllu.parse_incr(infile))):

            for is_base_pattern, pattern, content in sentence_patterns:
                if not is_base_pattern:
                    if content not in base_patterns:
                        base_patterns[content] = ([])
                    patterns[pattern].add(content)
                else:
                    base_patterns[pattern].append(content)


    for pattern in patterns.keys():
        patterns[pattern] = list(patterns[pattern])
    with open_file(outfile_patterns, 'w') as outfile:
        json.dump(patterns, outfile)

    with open_file(outfile_base, 'w') as outfile:
        json.dump(base_patterns, outfile)

