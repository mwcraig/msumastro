from astropysics import obstools
from fitskeyword import FITSKeyword
import numpy as np


class FederSite(obstools.Site):

    """
    The Feder Observatory site.

    An astropysics site with the observatory location and name pre-set.
    """

    def __init__(self):
        """
        Location/name information are set for Feder Observatory.

        `lat` = 46.86678 degrees

        `long` = -96.453278 degrees Eaast

        `alt` = 311.8 meters

        `name` = Feder Observatory
        """
        obstools.Site.__init__(self,
                               lat=46.86678,
                               long=-96.453278,
                               alt=311.8,
                               name='Feder Observatory')

    def localSiderialTime(self, seconds_decimal=None, *arg, **kwd):
        import datetime
        try:
            return_type = kwd['returntype']
        except KeyError:
            return_type = 'hours'

        if return_type is None or return_type == 'hours':
            return super(FederSite, self).localSiderialTime(*arg,
                                                            **kwd)

        return_type = kwd.pop('returntype', None)
        lst = super(FederSite, self).localSiderialTime(*arg,
                                                       returntype='datetime',
                                                       **kwd)
        if seconds_decimal is not None:
            seconds = np.round(lst.second + lst.microsecond / 1e6,
                               seconds_decimal)
            sec = np.int(seconds)
            microsec = np.int(np.round((seconds - sec) * 1e6))
            lst = datetime.time(lst.hour, lst.minute, sec, microsec)
        if return_type == 'string':
            lst = lst.isoformat()
        return lst


class Instrument(object):

    """
    Telescope instrument with simple properties.

    Properties
    __________

    name
    fits_names
    rows
    columns
    overscan_start
    """

    def __init__(self, name, fits_names=None,
                 rows=0, columns=0,
                 overscan_start=None,
                 overscan_axis=None):
        self.name = name
        self.fits_names = fits_names
        self.rows = rows
        self.columns = columns
        self.overscan_start = overscan_start
        self.overscan_axis = overscan_axis

    def has_overscan(self, image_dimensions):
        if (image_dimensions[self.overscan_axis - 1] >
                self.overscan_start):

            return True
        else:
            return False


class ApogeeAltaU9(Instrument):

    def __init__(self):
        Instrument.__init__(self, "Apogee Alta U9",
                            fits_names=["Apogee Alta", "Apogee USB/Net"],
                            rows=2048, columns=3085,
                            overscan_start=3073,
                            overscan_axis=1)


class ImageSoftware(object):

    """
    Represents software that takes images at telescope.

    Properties

    name : str

        Name of the software. Can be the same is the name in the FITS file,
        or not.

    fits_keyword : str

        Name of the FITS keyword that contains the name of the software.

    fits_name : str

        Name of the software as written in the FITS file

    major_version : int

        Major version number of the software.

    minor_version : int

        Minor version number of the software.

    bad_keywords : list of strings

        Names of any keywords that should be removed from the FITS before
        further processing.
    """

    def __init__(self, name, fits_name=None,
                 major_version=None,
                 minor_version=None,
                 bad_keywords=None,
                 fits_keyword=None,
                 purged_flag_keyword='PURGED'):
        self.name = name
        self.fits_name = fits_name
        self.major_version = major_version
        self.minor_version = minor_version
        self.bad_keywords = bad_keywords
        self.fits_keyword = fits_keyword
        self.purged_flag_keyword = purged_flag_keyword

    def created_this(self, version_string):
        """
        Indicate whether version string matches this software
        """
        return version_string == self.fits_name


class MaximDL4(ImageSoftware):

    """
    Represents MaximDL version 4, all sub-versions
    """

    def __init__(self):
        super(MaximDL4, self).__init__("MaxImDL",
                                       fits_name='MaxIm DL Version 4.10',
                                       major_version=4,
                                       minor_version=10,
                                       bad_keywords=[],
                                       fits_keyword='SWCREATE')


