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

        run_astrometry.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from msumastro.scripts import run_astrometry
        run_astrometry.main(['/my/folder/of/images'])
"""
from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import shutil
from os import path, getcwd
import logging

import numpy as np

from astropy.io import fits
import astropy.units as u
from astropy.coordinates import SkyCoord

from ccdproc import CCDData

from ..customlogger import console_handler, add_file_handlers
from ..header_processing import astrometry as ast
from .. import ImageFileCollection
from .script_helpers import (construct_default_parser, setup_logging,
                             handle_destination_dir_logging_check,
                             _main_function_docstring)

logger = logging.getLogger()
screen_handler = console_handler()
logger.addHandler(screen_handler)


def astrometry_for_directory(directories,
                             destination=None,
                             no_log_destination=False,
                             blind=False,
                             custom_sextractor=False,
                             odds_ratio=None,
                             astrometry_config=None,
                             camera=None):
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

    for currentDir in directories:
        images = ImageFileCollection(currentDir,
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

            original_fname = path.join(working_dir, light_file)
            img = CCDData.read(original_fname, unit='adu')
            try:
                ra = img.header['ra']
                dec = img.header['dec']
                ra_dec = (ra, dec)
            except KeyError:
                ra_dec = None

            if (ra_dec is None) and (not blind):
                root, ext = path.splitext(original_fname)
                f = open(root + '.blind', 'wb')
                f.close()
                continue

            astrometry = ast.add_astrometry(original_fname,
                                            ra_dec=ra_dec,
                                            note_failure=True,
                                            overwrite=True,
                                            custom_sextractor=custom_sextractor,
                                            odds_ratio=odds_ratio,
                                            astrometry_config=astrometry_config,
                                            camera=camera)

            with fits.open(original_fname,
                           do_not_scale_image_data=True) as f:
                try:
                    del f[0].header['imageh'], f[0].header['imagew']
                    f.writeto(original_fname, clobber=True)
                except KeyError:
                    pass

            if astrometry and ra_dec is None:
                root, ext = path.splitext(original_fname)
                img_new = CCDData.read(original_fname, unit='adu')

                # The ndmin below ensures center_pix has the right shape
                # for WCS conversion.
                center_pix = np.trunc(np.array(img_new.shape, ndmin=2) / 2)
                print(center_pix[np.newaxis, :].shape)
                ra_dec = \
                    img_new.wcs.all_pix2world(center_pix,
                                              1)
                ra_dec = ra_dec[0]
                # RA/Dec are in degrees. Convert them to sexagesimal for
                # output. Yuck, but makes it easier for existing code to
                # handle.
                # Note that FK5 is J2000.
                coords = SkyCoord(*ra_dec, unit=(u.degree, u.degree),
                                  frame='fk5')

                img_new.header['RA'] = coords.ra.to_string(unit=u.hour,
                                                           sep=':')
                img_new.header['DEC'] = coords.dec.to_string(sep=':')
                img_new.write(original_fname, clobber=True)


def construct_parser():
    parser = construct_default_parser(__doc__)

    blind_help = 'Turn ON blind astrometry; '
    blind_help += 'disabled by default because it is so slow.'
    parser.add_argument('-b', '--blind',
                        help=blind_help, action='store_true')
    parser.add_argument('-c', '--custom-sextractor', action='store_true',
                        help='Use Feder-specific SExtractor settings')
    parser.add_argument('-o', '--odds-ratio', action='store',
                        help='Change the odds-ratio for accepting a match'
                             ' from the default of 1e9.')
    parser.add_argument('--astrometry-config', action='store',
                        help='File to use for configuring astrometry engine, '
                             'including, e.g., the location of index files.')
    parser.add_argument('--camera', action='store',
                        help='Name of camera; used to set pixel scale in '
                             'solve. If omitted, uses settings for Apogee '
                             'Alta U9.')

    return parser


def main(arglist=None):
    """See script_helpers._main_function_docstring for actual documentation
    """

    parser = construct_parser()
    args = parser.parse_args(arglist)

    setup_logging(logger, args, screen_handler)

    add_file_handlers(logger, getcwd(), 'run_astrometry')

    do_not_log_in_destination = handle_destination_dir_logging_check(args)

    astrometry_for_directory(args.dir,
                             destination=args.destination_dir,
                             blind=args.blind,
                             custom_sextractor=args.custom_sextractor,
                             no_log_destination=do_not_log_in_destination,
                             odds_ratio=args.odds_ratio,
                             astrometry_config=args.astrometry_config,
                             camera=args.camera)


main.__doc__ = _main_function_docstring(__name__)
