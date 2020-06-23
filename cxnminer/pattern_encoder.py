import abc
import base64
import math
import pickle

import bitarray
import bitarray.util

from cxnminer.pattern import PatternElement

class EncodeError(ValueError):

    pass

class PatternEncoder(metaclass=abc.ABCMeta):

    token_start = "__TOKEN_START__"
    token_end = "__TOKEN_END__"

    @abc.abstractmethod
    def encode_item(self, item):
        pass # pragma: no cover

    @abc.abstractmethod
    def encode(self, pattern):
        pass # pragma: no cover

    @abc.abstractmethod
    def decode(self, encoded_pattern):
        pass # pragma: no cover

    @abc.abstractmethod
    def get_levels(self):
        pass # pragma: no cover

    @abc.abstractmethod
    def append(self, encoded_pattern, encoded_item):
        pass # pragma: no cover


    def save(self, file_):

        pickle.dump(self.__class__, file_)
        self._save(file_)

    def _save(self, file_):

        pickle.dump(self, file_)

    @classmethod
    def load(cls, file_):

        cls_ = cls.get_saved_encoder_class(file_)
        return cls_._load(file_)

    @classmethod
    def _load(cls, file_):

        return pickle.load(file_)


    @classmethod
    def get_saved_encoder_class(cls, file_):

        return pickle.load(file_)


    ### helper methods
    @classmethod
    def _int_2_bytes(cls, number):

        # https://docs.python.org/3/library/stdtypes.html#int.to_bytes
        return number.to_bytes((number.bit_length() + 7) // 8, byteorder='little')

    @classmethod
    def _bytes_2_int(cls, bytes_):

        return int.from_bytes(bytes_, byteorder='little')


    def get_pattern_type(self):

        return self.pattern_type


class CombinablePatternEncoder(PatternEncoder):
    """A pattern encoder that creates combinable patterns.

    Combinable means that elements can be appended to patterns without knowing
    specifics of the instantiated encoder.

    """

    @classmethod
    @abc.abstractmethod
    def combine(cls, encoded_pattern, encoded_item):
        pass # pragma: no cover


class Base64Encoder(PatternEncoder):

    def __init__(self, encoder, binary=True):

        self.encoder = encoder
        self.binary = binary

    def get_levels(self):
        return self.encoder.get_levels()

    def get_pattern_type(self):

        return self.encoder.get_pattern_type()

    @classmethod
    def b64encode(cls, pattern, binary=True):

        encoded = base64.b64encode(pattern)
        if binary:
            return encoded
        else:
            return encoded.decode('ascii')

    @classmethod
    def b64decode(cls, pattern):

        return base64.b64decode(pattern)

    def encode_item(self, item):

        return self.b64encode(self.encoder.encode_item(item), self.binary)

    def encode(self, pattern):

        return self.b64encode(self.encoder.encode(pattern), self.binary)

    def decode(self, encoded_pattern):

        return self.encoder.decode(self.b64decode(encoded_pattern))

    def append(self, encoded_pattern, encoded_item):

        return self.b64encode(
            self.encoder.append(self.b64decode(encoded_pattern),
                                self.b64decode(encoded_item)), self.binary)

    def _save(self, file_):

        pickle.dump(self.binary, file_)
        self.encoder.save(file_)

    @classmethod
    def _load(cls, file_):

        binary = pickle.load(file_)
        return Base64Encoder(PatternEncoder.load(file_), binary=binary)


class BitEncoder(PatternEncoder):
    """Encode a Pattern as a bit string (integer).

    Using dictionaries for different levels of PatternElements and special
    characters to encode PatternElements as integers and combine them into a
    bit string.

    Args:
        dictionaries (dict): A dictionary containing dictionaries for
            the different levels of PatternElements that will appear.
            The specific dictionaries can be actual `dict`s mapping elements to ids
            that are supposed to be numeric and unique per dictionary.
            If they are only a collection of elements, then ids are created.
        pattern_type (cls): A subclass of Pattern. Determines the type of patterns
            that this encoder will be used to encode.
        unknown (optional): If set, unknown pattern elements are encoded to a unique id
            and set to the value of unknown during decoding.

    """

    def __init__(self, dictionaries, pattern_type, unknown=None):

        self.pattern_type = pattern_type
        self.special_characters = self.pattern_type.specialElements()

        self.unknown = unknown

        self.level_offsets = {}
        curr_offset = 1

        self.dictionaries = dictionaries

        for level in self.dictionaries.keys():

            self.level_offsets[level] = curr_offset
            curr_offset += len(self.dictionaries[level])
            if self.unknown is not None:
                curr_offset += 1

            if not hasattr(self.dictionaries[level], "items"):
                self.dictionaries[level] = {
                    word: id_
                    for id_, word in enumerate(self.dictionaries[level])
                }

        self.special_offset = curr_offset

        ## calculate the number of bits needed (additional 2 are for token_start and token_end)
        dict_size = self.special_offset + len(self.special_characters) + 2
        self.element_size = math.floor(math.log(dict_size-1, 2) + 1)


    def get_levels(self):
        return set(self.level_offsets.keys())

    def _get_word_for_id(self, word_id):

        if not hasattr(self, '_ids_2_words'):

            self._ids_2_words = {}
            for level in self.dictionaries.keys():

                for word, id_ in self.dictionaries[level].items():
                    self._ids_2_words[id_ + self.level_offsets[level]] = (word , level)

                if self.unknown is not None:
                    self._ids_2_words[id_ + 1 + self.level_offsets[level]] = (self.unknown, level)

            for id_, word in enumerate(self.special_characters):
                self._ids_2_words[id_ + self.special_offset] = (word, None)

        return self._ids_2_words[word_id]

    def encode_item(self, item):

        code = 0

        if item == self.token_start:

            code = self.special_offset + len(self.special_characters)

        elif item == self.token_end:

            code = self.special_offset + len(self.special_characters) + 1

        else:

            try:
                code = self.special_characters.index(item) + self.special_offset

            except ValueError:

                try:
                    code = self.dictionaries[item.level][item.form] + self.level_offsets[item.level]

                except AttributeError:

                    ## it is a token - so encode this
                    return self._encode(
                        [self.token_start] +
                        [PatternElement(value, level) for level, value in item.items()] +
                        [self.token_end]
                    )

                except KeyError:

                    if self.unknown is not None:
                        code = len(self.dictionaries[item.level]) + self.level_offsets[item.level]
                    else:
                        raise EncodeError("Element not in dictionary: " + str(item))

        return self._int_2_bytes(code)

    def append(self, encoded_pattern, encoded_item):

        encoded_pattern = self._bytes_2_int(encoded_pattern)
        encoded_item = self._bytes_2_int(encoded_item)

        element_size = math.ceil(encoded_item.bit_length() / self.element_size) * self.element_size
        return self._int_2_bytes(encoded_pattern << element_size | encoded_item)

    def _encode(self, pattern):

        code = b''

        for element in pattern:
            code = self.append(code, self.encode_item(element))

        return code

    def encode(self, pattern):

        return(self._encode(pattern.get_element_list()))


    def decode(self, encoded_pattern):

        encoded_pattern = self._bytes_2_int(encoded_pattern)

        pattern = []
        element_size_int = 2**self.element_size - 1

        in_token = False

        while encoded_pattern != 0:
            element_id = int(encoded_pattern & element_size_int)
            try:
                word, level = self._get_word_for_id(element_id)
                if in_token:
                    current_token[level] = word
                else:
                    if level is not None:
                        pattern.append(PatternElement(word, level))
                    else:
                        pattern.append(word)

            except:
                ## end of token - treat as start as pattern is reversed
                if element_id == len(self._ids_2_words) + 2:
                    in_token = True
                    current_token = {}
                ## start of token - treat as start as pattern is reversed
                elif element_id == len(self._ids_2_words) + 1:
                    in_token = False
                    pattern.append(current_token)

                else:
                    raise ValueError("Cannot decode pattern, unknown key " + str(element_id))

            encoded_pattern = encoded_pattern >> self.element_size

        pattern.reverse()
        return self.pattern_type.from_element_list(pattern)


class HuffmanEncoder(CombinablePatternEncoder):


    # a 1 that is prefixed to the bitarray before
    # converting it to a byte representation of the
    # encoded integer in order to avoid the loss of
    # leading 0's
    prefix = bitarray.bitarray('1')

    def __init__(self, frequency_dictionaries, pattern_type, special_weight=1, unknown=None):

        self.pattern_type = pattern_type

        huffman_freq_dict = {}
        max_freq = 0

        self.levels = set(frequency_dictionaries.keys())

        for level, dict_ in frequency_dictionaries.items():
            for word, freq in dict_.items():

                if max_freq < freq:
                    max_freq = freq

                huffman_freq_dict[PatternElement(word, level)] = freq

        special_frequency = max_freq*special_weight
        for special_element in self.pattern_type.specialElements():
            huffman_freq_dict[special_element] = special_frequency

        self.unknown = unknown
        if self.unknown is not None:
            for level in frequency_dictionaries.keys():
                huffman_freq_dict[PatternElement(unknown, level)] = special_frequency

        huffman_freq_dict[self.token_start] = max(max_freq, special_frequency)
        huffman_freq_dict[self.token_end] = max(max_freq, special_frequency)

        self.huffman_dict = bitarray.util.huffman_code(huffman_freq_dict)

    def get_levels(self):
        return self.levels

    @classmethod
    def _bytes_2_bitarray(cls, bytes_):

        return bitarray.util.int2ba(cls._bytes_2_int(bytes_))[cls.prefix.length():]

    @classmethod
    def _bitarray_2_bytes(cls, bitarray_):

        return cls._int_2_bytes(bitarray.util.ba2int(cls.prefix + bitarray_))

    def _encode_to_bitarray(self, pattern):

        code = bitarray.bitarray()

        try:
            code.encode(self.huffman_dict, pattern)
        except ValueError as e:
            code = bitarray.bitarray()
            for element in pattern:
                if not hasattr(element, 'items'):
                    try:
                        code.encode(self.huffman_dict, [element])
                    except ValueError:
                        if self.unknown is not None:
                            code.encode(self.huffman_dict, [PatternElement(self.unknown, element.level)])
                        else:
                            raise EncodeError(str(e))
                else:
                    ## encode a whole token (a dict)
                    code.extend(
                        self._encode_to_bitarray(
                            [self.token_start] +
                            [PatternElement(value, level) for level, value in element.items()] +
                            [self.token_end]))


        return code

    def _encode(self, pattern):

        return self._bitarray_2_bytes(self._encode_to_bitarray(pattern))

    def encode_item(self, pattern_element):

        return self._encode([pattern_element])

    def encode(self, pattern):

        return self._encode(pattern.get_element_list())


    def decode(self, encoded_pattern):

        encoded = self._bytes_2_bitarray(encoded_pattern)
        flat_pattern = encoded.decode(self.huffman_dict)

        pattern = []
        in_token = False
        for element in flat_pattern:

            if in_token:
                if element == self.token_end:
                    pattern.append(current_token)
                    in_token = False
                else:
                    current_token[element.level] = element.form
            else:
                if element == self.token_start:
                    current_token = {}
                    in_token = True
                else:
                    pattern.append(element)

        return self.pattern_type.from_element_list(pattern)

    def append(self, encoded_pattern, encoded_item):

        return self.combine(encoded_pattern, encoded_item)

    @classmethod
    def combine(cls, encoded_pattern, encoded_item):

        encoded = cls._bytes_2_bitarray(encoded_pattern)
        encoded.extend(cls._bytes_2_bitarray(encoded_item))

        return cls._bitarray_2_bytes(encoded)


    def _save(self, file_):

        pickle.dump(self.pattern_type, file_)
        pickle.dump(self.unknown, file_)
        for key, element in self.huffman_dict.items():
            pickle.dump(key, file_)
            pickle.dump(element, file_)

    @classmethod
    def _load(cls, file_):

        pattern_type = pickle.load(file_)
        unknown = pickle.load(file_)

        encoder = cls({}, pattern_type, unknown=unknown)
        huffman_dict = {}
        while True:
            try:
                key = pickle.load(file_)
                value = pickle.load(file_)
                huffman_dict[key] = value
            except EOFError:
                break

        encoder.huffman_dict = huffman_dict
        return encoder
