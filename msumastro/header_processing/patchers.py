from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from os import path
from datetime import datetime
import logging
from socket import timeout

import numpy as np
import astropy.io.fits as fits
from astropy.time import Time
from astropy.coordinates import Angle, name_resolve, SkyCoord, AltAz
from astropy import units as u
from astropy.table import Table

from astropy.extern.six.moves.urllib import parse as urlparse

try:
    from .feder import Feder
    feder = Feder()
except ImportError:
    feder = None
    pass

from ..image_collection import ImageFileCollection
from .fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)


#__all__ = ['patch_headers', 'add_object_info', 'add_ra_dec_from_object_name']


def IRAF_image_type(image_type):
    """
    Convert MaximDL default image type names to IRAF

    Parameters
    ----------
    image_type : str
        Value of the FITS header keyword IMAGETYP; acceptable values are
        below in Notes.

    Returns
    -------
    str
        IRAF image type (one of 'BIAS', 'DARK', 'FLAT' or 'LIGHT')

    Notes
    -----
    The MaximDL default is, e.g. 'Bias Frame', which IRAF calls
    'BIAS'. Can safely be called with an IRAF-style image_type.
    """
    return image_type.split()[0].upper()


def _lst_from_obstime(obstime):
    try:
        LST = obstime.sidereal_time('apparent',
                                    longitude=feder.site.longitude)
    except IndexError:
        # We are outside the range of the IERS table installed with astropy,
        # so get a newer one.
        from astropy.utils import iers
        from astropy.utils.data import download_file
        iers_a = iers.IERS_A.open(download_file(iers.IERS_A_URL,
                                  cache=True))
        obstime.delta_ut1_utc = obstime.get_delta_ut1_utc(iers_a)
        LST = obstime.sidereal_time('apparent',
                                    longitude=feder.site.longitude)
    return LST


def add_time_info(header, history=False):
    """
    Add JD, MJD, LST to FITS header

    Parameters
    ----------
    header : astropy..io.fits.Header
        FITS header to be modified.
    history : bool
        If `True`, write history for each keyword changed.
    """
    dateobs = Time(header['date-obs'], scale='utc')
    feder.JD_OBS.value = dateobs.jd
    feder.MJD_OBS.value = dateobs.mjd

    LST_tmp = _lst_from_obstime(dateobs)

    feder.LST.value = LST_tmp.to_string(unit=u.hour, sep=':', precision=4,
                                        pad=True)

    for keyword in feder.keywords_for_all_files:
        keyword.add_to_header(header, history=history)
        logger.info(keyword.history_comment())


def add_object_pos_airmass(header, history=False):
    """
    Add object information, such as RA/Dec and airmass.

    Parameters
    ----------
    header : astropy..io.fits.Header
        FITS header to be modified.
    history : bool
        If `True`, write history for each keyword changed.

    Notes
    -----
    Has side effect of setting feder site JD to JD-OBS, which means it
    also assume JD.value has been set.

    """
    # not sure why coverage is not picking up both branches, but it is not, so
    # marking it no cover
    if feder.JD_OBS.value is None:   # pragma: no cover
        raise ValueError('Need to set JD_OBS.value '
                         'before calling.')

    try:
        feder.RA.set_value_from_header(header)
    except ValueError:
        raise ValueError("No RA is present.")

    feder.DEC.set_value_from_header(header)
    feder.RA.value = feder.RA.value.replace(' ', ':')
    feder.DEC.value = feder.DEC.value.replace(' ', ':')

    obj_coord2 = SkyCoord(feder.RA.value, feder.DEC.value,
                          unit=(u.hour, u.degree), frame='fk5')

    obstime = Time(feder.MJD_OBS.value, format='mjd')
    alt_az = obj_coord2.transform_to(AltAz(obstime=obstime,
                                           location=feder.site))

    feder.ALT_OBJ.value = round(alt_az.alt.degree, 5)
    feder.AZ_OBJ.value = round(alt_az.az.degree, 5)
    feder.AIRMASS.value = round(1 / np.cos(np.pi / 2 - alt_az.alt.radian), 3)

    # TODO: replace the LST calculation
    LST = _lst_from_obstime(obstime)
    HA = LST.hour - obj_coord2.ra.hour
    HA = Angle(HA, unit=u.hour)

    feder.HA.value = HA.to_string(unit=u.hour, sep=':')

    for keyword in feder.keywords_for_light_files:
        if keyword.value is not None:
            keyword.add_to_header(header, history=history)
            logger.info(keyword.history_comment())


