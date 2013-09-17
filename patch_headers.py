from os import path
from math import cos, pi
from datetime import datetime
import numpy as np

import astropy.io.fits as fits
from astropysics import coords
from astropy.time import Time

from feder import *

from image_collection import ImageFileCollection

federstuff = Feder()
feder = federstuff.site


class FederImage(object):

    """Unsigned integer image for which no data modification is allowed"""

    def __init__(self, fname):
        self._hdulist = fits.open(fname, do_not_scale_image_data=True)
        self._hdulist.verify('fix')

    @property
    def header(self):
        return self._hdulist[0].header

    def save(self, fname, clobber=False):
        self._hdulist.writeto(fname, clobber=clobber)

    def close(self):
        self._hdulist.close()


def sexagesimal_string(dms, precision=2, sign=False):
    """Convert degrees, minutes, seconds into a string

    `dms` should be a list or tuple of (degrees or hours, minutes,
    seconds)

    `precision` is the number of digits to be kept to the right of the
    decimal in the seconds (default is 2)

    Set `sign` to `True` if a leading sign should be displayed for
    positive values.
    """
    if sign:
        degree_format = '{0[0]:+03}'
    else:
        degree_format = '{0[0]:02}'

    seconds_width = str(precision + 3)
    format_string = degree_format + \
        ':{0[1]:02}:{0[2]:0' + seconds_width + '.' + str(precision) + 'f}'
    return format_string.format(dms)


