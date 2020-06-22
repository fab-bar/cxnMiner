import filecmp
import json
import os
import os.path

import pytest
from click.testing import CliRunner

from cxnminer.pattern import PatternElement
from cxnminer.pattern_encoder import PatternEncoder, Base64Encoder
from cxnminer.cli import main

basepatterns_with_tokens = {
    "dog [over, the, lazy]":
        "{'lemma': 'dog', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +       "["
    +       "{'lemma': 'over', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'lazy', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "fox [the, quick, brown]":
        "{'lemma': 'fox', 'upostag': 'NOUN', 'np_function': 'nsubj'} "
    +       "["
    +       "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'quick', 'upostag': 'ADJ', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'brown', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "__unknown__ [__unknown__, the, __unknown__]":
        "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "__unknown__,":
        "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +       "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}",
    "__unknown__ [,, __unknown__]":
        "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +       "["
    +       "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upostag': '__unknown__', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox [the, quick, brown], dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upostag': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upostag': 'NOUN', 'np_function': 'nsubj'} "
    +           "["
    +           "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'quick', 'upostag': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'brown', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': 'dog', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +           "{'lemma': 'over', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'lazy', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': '.', 'upostag': 'PUNCT', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox, dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upostag': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upostag': 'NOUN', 'np_function': 'nsubj'}, "
    +       "{'lemma': 'dog', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +           "{'lemma': 'over', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'lazy', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': '.', 'upostag': 'PUNCT', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upostag': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upostag': 'NOUN', 'np_function': 'nsubj'} "
    +           "["
    +           "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'quick', 'upostag': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'brown', 'upostag': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +               "["
    +               "{'lemma': '__unknown__', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +               "{'lemma': '__unknown__', 'upostag': 'ADJ', 'np_function': '__unknown__'}"
    +               "]"
    +           "], "
    +       "{'lemma': 'dog', 'upostag': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +               "{'lemma': 'over', 'upostag': 'ADP', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'the', 'upostag': 'DET', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'lazy', 'upostag': 'ADJ', 'np_function': '__unknown__'}], "
    +               "{'lemma': '.', 'upostag': 'PUNCT', 'np_function': '__unknown__'}"
    +           "]",
    "__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]":
        "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +           "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +           "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +           "["
    +           "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upostag': '__unknown__', 'np_function': '__unknown__'}"
    +           "]"
    +       "]",
    "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]":
        "{'lemma': '__unknown__', 'upostag': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upostag': '__unknown__', 'np_function': 'nsubj'}, "
    +       "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': '__unknown__'} "
    +           "["
    +           "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +               "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +               "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upostag': 'NOUN', 'np_function': 'conj'} "
    +               "["
    +               "{'lemma': ',', 'upostag': 'PUNCT', 'np_function': '__unknown__'}, "
    +               "{'lemma': '__unknown__', 'upostag': '__unknown__', 'np_function': '__unknown__'}"
    +               "]"
    +           "], "
    +       "{'lemma': '.', 'upostag': 'PUNCT', 'np_function': '__unknown__'}"
    +       "]",
}

expected_patterns_without_phrase_and_unknown = {
    # "fox [The, quick, brown]"
    "NOUN [the, quick, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [DET, quick, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [the, ADJ, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [the, quick, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},

    "NOUN [DET, quick, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "NOUN [the, ADJ, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "NOUN [the, quick, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [DET, ADJ, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [DET, quick, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [the, ADJ, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},

    "NOUN [DET, ADJ, brown]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "NOUN [DET, quick, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "NOUN [the, ADJ, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},
    "fox [DET, ADJ, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},

    "NOUN [DET, ADJ, ADJ]": {basepatterns_with_tokens["fox [the, quick, brown]"]},

    # "dog [over, the, lazy]"
    "NOUN [over, the, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [ADP, the, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [over, DET, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [over, the, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},

    "NOUN [ADP, the, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "NOUN [over, DET, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "NOUN [over, the, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [ADP, DET, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [ADP, the, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [over, DET, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},

    "NOUN [ADP, DET, lazy]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "NOUN [over, DET, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},
    "dog [ADP, DET, ADJ]": {basepatterns_with_tokens["dog [over, the, lazy]"]},

    # "dog [over, the, lazy]"
    # "tail [with, the, long]",
    "NOUN [ADP, the, ADJ]": {
        basepatterns_with_tokens["dog [over, the, lazy]"],
        basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
    "NOUN [ADP, DET, ADJ]": {
        basepatterns_with_tokens["dog [over, the, lazy]"],
        basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},

    # "oranges,"
    # "pears,"
    "NOUN,": {basepatterns_with_tokens["__unknown__,"]},
    "NOUN PUNCT": {basepatterns_with_tokens["__unknown__,"]},
}

expected_patterns_without_phrase = {
    **expected_patterns_without_phrase_and_unknown,
    **{
        # "tail [with, the, long]"
        "NOUN [__unknown__, the, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [ADP, the, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [__unknown__, DET, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [__unknown__, the, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},

        "NOUN [ADP, the, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "NOUN [__unknown__, DET, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "NOUN [__unknown__, the, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [ADP, DET, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [ADP, the, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [__unknown__, DET, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},

        "NOUN [ADP, DET, __unknown__]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "NOUN [__unknown__, DET, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},
        "__unknown__ [ADP, DET, ADJ]": {basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]},

        # "bananas [,, and]"
        "NOUN [,, __unknown__]": {basepatterns_with_tokens["__unknown__ [,, __unknown__]"]},
        "__unknown__ [PUNCT, __unknown__]": {basepatterns_with_tokens["__unknown__ [,, __unknown__]"]},
        "__unknown__ [,, __unknown__]": {basepatterns_with_tokens["__unknown__ [,, __unknown__]"]},
        "NOUN [PUNCT, __unknown__]": {basepatterns_with_tokens["__unknown__ [,, __unknown__]"]},

        # "oranges,"
        # "pears,"
        "__unknown__ PUNCT": {basepatterns_with_tokens["__unknown__,"]},
    }
}


expected_patterns_with_phrase = {
    # "jumps [nsubj, nmod, .]"
    "jump [nsubj, nmod, .]": {
        basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"],
    },
    "VERB [nsubj, nmod, .]": {
        basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"],
    },
    "jump [nsubj, nmod, PUNCT]": {
        basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"],
    },
    "VERB [nsubj, nmod, PUNCT]": {
        basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"],
        basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"],
    },

    # "jump [Foxes, nmod, .]"
    "jump [fox, nmod, .]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "VERB [fox, nmod, .]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "jump [NOUN, nmod, .]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "jump [fox, nmod, PUNCT]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "VERB [NOUN, nmod, .]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "VERB [fox, nmod, PUNCT]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "jump [NOUN, nmod, PUNCT]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},
    "VERB [NOUN, nmod, PUNCT]": {basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]},

    # "have [We, obj, .]"
    "__unknown__ [__unknown__, __unknown__, .]": {
        basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]
    },
    "VERB [__unknown__, __unknown__, .]": {
        basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]
    },
    "__unknown__ [__unknown__, __unknown__, PUNCT]": {
        basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]
    },
    "VERB [__unknown__, __unknown__, PUNCT]": {
        basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]
    },

    # "apples [conj, conj, conj]"
    "__unknown__ [conj, conj, conj]": {
        basepatterns_with_tokens["__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"]
    },
    "NOUN [conj, conj, conj]": {
        basepatterns_with_tokens["__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"]
    }
}

expected_basepatterns_without_phrase_without_unknown = {
    basepatterns_with_tokens["fox [the, quick, brown]"]: [1],
    basepatterns_with_tokens["dog [over, the, lazy]"]: [1,2,3],
    basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]: [3],
    basepatterns_with_tokens["__unknown__,"]: [4,4]
}

expected_basepatterns_without_phrase = {
    **expected_basepatterns_without_phrase_without_unknown,
    **{
        basepatterns_with_tokens["__unknown__ [,, __unknown__]"]: [4],
    }
}

expected_basepatterns_with_phrase = {
    basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"]: [1],
    basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]: [2],
    basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"]: [3],
    basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]: [4],
    basepatterns_with_tokens["__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"]: [4]
}

