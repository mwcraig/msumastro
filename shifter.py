from os import path
import logging

import numpy as np

from image import ImageWithWCS

logger = logging.getLogger(__name__)


def shift_images(files, source_dir, output_file='_shifted'):
    """Align images based on astrometry."""

    ref = files[0]  # TODO: make reference image an input
    ref_im = ImageWithWCS(path.join(source_dir, ref))
    ref_pix = np.int32(np.array(ref_im.data.shape) / 2)
    ref_ra_dec = ref_im.wcs_pix2sky(ref_pix)
    base, ext = path.splitext(files[0])
    ref_im.save(path.join(source_dir, base + output_file + ext))
    for fil in files[1:]:
        img = ImageWithWCS(path.join(source_dir, fil))
        ra_dec_pix = img.wcs_sky2pix(ref_ra_dec)
        shift = ref_pix - np.int32(ra_dec_pix)
        # FITS order of axes opposite of numpy, so swap:
        shift = shift[::-1]
        img.shift(shift, in_place=True)
        base, ext = path.splitext(fil)
        img.save(path.join(source_dir, base + output_file + ext))
