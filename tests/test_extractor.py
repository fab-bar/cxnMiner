import functools

import pytest
from pytest_cases import parametrize, parametrize_with_cases, THIS_MODULE

import conllu

from cxnminer.extractor import SyntacticNGramExtractor
from cxnminer.pattern import SNGram

test_sentences = conllu.parse(
"""
# text = The quick brown fox jumps over the lazy dog.
1   The     the    DET    DT   Definite=Def|PronType=Art   4   det     _   _
2   quick   quick  ADJ    JJ   Degree=Pos                  4   amod    _   _
3   brown   brown  ADJ    JJ   Degree=Pos                  4   amod    _   _
4   fox     fox    NOUN   NN   Number=Sing                 5   nsubj   _   _
5   jumps   jump   VERB   VBZ  Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin   0   root    _   _
6   over    over   ADP    IN   _                           9   case    _   _
7   the     the    DET    DT   Definite=Def|PronType=Art   9   det     _   _
8   lazy    lazy   ADJ    JJ   Degree=Pos                  9   amod    _   _
9   dog     dog    NOUN   NN   Number=Sing                 5   nmod    _   SpaceAfter=No
10  .       .      PUNCT  .    _                           5   punct   _   _

# text = Foxes jump over the lazy dog.
1   Foxes     fox    NOUN   NN   Number=Plur                 2   nsubj   _   _
2   jump   jump   VERB   VBZ  Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin   0   root    _   _
3   over    over   ADP    IN   _                           6   case    _   _
4   the     the    DET    DT   Definite=Def|PronType=Art   6   det     _   _
5   lazy    lazy   ADJ    JJ   Degree=Pos                  6   amod    _   _
6   dog     dog    NOUN   NN   Number=Sing                 2   nmod    _   SpaceAfter=No
7  .       .      PUNCT  .    _                           2   punct   _   _

# text = The quick brown fox with the long tail jumps over the lazy dog.
1   The     the    DET    DT   Definite=Def|PronType=Art   4   det     _   _
2   quick   quick  ADJ    JJ   Degree=Pos                  4   amod    _   _
3   brown   brown  ADJ    JJ   Degree=Pos                  4   amod    _   _
4   fox     fox    NOUN   NN   Number=Sing                 9   nsubj   _   _
5   with     with    ADP   IN   _                 8   case   _   _
6   the     the    DET   DT   Definite=Def|PronType=Art    8   det   _   _
7   long     long    ADJ   JJ   Degree=Pos                 8   amod   _   _
8   tail     tail    NOUN   NN   Number=Sing                 4   nmod   _   _
9   jumps   jump   VERB   VBZ  Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin   0   root    _   _
10   over    over   ADP    IN   _                           13   case    _   _
11   the     the    DET    DT   Definite=Def|PronType=Art   13   det     _   _
12  lazy    lazy   ADJ    JJ   Degree=Pos                  13   amod    _   _
13   dog     dog    NOUN   NN   Number=Sing                 9   nmod    _   SpaceAfter=No
14  .       .      PUNCT  .    _                           9   punct   _   _

# text = We have apples, pears, oranges, and bananas.
1   We     we    PRON   PRP   Number=Plur   2   nsubj     _   _
2   have   have  VERB    VBZ   Mood=Ind|Number=Plur|Person=1|Tense=Pres|VerbForm=Fin                  0   root    _   _
3   apples   apple  NOUN    NN   Number=Plur                  2   obj    _   _
4   ,     ,    PUNCT   ,   _                 5   punct   _   _
5   pears     pear    NOUN   NN   Number=Plur                 3   conj   _   _
6   ,     ,    PUNCT   ,   _    7   punct   _   _
7   oranges     orange    NOUN   NN   Number=Plur                 3   conj   _   _
8   ,     ,    PUNCT   ,   _                 10   punct   _   _
9   and   and   SCONJ   CC  _   10   cc    _   _
10  bananas    banana   NOUN    NN   Number=Plur                           3   conj    _   _
11  .       .      PUNCT  .    _                           2   punct   _   _
"""
)

