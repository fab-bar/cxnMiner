import abc
import itertools

class Pattern(metaclass=abc.ABCMeta):
    """A pattern of any kind."""

    @property
    def length(self):
        return self._length


class TokenPattern(metaclass=abc.ABCMeta):
    """TokenPattern contain tokens with additional features (representad as dictionary)."""

    @abc.abstractmethod
    def get_pattern_list(self, features):
        """Generate the list of pattern when only features are used to represent elements."""
        pass # pragma: no cover


class SNGram(Pattern):
    """A syntactic n-gram is a subtree of a syntax tree with size n."""

    class Tree:

        def __init__(self, token, children):

            self.token = token
            self.children = children

    def _add_tree_length(self, head):

        self._length += 1
        if head.children is not None:
            for child in head.children:
                self._add_tree_length(child)

    def __init__(self, tree):

        self.tree = tree
        self._length = None

    @property
    def length(self):

        if self._length is None:
            self._length = 0
            self._add_tree_length(self.tree)

        return super().length

    def _get_subtree_str(self, head):

        tree_str = str(head.token)
        if head.children is not None:
            if len(head.children) == 1:
                tree_str += " " + self._get_subtree_str(head.children[0])
            else:
                tree_str += ' [' + ", ".join([self._get_subtree_str(child) for child in head.children]) + ']'

        return tree_str

    def __str__(self):
        """Follows the metalanguage of Grigori Sidorov (2013)"""

        return self._get_subtree_str(self.tree)


class TokenSNGram(SNGram, TokenPattern):

    def _map_tree(self, head, features):

        trees = []

        child_trees = []
        for child in head.children:
            child_trees.append(self._map_tree(child, features))

        if child_trees:
            children_iter = itertools.product(*child_trees)
        else:
            children_iter = [None]

        for feature, children in itertools.product(features, children_iter):

            trees.append(SNGram.Tree(head.token[feature], children))

        return trees

    def get_pattern_list(self, features=frozenset(['form'])):

        return [SNGram(tree) for tree in self._map_tree(self.tree, features)]