def get_software_name(header, file_name=None, use_observatory=None):
    """
    Determine the name of the software that created FITIS header

    Parameters
    ----------

    header : astropy.io.fits Header
        Header from a FITS extension/hdu

    file_name : str, optional
        Name of the file containing this header; used to add information to
        error/warning messages.

    use_observatory : msumastro.Feder instance, optional
        Object that contains names of FITS keywords that might be present and
        contain name of the software that made this header. The default value
        is the instance defined at the beginning of this module

    Returns
    -------

    msumastro.feder.Software object
    """
    fits_file = file_name or ''
    observatory = use_observatory or feder

    known_software_keywords = observatory.software_FITS_keywords

    software_name_in_header = FITSKeyword(name=known_software_keywords[0],
                                          synonyms=known_software_keywords)
    software_name_in_header.set_value_from_header(header)

    try:
        software = observatory.software[software_name_in_header.value]
    except KeyError:
        raise KeyError('Software named {0} not recognized in header '
                       'for file {1}'.format(software_name_in_header.value,
                                             fits_file))
    return software


def purge_bad_keywords(header, history=False, force=False, file_name=None):
    """
    Remove keywords from FITS header that may be incorrect

    Parameters
    ----------
    header : astropy.io.fits.Header
        Header from which the bad keywords (as defined by the software that
        recorded the image) should be purged.

    history : bool
        If `True` write detailed history for each keyword removed.

    force : bool
        If `True`, force keywords to be purged even if the FITS header
        indicates it has already been purged.

    file_name : str, optional
        Name of file containing the header; if provided it is used to generate
        more informative log messages.
    """
    software = get_software_name(header, file_name=file_name)

    try:
        purged = header[software.purged_flag_keyword]
    except KeyError:
        purged = False

    if purged and not force:
        warn_msg = 'Not removing headers from {0} again, '
        warn_msg += 'set force=True to force removal.'
        logger.warn(warn_msg.format(file_name))
        return

    for keyword in software.bad_keywords:
        try:
            comment = ('Deleted keyword ' + keyword +
                       ' with value ' + str(header[keyword]))
            del header[keyword]
        except KeyError:
            continue

        logger.info(comment)

        if history:
            header.add_history(comment)

    header[software.purged_flag_keyword] = (True,
                                            'Have bad keywords been removed?')


def change_imagetype_to_IRAF(header, history=True):
    """
    Change IMAGETYP to default used by IRAF

    Parameters
    ----------
    header : astropy.io.fits.Header
        Header object in which image type is to be changed.

    history : bool, optional
        If `True`, add history of keyword modification to `header`.
    """
    imagetype = 'imagetyp'  # FITS keyword name is truncated at 8 chars
    current_type = header[imagetype]
    IRAF_type = IRAF_image_type(current_type)
    if current_type != IRAF_type:
        header[imagetype] = IRAF_type
        comment = 'Changed {0} from {1} to {2}'.format(imagetype.upper(),
                                                       current_type,
                                                       IRAF_type)
        logger.info(comment)
        if history:
            header.add_history(comment)


def add_image_unit(header, history=True):
    """
    Add unit of image to header.

    Parameters
    ----------
    header : astropy.io.fits.Header
        Header object in which image type is to be changed.

    history : bool, optional
        If `True`, add history of keyword modification to `header`.
    """
    instrument_key = 'instrume'
    instrument = feder.instruments[header[instrument_key]]
    if instrument.image_unit is not None:
        unit_string = instrument.image_unit.to_string()
        comment = 'Set image data unit to {}'.format(unit_string)
        header['BUNIT'] = unit_string
        print('UNIT STRING IS =========> {}'.format(unit_string))
        logger.info(comment)
        if history:
            header.add_history(comment)


def list_name_is_url(name):
    may_be_url = urlparse.urlparse(name)
    return (may_be_url.scheme and may_be_url.netloc)


