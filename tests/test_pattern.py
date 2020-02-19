import pytest
from pytest_cases import cases_data, THIS_MODULE

import conllu

from cxnminer.pattern import TokenSNGram

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
        "str": "fox [The, quick, brown]"}


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
        "str": "dog [over, the, lazy]"}


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
        "str": "jumps [fox [The, quick, brown], dog [over, the, lazy], .]"}


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
        "str": "y di par [un, de]"}

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
        "str": "y di [le, par, de_mala_gana]"}



@cases_data(module=THIS_MODULE)
def test_sngram_length(case_data):

    sngram, expected = case_data.get()

    assert sngram.length == expected['length']

@cases_data(module=THIS_MODULE)
def test_sngram_str(case_data):

    sngram, expected = case_data.get()

    assert str(sngram.get_pattern_list(['form'])[0]) == expected['str']


@cases_data(module=THIS_MODULE)
@pytest.mark.parametrize("features", [(['form', 'upostag'])])
def test_tsngram_pattern_list(case_data, features):

    sngram, expected = case_data.get()

    assert len(sngram.get_pattern_list(features)) == len(features)**sngram.length
