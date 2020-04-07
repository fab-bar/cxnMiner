import io

import pytest

from cxnminer.pattern_encoder import PatternEncoder, Base64Encoder, BitEncoder, HuffmanEncoder, EncodeError
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
def test_huffman_encode_unknown_item(freq_dict):

    test = HuffmanEncoder(freq_dict, SNGram)

    element = PatternElement('unknown', 'form')

    with pytest.raises(EncodeError):
        test.encode_item(element)


### encoders to test
encoder = [
    BitEncoder({'form': {'fox': 0, 'The': 2, 'quick': 1, 'brown': 3}}, SNGram),
    BitEncoder({'form': set(['fox', 'The', 'quick', 'brown'])}, SNGram),
    HuffmanEncoder({'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}, SNGram),
    Base64Encoder(HuffmanEncoder({'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}, SNGram)),
    Base64Encoder(HuffmanEncoder({'form': {'fox': 5, 'The': 10, 'quick': 3, 'brown': 8}}, SNGram), binary=False)
]

@pytest.mark.parametrize("encoder", encoder)
def test_encode_decode(encoder):

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

    assert encoder.decode(encoder.encode(pattern)) == pattern


@pytest.mark.parametrize("encoder", encoder)
def test_encode_item(encoder):

    element = PatternElement('fox', 'form')
    expected_pattern = SNGram.from_element_list([element])

    assert encoder.decode(encoder.encode_item(element)) == expected_pattern


@pytest.mark.parametrize("encoder", encoder)
def test_append(encoder):

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
        pattern = encoder.append(pattern, encoder.encode_item(element))

    assert encoder.decode(pattern) == expected_pattern


comparison_function = {
    BitEncoder: lambda orig, loaded: orig.dictionaries == loaded.dictionaries,
    HuffmanEncoder: lambda orig, loaded: orig.huffman_dict == loaded.huffman_dict,
    Base64Encoder:lambda orig, loaded: (orig.binary == loaded.binary) and (
        comparison_function[orig.encoder.__class__](orig.encoder, loaded.encoder))
}

@pytest.mark.parametrize("encoder", encoder)
def test_save(encoder):

    output = io.BytesIO()

    encoder.save(output)
    output.seek(0)
    encoder_loaded = PatternEncoder.load(output)

    output.close()

    assert comparison_function[encoder.__class__](encoder, encoder_loaded)
