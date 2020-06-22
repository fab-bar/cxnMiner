import abc
import hashlib
import itertools

class Pattern(metaclass=abc.ABCMeta):
    """A pattern of any kind."""

    @property
    def length(self):
        return self._length

    @classmethod
    @abc.abstractmethod
    def specialElements(cls):
        pass # pragma: no cover

    @abc.abstractmethod
    def get_element_list(self):
        pass # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def from_element_list(cls, element_list):
        pass # pragma: no cover

    def get_pattern_profile(self, get_hash=True):

        if isinstance(self, TokenPattern):
            raise TypeError("TokenPattern has no profile")

        pattern_type = " ".join([getattr(element, "level", element) for element in self.get_element_list()])

        if get_hash:
            return hashlib.md5(pattern_type.encode()).hexdigest()
        else:
            return pattern_type


class TokenPattern(metaclass=abc.ABCMeta):
    """TokenPattern contain tokens with additional features (representad as dictionary)."""

    @abc.abstractmethod
    def get_pattern_list(self, features):
        """Generate the list of pattern when only features are used to represent elements."""
        pass # pragma: no cover

    @abc.abstractmethod
    def get_base_pattern(self, feature):
        """Generate the pattern where only feature is used to represent elements."""
        pass # pragma: no cover

class PatternElement:

    def __init__(self, form, level=None, order_id=None):

        self.form = form
        self.level = level
        self.order_id = order_id

    def __repr__(self):

        return "_".join([self.level, str(self.form)])

    def __str__(self):

        return str(self.form)

    def __eq__(self, other):

        return (
            self.__class__ == other.__class__ and
            self.form == other.form and
            self.level == other.level and
            self.order_id == other.order_id
        )

    def __hash__(self):

        return hash(self.form + '_' + self.level)

