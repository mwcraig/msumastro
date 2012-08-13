from os import path
from math import cos, pi
from datetime import datetime
import numpy as np

import asciitable
import pyfits
from astropysics import obstools, coords

from feder import *
from astrometry import add_astrometry

from image_collection import ImageFileCollection

federstuff = Feder()
feder = federstuff.site

class FederImage(object):
    """Unsigned integer image for which no data modification is allowed"""
    def __init__(self, fname):
        self._hdulist = pyfits.open(fname, do_not_scale_image_data=True)
        self._hdulist.verify('fix')
        
    @property
    def header(self):
        return self._hdulist[0].header

    def save(self, fname, clobber=False):
        self._hdulist.writeto(fname, clobber=clobber)

    def close(self):
        self._hdulist.close()

def parse_dateobs(dateobs):
    """
    Parse a MaximDL DATE-OBS.

    `dateobs` is a DATE-OBS in the format `yyy-mm-ddThh:mm:ss`

    Returns a `datetime` object with date and time.
    """
    date, time = dateobs.split('T')
    date = date.split('-')
    date = map(int, date)
    time = map(int, time.split(':'))
    date.extend(time)
    return date
    
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
    format_string = degree_format+':{0[1]:02}:{0[2]:0'+seconds_width+'.'+str(precision)+'f}'
    return format_string.format(dms)

def deg2dms(dd):
    """Convert decimal degrees to degrees, minutes, seconds.

    `dd` is decimal degrees.
    
    Poached from stackoverflow.
    """
    mnt,sec = divmod(dd*3600,60)
    deg,mnt = divmod(mnt,60)
    return int(deg),int(mnt),sec

def add_time_info(header, history=False):
    """
    Add JD, MJD, LST to FITS header; `header` should be a pyfits
    header object.

    history : bool
        If `True`, write history for each keyword changed.
    
    Uses `feder.currentobsjd` as the date.
    """
    dateobs = parse_dateobs(header['date-obs'])
    JD.value = round(obstools.calendar_to_jd(dateobs), 6)
    MJD.value = round(obstools.calendar_to_jd(dateobs, mjd=True), 6)
    
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
    RA.value = RA.value.replace(' ',':')
    Dec.value = Dec.value.replace(' ',':')
    object_coords = coords.EquatorialCoordinatesEquinox((RA.value, Dec.value))
    alt_az = feder.apparentCoordinates(object_coords, refraction=False)
    altitude.value = round(alt_az.alt.d, 5)
    azimuth.value = round(alt_az.az.d, 5)
    airmass.value = round(1/cos(pi/2 - alt_az.alt.r),3)
    hour_angle.value = sexagesimal_string(
        coords.EquatorialCoordinatesEquinox((feder.localSiderialTime()-
                                            object_coords.ra.hours,
                                             0)).ra.hms)
    for keyword in keywords_for_light_files:
        if keyword.value is not None:
            keyword.addToHeader(header, history=history)
            

def keyword_names_as_string(list_of_keywords):
    return ' '.join([' '.join(keyword.names) for keyword in list_of_keywords])

def read_object_list(dir='.',list='obsinfo.txt'):
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
        object_file = open(path.join(dir,list),'rb')
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
    
def patch_headers(dir='.', new_file_ext='new',
                  overwrite=False, detailed_history=True):
    """
    Add minimal information to Feder FITS headers.

    `dir` is the directory containing the files to be patched.
    
    `new_file_ext` is the name added to the FITS files with updated
    header information. It is added to the base name of the input
    file, between the old file name and the `.fit` or `.fits` extension.

    `overwrite` should be set to `True` to replace the original files.

    detailed_history : bool
        If `True`, write name and value of each keyword changed to
        output FITS files. If `False`, write only a list of which
        keywords changed.
    """
    images = ImageFileCollection(location=dir, keywords=['imagetyp'])

    latitude.value = sexagesimal_string(feder.latitude.dms)
    longitude.value = sexagesimal_string(feder.longitude.dms)
    obs_altitude.value = feder.altitude

    for header in images.headers(save_with_name=new_file_ext,
                                 clobber=overwrite,
                                 do_not_scale_image_data=True):
        run_time = datetime.now()
        header.add_history(history(patch_headers, mode='begin',
                                   time=run_time))
        header.add_history('patch_headers.py modified this file on %s'
                           % run_time)
        add_time_info(header, history=detailed_history)
        if not detailed_history:
            header.add_history('patch_headers.py updated keywords %s' %
                               keyword_names_as_string(keywords_for_all_files))
        if header['imagetyp'] == 'LIGHT':
            try:
                add_object_pos_airmass(header,
                                 history=detailed_history)
                if not detailed_history:
                    header.add_history('patch_headers.py updated keywords %s' %
                                       keyword_names_as_string(keywords_for_light_files))
            except ValueError:
                print 'Skipping file %s' % image
                continue
        header.add_history(history(patch_headers, mode='end',
                                   time=run_time))
        