def read_object_list(directory=None, input_list=None,
                     skip_consistency_check=False, check_radius=20.0,
                     skip_lookup_from_object_name=False):
    """
    Read a list of objects from a text file.

    Parameters
    ----------
    directory : str
        Directory containing the file. Default is the current directory, ``.``

    input_list : str, optional
        Name of the file or URL of file. Default value is ``obsinfo.txt``. If
        the name is a URL the directory argument is ignored.

    skip_consistency_check : bool optional
        If ``True``, skip checking whether objects on the list have unique
        coordinates given `check_radius`.

    check_radius : float, optional
        Match radius, in arcminutes. Objects on the list must be separated by
        an angular distance greater than this for the list to be
        self-consistent.

    skip_lookup_from_object_name : bool, optional
        Set to ``True`` to skip lookup of coordinates from Simbad if RA/Dec
        are not in the object file.

    Notes
    -----

    There are two file formats; one contains just a list of objects, the
    other has an RA and Dec for each object.

    In both types any lines that start with ``#`` are ignored and treated
    as comments.

    **File with list of objects only:**
        + Object coordinates are determined by lookup with
          `Simbad <http://simbad.u-strasbg.fr/simbad/>`_. You should make sure
          the object names you use are known to simbad.
        + The first non-comment line MUST be the word ``object`` and only
          the word ``object``. It is case sensitive; ``Object`` or ``OBJECT``
          will not work.
        + Remaining line(s) are name(s) of object(s), one per line. Case does
          **not** matter for object name.
        + Example::

            # my list is below
            object
            m101
            sz lyn
            # the next object is after this comment
            RR LYR

    **File with object name and position:**
        + RA and Dec **must be J2000**.
        + RA **must be given in hours**, though it can be either sexagesimal
          (e.g. ``19:25:27.9``) or decimal (e.g. ``19.423861``).
        + Dec **must be given in degrees**, though it can be either sexagesimal
          (e.g. ``42:47:3.69``) or decimal (e.g. ``42.7843583``)
        + The first non-comment line MUST be these words: ``object,RA,Dec``.
          These are column headings for your file. It is **not** case
          sensitive; for example, using ``DEC`` instead of ``Dec`` will work.
        + Each remaining line should be an object name, object RA and Dec.
          Case does **not** matter for object name.
        + Example::

            # my list with RA and Dec
            # RA and Dec are assumed to be J2000
            # RA MUST BE IN HOURS
            # DEC MUST BE IN DEGREES
            object,RA,Dec
            m101,14:03:12.583, +54:20:55.50
            # note that the leading sign for the Dec is optional if Dec is
            # positive
            sz lyn,08:09:35.748, 44:28:17.61
            # You can mix sexagesimal and decimal RA/Dec.
            RR Lyr, 19.423861,42.7843583

    """
    def normalize_column_name(key, table):
        """
        Find any column in table whose name matches, aside from case, key
        and change the name of the column to key
        """
        contains_col = lambda key, names: key.lower() in [name.lower() for name
                                                          in names]

        if not contains_col(key, table.columns):
            raise KeyError('Keyword {0} not found in table'.format(key))

        for column in table.columns:
            if ((key.lower() == column.lower()) and (key != column)):
                table.rename_column(column, key)
                break

    if directory is None:
        directory = '.'
    list_name = input_list if input_list is not None else 'obsinfo.txt'

    if not list_name_is_url(list_name):
        full_name = path.join(directory, list_name)
    else:
        full_name = list_name

    objects = Table.read(full_name,
                         format='ascii',
                         comment='#',
                         delimiter=',')

    try:
        normalize_column_name('object', objects)
    except KeyError as e:
        logger.debug('%s', e)
        raise RuntimeError(
              'No column named object found in file {}'.format(list_name))

    try:
        normalize_column_name('RA', objects)
        normalize_column_name('Dec', objects)
        RA = objects['RA']
        Dec = objects['Dec']
    except KeyError:
        RA = None
        Dec = None
        ra_dec = None

    object_names = objects['object']

    if (RA is not None) and (Dec is not None):
        default_angle_units = (u.hour, u.degree)
        ra_dec = SkyCoord(RA, Dec, unit=default_angle_units, frame='fk5')
    else:
        if skip_lookup_from_object_name:
            ra_dec = None
        else:
            try:
                ra_dec = [SkyCoord.from_name(obj) for obj in object_names]
            except (name_resolve.NameResolveError, timeout) as e:
                logger.error('Unable to do lookup of object positions')
                logger.error(e)
                raise name_resolve.NameResolveError('Unable to do lookup of '
                                                    'object positions')
            ra = []
            dec = []
            for a_coord in ra_dec:
                ra.append(a_coord.ra.radian)
                dec.append(a_coord.dec.radian)
            ra_dec = SkyCoord(ra, dec, unit=(u.radian, u.radian), frame='fk5')

    if skip_consistency_check and skip_lookup_from_object_name:
        return object_names, ra_dec

    if skip_consistency_check or not ra_dec:
        return object_names, ra_dec

    # sanity check object list--the objects should not be so close together
    # that any pair is within match radius of each other.
    logger.debug('Testing object list for self-consistency')

    # need 2nd neighbor below or objects will match themselves
    try:
        matches, d2d, d3d = ra_dec.match_to_catalog_sky(ra_dec,
                                                        nthneighbor=2)
        bad_object_list = (d2d.arcmin < check_radius).any()
    except IndexError:
        # There was only one item in the table...so no object can
        # be duplicated, so make a fake distance that doesn't match
        bad_object_list = False

    if bad_object_list:
        err_msg = ('Object list {} in directory {} contains at least one '
                   'pair of objects that '
                   'are closer together than '
                   'match radius {} arcmin').format(input_list,
                                                    directory,
                                                    check_radius)
        logger.error(err_msg)
        raise RuntimeError(err_msg)
    logger.debug('Passed: object list is self-consistent')

    return object_names, ra_dec


