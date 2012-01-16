import astrometry as ast
from astropysics import ccd
from os import path
import sys
import triage_fits_files as tff

for currentDir in sys.argv[1:]:
    images = tff.ImageFileCollection(currentDir, keywords=['imagetyp'])
    summary = images.summary_info
    lights = summary.where(summary['imagetyp'] == 'LIGHT')
    for light_file in lights:
        img = ccd.FitsImage(path.join(currentDir,light_file['file']))
        try:
            ra = img.fitsfile[0].header['ra']
            dec = img.fitsfile[0].header['dec']
            ra_dec = (ra, dec)
        except KeyError:
            ra_dec = None
        astrometry = ast.add_astrometry(img.fitsfile.filename(), ra_dec=ra_dec,
                          note_failure=True)

