import pytest
from pytest_cases import parametrize_with_cases, THIS_MODULE

import conllu

from cxnminer.pattern import PatternElement, TokenSNGram, SNGram

def case_fox():

    data = """
# text = The quick brown fox
1   The     the    DET    DT   Definite=Def|PronType=Art   4   det     _   _
2   quick   quick  ADJ    JJ   Degree=Pos                  4   amod    _   _
3   brown   brown  ADJ    JJ   Degree=Pos                  4   amod    _   _
4   fox     fox    NOUN   NN   Number=Sing                 0   nsubj   _   _

"""

    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 4,
        "str": "fox [The, quick, brown]",
        "repr": [
            PatternElement('fox', 'form', 4),
            SNGram.LEFT_BRACKET,
            PatternElement('The', 'form', 1),
            SNGram.COMMA,
            PatternElement('quick', 'form', 2),
            SNGram.COMMA,
            PatternElement('brown', 'form', 3),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form [ form , form , form ]"])
    }


def case_dog():

    data = """
# text = over the lazy dog
6   over    over   ADP    IN   _                           9   case    _   _
7   the     the    DET    DT   Definite=Def|PronType=Art   9   det     _   _
8   lazy    lazy   ADJ    JJ   Degree=Pos                  9   amod    _   _
9   dog     dog    NOUN   NN   Number=Sing                 0   nmod    _   SpaceAfter=No

"""
    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 4,
        "str": "dog [over, the, lazy]",
        "repr": [
            PatternElement('dog', 'form', 9),
            SNGram.LEFT_BRACKET,
            PatternElement('over', 'form', 6),
            SNGram.COMMA,
            PatternElement('the', 'form', 7),
            SNGram.COMMA,
            PatternElement('lazy', 'form', 8),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form [ form , form , form ]"])
    }


def case_jumps():

    data = """
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

"""
    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 10,
        "str": "jumps [fox [The, quick, brown], dog [over, the, lazy], .]",
        "repr": [
            PatternElement('jumps', 'form', 5),
            SNGram.LEFT_BRACKET,
            PatternElement('fox', 'form', 4),
            SNGram.LEFT_BRACKET,
            PatternElement('The', 'form', 1),
            SNGram.COMMA,
            PatternElement('quick', 'form', 2),
            SNGram.COMMA,
            PatternElement('brown', 'form', 3),
            SNGram.RIGHT_BRACKET,
            SNGram.COMMA,
            PatternElement('dog', 'form', 9),
            SNGram.LEFT_BRACKET,
            PatternElement('over', 'form', 6),
            SNGram.COMMA,
            PatternElement('the', 'form', 7),
            SNGram.COMMA,
            PatternElement('lazy', 'form', 8),
            SNGram.RIGHT_BRACKET,
            SNGram.COMMA,
            PatternElement('.', 'form', 10),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form [ form [ form , form , form ] , form [ form , form , form ] , form ]"])
    }

