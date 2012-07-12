import astrometry as ast
from astropysics import ccd
from os import path, rename
import sys
import numpy as np
import image_collection as tff
from image import ImageWithWCS

def astrometry_img_group(img_group, directory='.'):
    """
    Add astrometry to a set of images of the same object.

    Tries to save a bit of time by using the WCS file from the first
    successful fit as a starting guess for the remainer of the files
    in the group.
    """
    astrometry = False
    while not astrometry:
        for idx, img in enumerate(img_group):
            ra_dec = (img['ra'], img['dec'])
            img_file = path.join(directory,img['file'])
            astrometry = ast.add_astrometry(img_file, ra_dec=ra_dec,
                                            note_failure=True,
                                            overwrite=True,
                                            save_wcs=True)
            if astrometry:
                break
        else:
            break
        wcs_file = path.splitext(img_file)[0] + '.wcs'
        
        # loop over files, terminating when astrometry is successful.
            # at this stage want to *keep* the wcs file (need to modify
            # add_astrometry/call_astrometry to allow this)
        # save name of this wcs file.
    print idx, len(img_group)
    for img in img_group.rows(range(idx+1,len(img_group))):
        img_file = path.join(directory,img['file'])
        astrometry = ast.add_astrometry(img_file, ra_dec=ra_dec,
                                        note_failure=True,
                                        overwrite=True,
                                        verify=wcs_file)
        
    # loop over remaining files, with addition of --verify option to
    # add_astrometry (which I'll need to write)    

    
for currentDir in sys.argv[1:]:
    images = tff.ImageFileCollection(currentDir,
                                     keywords=['imagetyp', 'object',
                                               'wcsaxes', 'ra', 'dec'])
    summary = images.summary_info
    if len(summary) == 0:
        continue
    lights = summary.where((summary['imagetyp'] == 'LIGHT') &
                           (summary['wcsaxes'] == ''))

    print lights['file']
    can_group = ((lights['object'] != '') &
                 (lights['ra'] != '') &
                 (lights['dec'] != ''))

    if can_group.any():
        groupable = lights.where(can_group)
        objects = np.unique(groupable['object'])
        for obj in objects:
            astrometry_img_group(groupable.where(groupable['object']==obj),
                                 directory=currentDir)
    
    for light_file in lights.where(np.logical_not(can_group)):
        img = ImageWithWCS(path.join(currentDir,light_file['file']))
        try:
            ra = img.header['ra']
            dec = img.header['dec']
            ra_dec = (ra, dec)
        except KeyError:
            ra_dec = None

        if ra_dec is None:
            original_fname = path.join(currentDir,light_file['file'])
            root, ext = path.splitext(original_fname)
            f = open(root+'.blind','wb')
            f.close()
            continue
            
        astrometry = ast.add_astrometry(img.fitsfile.filename(), ra_dec=ra_dec,
                                        note_failure=True, overwrite=True)
        if astrometry and ra_dec is None:
            original_fname = path.join(currentDir,light_file['file'])
            root, ext = path.splitext(original_fname)
            #astrometry_fname = root+'.new'
            #new_fname = root+'_new.fit'
            # print new_fname, astrometry_fname
            #rename( astrometry_fname, new_fname)
            img_new = ImageWithWCS(original_fname)
            ra_dec = img_new.wcs_pix2sky(np.trunc(np.array(img_new.shape)/2))
            img_new.header.update('RA',ra_dec[0])
            img_new.header.update('DEC',ra_dec[1])
            img_new.save(img_new.fitsfile.filename(), clobber=True)
            

