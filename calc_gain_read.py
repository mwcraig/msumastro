from os import path
import logging

import numpy as np
from astropysics import ccd

from image_collection import ImageFileCollection
from ccd_characterization import ccd_gain, ccd_read_noise

logger = logging.getLogger(__name__)


def as_images(tbl, src_dir):
    img = []
    for tb in tbl:
        img.append(ccd.FitsImage(path.join(src_dir, tb['file'])).data[1:, :])
    return img


def calc_gain_read(src_dir):
    """Calculate gain and read noise from images in `src_dir`

    Uses biases and any R band flats that are present.
    """
    img_col = ImageFileCollection(location=src_dir,
                                  keywords=['imagetyp', 'filter'],
                                  info_file=None)
    img_tbl = img_col.summary_info
    bias_tbl = img_tbl[(img_tbl['imagetyp'] == 'BIAS')]
    biases = as_images(bias_tbl, src_dir)
    r_flat_tbl = img_tbl[((img_tbl['imagetyp'] == 'FLAT') &
                          (img_tbl['filter'] == 'R'))]
    r_flats = as_images(r_flat_tbl, src_dir)
    n_files = len(biases)
    gain = []
    read_noise = []
    for i in range(0, n_files, 2):
        print biases[i].shape
        gain.append(ccd_gain(biases[i:i + 2], r_flats[i:i + 2]))
        read_noise.append(ccd_read_noise(biases[i:i + 2], gain=gain[-1]))
    return (np.array(gain), np.array(read_noise))
