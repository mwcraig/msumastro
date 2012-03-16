import astrometry as ast
from astropysics import ccd
from os import path, rename
import sys
import numpy as np
import triage_fits_files as tff
from image import ImageWithWCS

for currentDir in sys.argv[1:]:
    images = tff.ImageFileCollection(currentDir, keywords=['imagetyp'])
    summary = images.summary_info
    lights = summary.where(summary['imagetyp'] == 'LIGHT')
    for light_file in lights:
        img = ImageWithWCS(path.join(currentDir,light_file['file']))
        try:
            ra = img.header['ra']
            dec = img.header['dec']
            ra_dec = (ra, dec)
        except KeyError:
            ra_dec = None
        astrometry = ast.add_astrometry(img.fitsfile.filename(), ra_dec=ra_dec,
                                        note_failure=True)
        if astrometry and ra_dec is None:
            original_fname = path.join(currentDir,light_file['file'])
            root, ext = path.splitext(original_fname)
            astrometry_fname = root+'.new'
            new_fname = root+'_new.fit'
            print new_fname, astrometry_fname
            rename( astrometry_fname, new_fname)
            img_new = ImageWithWCS(new_fname)
            ra_dec = img_new.wcs_pix2sky(np.trunc(img_new.shape))
            img_new.header.update('RA',ra_dec[0])
            img_new.header.update('DEC',ra_dec[1])
            img_new.save(img_new.fitsfile.filename(), clobber=True)
            

