import logging
import subprocess
from os import path, remove, rename

__all__ = ['call_astrometry', 'add_astrometry']

logger = logging.getLogger(__name__)


def call_astrometry(filename, sextractor=False, feder_settings=True,
                    no_plots=True, minimal_output=True,
                    save_wcs=False, verify=None,
                    ra_dec=None, overwrite=False,
                    wcs_reference_image_center=True):
    """
    Wrapper around astrometry.net solve-field.

    Parameters
    ----------
    sextractor : bool or str, optional
        ``True`` to use `sextractor`, or a ``str`` with the
        path to sextractor.
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
    """
    solve_field = ["solve-field"]
    option_list = []

    option_list.append("--obj 40 --depth 20,40")
    if feder_settings:
        option_list.append(
            "--scale-low 0.4 --scale-high 0.56 --scale-units arcsecperpix")

    if isinstance(sextractor, basestring):
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
                   verify=None, try_builtin_source_finder=False):
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

    try_biultin_source_finder : bool
        If true, try using astrometry.net's built-in source extractor if
        sextractor fails.

    save_wcs :
    verify :
        See :func:`call_astrometry`

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

    logger.info('BEGIN ADDING ASTROMETRY on {0}'.format(filename))
    try:
        logger.debug('About to call call_astrometry')
        solved_field = (call_astrometry(filename,
                                        sextractor=True,
                                        ra_dec=ra_dec,
                                        save_wcs=save_wcs, verify=verify)
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