def history(function, mode=None, time=None):
    """
    Construct nicely formatted start/end markers in FITS history.

    Parameters
    ----------
    function : func
        Function calling `history`
    mode : str, 'begin' or 'end'
        A different string is produced for the beginning and the end. Default
        is 'begin'.
    time : datetime
        If not set, defaults to current date/time.
    """
    mode = mode or 'begin'
    if mode == 'begin':
        marker = '+'
    elif mode == 'end':
        marker = '-'
    else:
        raise ValueError('mode must be "begin" or "end"')

    if time is None:
        time = datetime.now()

    marker *= 5
    return "%s %s %s history on %s %s" % (marker, mode.upper(),
                                          function.__name__, time,
                                          marker)


def patch_headers(dir=None,
                  new_file_ext=None,
                  save_location=None,
                  overwrite=False,
                  purge_bad=True,
                  add_time=True,
                  add_apparent_pos=True,
                  add_overscan=True,
                  fix_imagetype=True,
                  add_unit=True):
    """
    Add minimal information to Feder FITS headers.

    Parameters
    ----------
    dir : str, optional
        Directory containing the files to be patched. Default is the current
        directory, ``.``

    new_file_ext : str, optional
        Name added to the FITS files with updated header information. It is
        added to the base name of the input file, between the old file name
        and the `.fit` or `.fits` extension. Default is 'new'.

    save_location : str, optional
        Directory to which the patched files should be written, if not `dir`.

    overwrite : bool, optional
        Set to `True` to replace the original files.

    purge_bad : bool, optional
        Remove "bad" keywords form header before any other processing. See
        :func:`purge_bad_keywords` for details.

    add_time : bool, optional
        If ``True``, add time information (e.g. JD, LST); see
        :func:`add_time_info` for details.

    add_apparent_pos : bool, optional
        If ``True``, add apparent position (e.g. alt/az) to headers. See
        :func:`add_object_pos_airmass` for details.

    add_overscan : bool, optional
        If ``True``, add overscan keywords to the headers. See
        :func:`add_overscan_header` for details.

    fix_imagetype : bool, optional
        If ``True``, change image types to IRAF-style. See
        :func:`change_imagetype_to_IRAF` for details.

    add_unit : bool, optional
        If ``True``, add image unit to FITS header.
    """
    dir = dir or '.'
    if new_file_ext is None:
        new_file_ext = 'new'

    images = ImageFileCollection(location=dir, keywords=['imagetyp'])

    for header, fname in images.headers(save_with_name=new_file_ext,
                                        save_location=save_location,
                                        overwrite=overwrite,
                                        do_not_scale_image_data=True,
                                        return_fname=True):
        run_time = datetime.now()

        logger.info('START PATCHING FILE: {0}'.format(fname))

        header.add_history(history(patch_headers, mode='begin',
                                   time=run_time))
        header.add_history('patch_headers.py modified this file on %s'
                           % run_time)
        try:
            # each of the next 3 lines checks for presences of something
            get_software_name(header)  # is there some software?
            header['instrume']  # is there an instrument?
            header['imagetyp']  # is there an image type?

            if purge_bad:
                purge_bad_keywords(header, history=True, file_name=fname)

            if fix_imagetype:
                change_imagetype_to_IRAF(header, history=True)

            if add_time:
                add_time_info(header, history=True)

            if add_overscan:
                add_overscan_header(header, history=True)

            if add_unit:
                add_image_unit(header, history=True)

            # add_apparent_pos_airmass can raise a ValueError, do it last.
            if add_apparent_pos and (header['imagetyp'] == 'LIGHT'):
                add_object_pos_airmass(header,
                                       history=True)

        except (KeyError, ValueError) as e:
            warning_msg = ('********* FILE NOT PATCHED *********'
                           'Stopped patching header of {0} because of '
                           '{1}: {2}'.format(fname, type(e).__name__, e))
            logger.warn(warning_msg)
            header.add_history(warning_msg)
            continue
        finally:
            header.add_history(history(patch_headers, mode='end',
                               time=run_time))
            logger.info('END PATCHING FILE: {0}'.format(fname))


