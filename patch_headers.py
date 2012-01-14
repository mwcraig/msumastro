from os import path
from math import cos, pi
from datetime import datetime

import asciitable
import pyfits
from astropysics import obstools, coords

from feder import *
from astrometry import add_astrometry

import triage_fits_files as tff

feder = FederSite()

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

def add_time_info(header):
    """
    Add JD, MJD, LST to FITS header; `header` should be a pyfits
    header object.

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
        keyword.addToHeader(header, history=False)

def add_object_pos_airmass(header):
    """Add object information, such as RA/Dec and airmass.

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
            keyword.addToHeader(header, history=False)
            

def keyword_names_as_string(list_of_keywords):
    return ' '.join([' '.join(keyword.names) for keyword in list_of_keywords])
    
def patch_headers(dir='.',manifest='Manifest.txt', new_file_ext='new',
                  overwrite=False):
    """
    Add minimal information to Feder FITS headers.

    `dir` is the directory containing the files to be patched.
    
    `manifest` is the name of the file which should contain a listing
    of all of the FITS files in the directory and their types. If the
    file isn't present, the list of files is generated automatically.

    `new_file_ext` is the name added to the FITS files with updated
    header information. It is added to the base name of the input
    file, between the old file name and the `.fit` or `.fits` extension.

    `overwrite` should be set to `True` to replace the original files.
    """
    try:
        image_info_file = open(path.join(dir, manifest))
        image_info = asciitable.read(image_info_file, delimiter=',')
        image_info_file.close()
        files = image_info['file']
    except IOError:
        files = tff.fits_files_in_directory(dir)


    latitude.value = sexagesimal_string(feder.latitude.dms)
    longitude.value = sexagesimal_string(feder.longitude.dms)
    obs_altitude.value = feder.altitude

    for image in files:
        hdulist = pyfits.open(path.join(dir,image))
        header = hdulist[0].header
        int16 = (header['bitpix'] == 16)
        hdulist.verify('fix')
        header.add_history('patch_headers.py modified this file on %s'
                           % datetime.now())
        add_time_info(header)
        header.add_history('patch_headers.py updated keywords %s' %
                            keyword_names_as_string(keywords_for_all_files))
        if header['imagetyp'] == 'LIGHT':
            try:
                add_object_pos_airmass(header)
            except ValueError:
                print 'Skipping file %s' % image
                continue
                
        header.add_history('patch_headers.py updated keywords %s' %
                           keyword_names_as_string(keywords_for_light_files))
        if overwrite:
            new_image = image
        else:
            root, ext = path.splitext(image)
            new_image = root + new_file_ext + ext
            
        if int16:
            hdulist[0].scale('int16')
        hdulist.writeto(path.join(dir,new_image), clobber=overwrite)
        hdulist.close()