class SNGram(Pattern):
    """A syntactic n-gram is a subtree of a syntax tree with size n."""

    class Tree:

        def __init__(self, token, children, orig_tree=None):

            self.token = token
            self.children = children
            self.orig_tree = orig_tree

        def __eq__(self, other):

            return (
                self.__class__ == other.__class__ and
                self.token == other.token and
                self.children == other.children
            )

    def _add_tree_length(self, head):

        self._length += 1
        if head.children is not None:
            for child in head.children:
                self._add_tree_length(child)

    def __init__(self, tree,
                 left_bracket=None, right_bracket=None, comma=None):

        self.tree = tree
        self._length = None

        if left_bracket is not None:
            self.LEFT_BRACKET = left_bracket
        if right_bracket is not None:
            self.RIGHT_BRACKET = right_bracket
        if comma is not None:
            self.COMMA = comma

    def __eq__(self, other):

        return (
            self.__class__ == other.__class__ and
            self.tree == other.tree
        )

    @property
    def length(self):

        if self._length is None:
            self._length = 0
            self._add_tree_length(self.tree)

        return super().length

    LEFT_BRACKET = "["
    RIGHT_BRACKET = "]"
    COMMA = ","

    @classmethod
    def specialElements(cls):
        return [cls.LEFT_BRACKET, cls.RIGHT_BRACKET, cls.COMMA]

    def _get_subtree_list(self, head):

        element_list = [head.token]

        if head.children is not None and len(head.children) >= 1:
            if len(head.children) == 1:
                element_list.extend(self._get_subtree_list(head.children[0]))
            else:
                element_list.append(self.LEFT_BRACKET)
                for child in head.children:
                    element_list.extend(self._get_subtree_list(child))
                    element_list.append(self.COMMA)
                element_list[-1] = self.RIGHT_BRACKET

        return element_list

    def get_element_list(self):

        return self._get_subtree_list(self.tree)

    @classmethod
    def _tree_from_element_list(cls, element_list,
                                left_bracket=None, right_bracket=None, comma=None):

        if left_bracket is None:
            left_bracket = cls.LEFT_BRACKET
        if right_bracket is None:
            right_bracket = cls.RIGHT_BRACKET
        if comma is None:
            comma = cls.COMMA

        ## split into head and rest
        head = element_list[0]
        rest = element_list[1:]

        if not rest:
            return [cls.Tree(head, None)]
        elif rest[0] == left_bracket:

            ## get closing bracket
            open_brackets = 1
            closing_index = 0

            ## get parts separated by comma
            parts = []
            while open_brackets:

                closing_index += 1
                if rest[closing_index] == right_bracket:
                    open_brackets -= 1
                elif rest[closing_index] == left_bracket:
                    open_brackets += 1
                elif open_brackets == 1 and rest[closing_index] == comma:
                    parts.append(closing_index)

            parts.append(closing_index)
            children = []
            start = 1
            for part in parts:
                children.extend(cls._tree_from_element_list(rest[start:part],
                                                            left_bracket, right_bracket, comma))
                start = part + 1

            children = tuple(children)

            trees = [cls.Tree(head, tuple(children))]

            if closing_index + 1 < len(rest):
                ## should not happen as parts in brackets are extracted
                raise ValueError("Could not convert element list.")  # pragma: no cover

            return tuple(trees)

        elif rest[0] == comma:
            ## should only happen when there appears a comma that is not enclosed in brackets
            ## which is not allowed
            raise ValueError("Could not convert element list: Syntactic n-grams need a single head.")  # pragma: no cover
        else:
            ## next element is a pattern element
            return (cls.Tree(head, tuple(cls._tree_from_element_list(rest, left_bracket, right_bracket, comma))),)

    @classmethod
    def from_element_list(cls, element_list,
                          left_bracket=None, right_bracket=None, comma=None):

        return cls(cls._tree_from_element_list(element_list, left_bracket, right_bracket, comma)[0],
                   left_bracket, right_bracket, comma)

    def __str__(self):
        """Follows the metalanguage of Grigori Sidorov (2013)"""

        return " ".join(
            map(lambda x: str(x), self.get_element_list())
        ).replace(" " + self.COMMA, self.COMMA
        ).replace(self.LEFT_BRACKET + " ", self.LEFT_BRACKET
        ).replace(" " + self.RIGHT_BRACKET, self.RIGHT_BRACKET)


class TokenSNGram(SNGram, TokenPattern):

    def _map_tree(self, head, features, use_orig=False):

        trees = []
        if use_orig and getattr(head, 'orig_tree', None) is not None:
            head = head.orig_tree

        child_trees = []
        for child in head.children:
            child_trees.append(self._map_tree(child, features, use_orig))

        if child_trees:
            children_iter = itertools.product(*child_trees)
        else:
            children_iter = [None]

        for feature, children in itertools.product(features, children_iter):

            if feature in head.token:

                trees.append(SNGram.Tree(
                    PatternElement(head.token[feature], feature, order_id=head.token.get('id', None)), children))

        return trees

    def get_pattern_list(self, features=frozenset(['form'])):

        return [SNGram(tree, self.LEFT_BRACKET, self.RIGHT_BRACKET, self.COMMA)
                for tree in self._map_tree(self.tree, features)]

    def get_base_pattern(self, feature='form'):

        tree_list = self._map_tree(self.tree, [feature], use_orig=True)

        ## make sure that only one pattern is returned
        if len(tree_list) > 1:
            raise RuntimeError("Created more than one pattern.") # pragma: no cover

        return SNGram(tree_list[0], self.LEFT_BRACKET, self.RIGHT_BRACKET, self.COMMA)

    def _return_orig_tree(self, head):

        if getattr(head, 'orig_tree', None) is not None:
            head = head.orig_tree
        return SNGram.Tree(head.token, [ self._return_orig_tree(child) for child in head.children ])

    def get_full_pattern(self):

        return TokenSNGram(self._return_orig_tree(self.tree), self.LEFT_BRACKET, self.RIGHT_BRACKET, self.COMMA)