def deg2dms(dd):
    """Convert decimal degrees to degrees, minutes, seconds.

    `dd` is decimal degrees.

    Poached from stackoverflow.
    """
    mnt, sec = divmod(dd * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return int(deg), int(mnt), sec


def add_time_info(header, history=False):
    """
    Add JD, MJD, LST to FITS header; `header` should be a fits
    header object.

    history : bool
        If `True`, write history for each keyword changed.

    Uses `feder.currentobsjd` as the date.
    """
    dateobs = Time(header['date-obs'], scale='utc')
    JD.value = dateobs.jd
    MJD.value = dateobs.mjd

    # setting currentobsjd makes calls following it use that time
    # for calculations

    feder.currentobsjd = JD.value
    LST.value = feder.localSiderialTime()
    LST.value = sexagesimal_string(deg2dms(LST.value))

    for keyword in keywords_for_all_files:
        keyword.addToHeader(header, history=history)


def add_object_pos_airmass(header, history=False):
    """Add object information, such as RA/Dec and airmass.

    history : bool
        If `True`, write history for each keyword changed.

    Has side effect of setting feder site JD to JD-OBS, which means it
    also assume JD.value has been set.
    """
    if JD.value is not None:
        feder.currentobsjd == JD.value
    else:
        raise ValueError('Need to set JD.value before calling.')

    try:
        RA.setValueFromHeader(header)
    except ValueError:
        raise ValueError("No RA is present.")
        return

    Dec.setValueFromHeader(header)
    RA.value = RA.value.replace(' ', ':')
    Dec.value = Dec.value.replace(' ', ':')
    object_coords = coords.EquatorialCoordinatesEquinox((RA.value, Dec.value))
    alt_az = feder.apparentCoordinates(object_coords, refraction=False)
    altitude.value = round(alt_az.alt.d, 5)
    azimuth.value = round(alt_az.az.d, 5)
    airmass.value = round(1 / cos(pi / 2 - alt_az.alt.r), 3)
    hour_angle.value = sexagesimal_string(
        coords.EquatorialCoordinatesEquinox((feder.localSiderialTime() -
                                            object_coords.ra.hours,
                                             0)).ra.hms)
    for keyword in keywords_for_light_files:
        if keyword.value is not None:
            keyword.addToHeader(header, history=history)


def purge_bad_keywords(header, history=False, force=False):
    """
    Remove keywords from FITS header that may be incorrect

    history : bool
        If `True` write detailed history for each keyword removed.

    force : bool
        If `True`, force keywords to be purged even if the FITS header
        indicates it has already been purged.
    """
    for software in federstuff.software:
        if software.created_this(header[software.fits_keyword]):
            break

    try:
        purged = header[software.purged_flag_keyword]
    except KeyError:
        purged = False

    if purged and not force:
        print "Not removing headers again, set force=True to force removal."
        return

    for keyword in software.bad_keywords:
        try:
            comment = ('Deleted keyword ' + keyword +
                       ' with value ' + str(header[keyword]))
        except KeyError:
            continue

        del header[keyword]
        if history:
            header.add_history(comment)

    header[software.purged_flag_keyword] = (True,
                                            'Have bad keywords been removed?')


def keyword_names_as_string(list_of_keywords):
    return ' '.join([' '.join(keyword.names) for keyword in list_of_keywords])


def read_object_list(dir='.', list='obsinfo.txt'):
    """
    Read a list of objects from a text file.

    `dir` is the directory containing the file.

    `list` is the name of the file.

    File format:
        + All lines in the files that start with # are ignored.
        + First line is the name(s) of the observer(s)
        + Remaining line(s) are name(s) of object(s), one per line
    """
    try:
        object_file = open(path.join(dir, list), 'rb')
    except IOError:
        raise IOError('File %s in directory %s not found.' % (list, dir))

    first_line = True
    objects = []
    for line in object_file:
        if not line.startswith('#'):
            if first_line:
                first_line = False
                observer = line.strip()
            else:
                if line.strip():
                    objects.append(line.strip())

    return (observer, objects)


def history(function, mode='begin', time=None):
    """
    Construct nicely formatted start/end markers in FITS history.

    Parameters

    function : func
        Function calling `history`
    mode : str, 'begin' or 'end'
    time : datetime
        If not set, defaults to current date/time.
    """
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


def patch_headers(dir='.',
                  new_file_ext='new',
                  save_location=None,
                  overwrite=False,
                  purge_bad=True,
                  add_time=True,
                  add_apparent_pos=True,
                  add_overscan=True):
    """
    Add minimal information to Feder FITS headers.

    `dir` is the directory containing the files to be patched.

    `new_file_ext` is the name added to the FITS files with updated
    header information. It is added to the base name of the input
    file, between the old file name and the `.fit` or `.fits` extension.

    `save_location` is the directory to which the patched files
        should be written, if not `dir`

    `overwrite` should be set to `True` to replace the original files.

    `purge_bad`, `add_time`, `add_apparent_pos` and `add_overscan` are flags
    that control which aspect of the headers is modified.
    """
    images = ImageFileCollection(location=dir, keywords=['imagetyp'])

    latitude.value = sexagesimal_string(feder.latitude.dms)
    longitude.value = sexagesimal_string(feder.longitude.dms)
    obs_altitude.value = feder.altitude

    for header in images.headers(save_with_name=new_file_ext,
                                 save_location=save_location,
                                 clobber=overwrite,
                                 do_not_scale_image_data=True):
        run_time = datetime.now()
        header.add_history(history(patch_headers, mode='begin',
                                   time=run_time))
        header.add_history('patch_headers.py modified this file on %s'
                           % run_time)

        if purge_bad:
            purge_bad_keywords(header, history=True)

        if add_time:
            add_time_info(header, history=True)

        if add_apparent_pos and (header['imagetyp'] == 'LIGHT'):
            try:
                add_object_pos_airmass(header,
                                       history=True)
            except ValueError:
                print ('Skipping file with header:')
                print(header)
                continue

        if add_overscan:
            add_overscan_header(header, history=True)

        header.add_history(history(patch_headers, mode='end',
                                   time=run_time))


def add_overscan_header(header, history=True):
    """
    Add overscan information to a FITS header.
    """
    feder_info = Feder()
    image_dim = [header['naxis1'], header['naxis2']]
    instrument = feder_info.instrument[header['instrume']]
    overscan_present.value = instrument.has_overscan(image_dim)
    overscan_present.addToHeader(header, history=history)
    modified_keywords = [overscan_present]
    if overscan_present.value:
        overscan_axis.value = instrument.overscan_axis
        overscan_start.value = instrument.overscan_start
        overscan_axis.addToHeader(header,
                                  history=history)
        overscan_start.addToHeader(header,
                                   history=history)
        modified_keywords.extend([overscan_axis, overscan_start])

    return modified_keywords


def add_object_info(directory='.', object_list=None,
                    match_radius=20.0, new_file_ext='new',
                    overwrite=False, detailed_history=True):
    """
    Automagically add object information to FITS files.

    `directory` is the directory containing the FITS files to be fixed
    up and an `object_list`. Set `object_list` to `None` to use
    default object list name.

    `match_radius` is the maximum distance, in arcmin, between the
    RA/Dec of the image and a particular object for the image to be
    considered an image of that object.
    """
    from astro_object import AstroObject
    from fitskeyword import FITSKeyword

    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'RA',
                                           'Dec', 'object'])
    summary = images.summary_info

    print summary['file']
    try:
        observer, object_names = read_object_list(directory)
    except IOError:
        print 'No object list in directory %s, skipping.' % directory
        return

