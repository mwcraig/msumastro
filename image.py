import numpy as np
from astropysics import ccd
import pywcs

class ImageWithWCS(ccd.FitsImage):
     """Astropysics FitsImage with astrometric functions"""

     def __init__(self, fnordata):
         ccd.FitsImage.__init__(self, fnordata)
         self._wcs = pywcs.WCS(self.header)
         
     @property
     def header(self):
         """FITS header for this file"""
         return self.fitsfile[0].header

     @property
     def wcs(self):
         """pyWCS object for this file"""
         return self._wcs
         
     def shift(self, int_shift, in_place=False):
         """
         Shift image by an integer number of pixels without
         interpolation.
         
         `int_shift` is a tuple, numpy array or list of integers
         (floats will be rounded).

         If `in_place` is true the image is shifted in place, and the
         wcs reference pixel is updated appropriately.
         """
         from scipy import ndimage

         if (np.int32(np.array(int_shift)) !=
             np.array(int_shift)).any():
             raise ValueError('Shift must be integer amount!')

         res = ndimage.shift(self.data, int_shift, order=0)

         if in_place:
             self._applyArray(None, res)
             self.header['crpix1'] += int_shift[0]
             self.header['crpix2'] += int_shift[1]
             self._wcs = pywcs.WCS(self.header)

             #raise RuntimeWarning('salf.data and fitsfile data are now inconsistent.')
             res = None
             
         return res
             
         

     def wcs_pix2sky(self, pix, **kwargs):
         """
          Wrapper around pywcs function that handles a single tuple
         gracefully.
         
         `pix` must be a numpy array either of dimension 2
         (e.g. [xpix, ypix]) or an Nx2 array if you want sky
         coordinates at several points.
         
         Returns a numpy array of the same format as `pix`,

         TO DO: always  in the order (ra, dec). pywcs ra_dec_order is broken?
         """
        
         return self._wcs_wrapper(pix, self.wcs.wcs_pix2sky, **kwargs)

     def wcs_sky2pix(self, sky, **kwargs):
         """Wrapper around pyWCS function that handles a single tuple
         gracefully.
         
         `pix` must be a numpy array either of dimension 2
         (e.g. [xpix, ypix]) or an Nx2 array if you want sky
         coordinates at several points.
         
         Returns a numpy array of the same format as `pix`,

         TO DO: always  in the order (ra, dec). pywcs ra_dec_order is
         broken?
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
             use_pix=inp
             return_1d_array = False
             
         ret = transform(use_pix, 1, **kwargs) #1 bc it is a fits file
         if return_1d_array:
             ret = ret[0]

         return ret

     def save(self, fname):
         ccd.FitsImage.save(self, fname, clobber=False)