def case_jumps_phrases():

    tree = SNGram.Tree(
        {'form': 'jumps', 'id': 5},
        [
            SNGram.Tree(
                {'form': 'nsubj', 'id': 4}, [],
                SNGram.Tree({'form': 'fox', 'id': 4}, [
                    SNGram.Tree({'form': 'The', 'id': 1}, []),
                    SNGram.Tree({'form': 'quick', 'id': 2}, []),
                    SNGram.Tree({'form': 'brown', 'id': 3}, []),
                ])
            ),
            SNGram.Tree(
                {'form': 'nmod', 'id': 9}, [],
                SNGram.Tree({'form': 'dog', 'id': 9}, [
                    SNGram.Tree({'form': 'over', 'id': 6}, []),
                    SNGram.Tree({'form': 'the', 'id': 7}, []),
                    SNGram.Tree({'form': 'lazy', 'id': 8}, []),
                ])
            ),
            SNGram.Tree(
                {'form': '.', 'id': 10}, []
            )
        ]
    )

    return TokenSNGram(tree), {
        "length": 4,
        "str": "jumps [nsubj, nmod, .]",
        "repr": [
            PatternElement('jumps', 'form', 5),
            SNGram.LEFT_BRACKET,
            PatternElement('nsubj', 'form', 4),
            SNGram.COMMA,
            PatternElement('nmod', 'form', 9),
            SNGram.COMMA,
            PatternElement('.', 'form', 10),
            SNGram.RIGHT_BRACKET
        ],
        "repr_full": [
            PatternElement('jumps', 'form', 5),
            SNGram.LEFT_BRACKET,
            PatternElement('fox', 'form', 4),
            SNGram.LEFT_BRACKET,
            PatternElement('The', 'form', 1),
            SNGram.COMMA,
            PatternElement('quick', 'form', 2),
            SNGram.COMMA,
            PatternElement('brown', 'form', 3),
            SNGram.RIGHT_BRACKET,
            SNGram.COMMA,
            PatternElement('dog', 'form', 9),
            SNGram.LEFT_BRACKET,
            PatternElement('over', 'form', 6),
            SNGram.COMMA,
            PatternElement('the', 'form', 7),
            SNGram.COMMA,
            PatternElement('lazy', 'form', 8),
            SNGram.RIGHT_BRACKET,
            SNGram.COMMA,
            PatternElement('.', 'form', 10),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form [ form , form , form ]"])
    }

def case_changed_special():

    data = """
# text = The quick brown fox
1   The     the    DET    DT   Definite=Def|PronType=Art   4   det     _   _
2   quick   quick  ADJ    JJ   Degree=Pos                  4   amod    _   _
3   brown   brown  ADJ    JJ   Degree=Pos                  4   amod    _   _
4   fox     fox    NOUN   NN   Number=Sing                 0   nsubj   _   _

"""

    return TokenSNGram(conllu.parse_tree(data)[0], left_bracket="(", right_bracket=")", comma="_"), {
        "length": 4,
        "str": "fox (The_ quick_ brown)",
        "repr": [
            PatternElement('fox', 'form', 4),
            "(",
            PatternElement('The', 'form', 1),
            "_",
            PatternElement('quick', 'form', 2),
            "_",
            PatternElement('brown', 'form', 3),
            ")"
        ],
        "profiles": set(["form ( form _ form _ form )"])
    }


## Examples from Grigori Sidorov (2013): Non-linear construction of n-grams in computational linguistics

def case_sidorov1():

    data = """
# text = y le di un par de vueltas de_mala_gana
1   y    _  _  _  _  0  _  _  _
2   di   _  _  _  _  1  _  _  _
3   un   _  _  _  _  4  _  _  _
4   par  _  _  _  _  2  _  _  _
5   de   _  _  _  _  4  _  _  _

"""
    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 5,
        "str": "y di par [un, de]",
        "repr": [
            PatternElement('y', 'form', 1),
            PatternElement('di', 'form', 2),
            PatternElement('par', 'form', 4),
            SNGram.LEFT_BRACKET,
            PatternElement('un', 'form', 3),
            SNGram.COMMA,
            PatternElement('de', 'form', 5),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form form form [ form , form ]"])
    }

def case_sidorov2():

    data = """
# text = y le di un par de vueltas de_mala_gana
1   y              _  _  _  _  0  _  _  _
2   le             _  _  _  _  3  _  _  _
3   di             _  _  _  _  1  _  _  _
4   par            _  _  _  _  3  _  _  _
5   de_mala_gana   _  _  _  _  3  _  _  _

"""
    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 5,
        "str": "y di [le, par, de_mala_gana]",
        "repr": [
            PatternElement('y', 'form', 1),
            PatternElement('di', 'form', 3),
            SNGram.LEFT_BRACKET,
            PatternElement('le', 'form', 2),
            SNGram.COMMA,
            PatternElement('par', 'form', 4),
            SNGram.COMMA,
            PatternElement('de_mala_gana', 'form', 5),
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form form [ form , form , form ]"])
    }

def case_apples():

    data = """
# text = apples, pears, oranges, and bananas.
1   apples   apple  NOUN    NN   Number=Plur                  0   obj    _   _
2   ,     ,    PUNCT   ,   _                 3   punct   _   _
3   pears     pear    NOUN   NN   Number=Plur                 1   conj   _   _
4   ,     ,    PUNCT   ,   _    5   punct   _   _
5   oranges     orange    NOUN   NN   Number=Plur                 1   conj   _   _
6   ,     ,    PUNCT   ,   _                 8   punct   _   _
7   and   and   SCONJ   CC  _   8   cc    _   _
8   bananas    banana   NOUN    NN   Number=Plur                           1   conj    _   _

"""
    return TokenSNGram(conllu.parse_tree(data)[0]), {
        "length": 8,
        "str": "apples [pears,, oranges,, bananas [,, and]]",
        "repr": [
            PatternElement('apples', 'form', 1),
            SNGram.LEFT_BRACKET,
            PatternElement('pears', 'form', 3),
            PatternElement(',', 'form', 2),
            SNGram.COMMA,
            PatternElement('oranges', 'form', 5),
            PatternElement(',', 'form', 4),
            SNGram.COMMA,
            PatternElement('bananas', 'form', 8),
            SNGram.LEFT_BRACKET,
            PatternElement(',', 'form', 6),
            SNGram.COMMA,
            PatternElement('and', 'form', 7),
            SNGram.RIGHT_BRACKET,
            SNGram.RIGHT_BRACKET
        ],
        "profiles": set(["form [ form form , form form , form [ form , form ] ]"])
    }

@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_sngram_length(sngram, expected):

    assert sngram.length == expected['length']

@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_sngram_str(sngram, expected):

    assert str(sngram.get_pattern_list(['form'])[0]) == expected['str']

@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_sngram_element_list(sngram, expected):

    assert sngram.get_pattern_list(['form'])[0].get_element_list() == expected['repr']

@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_sngram_from_element_list(sngram, expected):

    assert sngram.get_pattern_list(['form'])[0] == SNGram.from_element_list(expected['repr'],
                                                                            left_bracket=sngram.LEFT_BRACKET,
                                                                            right_bracket=sngram.RIGHT_BRACKET,
                                                                            comma=sngram.COMMA)

@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
@pytest.mark.parametrize("features", [(['form', 'upostag'])])
def test_tsngram_pattern_list(sngram, expected, features):

    assert len(sngram.get_pattern_list(features)) == len(features)**sngram.length


@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
@pytest.mark.parametrize("feature", ['form'])
def test_tsngram_pattern_list(sngram, expected, feature):

    assert sngram.get_base_pattern(feature).get_element_list() == expected.get(
        'repr_full',
        expected['repr']
    )


@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_tsngram_get_pattern_profile(sngram, expected):

    with pytest.raises(TypeError):
        sngram.get_pattern_profile()


@parametrize_with_cases("sngram,expected", cases=THIS_MODULE)
def test_sngram_get_pattern_profile(sngram, expected):

    for pattern in sngram.get_pattern_list(['form']):

        assert pattern.get_pattern_profile(False) in expected.get("profiles", set())

