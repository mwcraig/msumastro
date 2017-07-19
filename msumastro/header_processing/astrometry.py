from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import logging
import subprocess
from os import path, remove, rename
import tempfile
from textwrap import dedent

from astropy.extern import six

__all__ = ['call_astrometry', 'add_astrometry']

logger = logging.getLogger(__name__)


def call_astrometry(filename, sextractor=False,
                    custom_sextractor_config=False, feder_settings=True,
                    no_plots=True, minimal_output=True,
                    save_wcs=False, verify=None,
                    ra_dec=None, overwrite=False,
                    wcs_reference_image_center=True,
                    odds_ratio=None,
                    astrometry_config=None,
                    additional_args=None):
    """
    Wrapper around astrometry.net solve-field.

    Parameters
    ----------
    sextractor : bool or str, optional
        ``True`` to use `sextractor`, or a ``str`` with the
        path to sextractor.
    custom_sextractor_config : bool, optional
        If ``True``, use a sexractor configuration file customized for Feder
        images.
    feder_settings : bool, optional
        Set True if you want to use plate scale appropriate for Feder
        Observatory Apogee Alta U9 camera.
    no_plots : bool, optional
        ``True`` to suppress astrometry.net generation of
        plots (pngs showing object location and more)
    minimal_output : bool, optional
        If ``True``, suppress, as separate files, output of: WCS
        header, RA/Dec object list, matching objects list, but see
        also `save_wcs`
    save_wcs : bool, optional
        If ``True``, save WCS header even if other output is suppressed
        with `minimial_output`
    verify : str, optional
        Name of a WCS header to be used as a first guess
        for the astrometry fit; if this plate solution does not work
        the solution is found as though `verify` had not been specified.
    ra_dec : list or tuple of float
        (RA, Dec); also limits search radius to 1 degree.
    overwrite : bool, optional
        If ``True``, perform astrometry even if astrometry.net files from a
        previous run are present.
    wcs_reference_image_center :
        If ``True``, force the WCS reference point in the image to be the
        image center.
    odds_ratio : float, optional
        The odds ratio to use for a successful solve. Default is to use the
        default in `solve-field`.
    astrometry_config : str, optional
        Name of configuration file to use for SExtractor.
    additional_args : str or list of str, optional
        Additional arguments to pass to `solve-field`
    """
    solve_field = ["solve-field"]
    option_list = []

    option_list.append("--obj 200")
    if feder_settings:
        option_list.append(
            "--scale-low 0.4 --scale-high 0.6 --scale-units arcsecperpix")

    if additional_args is not None:
        if isinstance(additional_args, six.string_types):
            add_ons = [additional_args]
        else:
            add_ons = additional_args
        option_list.extend(add_ons)

    if isinstance(sextractor, six.string_types):
        option_list.append("--sextractor-path " + sextractor)
    elif sextractor:
        option_list.append("--use-sextractor")

    if no_plots:
        option_list.append("--no-plot")

    if minimal_output:
        option_list.append("--corr none --rdls none --match none")
        if not save_wcs:
            option_list.append("--wcs none")

    if ra_dec is not None:
        option_list.append("--ra %s --dec %s --radius 0.5" % ra_dec)

    if overwrite:
        option_list.append("--overwrite")

    if wcs_reference_image_center:
        option_list.append("--crpix-center")

    options = " ".join(option_list)

    solve_field.extend(options.split())

    if custom_sextractor_config:
        tmp_location = tempfile.mkdtemp()
        param_location = path.join(tmp_location, 'default.param')
        config_location = path.join(tmp_location, 'feder.config')
        config_contents = SExtractor_config.format(param_file=param_location)
        with open(config_location, 'w') as f:
            f.write(config_contents)
        with open(param_location, 'w') as f:
            contents = """
                X_IMAGE
                Y_IMAGE
                MAG_AUTO
                FLUX_AUTO
            """

            f.write(dedent(contents))

        additional_solve_args = [
            '--sextractor-config', config_location,
            '--x-column', 'X_IMAGE',
            '--y-column',  'Y_IMAGE',
            '--sort-column', 'MAG_AUTO',
            '--sort-ascending'
        ]

        solve_field.extend(additional_solve_args)

    if odds_ratio is not None:
        solve_field.append('--odds-to-solve')
        solve_field.append(odds_ratio)

    if astrometry_config is not None:
        solve_field.append('--config')
        solve_field.append(astrometry_config)

    # kludge to handle case when path of verify file contains a space--split
    # above does not work for that case.

    if verify is not None:
        solve_field.append("--verify")
        solve_field.append("%s" % verify)

    solve_field.extend([filename])
    logger.debug(' '.join(solve_field))
    try:
        solve_field_output = subprocess.check_output(solve_field,
                                                     stderr=subprocess.STDOUT)
        return_status = 0
        log_level = logging.DEBUG
    except subprocess.CalledProcessError as e:
        return_status = e.returncode
        solve_field_output = 'Output from astrometry.net:\n' + e.output
        log_level = logging.WARN
        logger.warning('Adding astrometry failed for %s', filename)
        raise e
    logger.log(log_level, solve_field_output)
    return return_status


