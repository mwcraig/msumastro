from .fitskeyword import FITSKeyword
try:
    from .feder import Feder
except ImportError:
    pass
from .patchers import *
from .astrometry import *
