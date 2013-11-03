from itertools import chain
import logging
import datetime

from astropysics import obstools
import numpy as np

from fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)


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
        """
        Determine whether an image taken by this instrument has overscan

        Parameters
        ----------

        image_dimensions : list-like with two elements
            Shape of the image; can be any type as long as it has two elements.
        """
        if (image_dimensions[self.overscan_axis - 1] >
                self.overscan_start):

            return True
        else:
            return False


class ApogeeAltaU9(Instrument):
    """
    The Apogee Alta U9
    """
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
    ----------

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
                                       bad_keywords=['OBSERVER'],
                                       fits_keyword='SWCREATE')


class MaximDL5(ImageSoftware):

    """
    Represents MaximDL version 5, all sub-versions
    """

    def __init__(self):
        bad_keys = ['OBJECT', 'JD', 'JD-HELIO', 'OBJCTALT', 'OBJCTAZ',
                    'OBJCTHA', 'AIRMASS', 'OBSERVER']
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
        self._keywords_for_light_files = []
        self._define_keywords_for_light_files()
        self._overscan_keywords = []
        self._define_overscan_keywords()
        for key in chain(self.keywords_for_all_files,
                         self.keywords_for_light_files,
                         self.keywords_for_overscan):
            name = key.name
            name = name.replace('-', '_')
            setattr(self, name, key)

    @property
    def keywords_for_all_files(self):
        return self._keywords_for_all_files

    @property
    def keywords_for_light_files(self):
        return self._keywords_for_light_files

    @property
    def keywords_for_overscan(self):
        return self._overscan_keywords

    def _define_keywords_for_light_files(self):
        RA = FITSKeyword(name='ra',
                         comment='Approximate RA at EQUINOX',
                         synonyms=['objctra'])

        Dec = FITSKeyword(name='DEC',
                          comment='Approximate DEC at EQUINOX',
                          synonyms=['objctdec'])

        target_object = FITSKeyword(name='object',
                                    comment='Target of the observations')

        hour_angle = FITSKeyword(name='ha',
                                 comment='Hour angle')

        airmass = FITSKeyword(name='airmass',
                              comment='Airmass (Sec(Z)) at start of observation',
                              synonyms=['secz'])

        altitude = FITSKeyword(name='alt-obj',
                               comment='[degrees] Altitude of object, no refraction')

        azimuth = FITSKeyword(name='az-obj',
                              comment='[degrees] Azimuth of object, no refraction')
        self._keywords_for_light_files.append(RA)
        self._keywords_for_light_files.append(Dec)
        self._keywords_for_light_files.append(target_object)
        self._keywords_for_light_files.append(hour_angle)
        self._keywords_for_light_files.append(airmass)
        self._keywords_for_light_files.append(altitude)
        self._keywords_for_light_files.append(azimuth)

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

    def _define_overscan_keywords(self):
        overscan_present = FITSKeyword(name='oscan',
                                       comment='True if image has overscan region')

        overscan_axis = FITSKeyword(name='oscanax',
                                    comment='Overscan axis, 1 is NAXIS1, 2 is NAXIS 2')

        overscan_start = FITSKeyword(name='oscanst',
                                     comment='Starting pixel of overscan region')
        self._overscan_keywords.extend([overscan_present,
                                       overscan_axis,
                                       overscan_start])