class MaximDL5(ImageSoftware):

    """
    Represents MaximDL version 5, all sub-versions
    """

    def __init__(self):
        bad_keys = ['OBJECT', 'JD', 'JD-HELIO', 'OBJCTALT', 'OBJCTAZ',
                    'OBJCTHA', 'AIRMASS']
        fits_name = 'MaxIm DL Version 5.21 130912 01A17'
        super(MaximDL5, self).__init__("MaxImDL",
                                       fits_name=fits_name,
                                       major_version=5,
                                       minor_version=21,
                                       bad_keywords=bad_keys,
                                       fits_keyword='SWCREATE'
                                       )


class Feder(object):

    def __init__(self):
        self.site = FederSite()
        self._apogee_alta_u9 = ApogeeAltaU9()
        self.instrument = {}
        for name in self._apogee_alta_u9.fits_names:
            self.instrument[name] = self._apogee_alta_u9
        self._maximdl4 = MaximDL4()
        self._maximdl5 = MaximDL5()
        self.software = [self._maximdl4, self._maximdl5]
        self._keywords_for_all_files = []
        self._set_site_keywords_values()
        self._time_keywords_to_set()
        for key in self.keywords_for_all_files:
            name = key.name
            name = name.replace('-', '_')
            setattr(self, name, key)

    @property
    def keywords_for_all_files(self):
        return self._keywords_for_all_files

    def _set_site_keywords_values(self):
        latitude = FITSKeyword(name="latitude",
                               comment='[degrees] Observatory latitude',
                               synonyms=['sitelat'])

        longitude = FITSKeyword(name='longitud',
                                comment='[degrees east] Observatory longitude',
                                synonyms='sitelong')
        obs_altitude = FITSKeyword(name='altitude',
                                   comment='[meters] Observatory altitude')
        latitude.value = self.site.latitude.getDmsStr(canonical=True)
        longitude.value = self.site.longitude.getDmsStr(canonical=True)
        obs_altitude.value = self.site.altitude
        self._keywords_for_all_files.extend([latitude, longitude,
                                            obs_altitude])

    def _time_keywords_to_set(self):
        LST = FITSKeyword(name='LST',
                          comment='Local Sidereal Time at start of observation')

        JD = FITSKeyword(name='jd-obs',
                         comment='Julian Date at start of observation')

        MJD = FITSKeyword(name='mjd-obs',
                          comment='Modified Julian date at start of observation')
        self._keywords_for_all_files.extend([LST, JD, MJD])


keywords_for_light_files = []


# Overscan is also added to all files, but as a separate pass from the
# other all-file keywords.
overscan_present = FITSKeyword(name='oscan',
                               comment='True if image has overscan region')

overscan_axis = FITSKeyword(name='oscanax',
                            comment='Overscan axis, 1 is NAXIS1, 2 is NAXIS 2')

overscan_start = FITSKeyword(name='oscanst',
                             comment='Starting pixel of overscan region')

# Keywords below are added only to light images
RA = FITSKeyword(name='ra',
                 comment='Approximate RA at EQUINOX',
                 synonyms=['objctra'])
keywords_for_light_files.append(RA)

Dec = FITSKeyword(name='DEC',
                  comment='Approximate DEC at EQUINOX',
                  synonyms=['objctdec'])
keywords_for_light_files.append(Dec)

target_object = FITSKeyword(name='object',
                            comment='Target of the observations')
keywords_for_light_files.append(target_object)

hour_angle = FITSKeyword(name='ha',
                         comment='Hour angle')

airmass = FITSKeyword(name='airmass',
                      comment='Airmass (Sec(Z)) at start of observation',
                      synonyms=['secz'])

altitude = FITSKeyword(name='alt-obj',
                       comment='[degrees] Altitude of object, no refraction')

azimuth = FITSKeyword(name='az-obj',
                      comment='[degrees] Azimuth of object, no refraction')

keywords_for_light_files.append(hour_angle)
keywords_for_light_files.append(airmass)
keywords_for_light_files.append(altitude)
keywords_for_light_files.append(azimuth)
