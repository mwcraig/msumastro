from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from itertools import chain
import logging
import datetime

from astropy.coordinates import EarthLocation
import astropy.units as u
import numpy as np
from ccdproc.utils.slices import slice_from_string

from .fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)

__all__ = ['FederSite', 'ImageSoftware', 'Instrument', 'ApogeeAltaU9',
           'MaximDL4', 'MaximDL5']


class FederSite(EarthLocation):
    """
    The Feder Observatory site.

    An astropy location with the observatory location pre-set to:

        + `lat` = 46.86678 degrees North
        + `long` = -96.453278 degrees East
        + `height` = 311.8 meters

    and a few additional properties/methods that are convenient:

        + `name` = Feder Observatory
    """

    def __new__(cls):
        return EarthLocation.__new__(FederSite,
                                     lat=46.86678*u.degree,
                                     lon=-96.453278*u.degree,
                                     height=311.8*u.m)

    def __init__(self):
        self._name = 'Feder Observatory'

    @property
    def name(self):
        return self._name


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

    image_unit : astropy.units.Unit
        Unit of the image; default value is ``None``

    trim_region : string
        Region of the CCD that should be preserved after overscan subtraction.
        Should use *FITS* conventions for specifying slices (i.e. slice
        starts at 1, includes endpoint, and uses FITS NAXIS1, NAXIS2 for
        order of indices).

    useful_overscan_region : string
        Complete specification of the region of the CCD actually useful for
        overscan calibration. This may (or may not) be smaller than the
        entire portion of the chip the manufacturer labels as overscan.
        Should use *FITS* conventions for specifying slices (i.e. slice
        starts at 1, includes endpoint, and uses FITS NAXIS1, NAXIS2 for
        order of indices).

    Examples
    --------

    Consider an image whose dimensions as given in its FITS header are
    ``NAXIS1 = 3085`` and ``NAXIS2 = 2048`` with an overscan region that
    begins at position 3073 along axis 1. The useful part of that overscan is
    from FITS column 3076 up to and including, 3079, and the full range of
    rows (``NAXIS2``). The correct overscan settings for this instrument are::

        # Note not all of the overscan region is actually useful.
        useful_overscan_region = '[3076:3079, :]'
        # But the whole overscan region should be trimmed away in reduction.
        trim_region = '[1:3073, :]'
    """

    def __init__(self, name, fits_names=None,
                 rows=0, columns=0,
                 image_unit=None,
                 trim_region=None,
                 useful_overscan_region=None):
        self.name = name
        self.fits_names = fits_names
        self.rows = rows
        self.columns = columns
        self.image_unit = image_unit
        self.trim_region = trim_region
        self.useful_overscan = useful_overscan_region

    def has_overscan(self, image_dimensions):
        """
        Determine whether an image taken by this instrument has overscan

        Parameters
        ----------
        image_dimensions : list-like with two elements
            Shape of the image; can be any type as long as it has two elements.
            The order should be the FITS order, ``NAXIS1`` then ``NAXIS2``.

        Returns
        -------
        bool
            Indicates whether or not image has overscan present.
        """

        if self.trim_region is None:
            return False

        # Grab the trim region as a slice to make it easier to access end
        # points. Do *not* convert from FITS convention because input
        # dimensions follow FITS conventions.
        trim_dim = slice_from_string(self.trim_region)

        dim_end = lambda ax: (trim_dim[ax].stop + 1
                              if trim_dim[ax].stop is not None
                              else image_dimensions[ax])
        # print(trim_dim1, trim_dim2)
        # if trim_dim1.stop is not None:
        #     dim1_end = trim_dim1.stop + 1
        # else:
        #     # None means use the whole thing....
        #     dim1_end = image_dimensions[0]

        # if trim_dim2.stop is not None:
        #     dim2_end = trim_dim2.stop + 1
        # else:
        #     # None means use the whole thing....
        #     dim2_end = image_dimensions[1]

        if (dim_end(0) < image_dimensions[0] or
            dim_end(1) < image_dimensions[1]):

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
                            useful_overscan_region='[3076:3079, :]',
                            trim_region='[1:3073, :]',
                            image_unit=u.adu)


class SBIGSpectrometer(Instrument):
    """
    SBIG ST-7 spectromter.
    """
    def __init__(self):
        super(SBIGSpectrometer, self).__init__("SBIG ST-7 Spectrometer",
                                               fits_names=["SBIG ST-7"])


class CelestronNightscape10100(Instrument):
    """
    The Celestron Nightscape 10100, an RGB color CCD.
    """
    def __init__(self):
        Instrument.__init__(self, "Celestron Nightscape 10100",
                            fits_names=["Celestron Nightscape 10100"],
                            image_unit=u.adu)


class ApogeeAspenCG16(Instrument):
    """
    Apogee Aspen CG16 (manufactured by Andor).by
    """
    def __init__(self):
        super(ApogeeAspenCG16, self).__init__(
            'Apogee Aspen CG16',
            fits_names=["Apogee Aspen CG16M"],
            rows=4096, columns=4109,
            useful_overscan_region='[4096:4109]',
            trim_region='[1:4096, :]',
            image_unit=u.adu
        )


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
                     'MaxIm DL Version 5.23 130912 01A17',
                     'MaxIm DL Version 5.15']
        super(MaximDL5, self).__init__("MaxImDL",
                                       fits_name=fits_name,
                                       major_version=5,
                                       minor_version=21,
                                       bad_keywords=bad_keys,
                                       fits_keyword='SWCREATE'
                                       )


class SBIGCCDOps(ImageSoftware):
    """
    Represents software used to create images from the SBIG spectrometer.
    """
    def __init__(self):
        bad_keys = []
        fits_name = ['SBIG Win CCDOPS Version 5.47 Build 6-NT']
        super(SBIGCCDOps, self).__init__("SBIG CCDOps",
                                         fits_name=fits_name,
                                         major_version=5,
                                         minor_version=47,
                                         bad_keywords=[],
                                         fits_keyword='SWCREATE')


class CelestronAstroFX(ImageSoftware):
    """
    Represents software used to create images from the SBIG spectrometer.
    """
    def __init__(self):
        bad_keys = []
        fits_name = ['Celestron AstroFX V1.06']
        super(CelestronAstroFX, self).__init__("Celestron AstroFX",
                                               fits_name=fits_name,
                                               major_version=1,
                                               minor_version="06",
                                               bad_keywords=bad_keys,
                                               fits_keyword='SWCREATE')


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
        self._sbig_spectrometer = SBIGSpectrometer()
        self._celestron_10100 = CelestronNightscape10100()
        self._apogee_aspen = ApogeeAspenCG16()
        self._instrument_objects = [self._apogee_alta_u9,
                                    self._sbig_spectrometer,
                                    self._celestron_10100,
                                    self._apogee_aspen]
        self.instruments = {}
        for instrument in self._instrument_objects:
            for name in instrument.fits_names:
                self.instruments[name] = instrument
        self._maximdl4 = MaximDL4()
        self._maximdl5 = MaximDL5()
        self._sbig_ccdops = SBIGCCDOps()
        self._astrofx = CelestronAstroFX()
        self._software_objects = \
            [self._maximdl4, self._maximdl5, self._sbig_ccdops, self._astrofx]
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
        lat_lon_format = {'sep': ':', 'pad': True, 'alwayssign': True}
        latitude.value = self.site.latitude.to_string(**lat_lon_format)
        longitude.value = self.site.longitude.to_string(**lat_lon_format)
        obs_altitude.value = self.site.height.value
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
        overscan_region = FITSKeyword(name='biassec',
                                    comment='Useful region of the overscan')

        trim_region = FITSKeyword(name='trimsec',
            comment=('Region to keep after trimming overscan'))

        self._overscan_keywords.extend([overscan_region,
                                       trim_region])
