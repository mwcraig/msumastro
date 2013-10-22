import logging

import astropy.io.fits as fits

logger = logging.getLogger(__name__)


def image_gen(filein, data=None, fileout=None):
    hdulist = fits.open(filein)
    primary = hdulist[0]
    primary.data = data
    if fileout is not None:
        hdulist.writeto(fileout)