def add_astrometry(filename, overwrite=False, ra_dec=None,
                   note_failure=False, save_wcs=False,
                   verify=None, try_builtin_source_finder=False,
                   custom_sextractor=False,
                   odds_ratio=None,
                   astrometry_config=None,
                   camera=''):
    """Add WCS headers to FITS file using astrometry.net

    Parameters
    ----------
    overwrite : bool, optional
        Set ``True`` to overwrite the original file. If `False`,
        the file astrometry.net generates is kept.

    ra_dec : list or tuple of float or str
        (RA, Dec) of field center as either decimal or sexagesimal; also
        limits search radius to 1 degree.

    note_failure : bool, optional
        If ``True``, create a file with extension "failed" if astrometry.net
        fails. The "failed" file contains the error messages genreated by
        astrometry.net.

    try_builtin_source_finder : bool
        If true, try using astrometry.net's built-in source extractor if
        sextractor fails.

    save_wcs :
    verify :
        See :func:`call_astrometry`

    camera : str, one of ['celestron', 'u9', 'cp16'], optional
        Name of camera; determines the pixel scale used in the solved. Default
        is to use `'u9'`.
    Returns
    -------
    bool
        ``True`` on success.

    Notes
    -----

    Tries a couple strategies before giving up: first sextractor,
    then, if that fails, astrometry.net's built-in source extractor.

    It also cleans up after astrometry.net, keeping only the new FITS
    file it generates, the .solved file, and, if desired, a ".failed" file
    for fields which it fails to solve.

    For more flexible invocation of astrometry.net, see :func:`call_astrometry`
    """
    base, ext = path.splitext(filename)

    # All are in arcsec per pixel, values are approximate
    camera_pixel_scales = {
        'celestron': 0.3,
        'u9': 0.55,
        'cp16': 0.55
    }

    if camera:
        use_feder = False
        scale = camera_pixel_scales[camera]
        scale_options = ("--scale-low {low} --scale-high {high} "
                         "--scale-units arcsecperpix".format(low=0.8*scale, high=1.2 * scale))
    else:
        use_feder = True
        scale_options = None

    logger.info('BEGIN ADDING ASTROMETRY on {0}'.format(filename))
    try:
        logger.debug('About to call call_astrometry')
        solved_field = (call_astrometry(filename,
                                        sextractor=True,
                                        ra_dec=ra_dec,
                                        save_wcs=save_wcs, verify=verify,
                                        custom_sextractor_config=custom_sextractor,
                                        odds_ratio=odds_ratio,
                                        astrometry_config=astrometry_config,
                                        feder_settings=use_feder,
                                        additional_args=scale_options)
                        == 0)
    except subprocess.CalledProcessError as e:
        logger.debug('Failed with error')
        failed_details = e.output
        solved_field = False

    if (not solved_field) and try_builtin_source_finder:
        log_msg = 'Astrometry failed using sextractor, trying built-in '
        log_msg += 'source finder'
        logger.info(log_msg)
        try:
            solved_field = (call_astrometry(filename, ra_dec=ra_dec,
                                            overwrite=True,
                                            save_wcs=save_wcs, verify=verify)
                            == 0)
        except subprocess.CalledProcessError as e:
            failed_details = e.output
            solved_field = False

    if solved_field:
        logger.info('Adding astrometry succeeded')
    else:
        logger.warning('Adding astrometry failed for file %s', filename)

    if overwrite and solved_field:
        logger.info('Overwriting original file with image with astrometry')
        try:
            rename(base + '.new', filename)
        except OSError as e:
            logger.error(e)
            return False

    # whether we succeeded or failed, clean up
    try:
        remove(base + '.axy')
    except OSError:
        pass

    if solved_field:
        try:
            remove(base + '-indx.xyls')
            remove(base + '.solved')
        except OSError:
            pass

    if note_failure and not solved_field:
        try:
            f = open(base + '.failed', 'wb')
            f.write(failed_details)
            f.close()
        except IOError as e:
            logger.error('Unable to save output of astrometry.net %s', e)
            pass

    logger.info('END ADDING ASTROMETRY for %s', filename)
    return solved_field


