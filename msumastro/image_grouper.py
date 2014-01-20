from collections import Iterable

from astropy.table import Table


class ImageGroup(object):
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
        Key which is used to indicate which row of the input table are in each
        group; it must be the name of one of the columns in `table`. Values of
        the index must uniquely identify rows of the table (in database
        parlance, index must be able to serve as a primary key for the table).

    Attributes
    ----------

    """
    def __init__(self, table, tree_keys, index_key):
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

    @property
    def table(self):
        return self._table

    @property
    def tree_keys(self):
        return self._tree_keys

    @property
    def index_key(self):
        return self._index_key