def add_overscan_header(header, history=True):
    """
    Add overscan information to a FITS header.

    Parameters
    ----------
    header : astropy.io.fits.Header
        Header object to which overscan is to be added.

    history : bool, optional
        If `True`, add history of keyword modification to `header`.

    Returns
    -------
    list of str
        List of the keywords added to the header by this function.
    """
    image_dim = [header['naxis1'], header['naxis2']]
    instrument = feder.instruments[header['instrume']]
    overscan_present = instrument.has_overscan(image_dim)
    modified_keywords = []
    if overscan_present:
        overscan_region = feder.BIASSEC
        trim_region = feder.TRIMSEC
        overscan_region.value = instrument.useful_overscan
        trim_region.value = instrument.trim_region
        overscan_region.add_to_header(header, history=history)
        trim_region.add_to_header(header, history=history)
        modified_keywords.extend([overscan_region, trim_region])

    for keyword in modified_keywords:
        logger.info(keyword.history_comment())

    return modified_keywords


def add_object_info(directory=None,
                    object_list=None,
                    object_list_dir=None,
                    match_radius=20.0, new_file_ext=None,
                    save_location=None,
                    overwrite=False, detailed_history=True):
    """
    Add object information to FITS files that contain pointing information
    given a list of objects.

    Parameters
    ----------
    directory : str
        Directory containing the FITS files to be fixed. Default is the
        current directory, ``.``.

    object_list : str, optional
        Name of file containing list of objects. Default is set by
        :func:`read_object_list` which also explains the format of this file.

    object_list_dir : str, optional
        Directory in which the `object_list` is contained. Default is
        `directory`.

    match_radius : float, optional
        Maximum distance, in arcmin, between the RA/Dec of the image and a
        particular object for the image to be considered an image of that
        object.

    new_file_ext : str, optional
        Name added to the FITS files with updated header information. It is
        added to the base name of the input file, between the old file name
        and the `.fit` or `.fits` extension. Default is 'new'.

    save_location : str, optional
        Directory to which the patched files should be written, if not `dir`.

    overwrite : bool, optional
        Set to `True` to replace the original files.
    """
    directory = directory or '.'
    if new_file_ext is None:
        new_file_ext = 'new'

    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'ra',
                                           'dec', 'object'])
    im_table = images.summary_info

    object_dir = directory if object_list_dir is None else object_list_dir

    logger.debug('About to read object list')
    try:
        object_names, ra_dec = read_object_list(object_dir,
                                                input_list=object_list)
    except IOError:
        warn_msg = 'No object list in directory {0}, skipping.'
        logger.warn(warn_msg.format(directory))
        return
    except name_resolve.NameResolveError:
        logger.error('Unable to add objects--name resolve error')
        return

    object_names = np.array(object_names)

    # I want rows which...
    #
    # ...have no OBJECT...
    needs_object = im_table['object'].mask
    # ...and have coordinates.
    needs_object &= ~ (im_table['ra'].mask | im_table['dec'].mask)

    logger.debug('Looking for objects for %s images', needs_object.sum())
    # Qualifying rows need a search for a match.
    # the search returns a match for every row provided, but some matches
    # may be farther away than desired, so...
    #
    # ...`and` the previous index mask with those that matched, and
    # ...construct list of object names for those images.
    default_angle_units = (u.hour, u.degree)

    img_pos = SkyCoord(im_table['ra'][needs_object],
                       im_table['dec'][needs_object],
                       unit=default_angle_units,
                       frame='fk5')
    match_idx, d2d, d3d = img_pos.match_to_catalog_sky(ra_dec)
    good_match = (d2d.arcmin <= match_radius)
    found_object = np.array(needs_object)
    found_object[needs_object] = good_match
    matched_object_name = object_names[match_idx][good_match]

    no_match_found = needs_object & ~found_object
    if no_match_found.any():
        for fname in np.array(images.files)[no_match_found]:
            warn_msg = "No object found for image {0}".format(fname)
            logger.warn(warn_msg)

    if not found_object.any():
        logger.info('NO OBJECTS MATCHED TO IMAGES IN: {0}'.format(directory))
        return

    im_table['file'].mask = ~found_object

    for idx, (header, fname) in enumerate(images.headers(save_with_name=new_file_ext,
                                          overwrite=overwrite,
                                          save_location=save_location,
                                          return_fname=True)):

        logger.info('START ATTEMPTING TO ADD OBJECT to: {0}'.format(fname))

        object_name = matched_object_name[idx]
        logger.debug('Found matching object named %s', object_name)
        obj_keyword = FITSKeyword('object', value=object_name)
        obj_keyword.add_to_header(header, history=True)
        logger.info(obj_keyword.history_comment())
        logger.info('END ATTEMPTING TO ADD OBJECT to: {0}'.format(fname))


