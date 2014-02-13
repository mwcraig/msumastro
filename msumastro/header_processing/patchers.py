from os import path
from datetime import datetime
import logging

import numpy as np
import astropy.io.fits as fits
from astropy.time import Time
from astropy.coordinates import Angle, FK5, name_resolve
from astropy import units as u
from astropy.table import Table

from feder import Feder
from ..image_collection import ImageFileCollection
from fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)

feder = Feder()

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

    # setting currentobsjd makes calls following it use that time
    # for calculations

    feder.site.currentobsjd = feder.JD_OBS.value
    LST_tmp = Angle(feder.site.localSiderialTime(), unit=u.hour)
    feder.LST.value = LST_tmp.to_string(unit=u.hour, sep=':', precision=2,
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
    if feder.JD_OBS.value is not None:
        feder.site.currentobsjd = feder.JD_OBS.value
    else:
        raise ValueError('Need to set JD_OBS.value before calling.')

    try:
        feder.RA.set_value_from_header(header)
    except ValueError:
        raise ValueError("No RA is present.")
        return

    feder.DEC.set_value_from_header(header)
    feder.RA.value = feder.RA.value.replace(' ', ':')
    feder.DEC.value = feder.DEC.value.replace(' ', ':')

    obj_coord2 = FK5(feder.RA.value, feder.DEC.value,
                     unit=(u.hour, u.degree))

    # monkeypatch obj_coord2 so it looks like an astropysics coord
    obj_coord2.raerr = None
    obj_coord2.decerr = None
    # and, for astropy 0.3, monkeypatch an hours method and a radians method:
    obj_coord2.ra.hours = obj_coord2.ra.hour
    obj_coord2.dec.radians = obj_coord2.dec.radian

    alt_az = feder.site.apparentCoordinates(obj_coord2, refraction=False)

    feder.ALT_OBJ.value = round(alt_az.alt.d, 5)
    feder.AZ_OBJ.value = round(alt_az.az.d, 5)
    feder.AIRMASS.value = round(1 / np.cos(np.pi / 2 - alt_az.alt.r), 3)

    HA = feder.site.localSiderialTime() - obj_coord2.ra.hours
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
        except KeyError:
            continue
        logger.info(comment)
        del header[keyword]
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


def read_object_list(dir=None, input_list=None):
    """
    Read a list of objects from a text file.

    Parameters
    ----------
    dir : str
        Directory containing the file. Default is the current directory, ``.``

    input_list : str, optional
        Name of the file. Default value is ``obsinfo.txt``

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
            raise(KeyError, 'Keyword {0} not found in table'.format(key))

        for column in table.columns:
            if ((key.lower() == column.lower()) and (key != column)):
                table.rename_column(column, key)
                break

    dir = dir or '.'
    list = (input_list if input_list is not None else 'obsinfo.txt')
    objects = Table.read(path.join(dir, list),
                         format='ascii',
                         comment='#',
                         delimiter=',')

    try:
        normalize_column_name('object', objects)
    except KeyError as e:
        logger.debug('%s', e)
        raise(RuntimeError,
              'No column named object found in file {}'.format(list))

    try:
        normalize_column_name('RA', objects)
        normalize_column_name('Dec', objects)
        RA = objects['RA']
        Dec = objects['Dec']
    except KeyError:
        RA = None
        Dec = None

    return objects['object'], RA, Dec


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
                  fix_imagetype=True):
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
    """
    dir = dir or '.'
    if new_file_ext is None:
        new_file_ext = 'new'

    images = ImageFileCollection(location=dir, keywords=['imagetyp'])

    for header, fname in images.headers(save_with_name=new_file_ext,
                                        save_location=save_location,
                                        clobber=overwrite,
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

            if add_apparent_pos and (header['imagetyp'] == 'LIGHT'):
                add_object_pos_airmass(header,
                                       history=True)
            if add_overscan:
                add_overscan_header(header, history=True)
        except (KeyError, ValueError) as e:
            warning_msg = ('********* FILE NOT PATCHED *********\n'
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
    overscan_present = feder.OSCAN
    overscan_present.value = instrument.has_overscan(image_dim)
    overscan_present.add_to_header(header, history=history)
    modified_keywords = [overscan_present]
    if overscan_present.value:
        overscan_axis = feder.OSCANAX
        overscan_start = feder.OSCANST
        overscan_axis.value = instrument.overscan_axis
        overscan_start.value = instrument.overscan_start
        overscan_axis.add_to_header(header, history=history)
        overscan_start.add_to_header(header, history=history)
        modified_keywords.extend([overscan_axis, overscan_start])

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
                                 keywords=['imagetyp', 'RA',
                                           'Dec', 'object'])
    im_table = images.summary_info

    object_dir = directory if object_list_dir is None else object_list_dir

    logger.debug('About to read object list')
    try:
        object_names, RAs, Decs = read_object_list(object_dir,
                                                   input_list=object_list)
    except IOError:
        warn_msg = 'No object list in directory {0}, skipping.'
        logger.warn(warn_msg.format(directory))
        return

    object_names = np.array(object_names)
    ra_dec = []
    default_angle_units = (u.hour, u.degree)

    if (RAs is not None) and (Decs is not None):
        ra_dec = FK5(RAs, Decs, unit=default_angle_units)
    else:
        try:
            ra_dec = [FK5.from_name(obj) for obj in object_names]
        except name_resolve.NameResolveError as e:
            logger.error('Unable to do lookup of object positions')
            logger.error(e)
            return
        ra = []
        dec = []
        for a_coord in ra_dec:
            ra.append(a_coord.ra.radian)
            dec.append(a_coord.dec.radian)
        ra_dec = FK5(ra, dec, unit=(u.radian, u.radian))
    # sanity check object list--the objects should not be so close together
    # that any pair is within match radius of each other.
    logger.debug('Testing object list for self-consistency')

    # need 2nd neighbor below or objects will match themselves
    try:
        matches, d2d, d3d = ra_dec.match_to_catalog_sky(ra_dec,
                                                        nthneighbor=2)
        bad_object_list = (d2d.arcmin < match_radius).any()
    except IndexError:
        # There was only one item in the table...so no object can
        # be duplicated, so make a fake distance that doesn't match
        bad_object_list = False

    if bad_object_list:
        err_msg = ('Object list {} in directory {} contains at least one '
                   'pair of objects that '
                   'are closer together than '
                   'match radius {} arcmin').format(object_list,
                                                    object_list_dir,
                                                    match_radius)
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    # I want rows which...
    #
    # ...have no OBJECT...
    needs_object = im_table['object'].mask
    # ...and have coordinates.
    needs_object &= ~ (im_table['RA'].mask | im_table['Dec'].mask)

    # Qualifying rows need a search for a match.
    # the search returns a match for every row provided, but some matches
    # may be farther away than desired, so...
    #
    # ...`and` the previous index mask with those that matched, and
    # ...construct list of object names for those images.

    img_pos = FK5(im_table['RA'][needs_object], im_table['Dec'][needs_object],
                  unit=default_angle_units)
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
                                          clobber=overwrite,
                                          save_location=save_location,
                                          return_fname=True)):

        logger.info('START ATTEMPTING TO ADD OBJECT to: {0}'.format(fname))

        object_name = matched_object_name[idx]
        logger.debug('Found matching object named %s', object_name)
        obj_keyword = FITSKeyword('object', value=object_name)
        obj_keyword.add_to_header(header, history=True)
        logger.info(obj_keyword.history_comment())
        logger.info('END ATTEMPTING TO ADD OBJECT to: {0}'.format(fname))


