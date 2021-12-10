from unittest.mock import patch

import pytest
from pytest_cases import case, get_case_tags, parametrize_with_cases, THIS_MODULE

import conllu
from spacy.vocab import Vocab
from spacy.tokens import Doc

from cxnminer.utils import wikiannotator


@case(tags=['dev'])
def case_spacy_german():

    data = """
# sent_id = testtext.1
1   Dies     Dies    PRON    PDS   _   2   sb     _   _
2   ist   sein  AUX    VAFIN   _                  0   ROOT    _   _
3   ein   einen  DET    ART   _                  4   nk    _   _
4   Test     Test    NOUN   NN   _                 2   pd   _   _
5   .     .    PUNCT   $.   _                 2   punct   _   _

"""

    result = conllu.parse(data)

    return (
        wikiannotator.Annotator.createAnnotator('spacy', {'model_name': 'de_core_news_sm'}),
        wikiannotator.SpacyAnnotator,
        {
            'text': 'Dies ist ein Test.',
            'textname': 'testtext',
            'parse': result
        }
    )

@patch('spacy.load')
def case_spacy(spacy_load_mock):


    import re
    data = re.sub(
        " +", "\t",
        """
# sent_id = testtext.1
1   Dies     Dies    PRON    PDS   _   2   sb     _   _
2   ist   sein  AUX    VAFIN   _                  0   ROOT    _   _
3   ein   einen  DET    ART   _                  4   nk    _   _
4   Test     Test    NOUN   NN   _                 2   pd   _   _
5   .     .    PUNCT   $.   _                 2   punct   _   _

""")

    result = conllu.parse(data)

    words = ["Dies", "ist", "ein", "Test", "."]
    vocab = Vocab(strings=words)

    heads = [1, 1, 3, 1, 1]
    tags = ["PDS", "VAFIN", "ART", "NN", "$."]
    pos = ["PRON", "AUX", "DET", "NOUN", "PUNCT"]
    lemmas = ["Dies", "sein", "einen", "Test", "."]
    deps = ["sb", "ROOT", "nk", "pd", "punct"]

    doc = Doc(vocab, words, pos=pos, tags=tags, lemmas=lemmas, deps=deps, heads=heads)

    spacy_annotator = spacy_load_mock.return_value
    spacy_annotator.return_value = doc

    annotator = wikiannotator.Annotator.createAnnotator('spacy', {'model_name': 'model_name'})
    spacy_load_mock.assert_called_once_with('model_name')

    return (
        annotator, wikiannotator.SpacyAnnotator,
        {
            'text': 'Dies ist ein Test.',
            'textname': 'testtext',
            'parse': result
        }
    )


## cases tagged with 'dev' need specific packages - test for availability
def language_model_filter(case):
    if 'dev' in get_case_tags(case):
        try:
            import de_core_news_sm
            return True
        except ImportError:
            return False
    else:
        return True

@parametrize_with_cases("annotator,expected_class,test_data", cases=THIS_MODULE, filter=language_model_filter)
def test_factory(annotator, expected_class, test_data):

    assert isinstance(annotator, expected_class)

def test_factory_not_implemented():

    with pytest.raises(ValueError):

        wikiannotator.Annotator.createAnnotator('not_implemented', {})


@parametrize_with_cases("annotator,expected_class,test_data", cases=THIS_MODULE, filter=language_model_filter)
def test_annotate_text(annotator, expected_class, test_data):

    result = annotator.annotate_text(test_data['text'], test_data['textname'], lambda x: False)

    for tok_t, tok_p in zip(test_data['parse'][0], result[0]):
        print(tok_t, tok_p)

    assert result == test_data['parse']



@parametrize_with_cases("annotator,expected_class,test_data", cases=THIS_MODULE, filter=language_model_filter)
def test_annotate_text_filter(annotator, expected_class, test_data):

    result = annotator.annotate_text("Some text. Does not matter.", "The name", lambda x: True)

    assert result == []