#    ra_dec_obj = {'er ori':(93.190,12.382), 'm101':(210.826,54.335),
#                  'ey uma':(135.575,49.810)}

    object_names = np.array(object_names)
    ra_dec = []
    for object_name in object_names:
        obj = AstroObject(object_name)
        ra_dec.append(obj.ra_dec)
    object_ra_dec = np.array(ra_dec)

    for header in images.headers(save_with_name=new_file_ext,
                                 clobber=overwrite,
                                 object='', RA='*', Dec='*'):
        image_ra_dec = coords.coordsys.FK5Coordinates(header['ra'],
                                                      header['dec'])
        distance = [(rd_tmp - image_ra_dec).arcmin for rd_tmp in object_ra_dec]
        distance = np.array(distance)
        matches = (distance < match_radius)
        if matches.sum() > 1:
            raise RuntimeError("More than one object match for image")

        if not matches.any():
            raise RuntimeWarning("No object foundn for image")
            continue
        object_name = (object_names[matches])[0]
        obj_keyword = FITSKeyword('object', value=object_name)
        obj_keyword.addToHeader(header, history=True)


def add_ra_dec_from_object_name(directory='.', new_file_ext=None):
    """
    Add RA/Dec to FITS file that has object name but no pointing.
    """
    from numpy import unique
    from astro_object import AstroObject

    images = ImageFileCollection(directory,
                                 keywords=['imagetyp', 'RA',
                                           'Dec', 'object'])
    summary = images.summary_info
    missing_dec = summary[(summary['object'] != '') &
                          (summary['RA'] == '') &
                          (summary['Dec'] == '')]
    if not missing_dec:
        return

    objects = unique(missing_dec['object'])
    for object_name in objects:
        obj = AstroObject(object_name)
        RA.value = obj.ra_dec.ra.getHmsStr(canonical=True)
        Dec.value = obj.ra_dec.dec.getDmsStr(canonical=True)
        these_files = missing_dec[missing_dec['object'] == object_name]
        for image in these_files:
            full_name = path.join(directory, image['file'])
            hdulist = fits.open(full_name)
            header = hdulist[0].header
            int16 = (header['bitpix'] == 16)
            RA.addToHeader(header, history=True)
            Dec.addToHeader(header, history=True)
            if new_file_ext is not None:
                base, ext = path.splitext(full_name)
                new_file_name = base + new_file_ext + ext
                overwrite = False
            else:
                new_file_name = full_name
                overwrite = True
            if int16:
                hdulist[0].scale('int16')
            hdulist.writeto(new_file_name, clobber=overwrite)
            hdulist.close()


def fix_int16_images(directory='.', new_file_ext=None):
    """Repair unsigned int16 images saved as signed.

    Use with care; if your data really is signed int16 this will corrupt it.
    """
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
    """
    hdu1 = fits.open(file1)
    hdu2 = fits.open(file2)

    identical = (hdu1[0].data == hdu2[0].data).all()
    hdu1.close()
    hdu2.close()
    return identical
