from collections import Iterable
from itertools import izip

from astropy.table import Table


class RecursiveTree(dict):
    """docstring for RecursiveTree"""
    def __init__(self):
        super(RecursiveTree, self).__init__()

    def __missing__(self, key):
        """
        Add the method that makes this tree recursive

        When an unknown key is encountered its default value is an empty
        instance of a RecursiveTree.

        Idea is from `Stack Overflow
        <http://stackoverflow.com/questions/6780952/how-to-change-behavior-of-dict-for-an-instance>`_
        """
        value = self[key] = type(self)()
        return value

    def add_keys(self, keys, value=None):
        for key in keys[:-1]:
            self = self[key]
        if value is not None:
            self[keys[-1]] = value
        else:
            self = self[keys[-1]]


class TableTree(RecursiveTree):
    """
    Base class for grouping images hierarchically into a tree based on metadata

    This class can be used directly, though subclasses for a few common cases
    are provided in this package.

    Parameters
    ----------
    table : astropy.table.Table instance
        Table containing the metadata to be used for grouping images.
    tree_keys : list of str
        Keys to be used in grouping images. Each key must be the name of a
        column in `table`.
    index_key : str
        Key which is used to indicate which rows of the input table are in each
        group; it must be the name of one of the columns in `table`. Values of
        the index must uniquely identify rows of the table (in database
        parlance, index must be able to serve as a primary key for the table).

    Attributes
    ----------
    table
    tree_keys
    index_key

    Raises
    ------
    TypeError
        Raised if the number of initialization arguments is incorrect or the
        types of any of the arguments is incorrect.
    """
    def __init__(self, *args):
        super(TableTree, self).__init__()
        if not args:
            return

        if len(args) != 3:
            raise TypeError("TableTree must be initialized with three "
                            "arguments")
        table = args[0]
        tree_keys = args[1]
        index_key = args[2]

        if not isinstance(table, Table):
            raise TypeError('First argument must be an '
                            'astropy.table.Table instance')
        if (isinstance(tree_keys, basestring) or
                not isinstance(tree_keys, Iterable)):
            raise TypeError('Second argument must be list-like but not '
                            'a single string.')
        if not isinstance(index_key, basestring):
            raise TypeError('Third argument must be a string.')
        self._table = table
        self._tree_keys = tree_keys
        self._validate_group_keys()
        self._index_key = index_key
        self._validate_index()
        self._build_tree()

    def _validate_group_keys(self):
        """
        Each key must be a table column name.
        """
        for key in self._tree_keys:
            try:
                self._table[key]
            except KeyError:
                raise

    def _validate_index(self):
        """
        The rows in the `table` column named `index` must be unique and `index`
        must be a column in the table. The second case is raised automatically
        by astropy.table.Table
        """
        index_column = self._table[self._index_key]
        if len(set(index_column)) != len(self._table):
            raise ValueError('The table column named {0} cannot be used as '
                             'and index because its values are '
                             'not unique'.format(self._index_key))

    def _build_tree(self):
        """
        Construct tree from grouping done by astropy table

        Because the tree is constructed
        """
        grouped = self.table.group_by(self.tree_keys)
        columns = list(self.tree_keys)
        columns.append(self.index_key)
        for group_key, members in izip(grouped.groups.keys,
                                       grouped.groups):
            key_list = list(group_key)  # table rows can't be indexed w/slice
            indexes = list(members[self.index_key])
            self.add_keys(key_list, value=indexes)

    @property
    def table(self):
        """
        astropy.table.Table of metadata used to group rows.
        """
        return self._table

    @property
    def tree_keys(self):
        """
        list of str, Table columns to be used in grouping the rows.
        """
        return self._tree_keys

    @property
    def index_key(self):
        """
        str, Name of column whose values uniquely identify each row.
        """
        return self._index_key

    def walk(self, *args, **kwd):
        """
        Walk the grouped tree

        The functionality provided is similar to that in os.walk: starting at
        the top of tree, yield a tuple of return values indicating parents,
        children and rows at each level of the tree.

        Parameters
        ----------
        None

        Returns
        -------
        parents, children, index : lists
        parents : list
            Dictionary keys that led to this return
        children : list
            Child nodes at this level
        index : list
            Index values for the items in the table that correspond to the
            values in `parents`
        """

        parent = kwd.pop("parent", [])
        if args:
            use_dict = args[0]
        else:
            use_dict = self

        try:
            tree_nodes = use_dict.keys()
            indexes = []
            yield parent, tree_nodes, indexes
        except AttributeError:
            tree_nodes = []
            yield parent, tree_nodes, use_dict

        for node in tree_nodes:
            new_parent = list(parent)
            new_parent.append(node)
            for val in self.walk(use_dict[node], parent=new_parent):
                yield val
