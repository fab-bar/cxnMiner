import abc
import itertools

import conllu
import conllu.parser

from .pattern import TokenSNGram, SNGram


class PatternExtractor(metaclass=abc.ABCMeta):

    @classmethod
    @abc.abstractmethod
    def get_pattern_type(cls):
        pass # pragma: no cover

    @abc.abstractmethod
    def extract_patterns(self, sentence):
        pass # pragma: no cover

class SyntacticNGramExtractor(PatternExtractor):
    """Extracts non-continous sn-grams from a given sentence that are bottom-up subtrees."""


    def get_pattern_type(cls):

        return SNGram # pragma: no cover

    def __init__(self, min_size=2, max_size=6,
                 special_node_conversion=None, max_open_path_size=0):

        self.min_size = min_size
        self.max_size = max_size
        if max_open_path_size is not None:
            self.max_open_path_size = max(max_open_path_size, max_size-1)
        else:
            self.max_open_path_size = None
        self.special_node_conversion = special_node_conversion

    def _add_path(self, path, still_open_paths, patterns):

        if self.max_open_path_size is None or path.length <= self.max_open_path_size:
            still_open_paths.append(path.tree)
        if path.length >= self.min_size and path.length <= self.max_size:
            patterns.append(path)

    def _add_special_path(self, tree, still_open_paths, patterns):

        if self.special_node_conversion is not None:
            special_path = self.special_node_conversion(tree)
            if special_path is not None:
                special_path.orig_tree = tree
                self._add_path(TokenSNGram(special_path), still_open_paths, patterns)

    def _get_bottom_up_subtrees(self, tree):

        still_open_paths = []
        open_paths = []
        patterns = []

        if not tree.children:

            self._add_path(TokenSNGram(tree), still_open_paths, patterns)
            self._add_special_path(tree, still_open_paths, patterns)

        else:
            for child in tree.children:

                local_paths, local_patterns = self._get_bottom_up_subtrees(child)

                patterns.extend(local_patterns)
                open_paths.append(local_paths)

            still_open_paths = []
            for open_path_iter in itertools.product(*open_paths):
                open_path = TokenSNGram(SNGram.Tree(tree.token, open_path_iter))

                self._add_path(open_path, still_open_paths, patterns)
                self._add_special_path(tree, still_open_paths, patterns)

        return still_open_paths, patterns

    def extract_patterns(self, sentence):

        unique_patterns = []

        try:
            tree = sentence.to_tree()
        except conllu.parser.ParseException:
            return unique_patterns

        patterns = sorted(self._get_bottom_up_subtrees(tree)[1], key=lambda pattern: str(pattern))
        for _, g in itertools.groupby(patterns, key=lambda pattern: str(pattern)):
            unique_patterns.append(next(g))

        return unique_patterns