def add_overscan(dir='.', new_file_ext='new',
                  overwrite=False, detailed_history=True):
    """
    Add overscan information to Feder FITS headers.

    `dir` is the directory containing the files to be patched.
    
    `new_file_ext` is the name added to the FITS files with updated
    header information. It is added to the base name of the input
    file, between the old file name and the `.fit` or `.fits` extension.

    `overwrite` should be set to `True` to replace the original files.

    detailed_history : bool
        If `True`, write name and value of each keyword changed to
        output FITS files. If `False`, write only a list of which
        keywords changed.
    """
    feder_info = Feder()
    images = ImageFileCollection(location=dir, keywords=['imagetyp', 'instrume'])
    for header in images.headers(save_with_name=new_file_ext,
                                 clobber=overwrite,
                                 do_not_scale_image_data=True):
        image_dim = [header['naxis1'], header['naxis2']]
        instrument = feder_info.instrument[header['instrume']]
        run_time = datetime.now()
        header.add_history(history(add_overscan, mode='begin',
                                   time=run_time))
        overscan_present.value = instrument.has_overscan(image_dim)
        overscan_present.addToHeader(header, history=detailed_history)
        modified_keywords = [overscan_present]
        if overscan_present.value:
            overscan_axis.value = instrument.overscan_axis
            overscan_start.value = instrument.overscan_start
            overscan_axis.addToHeader(header,
                                      history=detailed_history)
            overscan_start.addToHeader(header,
                                       history=detailed_history)
            modified_keywords.extend([overscan_axis, overscan_start])
        if not detailed_history:
            header.add_history('add_overscan updated keywords %s' %
                               keyword_names_as_string(modified_keywords))
        header.add_history(history(add_overscan, mode='end',
                                   time=run_time))

            
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
    import numpy as np
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
        
#    ra_dec_obj = {'er ori':(93.190,12.382), 'm101':(210.826,54.335), 'ey uma':(135.575,49.810)}

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
        distance = [(ra_dec - image_ra_dec).arcmin for ra_dec in object_ra_dec]
        distance = np.array(distance)
        matches = (distance < match_radius)
        if matches.sum() > 1:
            raise RuntimeError("More than one object match for image")

        if not matches.any():
            raise RuntimeWarning("No object foundn for image")
            continue
        object_name = (object_names[matches])[0]   
        obj_keyword = FITSKeyword('object',value=object_name)
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
    missing_dec = summary.where((summary['object'] != '') &
                                (summary['RA'] == '') &
                                (summary['Dec'] == ''))
    if not missing_dec:
        return
        
    objects = unique(missing_dec['object'])
    for object_name in objects:
        obj = AstroObject(object_name)
        RA.value = obj.ra_dec.ra.getHmsStr(canonical=True)
        Dec.value = obj.ra_dec.dec.getDmsStr(canonical=True)
        these_files = missing_dec.where(missing_dec['object'] == object_name)
        for image in these_files:
            full_name = path.join(directory,image['file'])
            hdulist = pyfits.open(full_name)
            header = hdulist[0].header
            int16 = (header['bitpix'] == 16)
            RA.addToHeader(header, history=True)
            Dec.addToHeader(header, history=True)
            if new_file_ext is not None:
                base, ext = path.splitext(full_name)
                new_file_name = base+ new_file_ext + ext
                overwrite=False
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
    bad = summary.where((summary['bitpix'] == 16) &
                        (summary['bzero'] == ''))

    print 'Potentially fixing %d files in %s' % (len(bad), directory)

    fix_needed = 0
    
    for to_fix in bad:
        full_name = path.join(directory, to_fix['file'])
        hdulist = pyfits.open(full_name)
        dat = np.int32(hdulist[0].data)
        negs = (dat < 0)
        if negs.any():
            dat[negs] += 2**16
            fix_needed += 1
        
        hdulist[0].data = np.uint16(dat)

        if new_file_ext is not None:
            base, ext = path.splitext(full_name)
            new_file_name = base+ new_file_ext + ext
            overwrite=False
        else:
            new_file_name = full_name
            overwrite = True

        hdulist.writeto(new_file_name, clobber=overwrite)

    print 'Changed values in  %d files out of %d that were fixed' % (fix_needed, len(bad))
    
def compare_data_in_fits(file1, file2):
    """
    Compare the image data in two FITS files.
    """
    hdu1 = pyfits.open(file1)
    hdu2 = pyfits.open(file2)

    identical = (hdu1[0].data == hdu2[0].data).all()
    hdu1.close()
    hdu2.close()
    return identical

