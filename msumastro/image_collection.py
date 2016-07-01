from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import logging
import warnings

from ccdproc import ImageFileCollection as RealIFC

logger = logging.getLogger(__name__)

__all__ = ['ImageFileCollection']


class ImageFileCollection(RealIFC):
    def __init__(self, *arg, **kwd):
        warnings.warn("ImageFileCollection will be removed from msumastro "
                      "in the next release. Import it from ccdproc instead.",
                      DeprecationWarning)
        super(ImageFileCollection, self).__init__(*arg, **kwd)