def add_ra_dec_from_object_name(directory=None, new_file_ext=None,
                                object_list=None, object_list_dir=None):
    """
    Add RA/Dec to FITS file that has object name but no pointing.

    Parameters
    ----------
    dir : str, optional
        Directory containing the files to be patched. Default is the current
        directory, ``.``

    new_file_ext : str, optional
        Name added to the FITS files with updated header information. It is
        added to the base name of the input file, between the old file name
        and the `.fit` or `.fits` extension. Default is 'new'.

    object_list : str, optional
        Name of file containing list of objects. Default is set by
        :func:`read_object_list` which also explains the format of this file.

    object_list_dir : str, optional
        Directory in which the `object_list` is contained. Default is
        `directory`.

    """
    directory = directory or '.'
    if new_file_ext is None:
        new_file_ext = 'new'
    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'ra',
                                           'dec', 'object'])
    summary = images.summary_info
    missing_dec = summary[(np.logical_not(summary['object'].mask)) &
                          (summary['ra'].mask) &
                          (summary['dec'].mask) &
                          (summary['object'] != '') &
                          (summary['imagetyp'] == 'LIGHT')]

    if not missing_dec:
        return

    objects = np.unique(missing_dec['object'])

    try:
        object_list, ra_dec_list = read_object_list(object_list_dir,
                                                    input_list=object_list)
    except IOError:
        object_list = []
        ra_dec_list = []
        object_dict = {}

    if len(object_list) and len(ra_dec_list):
        object_dict = {obj: ra_dec for obj, ra_dec in zip(object_list,
                                                          ra_dec_list)}

    # checks prior to this mean this loop always happens at least once,
    # which confuses coverage
    for object_name in objects:  # pragma: nobranch
        try:
            object_coords = object_dict[object_name]
        except KeyError:
            try:
                object_coords = SkyCoord.from_name(object_name)
            except (name_resolve.NameResolveError, timeout) as e:
                logger.warning('Unable to lookup position for %s', object_name)
                logger.warning(e)
                return

        common_format_keywords = {'sep': ':',
                                  'precision': 2,
                                  'pad': True}
        feder.RA.value = object_coords.ra.to_string(unit=u.hour,
                                                    **common_format_keywords)
        feder.DEC.value = object_coords.dec.to_string(unit=u.degree,
                                                      alwayssign=True,
                                                      **common_format_keywords)
        these_files = missing_dec[missing_dec['object'] == object_name]
        for image in these_files:
            full_name = path.join(directory, image['file'])
            hdulist = fits.open(full_name, do_not_scale_image_data=True)
            header = hdulist[0].header
            feder.RA.add_to_header(header, history=True)
            feder.DEC.add_to_header(header, history=True)
            if new_file_ext:
                base, ext = path.splitext(full_name)
                new_file_name = base + new_file_ext + ext
                overwrite = False
            else:
                new_file_name = full_name
                overwrite = True
            hdulist.writeto(new_file_name, clobber=overwrite)
            hdulist.close()
