import filecmp
import json
import os
import os.path

import pytest
from click.testing import CliRunner

from cxnminer.pattern import PatternElement
from cxnminer.pattern_encoder import PatternEncoder, Base64Encoder
from cxnminer.cli import main

expected_patterns_without_phrase = {
    # "fox [The, quick, brown]"
    "NOUN [the, quick, brown]": {"fox [the, quick, brown]"},
    "fox [DET, quick, brown]": {"fox [the, quick, brown]"},
    "fox [the, ADJ, brown]": {"fox [the, quick, brown]"},
    "fox [the, quick, ADJ]": {"fox [the, quick, brown]"},

    "NOUN [DET, quick, brown]": {"fox [the, quick, brown]"},
    "NOUN [the, ADJ, brown]": {"fox [the, quick, brown]"},
    "NOUN [the, quick, ADJ]": {"fox [the, quick, brown]"},
    "fox [DET, ADJ, brown]": {"fox [the, quick, brown]"},
    "fox [DET, quick, ADJ]": {"fox [the, quick, brown]"},
    "fox [the, ADJ, ADJ]": {"fox [the, quick, brown]"},

    "NOUN [DET, ADJ, brown]": {"fox [the, quick, brown]"},
    "NOUN [DET, quick, ADJ]": {"fox [the, quick, brown]"},
    "NOUN [the, ADJ, ADJ]": {"fox [the, quick, brown]"},
    "fox [DET, ADJ, ADJ]": {"fox [the, quick, brown]"},

    "NOUN [DET, ADJ, ADJ]": {"fox [the, quick, brown]"},

    # "dog [over, the, lazy]"
    "NOUN [over, the, lazy]": {"dog [over, the, lazy]"},
    "dog [ADP, the, lazy]": {"dog [over, the, lazy]"},
    "dog [over, DET, lazy]": {"dog [over, the, lazy]"},
    "dog [over, the, ADJ]": {"dog [over, the, lazy]"},

    "NOUN [ADP, the, lazy]": {"dog [over, the, lazy]"},
    "NOUN [over, DET, lazy]": {"dog [over, the, lazy]"},
    "NOUN [over, the, ADJ]": {"dog [over, the, lazy]"},
    "dog [ADP, DET, lazy]": {"dog [over, the, lazy]"},
    "dog [ADP, the, ADJ]": {"dog [over, the, lazy]"},
    "dog [over, DET, ADJ]": {"dog [over, the, lazy]"},

    "NOUN [ADP, DET, lazy]": {"dog [over, the, lazy]"},
    "NOUN [over, DET, ADJ]": {"dog [over, the, lazy]"},
    "dog [ADP, DET, ADJ]": {"dog [over, the, lazy]"},

    # "tail [with, the, long]"
    "NOUN [__unknown__, the, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [ADP, the, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [__unknown__, DET, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [__unknown__, the, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},

    "NOUN [ADP, the, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "NOUN [__unknown__, DET, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "NOUN [__unknown__, the, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [ADP, DET, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [ADP, the, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [__unknown__, DET, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},

    "NOUN [ADP, DET, __unknown__]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "NOUN [__unknown__, DET, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},
    "__unknown__ [ADP, DET, ADJ]": {"__unknown__ [__unknown__, the, __unknown__]"},

    # "dog [over, the, lazy]"
    # "tail [with, the, long]",
    "NOUN [ADP, the, ADJ]": {"dog [over, the, lazy]", "__unknown__ [__unknown__, the, __unknown__]"},
    "NOUN [ADP, DET, ADJ]": {"dog [over, the, lazy]", "__unknown__ [__unknown__, the, __unknown__]"},

    # "bananas [,, and]"
    "NOUN [,, __unknown__]": {"__unknown__ [,, __unknown__]"},
    "__unknown__ [PUNCT, __unknown__]": {"__unknown__ [,, __unknown__]"},
    "__unknown__ [,, __unknown__]": {"__unknown__ [,, __unknown__]"},
    "NOUN [PUNCT, __unknown__]": {"__unknown__ [,, __unknown__]"},

    # "oranges,"
    # "pears,"
    "NOUN,": {"__unknown__,"},
    "__unknown__ PUNCT": {"__unknown__,"},
    "NOUN PUNCT": {"__unknown__,"},
}

expected_patterns_with_phrase = {
    # "jumps [nsubj, nmod, .]"
    "jump [nsubj, nmod, .]": {
        "jump [fox [the, quick, brown], dog [over, the, lazy], .]",
        "jump [fox, dog [over, the, lazy], .]",
        "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]",
    },
    "VERB [nsubj, nmod, .]": {
        "jump [fox [the, quick, brown], dog [over, the, lazy], .]",
        "jump [fox, dog [over, the, lazy], .]",
        "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]",
    },
    "jump [nsubj, nmod, PUNCT]": {
        "jump [fox [the, quick, brown], dog [over, the, lazy], .]",
        "jump [fox, dog [over, the, lazy], .]",
        "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]",
    },
    "VERB [nsubj, nmod, PUNCT]": {
        "jump [fox [the, quick, brown], dog [over, the, lazy], .]",
        "jump [fox, dog [over, the, lazy], .]",
        "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]",
    },

    # "jump [Foxes, nmod, .]"
    "jump [fox, nmod, .]": {"jump [fox, dog [over, the, lazy], .]"},
    "VERB [fox, nmod, .]": {"jump [fox, dog [over, the, lazy], .]"},
    "jump [NOUN, nmod, .]": {"jump [fox, dog [over, the, lazy], .]"},
    "jump [fox, nmod, PUNCT]": {"jump [fox, dog [over, the, lazy], .]"},
    "VERB [NOUN, nmod, .]": {"jump [fox, dog [over, the, lazy], .]"},
    "VERB [fox, nmod, PUNCT]": {"jump [fox, dog [over, the, lazy], .]"},
    "jump [NOUN, nmod, PUNCT]": {"jump [fox, dog [over, the, lazy], .]"},
    "VERB [NOUN, nmod, PUNCT]": {"jump [fox, dog [over, the, lazy], .]"},

    # "have [We, obj, .]"
    "__unknown__ [__unknown__, __unknown__, .]": {
        "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"
    },
    "VERB [__unknown__, __unknown__, .]": {
        "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"
    },
    "__unknown__ [__unknown__, __unknown__, PUNCT]": {
        "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"
    },
    "VERB [__unknown__, __unknown__, PUNCT]": {
        "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"
    },

    # "apples [conj, conj, conj]"
    "__unknown__ [conj, conj, conj]": {
        "__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"
    },
    "NOUN [conj, conj, conj]": {
        "__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"
    }
}


expected_basepatterns_without_phrase = {
    "fox [the, quick, brown]": [1],
    "dog [over, the, lazy]": [1,2,3],
    "__unknown__ [__unknown__, the, __unknown__]": [3],
    "__unknown__ [,, __unknown__]": [4],
    "__unknown__,": [4,4]
}

expected_basepatterns_with_phrase = {
    "jump [fox [the, quick, brown], dog [over, the, lazy], .]": [1],
    "jump [fox, dog [over, the, lazy], .]": [2],
    "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]": [3],
    "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]": [4],
    "__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]": [4]
}

@pytest.mark.parametrize("parameters,expected_patterns,expected_basepatterns", [
    ([], expected_patterns_without_phrase, expected_basepatterns_without_phrase),
    (
        ["NOUN"],
        {**expected_patterns_without_phrase, **expected_patterns_with_phrase},
        {**expected_basepatterns_without_phrase, **expected_basepatterns_with_phrase}
    ),
])
def test_extract_patterns_with_phrases(parameters, expected_patterns, expected_basepatterns):

    infile_path = os.path.abspath('example_data/example_data_encoded.conllu')
    dictfile_path = os.path.abspath('example_data/example_data_dict_filtered_encoded.json')

    encoder_path = os.path.abspath('example_data/example_data_encoder')

    runner = CliRunner()
    with runner.isolated_filesystem():

        patterns_filename = 'patterns.json'
        base_filename = 'base.json'

        result = runner.invoke(main, [
            'extract-patterns',
            infile_path,
            patterns_filename,
            base_filename,
            'lemma'] + parameters +
            [
                '--encoded_dictionaries',
                dictfile_path
            ]
        )

        patterns = json.load(open(patterns_filename))
        basepatterns = json.load(open(base_filename))

        encoder = Base64Encoder(PatternEncoder.load(open(encoder_path, 'rb')))
        patterns = {str(encoder.decode(pattern)): set([str(encoder.decode(base)) for base in bases]) for pattern, bases in patterns.items()}
        basepatterns = {str(encoder.decode(pattern)): content for pattern, content in basepatterns.items()}

        assert patterns == expected_patterns

        assert basepatterns == expected_basepatterns


@pytest.mark.parametrize("tofile", [True, False])
def test_extract_patterns_with_logging(tofile):

    infile_path = os.path.abspath('example_data/example_data_encoded.conllu')
    dictfile_path = os.path.abspath('example_data/example_data_dict_filtered_encoded.json')

    encoder_path = os.path.abspath('example_data/example_data_encoder')

    runner = CliRunner()
    with runner.isolated_filesystem():

        patterns_filename = 'patterns.json'
        base_filename = 'base.json'
        log_filename = 'log.txt'

        logging_config = {
            "handlers": {
                "h": {
                    "level": "DEBUG",
                    "class": "logging.FileHandler",
                    "filename": log_filename,
                    "mode": "w",
                    "formatter": "f"
                }
            }
        }

        if tofile:
            logging_config_file = 'log_config.json'
            with open(logging_config_file, 'w') as outfile:
                json.dump(logging_config, outfile)
            logging_config = logging_config_file
        else:
            logging_config = json.dumps(logging_config)

        result = runner.invoke(main, [
            '--logging_config',
            logging_config,
            'extract-patterns',
            infile_path,
            patterns_filename,
            base_filename,
            'lemma',
            '--encoded_dictionaries',
            dictfile_path
        ])

        assert os.path.isfile(log_filename)


############################ tests for scripts in bin

def test_extract_vocabulary():

    infile_path = os.path.abspath('example_data/example_data.conllu')
    expected_outfile_path = os.path.abspath('example_data/example_data_dict.json')
    script_file = os.path.abspath('bin/extract_vocabulary')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_dict.json"

        os.system(script_file + " " + infile_path + " " + outfile + " lemma upostag np_function")

        expected_dict = json.load(open(expected_outfile_path, 'r'))
        result_dict = json.load(open(outfile, 'r'))

    assert result_dict == expected_dict

def test_filter_vocabulary():

    infile_path = os.path.abspath('example_data/example_data_dict.json')
    expected_outfile_path = os.path.abspath('example_data/example_data_dict_filtered.json')
    script_file = os.path.abspath('bin/filter_vocabulary')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_dict_filtered.json"

        os.system(script_file + " " + infile_path + " " + outfile + " 2")

        expected_dict = json.load(open(expected_outfile_path, 'r'))
        result_dict = json.load(open(outfile, 'r'))

    assert result_dict == expected_dict

def test_create_encoder():

    infile_path = os.path.abspath('example_data/example_data_dict_filtered.json')
    script_file = os.path.abspath('bin/create_encoder')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_encoder"

        exit_status = os.system(script_file + " " + infile_path + " " + outfile)

        encoder = Base64Encoder(PatternEncoder.load(open(outfile, 'rb')))
        dict_ = json.load(open(infile_path, 'r'))

        pattern_elements = [PatternElement(word, level) for level, elements in dict_.items() for word in elements.keys()]
        results = [
            encoder.decode(encoder.encode_item(pe)).get_element_list()[0] == pe for pe in pattern_elements
        ]

    assert all(results)

def test_encode_vocabulary():

    infile_path = os.path.abspath('example_data/example_data_dict_filtered.json')
    encoder_path = os.path.abspath('example_data/example_data_encoder')
    script_file = os.path.abspath('bin/encode_vocabulary')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_dict_filtered_encoded.json"

        os.system(script_file + " " + infile_path + " " + outfile + " " + encoder_path)

        encoder = Base64Encoder(PatternEncoder.load(open(encoder_path, 'rb')))

        result_dict = json.load(open(outfile, 'r'))

        results = [(level, decoded, encoder.decode(encoded).get_element_list()) for level, elements in result_dict.items() for decoded, encoded in elements.items()]
        results = [len(pe) == 1 and pe[0].level == level and pe[0].form == word for level, word, pe in results]

    assert all(results)

def test_encode_corpus():

    infile_path = os.path.abspath('example_data/example_data.conllu')
    encoded_dict_path = os.path.abspath('example_data/example_data_dict_filtered_encoded.json')
    encoder_path = os.path.abspath('example_data/example_data_encoder')
    expected_outfile_path = os.path.abspath('example_data/example_data_encoded.conllu')
    script_file = os.path.abspath('bin/encode_corpus')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_encoded.conllu"

        os.system(script_file + " " + infile_path + " " + outfile + " " + encoded_dict_path + " lemma upostag np_function --encoder_file " + encoder_path)


        assert filecmp.cmp(outfile, expected_outfile_path, shallow=False)