def add_ra_dec_from_object_name(directory=None, new_file_ext=None):
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

    """
    directory = directory or '.'
    if new_file_ext is None:
        new_file_ext = 'new'
    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'RA',
                                           'Dec', 'object'])
    summary = images.summary_info
    missing_dec = summary[(np.logical_not(summary['object'].mask)) &
                          (summary['RA'].mask) &
                          (summary['Dec'].mask) &
                          (summary['object'] != '') &
                          (summary['imagetyp'] == 'LIGHT')]

    if not missing_dec:
        return

    objects = np.unique(missing_dec['object'])
    for object_name in objects:
        try:
            object_coords = FK5.from_name(object_name)
        except name_resolve.NameResolveError as e:
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


def fix_int16_images(directory=None, new_file_ext=None):
    """
    Repair unsigned int16 images saved as signed int16.

    Use with care; if your data really is signed int16 this will corrupt it.

    Parameters
    ----------
    dir : str, optional
        Directory containing the files to be patched. Default is the current
        directory, ``.``

    new_file_ext : str, optional
        Name added to the FITS files with updated header information. It is
        added to the base name of the input file, between the old file name
        and the `.fit` or `.fits` extension.
    """
    directory = directory or '.'
    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'bitpix', 'bzero'])
    summary = images.summary_info
    bad = summary[((summary['bitpix'] == 16) &
                   (summary['bzero'] == ''))]

    print 'Potentially fixing %d files in %s' % (len(bad), directory)

    fix_needed = 0

    for to_fix in bad:
        full_name = path.join(directory, to_fix['file'])
        hdulist = fits.open(full_name)
        dat = np.int32(hdulist[0].data)
        negs = (dat < 0)
        if negs.any():
            dat[negs] += 2 ** 16
            fix_needed += 1

        hdulist[0].data = np.uint16(dat)

        if new_file_ext is not None:
            base, ext = path.splitext(full_name)
            new_file_name = base + new_file_ext + ext
            overwrite = False
        else:
            new_file_name = full_name
            overwrite = True

        hdulist.writeto(new_file_name, clobber=overwrite)
    result_message = 'Changed values in  %d files out of %d that were fixed'
    print result_message % (fix_needed, len(bad))


def compare_data_in_fits(file1, file2):
    """
    Compare the image data in two FITS files.

    Parameters
    ----------
    file1 : str
        Name of first FITS file
    file2 : str
        Name of second FITS file

    Returns
    -------
    bool
        ``True`` if the data in the files is identical, ``False`` otherwise.
    """
    hdu1 = fits.open(file1)
    hdu2 = fits.open(file2)

    identical = (hdu1[0].data == hdu2[0].data).all()
    hdu1.close()
    hdu2.close()
    return identical