test_data = {
    "The quick brown fox jumps over the lazy dog.": {
        "1_3_None": {
            "ngrams": set([
                "The",
                "quick",
                "brown",
                "over",
                "the",
                "lazy",
                ".",
            ]),
            "number": 7
        },
        "1_3_conversion_function": {
            "ngrams": set([
                "The",
                "quick",
                "brown",
                "nsubj",
                "over",
                "the",
                "lazy",
                "nmod",
                ".",
            ]),
            "number": 9
        },
        "2_3_None": {
            "ngrams": set([]),
            "number": 0
        },
        "2_3_conversion_function": {
            "ngrams": set([]),
            "number": 0
        },
        "2_4_None": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
            ]),
            "number": 2
        },
        "2_4_conversion_function": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
                "jumps [nsubj, nmod, .]",
            ]),
            "number": 3
        },
        "2_9_None": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
            ]),
            "number": 2
        },
        "2_9_conversion_function": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
                "jumps [fox [The, quick, brown], nmod, .]",
                "jumps [nsubj, dog [over, the, lazy], .]",
                "jumps [nsubj, nmod, .]",
            ]),
            "number": 5
        },
        "2_10_None": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
                "jumps [fox [The, quick, brown], dog [over, the, lazy], .]",
            ]),
            "number": 3
        },
        "2_10_conversion_function": {
            "ngrams": set([
                "fox [The, quick, brown]",
                "dog [over, the, lazy]",
                "jumps [fox [The, quick, brown], dog [over, the, lazy], .]",
                "jumps [fox [The, quick, brown], nmod, .]",
                "jumps [nsubj, dog [over, the, lazy], .]",
                "jumps [nsubj, nmod, .]",
            ]),
            "number": 6
        },
    },
    "Foxes jump over the lazy dog.": {
        "1_3_None": {
            "ngrams": set([
                "Foxes",
                "over",
                "the",
                "lazy",
                ".",
            ]),
            "number": 5
        },
        "1_3_conversion_function": {
            "ngrams": set([
                "Foxes",
                "nsubj",
                "over",
                "the",
                "lazy",
                "nmod",
                ".",
            ]),
            "number": 7
        },
        "2_3_None": {
            "ngrams": set([]),
            "number": 0
        },
        "2_3_conversion_function": {
            "ngrams": set([]),
            "number": 0
        },
        "2_4_None": {
            "ngrams": set([
                "dog [over, the, lazy]",
            ]),
            "number": 1
        },
        "2_4_conversion_function": {
            "ngrams": set([
                "dog [over, the, lazy]",
                "jump [Foxes, nmod, .]",
                "jump [nsubj, nmod, .]",
            ]),
            "number": 3
        },
        "2_9_None": {
            "ngrams": set([
                "dog [over, the, lazy]",
                "jump [Foxes, dog [over, the, lazy], .]",
            ]),
            "number": 2
        },
        "2_9_conversion_function": {
            "ngrams": set([
                "dog [over, the, lazy]",
                "jump [Foxes, nmod, .]",
                "jump [nsubj, dog [over, the, lazy], .]",
                "jump [Foxes, dog [over, the, lazy], .]",
                "jump [nsubj, nmod, .]",
            ]),
            "number": 5
        },
        "2_10_None": {
            "ngrams": set([
                "dog [over, the, lazy]",
                "jump [Foxes, dog [over, the, lazy], .]",
            ]),
            "number": 2
        },
        "2_10_conversion_function": {
            "ngrams": set([
                "dog [over, the, lazy]",
                "jump [Foxes, nmod, .]",
                "jump [nsubj, dog [over, the, lazy], .]",
                "jump [Foxes, dog [over, the, lazy], .]",
                "jump [nsubj, nmod, .]",
            ]),
            "number": 5
        },
    },
    "The quick brown fox with the long tail jumps over the lazy dog.": {
        "1_3_None": {
            "ngrams": set([
                "The",
                "quick",
                "brown",
                "with",
                "the",
                "long",
                "over",
                "the",
                "lazy",
                ".",
            ]),
            "number": 10
        },
        "1_3_conversion_function": {
            "ngrams": set([
                "The",
                "quick",
                "brown",
                "nsubj",
                "with",
                "the",
                "long",
                "over",
                "the",
                "lazy",
                "nmod",
                ".",
            ]),
            ## nmod appears twice in the pattern list
            ## ("dog [over, the, lazy]" and "tail [with, the, long]")
            "number": 13
        },
        "2_3_None": {
            "ngrams": set([]),
            "number": 0
        },
        "2_3_conversion_function": {
            "ngrams": set([]),
            "number": 0
        },
        "2_4_None": {
            "ngrams": set([
                "tail [with, the, long]",
                "dog [over, the, lazy]",
            ]),
            "number": 2
        },
        "2_4_conversion_function": {
            "ngrams": set([
                "tail [with, the, long]",
                "dog [over, the, lazy]",
                "jumps [nsubj, nmod, .]",
            ]),
            "number": 3
        },
        "2_9_None": {
            "ngrams": set([
                "tail [with, the, long]",
                "fox [The, quick, brown, tail [with, the, long]]",
                "dog [over, the, lazy]",
            ]),
            "number": 3
        },
        "2_9_conversion_function": {
            "ngrams": set([
                "tail [with, the, long]",
                "fox [The, quick, brown, tail [with, the, long]]",
                "dog [over, the, lazy]",
                "jumps [nsubj, dog [over, the, lazy], .]",
                "jumps [nsubj, nmod, .]",
                "jumps [fox [The, quick, brown, nmod], nmod, .]",
                "fox [The, quick, brown, nmod]",
            ]),
            "number": 7
        },
        "2_10_None": {
            "ngrams": set([
                "tail [with, the, long]",
                "fox [The, quick, brown, tail [with, the, long]]",
                "dog [over, the, lazy]",
            ]),
            "number": 3
        },
        "2_10_conversion_function": {
            "ngrams": set([
                "tail [with, the, long]",
                "fox [The, quick, brown, tail [with, the, long]]",
                "dog [over, the, lazy]",
                "fox [The, quick, brown, nmod]",
                "jumps [fox [The, quick, brown, nmod], nmod, .]",
                "jumps [nsubj, dog [over, the, lazy], .]",
                "jumps [nsubj, nmod, .]",
            ]),
            "number": 7
        },
    },
    "We have apples, pears, oranges, and bananas.": {
        "1_3_None": {
            "ngrams": set([
                "We",
                ",",
                "and",
                ".",
                "bananas [,, and]",
                "oranges,",
                "pears,"
            ]),
            ## "," appears 3 times in the pattern list
            "number": 9
        },
        "1_3_conversion_function": {
            "ngrams": set([
                "We",
                ",",
                "and",
                ".",
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "obj",
                "conj"
            ]),
            ## "," appears 3 times in the pattern list
            ## conj appears 3 times in the pattern list
            "number": 13
        },
        "2_3_None": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,"
            ]),
            "number": 3
        },
        "2_3_conversion_function": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,"
            ]),
            "number": 3
        },
        "2_4_None": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,"
            ]),
            "number": 3
        },
        "2_4_conversion_function": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "have [We, obj, .]",
                "apples [conj, conj, conj]",
            ]),
            "number": 5
        },
        "2_9_None": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "apples [pears,, oranges,, bananas [,, and]]",
            ]),
            "number": 4
        },
        "2_9_conversion_function": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "apples [pears,, oranges,, bananas [,, and]]",
                "apples [conj, conj, conj]",
                "apples [pears,, conj, conj]",
                "apples [conj, oranges,, conj]",
                "apples [conj, conj, bananas [,, and]]",
                "apples [pears,, oranges,, conj]",
                "apples [pears,, conj, bananas [,, and]]",
                "apples [conj, oranges,, bananas [,, and]]",
                "have [We, obj, .]",
                "have [We, apples [conj, conj, conj], .]",
                "have [We, apples [pears,, conj, conj], .]",
                "have [We, apples [conj, oranges,, conj], .]",
                "have [We, apples [conj, conj, bananas [,, and]], .]",
                "have [We, apples [pears,, oranges,, conj], .]"
            ]),
            "number": 17
        },
        "2_10_None": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "apples [pears,, oranges,, bananas [,, and]]",
            ]),
            "number": 4
        },
        "2_10_conversion_function": {
            "ngrams": set([
                "bananas [,, and]",
                "oranges,",
                "pears,",
                "apples [pears,, oranges,, bananas [,, and]]",
                "apples [conj, conj, conj]",
                "apples [pears,, conj, conj]",
                "apples [conj, oranges,, conj]",
                "apples [conj, conj, bananas [,, and]]",
                "apples [pears,, oranges,, conj]",
                "apples [pears,, conj, bananas [,, and]]",
                "apples [conj, oranges,, bananas [,, and]]",
                "have [We, obj, .]",
                "have [We, apples [conj, conj, conj], .]",
                "have [We, apples [pears,, conj, conj], .]",
                "have [We, apples [conj, oranges,, conj], .]",
                "have [We, apples [conj, conj, bananas [,, and]], .]",
                "have [We, apples [pears,, conj, bananas [,, and]], .]",
                "have [We, apples [conj, oranges,, bananas [,, and]], .]",
                "have [We, apples [pears,, oranges,, conj], .]"
            ]),
            "number": 19
        },
    },
}



