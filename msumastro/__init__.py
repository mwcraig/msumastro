from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from .image_collection import ImageFileCollection
from .table_tree import TableTree

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
