import io

import pytest

from cxnminer.pattern_encoder import PatternEncoder, BitEncoder, HuffmanEncoder, EncodeError
from cxnminer.pattern import SNGram, PatternElement


def test_bit_size_7():

    test = BitEncoder({'form': set(['a', 'b']), 'function': set(['a', 'b'])}, SNGram)
    assert test.element_size == 3

def test_bit_size_7_unknown():

    test = BitEncoder({'form': set(['a', 'b']), 'function': set(['a', 'b'])}, SNGram, '__unknown__')
    assert test.element_size == 4

def test_bit_size_8():

    test = BitEncoder({'form': set(['a', 'b', 'c']), 'function': set(['a', 'b'])}, SNGram)
    assert test.element_size == 4

@pytest.mark.parametrize("encoder_dict", [
    {'form': {'fox': 0, 'The': 2, 'quick': 1, 'brown': 3}},
    {'form': set(['fox', 'The', 'quick', 'brown'])}
])
def test_encode_decode(encoder_dict):

    test = BitEncoder(encoder_dict, SNGram)
    pattern =  SNGram.from_element_list([
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ])

    assert test.decode(test.encode(pattern)) == pattern


@pytest.mark.parametrize("encoder_dict", [
    {'form': {'fox': 0, 'The': 2, 'quick': 1, 'brown': 3}, 'pos': {'Noun': 0}},
    {'form': set(['fox', 'The', 'quick', 'brown']), 'pos': set(['Noun'])}
])
def test_encode_decode_different_levels(encoder_dict):

    test = BitEncoder(encoder_dict, SNGram)
    pattern =  SNGram.from_element_list([
        PatternElement('Noun', 'pos'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ])

    assert test.decode(test.encode(pattern)) == pattern

def test_encode_decode_unknown():

    unknown_token = "__unknown__"

    test = BitEncoder(
        {'form': set(['fox', 'quick', 'brown'])}, SNGram, unknown_token)

    pattern_list = [
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ]
    pattern =  SNGram.from_element_list(pattern_list)

    expected_pattern_list = pattern_list
    expected_pattern_list[2] = unknown_token
    expected_pattern = SNGram.from_element_list(expected_pattern_list)

    assert test.decode(test.encode(pattern)) == expected_pattern


def test_encode_unknown_not_set():

    test = BitEncoder(
        {'form': set(['fox', 'quick', 'brown'])}, SNGram)

    pattern_list = [
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ]
    pattern =  SNGram.from_element_list(pattern_list)

    with pytest.raises(EncodeError):
        test.encode(pattern)


def test_decode_unknown_not_set():

    test_encoder = BitEncoder(
        {'form': {'fox': 0, 'quick': 1, 'brown': 2}}, SNGram, "__unkonwn__")
    test_decoder = BitEncoder(
        {'form': {'fox': 0, 'quick': 1, 'brown': 2}}, SNGram)

    pattern_list = [
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ]
    pattern =  SNGram.from_element_list(pattern_list)
    encoded_pattern = test_encoder.encode(pattern)

    with pytest.raises(ValueError):
        test_decoder.decode(encoded_pattern)


@pytest.mark.parametrize("freq_dict", [
    {'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}
])
def test_huffman_encode_decode(freq_dict):

    test = HuffmanEncoder(freq_dict, SNGram)


    pattern_list = [
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ]
    expected_pattern = SNGram.from_element_list(pattern_list)

    assert test.decode(test.encode(expected_pattern)) == expected_pattern


@pytest.mark.parametrize("freq_dict", [
    {'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}
])
def test_huffman_encode_item(freq_dict):

    test = HuffmanEncoder(freq_dict, SNGram)

    element = PatternElement('fox', 'form')
    expected_pattern = SNGram.from_element_list([element])

    assert test.decode(test.encode_item(element)) == expected_pattern

@pytest.mark.parametrize("freq_dict", [
    {'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}
])
def test_huffman_encode_unknown_item(freq_dict):

    test = HuffmanEncoder(freq_dict, SNGram)

    element = PatternElement('unknown', 'form')

    with pytest.raises(EncodeError):
        test.encode_item(element)

@pytest.mark.parametrize("freq_dict", [
    {'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}
])
def test_huffman_append(freq_dict):

    test = HuffmanEncoder(freq_dict, SNGram)

    pattern_list = [
        PatternElement('fox', 'form'),
        SNGram.LEFT_BRACKET,
        PatternElement('The', 'form'),
        SNGram.COMMA,
        PatternElement('quick', 'form'),
        SNGram.COMMA,
        PatternElement('brown', 'form'),
        SNGram.RIGHT_BRACKET
    ]
    expected_pattern = SNGram.from_element_list(pattern_list)

    pattern = b''
    for element in pattern_list:
        pattern = test.append(pattern, test.encode_item(element))

    assert test.decode(pattern) == expected_pattern


@pytest.mark.parametrize("encoder_class,args,test_stm", [
    (
        BitEncoder, {'dictionaries': {'form': set(['fox', 'The', 'quick', 'brown']), 'pos': set(['Noun'])}},
        lambda orig, loaded: orig.dictionaries == loaded.dictionaries
    ),
    (
        HuffmanEncoder, {'frequency_dictionaries': {'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}},
        lambda orig, loaded: orig.huffman_dict == loaded.huffman_dict
    ),
])
def test_save(encoder_class, args, test_stm):

    output = io.BytesIO()

    test = encoder_class(**args, pattern_type=SNGram)

    test.save(output)
    output.seek(0)
    test_loaded = PatternEncoder.load(output)

    output.close()

    assert test_stm(test, test_loaded)