def conversion_function(tree):

    if tree.token['upostag'] == "NOUN":
        return SNGram.Tree(dict({'function': tree.token['deprel'], 'id': tree.token['id']}), [])
    else:
        return None

@parametrize(idgen="sentence={sentence.metadata[text]} min={min_max[0]}, max={min_max[1]}, conversion={conversion}",
                 sentence=test_sentences,
                 min_max=[(1,3), (2,3), (2,4), (2,9), (2,10)],
                 conversion=[None, conversion_function],
)
def case_simple_generator(sentence, min_max, conversion):

    return (
        sentence,
        SyntacticNGramExtractor(
            min_size=min_max[0], max_size=min_max[1], special_node_conversion=conversion),
        test_data[sentence.metadata['text']]["_".join([str(min_max[0]), str(min_max[1]), getattr(conversion, '__name__', 'None')])]
    )

@parametrize_with_cases("sentence,extractor,expected", cases=THIS_MODULE)
def test_extract_ngrams_numbers(sentence, extractor, expected):

    assert len([str(pattern.get_pattern_list(['form', 'function'])[0]) for pattern in extractor.extract_patterns(sentence)]) == expected['number']

@parametrize_with_cases("sentence,extractor,expected", cases=THIS_MODULE)
def test_extract_ngrams_elements(sentence, extractor, expected):

    assert set([str(pattern.get_pattern_list(['form', 'function'])[0]) for pattern in extractor.extract_patterns(sentence)]) == expected['ngrams']


@parametrize_with_cases("sentence,extractor,expected", cases=THIS_MODULE)
def test_extracting_storing_all_paths(sentence, extractor, expected):

    extractor = SyntacticNGramExtractor(
        min_size=extractor.min_size, max_size=extractor.max_size, special_node_conversion=extractor.special_node_conversion, max_open_path_size=None, max_open_path_number=None)
    assert len([str(pattern.get_pattern_list(['form', 'function'])[0]) for pattern in extractor.extract_patterns(sentence)]) == expected['number']

@parametrize_with_cases("sentence,extractor,expected", cases=THIS_MODULE)
def test_max_open_paths(sentence, extractor, expected):

    ## extract while only allowing one open path

    extractor = SyntacticNGramExtractor(
        min_size=extractor.min_size, max_size=extractor.max_size, special_node_conversion=extractor.special_node_conversion, max_open_path_number=1)
    assert extractor.extract_patterns(sentence) == []


def test_sentence_that_is_not_parseable():

    data = """
# sent_id = Liste von Unternehmen mit Namensherkunftserkl<C3><A4>rungen.Fu<C3><9F>noten.1

"""
    extractor = SyntacticNGramExtractor()
    assert extractor.extract_patterns(conllu.parse(data)[0]) == []


