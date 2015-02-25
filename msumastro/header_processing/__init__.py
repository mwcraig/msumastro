from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from .fitskeyword import FITSKeyword
try:
    from .feder import Feder
except ImportError:
    pass
from .patchers import *
from .astrometry import *