@pytest.mark.parametrize("parameters,expected_patterns,expected_basepatterns", [
    ([], expected_patterns_without_phrase, expected_basepatterns_without_phrase),
    (
        ["NOUN"],
        {**expected_patterns_without_phrase, **expected_patterns_with_phrase},
        {**expected_basepatterns_without_phrase, **expected_basepatterns_with_phrase}
    ),
    (["--skip_unknown"], expected_patterns_without_phrase_and_unknown, expected_basepatterns_without_phrase_without_unknown),
    (["--keep_only_dict_words"], expected_patterns_without_phrase, expected_basepatterns_without_phrase),
    (["--keep_only_dict_words", "--skip_unknown"], expected_patterns_without_phrase_and_unknown, expected_basepatterns_without_phrase_without_unknown)
])
def test_extract_patterns_with_phrases(parameters, expected_patterns, expected_basepatterns):

    infile_path = os.path.abspath('example_data/example_data_encoded.conllu')
    dictfile_path = os.path.abspath('example_data/example_data_dict_filtered_encoded.json')

    encoder_path = os.path.abspath('example_data/example_data_encoder')

    runner = CliRunner()
    with runner.isolated_filesystem():

        patterns_list_filename = 'patterns_sorted.json'
        base_list_filename = 'base_sorted.json'

        patterns_filename = 'patterns.json'
        base_filename = 'base.json'

        runner.invoke(main, [
            'extract-patterns',
            infile_path,
            patterns_list_filename,
            base_list_filename,
            dictfile_path,
            'lemma'] + parameters
        )

        # files need to be sorted
        for filename in [patterns_list_filename, base_list_filename]:
            with open(filename, 'r') as pattern_file:
                lines = [line.rstrip() for line in pattern_file]
                ## patterns list needs sorted with unique
                if filename == patterns_list_filename:
                    lines = set(lines)
                patterns = sorted(lines)

            with open(filename, 'w') as pattern_file:
                pattern_file.write('\n'.join(patterns) + '\n')

        with open(patterns_list_filename, 'r') as pattern_file:
            patterns = [line.rstrip() for line in pattern_file]
            print('\n'.join(patterns))

        runner.invoke(main, [
            'utils',
            'convert-pattern-list',
            '--is_int',
            base_list_filename,
            base_filename
        ])

        runner.invoke(main, [
            'utils',
            'convert-pattern-list',
            patterns_list_filename,
            patterns_filename,
        ])

        patterns = {}
        for line in open(patterns_filename):
            pattern, base_patterns = json.loads(line)
            patterns[pattern] = base_patterns

        basepatterns = []
        for line in open(base_filename):
            basepatterns.append(json.loads(line))

        encoder = Base64Encoder(PatternEncoder.load(open(encoder_path, 'rb')))
        patterns = {str(encoder.decode(pattern)): set([str(encoder.decode(base)) for base in bases]) for pattern, bases in patterns.items()}
        basepatterns = {str(encoder.decode(pattern)): content for pattern, content in basepatterns}

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
            dictfile_path,
            'lemma'
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
    expected_outfile_path = os.path.abspath('example_data/example_data_encoded.conllu')
    script_file = os.path.abspath('bin/encode_corpus')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_encoded.conllu"

        os.system(script_file + " " + infile_path + " " + outfile + " " + encoded_dict_path + " lemma upostag np_function --unknown \"__unknown__\"")


        assert filecmp.cmp(outfile, expected_outfile_path, shallow=False)
