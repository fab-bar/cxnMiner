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
        "{'lemma': 'dog', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +       "["
    +       "{'lemma': 'over', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'lazy', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "fox [the, quick, brown]":
        "{'lemma': 'fox', 'upos': 'NOUN', 'np_function': 'nsubj'} "
    +       "["
    +       "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'quick', 'upos': 'ADJ', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'brown', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "__unknown__ [__unknown__, the, __unknown__]":
        "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +       "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +       "]",
    "__unknown__,":
        "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +       "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}",
    "__unknown__ [,, __unknown__]":
        "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +       "["
    +       "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upos': '__unknown__', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox [the, quick, brown], dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upos': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upos': 'NOUN', 'np_function': 'nsubj'} "
    +           "["
    +           "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'quick', 'upos': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'brown', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': 'dog', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +           "{'lemma': 'over', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'lazy', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': '.', 'upos': 'PUNCT', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox, dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upos': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upos': 'NOUN', 'np_function': 'nsubj'}, "
    +       "{'lemma': 'dog', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +           "{'lemma': 'over', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'lazy', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +           "], "
    +       "{'lemma': '.', 'upos': 'PUNCT', 'np_function': '__unknown__'}"
    +       "]",
    "jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]":
        "{'lemma': 'jump', 'upos': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': 'fox', 'upos': 'NOUN', 'np_function': 'nsubj'} "
    +           "["
    +           "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'quick', 'upos': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': 'brown', 'upos': 'ADJ', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +               "["
    +               "{'lemma': '__unknown__', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +               "{'lemma': '__unknown__', 'upos': 'ADJ', 'np_function': '__unknown__'}"
    +               "]"
    +           "], "
    +       "{'lemma': 'dog', 'upos': 'NOUN', 'np_function': 'nmod'} "
    +           "["
    +               "{'lemma': 'over', 'upos': 'ADP', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'the', 'upos': 'DET', 'np_function': '__unknown__'}, "
    +               "{'lemma': 'lazy', 'upos': 'ADJ', 'np_function': '__unknown__'}], "
    +               "{'lemma': '.', 'upos': 'PUNCT', 'np_function': '__unknown__'}"
    +           "]",
    "__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]":
        "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +           "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +           "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +       "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +           "["
    +           "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upos': '__unknown__', 'np_function': '__unknown__'}"
    +           "]"
    +       "]",
    "__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]":
        "{'lemma': '__unknown__', 'upos': 'VERB', 'np_function': '__unknown__'} "
    +       "["
    +       "{'lemma': '__unknown__', 'upos': '__unknown__', 'np_function': 'nsubj'}, "
    +       "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': '__unknown__'} "
    +           "["
    +           "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +               "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +               "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +           "{'lemma': '__unknown__', 'upos': 'NOUN', 'np_function': 'conj'} "
    +               "["
    +               "{'lemma': ',', 'upos': 'PUNCT', 'np_function': '__unknown__'}, "
    +               "{'lemma': '__unknown__', 'upos': '__unknown__', 'np_function': '__unknown__'}"
    +               "]"
    +           "], "
    +       "{'lemma': '.', 'upos': 'PUNCT', 'np_function': '__unknown__'}"
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
    basepatterns_with_tokens["fox [the, quick, brown]"]: ['[1, [4, 1, 2, 3]]'],
    basepatterns_with_tokens["dog [over, the, lazy]"]: ['[1, [9, 6, 7, 8]]','[2, [6, 3, 4, 5]]','[3, [13, 10, 11, 12]]'],
    basepatterns_with_tokens["__unknown__ [__unknown__, the, __unknown__]"]: ['[3, [8, 5, 6, 7]]'],
    basepatterns_with_tokens["__unknown__,"]: ['[4, [5, 4]]','[4, [7, 6]]']
}

expected_basepatterns_without_phrase = {
    **expected_basepatterns_without_phrase_without_unknown,
    **{
        basepatterns_with_tokens["__unknown__ [,, __unknown__]"]: ['[4, [10, 8, 9]]'],
    }
}

expected_basepatterns_with_phrase = {
    basepatterns_with_tokens["jump [fox [the, quick, brown], dog [over, the, lazy], .]"]: ['[1, [5, 4, 1, 2, 3, 9, 6, 7, 8, 10]]'],
    basepatterns_with_tokens["jump [fox, dog [over, the, lazy], .]"]: ['[2, [2, 1, 6, 3, 4, 5, 7]]'],
    basepatterns_with_tokens["jump [fox [the, quick, brown, __unknown__ [__unknown__, the, __unknown__]], dog [over, the, lazy], .]"]: ['[3, [9, 4, 1, 2, 3, 8, 5, 6, 7, 13, 10, 11, 12, 14]]'],
    basepatterns_with_tokens["__unknown__ [__unknown__, __unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]], .]"]: ['[4, [2, 1, 3, 5, 4, 7, 6, 10, 8, 9, 11]]'],
    basepatterns_with_tokens["__unknown__ [__unknown__,, __unknown__,, __unknown__ [,, __unknown__]]"]: ['[4, [3, 5, 4, 7, 6, 10, 8, 9]]']
}

@pytest.mark.parametrize("parameters,expected_patterns,expected_basepatterns", [
    ([os.path.abspath('example_data/test_config_nophrase.json')], expected_patterns_without_phrase, expected_basepatterns_without_phrase),
    (
        [os.path.abspath('example_data/test_config.json')],
        {**expected_patterns_without_phrase, **expected_patterns_with_phrase},
        {**expected_basepatterns_without_phrase, **expected_basepatterns_with_phrase}
    ),
    ([os.path.abspath('example_data/test_config_nophrase.json'), "--skip_unknown"], expected_patterns_without_phrase_and_unknown, expected_basepatterns_without_phrase_without_unknown),
    ([os.path.abspath('example_data/test_config_nophrase.json'), "--keep_only_dict_words"], expected_patterns_without_phrase, expected_basepatterns_without_phrase),
    ([os.path.abspath('example_data/test_config_nophrase.json'), "--keep_only_dict_words", "--skip_unknown"], expected_patterns_without_phrase_and_unknown, expected_basepatterns_without_phrase_without_unknown)
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
            dictfile_path] + parameters
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


def test_extract_vocabulary():

    infile_path = os.path.abspath('example_data/example_data.conllu')
    expected_outfile_path = os.path.abspath('example_data/example_data_dict.json')
    configfile_path = os.path.abspath('example_data/example_config.json')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_dict.json"

        runner.invoke(main, [
            'utils',
            'extract-vocabulary',
            infile_path,
            outfile,
            configfile_path
        ])

        expected_dict = json.load(open(expected_outfile_path, 'r'))
        result_dict = json.load(open(outfile, 'r'))

    assert result_dict == expected_dict

def test_create_encoder():

    infile_path = os.path.abspath('example_data/example_data_dict_filtered.json')
    configfile_path = os.path.abspath('example_data/example_config.json')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_encoder"

        runner.invoke(main, [
            'utils',
            'create-encoder',
            infile_path,
            outfile,
            configfile_path
        ])

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
    configfile_path = os.path.abspath('example_data/example_config.json')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_dict_filtered_encoded.json"

        runner.invoke(main, [
            'utils',
            'encode-vocabulary',
            infile_path,
            outfile,
            encoder_path,
            configfile_path
        ])

        encoder = Base64Encoder(PatternEncoder.load(open(encoder_path, 'rb')))

        result_dict = json.load(open(outfile, 'r'))

        results = [(level, decoded, encoder.decode(encoded).get_element_list()) for level, elements in result_dict.items() for decoded, encoded in elements.items() if level != "__special__"]
        results = [len(pe) == 1 and pe[0].level == level and pe[0].form == word for level, word, pe in results]

    assert all(results)

def test_encode_corpus():

    infile_path = os.path.abspath('example_data/example_data.conllu')
    encoded_dict_path = os.path.abspath('example_data/example_data_dict_filtered_encoded.json')
    configfile_path = os.path.abspath('example_data/example_config.json')
    expected_outfile_path = os.path.abspath('example_data/example_data_encoded.conllu')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile = "example_data_encoded.conllu"

        runner.invoke(main, [
            'utils',
            'encode-corpus',
            infile_path,
            outfile,
            encoded_dict_path,
            configfile_path
        ])


        assert filecmp.cmp(outfile, expected_outfile_path, shallow=False)


@pytest.mark.parametrize("command,arguments,expected_outfile,options", [
    ('add-pattern-stats',
     [os.path.abspath('example_data/example_data_pattern_set.jsonl')],
     os.path.abspath('example_data/example_data_patterns_simple_stats.json'),
     ['--base_patterns', os.path.abspath('example_data/example_data_base_pattern_set.jsonl')]),
    ('filter-patterns',
     [os.path.abspath('example_data/example_data_pattern_set.jsonl'), os.path.abspath('example_data/example_data_patterns_simple_stats.json'), 'frequency', '2'],
     os.path.abspath('example_data/example_data_pattern_set_frequent.jsonl'),
     []),
    ('decode-patterns',
     [os.path.abspath('example_data/example_data_pattern_set_frequent.jsonl'), os.path.abspath('example_data/example_data_encoder')],
     os.path.abspath('example_data/example_data_pattern_set_frequent_decoded'),
     []),
    ('get-vocabulary-probs',
     [os.path.abspath('example_data/example_data_dict.json')],
     os.path.abspath('example_data/example_data_dictionary_probs.json'),
     []),
    ('get-pattern-type-freq',
     [os.path.abspath('example_data/example_data_pattern_set_frequent_decoded'), os.path.abspath('example_data/example_data_patterns_simple_stats.json')],
     os.path.abspath('example_data/example_data_pattern_set_frequent_type_frequencies.json'),
     []),
    ('add-pattern-stats',
     [os.path.abspath('example_data/example_data_pattern_set_frequent.jsonl')],
     os.path.abspath('example_data/example_data_patterns_stats.json'),
     ['--decoded_patterns', os.path.abspath('example_data/example_data_pattern_set_frequent_decoded'), '--config', os.path.abspath('example_data/example_config.json'), '--vocabulary_probs', os.path.abspath('example_data/example_data_dictionary_probs.json'), '--known_stats', os.path.abspath('example_data/example_data_patterns_simple_stats.json'), '--pattern_profile_frequency', os.path.abspath('example_data/example_data_pattern_set_frequent_type_frequencies.json')]),
    ('get-top-n',
     [os.path.abspath('example_data/example_data_pattern_set_frequent.jsonl'), os.path.abspath('example_data/example_data_patterns_stats.json'), 'uif-pmi', '2'],
     os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi.jsonl'),
     []),
    ('get-top-n-base-patterns',
     [os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi.jsonl'), os.path.abspath('example_data/example_data_base_pattern_set.jsonl'), '1'],
     os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi_basesel_1.jsonl'),
     ['--example_ids', os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_exampleids.json')]),
    ('decode-pattern-collection',
     [os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi_basesel_1.jsonl'), os.path.abspath('example_data/example_data_encoder')],
     os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_decoded.jsonl'),
     ## TODO not really an option but should work!
     [os.path.abspath('example_data/example_config.json'), '--string'])
])
def test_pattern_extraction_util(command, arguments, expected_outfile, options):

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfile_path = "example_data_extraction_util_result"

        runner.invoke(main,
                      [
                          'utils',
                          command
                      ] +
                      arguments +
                      [ outfile_path ] +
                      options
        )

        assert filecmp.cmp(outfile_path, expected_outfile, shallow=False)


def test_corpus2sentences():

    infile_path = os.path.abspath('example_data/example_data.conllu')
    example_ids_path = os.path.abspath('example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_exampleids.json')
    expected_outpath = os.path.abspath('example_data/sentences')

    runner = CliRunner()
    with runner.isolated_filesystem():

        outfolder = "example_sentences"

        result = runner.invoke(main, [
            'corpus2sentences',
            infile_path,
            outfolder,
            '--example_ids', example_ids_path
        ])

        print(result.exception)
        print(result.output)


        dir_comparator = filecmp.dircmp(outfolder, expected_outpath)
        assert not dir_comparator.left_only
        assert not dir_comparator.right_only
        assert not dir_comparator.diff_files
        assert not dir_comparator.funny_files


############################ tests for scripts in bin

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

