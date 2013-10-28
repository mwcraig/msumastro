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
        specified on the command line unless you use the --destination-dir
        option.

EXAMPLES
--------

    Invoking this script from the command line::

        python run_astrometry.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from run_astrometry import astrometry_for_directory
        astrometry_for_directory('/my/folder/of/images')


"""
import astrometry as ast
import shutil
import numpy as np
import image_collection as tff
from image import ImageWithWCS

import logging
from customlogger import console_handler, add_file_handlers

logger = logging.getLogger()
screen_handler = console_handler()
logger.addHandler(screen_handler)


def astrometry_for_directory(directories,
                             destination=None,
                             no_log_destination=False,
                             blind=False):
    """
    Add astrometry to files in list of directories

    Parameters
    ----------

    directories : str or list of str
        Directory or directories whose FITS files are to be processed.

    blind : bool, optional
        Set to True to force blind astrometry. False by default because
        blind astrometry is slow.
    """
    from os import path

    for currentDir in directories:
        images = tff.ImageFileCollection(currentDir,
                                         keywords=['imagetyp', 'object',
                                                   'wcsaxes', 'ra', 'dec'])
        summary = images.summary_info
        if len(summary) == 0:
            continue
        logger.debug('\n %s', '\n'.join(summary.pformat()))
        lights = summary[((summary['imagetyp'] == 'LIGHT') &
                          (summary['wcsaxes'].mask))]

        working_dir = destination if destination is not None else currentDir
        if (not no_log_destination) and (destination is not None):
            add_file_handlers(logger, working_dir, 'run_astrometry')

        logger.debug('About to loop over %d files', len(lights['file']))
        for light_file in lights['file']:
            if ((destination is not None) and (destination != currentDir)):
                src = path.join(currentDir, light_file)
                shutil.copy(src, destination)

            img = ImageWithWCS(path.join(working_dir, light_file))
            try:
                ra = img.header['ra']
                dec = img.header['dec']
                ra_dec = (ra, dec)
            except KeyError:
                ra_dec = None

            if (ra_dec is None) and (not blind):
                original_fname = path.join(working_dir, light_file)
                root, ext = path.splitext(original_fname)
                f = open(root + '.blind', 'wb')
                f.close()
                continue

            astrometry = ast.add_astrometry(img.fitsfile.filename(),
                                            ra_dec=ra_dec,
                                            note_failure=True,
                                            overwrite=True)

            if astrometry and ra_dec is None:
                original_fname = path.join(working_dir, light_file)
                root, ext = path.splitext(original_fname)
                img_new = ImageWithWCS(original_fname)
                ra_dec = img_new.wcs_pix2sky(np.trunc(np.array(img_new.shape) / 2))
                img_new.header['RA'] = ra_dec[0]
                img_new.header['DEC'] = ra_dec[1]
                img_new.save(img_new.fitsfile.filename(), clobber=True)

from script_helpers import construct_default_parser


def construct_parser():
    parser = construct_default_parser(__doc__)

    blind_help = 'Turn ON blind astrometry; '
    blind_help += 'disabled by default because it is so slow.'
    parser.add_argument('-b', '--blind',
                        help=blind_help, action='store_true')

    return parser

if __name__ == "__main__":
    from os import getcwd
    from script_helpers import (setup_logging,
                                handle_destination_dir_logging_check)

    parser = construct_parser()
    args = parser.parse_args()

    setup_logging(logger, args, screen_handler)

    add_file_handlers(logger, getcwd(), 'run_astrometry')

    do_not_log_in_destination = handle_destination_dir_logging_check(args)

    astrometry_for_directory(args.dir,
                             destination=args.destination_dir,
                             blind=args.blind,
                             no_log_destination=do_not_log_in_destination)
