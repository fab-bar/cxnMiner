import abc
import math

from cxnminer.pattern import PatternElement

class PatternEncoder(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def encode(self, pattern):
        pass # pragma: no cover

    @abc.abstractmethod
    def decode(self, encoded_pattern):
        pass # pragma: no cover

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

            if not hasattr(self.dictionaries[level], "items"):
                self.dictionaries[level] = {
                    word: id_
                    for id_, word in enumerate(self.dictionaries[level])
                }

        self.special_offset = curr_offset

        ## calculate the number of bits needed
        dict_size = self.special_offset + len(self.special_characters)
        if self.unknown is not None:
            dict_size += 1
        self.element_size = math.floor(math.log(dict_size-1, 2) + 1)


    def _get_word_for_id(self, word_id):

        if not hasattr(self, '_ids_2_words'):

            self._ids_2_words = {}
            for level in self.dictionaries.keys():

                for word, id_ in self.dictionaries[level].items():
                    self._ids_2_words[id_ + self.level_offsets[level]] = (word , level)

            for id_, word in enumerate(self.special_characters):
                self._ids_2_words[id_ + self.special_offset] = (word, None)

            if self.unknown is not None:
                self._ids_2_words[self.special_offset + len(self.special_characters)] = (self.unknown, None)


        return self._ids_2_words[word_id]

    def _get_element_id(self, element):

        try:
            return self.special_characters.index(element) + self.special_offset

        except ValueError:

            try:
                return self.dictionaries[element.level][element.form] + self.level_offsets[element.level]
            except KeyError:

                if self.unknown is not None:
                    return self.special_offset + len(self.special_characters)
                else:
                    raise ValueError("Element not in dictionary: " + str(element))


    def encode(self, pattern):

        code = 0

        pattern = pattern.get_element_list()

        for element in pattern:

            code = code << self.element_size | self._get_element_id(element)

        return code

    def decode(self, encoded_pattern):

        pattern = []
        element_size_int = 2**self.element_size - 1

        while encoded_pattern != 0:
            try:
                word, level = self._get_word_for_id(int(encoded_pattern & element_size_int))
            except:
                raise ValueError("Cannot decode pattern, unknown key " + str(int(encoded_pattern & element_size_int)))

            if level is not None:
                pattern.append(PatternElement(word, level))
            else:
                pattern.append(word)

            encoded_pattern = encoded_pattern >> self.element_size

        pattern.reverse()
        return self.pattern_type.from_element_list(pattern)
