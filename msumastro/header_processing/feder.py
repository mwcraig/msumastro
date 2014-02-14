from itertools import chain
import logging
import datetime

from astropysics import obstools
import numpy as np

from fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)

__all__ = ['FederSite', 'ImageSoftware', 'Instrument', 'ApogeeAltaU9',
           'MaximDL4', 'MaximDL5']


class FederSite(obstools.Site):
    """
    The Feder Observatory site.

    An astropysics site with the observatory location and name pre-set to:

        + `lat` = 46.86678 degrees North
        + `long` = -96.453278 degrees East
        + `alt` = 311.8 meters
        + `name` = Feder Observatory
    """

    def __init__(self):
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

    Parameters
    ----------
    name : str
        Name of the instrument.
    fits_names : list of str
        List of names by which the instrument is known in FITS headers
    rows : int
        Number of rows in an image produced by this instrument, including
        overscan.
    columns : int
        Number of columns in an image produced by this instrument, including
        overscan.
    overscan_start : int
        Position at which the overscan starts. The overscan region is assumed
        to extend from this starting position to the edge of the image.
    overscan_axis : one of (1, 2)
        Axis along which the overscan varies. Numbers correspond to ``NAXIS1``
        and ``NAXIS2`` in the FITS header.

    Examples
    --------

    Consider an image whose dimensions as given in its FITS header are
    ``NAXIS1 = 3085`` and ``NAXIS2 = 2048`` with an overscan region that
    begins at position 3073 along axis 1. The correct overscan settings for
    this instrument are::

        overscan_start = 3073
        overscan_axis = 1
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

        Returns
        -------
        bool
            Indicates whether or not image has overscan present.
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

    Parameters
    ----------
    name : str
        Name of the software. Can be the same is the name in the FITS file,
        or not.
    fits_keyword : str
        Name of the FITS keyword that contains the name of the software.
    fits_name : list of str
        Name of the software as written in the FITS file
    major_version : int
        Major version number of the software.
    minor_version : int
        Minor version number of the software.
    bad_keywords : list of strings
        Names of any keywords that should be removed from the FITS before
        further processing.
    purged_flag_keyword : str, optional
        Name of the keyword which indicates whether bad keywords have already
        been purged. Default value is 'PURGED'
    """

    def __init__(self, name, fits_name=None,
                 major_version=None,
                 minor_version=None,
                 bad_keywords=None,
                 fits_keyword=None,
                 purged_flag_keyword=None):
        self.name = name
        self.fits_name = fits_name
        self.major_version = major_version
        self.minor_version = minor_version
        self.bad_keywords = bad_keywords
        self.fits_keyword = fits_keyword
        self.purged_flag_keyword = purged_flag_keyword or "PURGED"

    def created_this(self, version_string):
        """
        Indicate whether version string matches this software

        Parameters
        ----------
        version_string : str
            String from FITS header that indicates software version.

        Returns
        -------
        bool
            ``True`` if the version string matches the software instance.
        """
        return version_string in self.fits_name


class MaximDL4(ImageSoftware):

    """
    Represents MaximDL version 4, all sub-versions
    """

    def __init__(self):
        fits_name = ['MaxIm DL Version 4.10']
        super(MaximDL4, self).__init__("MaxImDL",
                                       fits_name=fits_name,
                                       major_version=4,
                                       minor_version=10,
                                       bad_keywords=['OBSERVER'],
                                       fits_keyword='SWCREATE')


class MaximDL5(ImageSoftware):

    """
    Represents MaximDL version 5, all sub-versions.

    Subversions are included by listing the FITS names of all versions that
    have been used at Feder Observatory.
    """

    def __init__(self):
        bad_keys = ['OBJECT', 'JD', 'JD-HELIO', 'OBJCTALT', 'OBJCTAZ',
                    'OBJCTHA', 'AIRMASS', 'OBSERVER']
        fits_name = ['MaxIm DL Version 5.21 130912 01A17',
                     'MaxIm DL Version 5.21 120829 2R1M0',
                     'MaxIm DL Version 5.23 130912 01A17']
        super(MaximDL5, self).__init__("MaxImDL",
                                       fits_name=fits_name,
                                       major_version=5,
                                       minor_version=21,
                                       bad_keywords=bad_keys,
                                       fits_keyword='SWCREATE'
                                       )


class Feder(object):
    """
    Class encapsulating site, instrument, and software information for Feder
    Observatory.

    Attributes
    ----------
    site : feder.FederSite instance
    instrument : dict
        Instruments available; key is name, value is an :py:class:`Instrument`
    software : dict
        Software available; key is name, value is an :class:`ImageSoftware`
    software_FITS_keywords : list of str
        FITS names of all software available.
    keywords_for_all_files
    keywords_for_light_files
    keywords_for_overscan
    """
    def __init__(self):
        self.site = FederSite()
        self._apogee_alta_u9 = ApogeeAltaU9()
        self._instrument_objects = [self._apogee_alta_u9]
        self.instruments = {}
        for instrument in self._instrument_objects:
            for name in instrument.fits_names:
                self.instruments[name] = instrument
        self._maximdl4 = MaximDL4()
        self._maximdl5 = MaximDL5()
        self._software_objects = [self._maximdl4, self._maximdl5]
        self.software = {}
        self.software_FITS_keywords = []
        for software in self._software_objects:
            for name in software.fits_name:
                self.software[name] = software
                self.software_FITS_keywords.append(software.fits_keyword)
        self.software_FITS_keywords = list(set(self.software_FITS_keywords))
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
        """
        List of :class:`~msumastro.header_processing.fitskeyword.FITSKeyword` s
        whose values need to be set for all image types.
        """
        return self._keywords_for_all_files

    @property
    def keywords_for_light_files(self):
        """
        List of :class:`~msumastro.header_processing.fitskeyword.FITSKeyword` s
        whose values need to be set only for light image types.
        """
        return self._keywords_for_light_files

    @property
    def keywords_for_overscan(self):
        """
        List of :class:`~msumastro.header_processing.fitskeyword.FITSKeyword` s
        related to overscan.
        """
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
