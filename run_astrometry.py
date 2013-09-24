"""
DESCRIPTION
-----------
    For each directory provided on the command line add
    astrometry to the light files (those with ``IMAGETYP='LIGHT'`` in
    the FITS header).

    By default, astrometry is added only for those files with pointing
    information in the header (specifically, RA and Dec) because blind
    astrometry is fairly slow. It may be faster to insert RA/Dec into
    those files before doing astrometry.

    The functions called by this script set the WCS reference pixel
    to the center of the image, which turns out to make aligning images
    a little easier.

    For more control over the parameters see :func:`add_astrometry`
    and for even more control, :func:`call_astrometry`.

    .. Note::
        This script is **NOT RECURSIVE**; it will not process files in
        subdirectories of the the directories supplied on the command line.

    .. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

EXAMPLES

    Invoking this script from the command line::

        python run_astrometry.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from run_patch import patch_directories
        patch_directories('/my/folder/of/images')


"""
import astrometry as ast
from os import path
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
            img_file = path.join(directory, img['file'])
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
    for img in img_group[range(idx + 1, len(img_group))]:
        img_file = path.join(directory, img['file'])
        astrometry = ast.add_astrometry(img_file, ra_dec=ra_dec,
                                        note_failure=True,
                                        overwrite=True,
                                        verify=wcs_file)

    # loop over remaining files, with addition of --verify option to
    # add_astrometry (which I'll need to write)


def astrometry_for_directory(directories,
                             group_by_object=False,
                             blind=False):
    for currentDir in directories:
        images = tff.ImageFileCollection(currentDir,
                                         keywords=['imagetyp', 'object',
                                                   'wcsaxes', 'ra', 'dec'])
        summary = images.summary_info
        if len(summary) == 0:
            continue
        lights = summary[((summary['imagetyp'] == 'LIGHT') &
                          (summary['wcsaxes'] == ''))]

        print lights['file']
        can_group = ((lights['object'] != '') &
                     (lights['ra'] != '') &
                     (lights['dec'] != ''))
        can_group &= group_by_object

        if can_group.any():
            groupable = lights[can_group]
            objects = np.unique(groupable['object'])
            for obj in objects:
                astrometry_img_group(groupable[(groupable['object'] == obj)],
                                     directory=currentDir)

        for light_file in lights[np.logical_not(can_group)]:
            img = ImageWithWCS(path.join(currentDir, light_file['file']))
            try:
                ra = img.header['ra']
                dec = img.header['dec']
                ra_dec = (ra, dec)
            except KeyError:
                ra_dec = None

            if (ra_dec is None) and (not blind):
                original_fname = path.join(currentDir, light_file['file'])
                root, ext = path.splitext(original_fname)
                f = open(root + '.blind', 'wb')
                f.close()
                continue

            astrometry = ast.add_astrometry(img.fitsfile.filename(),
                                            ra_dec=ra_dec,
                                            note_failure=True,
                                            overwrite=True)

            if astrometry and ra_dec is None:
                original_fname = path.join(currentDir, light_file['file'])
                root, ext = path.splitext(original_fname)
                img_new = ImageWithWCS(original_fname)
                ra_dec = img_new.wcs_pix2sky(np.trunc(np.array(img_new.shape) / 2))
                img_new.header['RA'] = ra_dec[0]
                img_new.header['DEC'] = ra_dec[1]
                img_new.save(img_new.fitsfile.filename(), clobber=True)


def construct_parser():
    import script_helpers
    import argparse

    parser = argparse.ArgumentParser()
    script_helpers.setup_parser_help(parser, __doc__)
    script_helpers.add_verbose(parser)
    script_helpers.add_directories(parser)

    group_help = 'attempt to speed up astrometry by using WCS from one image '
    group_help += 'of an object as initial guess for others; may very well '
    group_help += 'NOT speed things up.'
    parser.add_argument('-g', '--group-by-object',
                        help=group_help, action='store_true')

    blind_help = 'Turn ON blind astrometry; '
    blind_help += 'disabled by default because it is so slow.'
    parser.add_argument('-b', '--blind',
                        help=blind_help, action='store_true')

    return parser

if __name__ == "__main__":
    parser = construct_parser()
    parser.parse_args()
    args = parser.parse_args()
    print dir(args)
    astrometry_for_directory(args.directories,
                             group_by_object=args.group_by_object,
                             blind=args.blind)
