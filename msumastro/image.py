import logging

import numpy as np
from scipy import ndimage
from astropy import wcs
from astropy.io import fits

logger = logging.getLogger(__name__)


class ImageWithWCS(object):

    """
    FITS image with WCS
        
    A FITS images with a few convenience methods defined, including easy
    access to WCS transforms.

    Parameters
    ----------
    filepath : str
        Path to the FITS file.
    kwd : dict, optional
        All keywords are passed through to astropy.io.fits.open

    Attributes
    ----------
    data
    header
    wcs
    """

    def __init__(self, filepath, **kwd):
        self.fitsfile = fits.open(filepath, **kwd)
        self._wcs = wcs.WCS(self.header)

    @property
    def header(self):
        """FITS header for this file"""
        return self.fitsfile[0].header

    @property
    def wcs(self):
        """WCS object for this file"""
        return self._wcs

    @property
    def data(self):
        """Image data; will be scaled by default using BZERO and BSCALE"""
        return self.fitsfile[0].data

    @data.setter
    def data(self, array):
        """Set image data to numpy array"""
        self.fitsfile[0].data = array

    def shift(self, int_shift, in_place=False):
        """
        Shift image by an integer number of pixels without
        interpolation.

        Parameters
        ----------
        int_shift : list-like of two integers
            Amount by which image should be shifted; floats will be rounded.

        in_place : bool, optional 
            If ``True`` the image is shifted in place, and the wcs reference
            pixel is updated appropriately. Otherwise an array is returned
            that is shifted with no WCS information.

        Raises
        ------
        ValueError
            If the shift is not by an integer amount.
        """
        if (np.int32(np.array(int_shift)) !=
                np.array(int_shift)).any():
            raise ValueError('Shift must be integer amount!')

        res = ndimage.shift(self.data, int_shift, order=0)

        if in_place:
            self.fitsfile[0].data = res
            # Indices for int_shift below ARE CORRECT because FITS axis
            # order is opposite that of numpy.
            self.header['crpix1'] += int_shift[1]
            self.header['crpix2'] += int_shift[0]
            self._wcs = wcs.WCS(self.header)
            res = None

        return res

    def wcs_pix2sky(self, pix, **kwargs):
        """
        Wrapper around astropy.wcs function that handles a single tuple
        gracefully.

        Parameters
        ----------
        pix : numpy array either of dimension 2 (e.g. [xpix, ypix]) or Nx2
            Pixel positions at which sky coordinates should be calculated.

        Returns
        -------
        numpy.ndarray with same shape as pix.
            Sky coordinates for each input pixel.
        """

        return self._wcs_wrapper(pix, self.wcs.wcs_pix2sky, **kwargs)

    def wcs_sky2pix(self, sky, **kwargs):
        """
        Wrapper around astropy.wcs function that handles a single tuple
        gracefully.

        Parameters
        ----------
        sky : numpy array either of dimension 2 (e.g. [xpix, ypix]) or Nx2
            Pixel positions at which sky coordinates should be calculated.

        Returns
        -------
        numpy.ndarray with same shape as sky.
            Pixel positions for each input sky coordinate.
        """
        return self._wcs_wrapper(sky, self.wcs.wcs_sky2pix, **kwargs)

    def _wcs_wrapper(self, inp, transform, **kwargs):
        """"Actually handles the wrapping"""
        if not isinstance(inp, np.ndarray):
            raise TypeError('inp must be a numpy array')

        if inp.ndim == 1:
            use_pix = np.array(inp, ndmin=2)
            return_1d_array = True
        else:
            use_pix = inp
            return_1d_array = False

        ret = transform(use_pix, 1, **kwargs)  # 1 bc it is a fits file
        if return_1d_array:
            ret = ret[0]

        return ret

    def save(self, fname, clobber=False):
        """
        Save FITS file.

        Parameters
        ----------
        fname : str
            Name of the file to save to

        clobber : bool, optional
            Set to ``True`` to overwrite an existing file.
        """
        self.fitsfile.writeto(fname, clobber=clobber)

    def close(self):
        """Close the file associated with this FITS image."""
        self.fitsfile.close()