SExtractor_config = """
# Configuration file for SExtractor 2.19.5 based on default by EB 2014-11-26
#

# modification was to change DETECT_MINAREA and turn of filter convolution

#-------------------------------- Catalog ------------------------------------

PARAMETERS_NAME  {param_file}  # name of the file containing catalog contents

#------------------------------- Extraction ----------------------------------

DETECT_TYPE      CCD            # CCD (linear) or PHOTO (with gamma correction)
DETECT_MINAREA   15              # min. # of pixels above threshold
DETECT_THRESH    1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2
ANALYSIS_THRESH  1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2

FILTER           N              # apply filter for detection (Y or N)?
FILTER_NAME      default.conv   # name of the file containing the filter

DEBLEND_NTHRESH  32             # Number of deblending sub-thresholds
DEBLEND_MINCONT  0.005          # Minimum contrast parameter for deblending

CLEAN            Y              # Clean spurious detections? (Y or N)?
CLEAN_PARAM      1.0            # Cleaning efficiency

MASK_TYPE        CORRECT        # type of detection MASKing: can be one of
                                # NONE, BLANK or CORRECT

#------------------------------ Photometry -----------------------------------

PHOT_APERTURES   10              # MAG_APER aperture diameter(s) in pixels
PHOT_AUTOPARAMS  2.5, 3.5       # MAG_AUTO parameters: <Kron_fact>,<min_radius>
PHOT_PETROPARAMS 2.0, 3.5       # MAG_PETRO parameters: <Petrosian_fact>,
                                # <min_radius>

SATUR_LEVEL      50000.0        # level (in ADUs) at which arises saturation
SATUR_KEY        SATURATE       # keyword for saturation level (in ADUs)

MAG_ZEROPOINT    0.0            # magnitude zero-point
MAG_GAMMA        4.0            # gamma of emulsion (for photographic scans)
GAIN             0.0            # detector gain in e-/ADU
GAIN_KEY         GAIN           # keyword for detector gain in e-/ADU
PIXEL_SCALE      1.0            # size of pixel in arcsec (0=use FITS WCS info)

#------------------------- Star/Galaxy Separation ----------------------------

SEEING_FWHM      1.2            # stellar FWHM in arcsec
STARNNW_NAME     default.nnw    # Neural-Network_Weight table filename

#------------------------------ Background -----------------------------------

BACK_SIZE        64             # Background mesh: <size> or <width>,<height>
BACK_FILTERSIZE  3              # Background filter: <size> or <width>,<height>

BACKPHOTO_TYPE   GLOBAL         # can be GLOBAL or LOCAL

#------------------------------ Check Image ----------------------------------

CHECKIMAGE_TYPE  NONE           # can be NONE, BACKGROUND, BACKGROUND_RMS,
                                # MINIBACKGROUND, MINIBACK_RMS, -BACKGROUND,
                                # FILTERED, OBJECTS, -OBJECTS, SEGMENTATION,
                                # or APERTURES
CHECKIMAGE_NAME  check.fits     # Filename for the check-image

#--------------------- Memory (change with caution!) -------------------------

MEMORY_OBJSTACK  3000           # number of objects in stack
MEMORY_PIXSTACK  300000         # number of pixels in stack
MEMORY_BUFSIZE   1024           # number of lines in buffer

#----------------------------- Miscellaneous ---------------------------------

VERBOSE_TYPE     NORMAL         # can be QUIET, NORMAL or FULL
HEADER_SUFFIX    .head          # Filename extension for additional headers
WRITE_XML        N              # Write XML file (Y/N)?
XML_NAME         sex.xml        # Filename for XML output

"""
