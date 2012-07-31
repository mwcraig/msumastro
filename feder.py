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
            seconds = np.round(lst.second + lst.microsecond/1e6, seconds_decimal)
            sec = np.int(seconds)
            microsec = np.int(np.round((seconds-sec)*1e6))
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
    fits_name
    rows
    columns
    overscan_start
    """
    def __init__(self, name, fits_names=None,
                 rows=0, columns=0,
                 overscan_start=None,
                 overscan_axis=None ):
        self.name = name
        self.fits_names = fits_names
        self.rows = rows
        self.columns = columns
        self.overscan_start = overscan_start
        self.overscan_axis = overscan_axis
        
    def has_overscan(self, image_dimensions):
        if (image_dimensions[self.overscan_axis-1] >
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
                
class Feder(object):
    def __init__(self):
        self.site = FederSite()
        self._apogee_alta_u9 = ApogeeAltaU9()
        self.instrument = {}
        for name in self._apogee_alta_u9.fits_names:
            self.instrument[name] = self._apogee_alta_u9

        
keywords_for_all_files = []
keywords_for_light_files = []

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

latitude = FITSKeyword(name="latitude",
                       comment='[degrees] Observatory latitude',
                       synonyms=['sitelat'])

longitude = FITSKeyword(name='longitud',
                        comment='[degrees east] Observatory longitude',
                        synonyms='sitelong')
obs_altitude = FITSKeyword(name='altitude',
                           comment='[meters] Observatory altitude')
keywords_for_all_files.append(latitude)
keywords_for_all_files.append(longitude)
keywords_for_all_files.append(obs_altitude)

overscan_present = FITSKeyword(name='oscan',
                               comment='True if image has overscan region')

overscan_axis = FITSKeyword(name='oscanax',
                            comment='Overscan axis, 1 for NAXIS1, 2 for NAXIS 2')

overscan_start = FITSKeyword(name='oscanst',
                             comment='Starting pixel of overscan region')

hour_angle = FITSKeyword(name='ha',
                         comment='Hour angle')

airmass = FITSKeyword(name='airmass',
                      comment='Airmass (Sec ZD) at start of observation',
                      synonyms=['secz'])

altitude = FITSKeyword(name='alt-obj',
                      comment='[degrees] Altitude of object above the horizon')

azimuth = FITSKeyword(name='az-obj',
                      comment='[degrees] Azimuth of object')

keywords_for_light_files.append(hour_angle)
keywords_for_light_files.append(airmass)
keywords_for_light_files.append(altitude)
keywords_for_light_files.append(azimuth)

LST = FITSKeyword(name='LST',
                  comment='Local Sidereal Time at start of observation')

JD = FITSKeyword(name='jd-obs',
                 comment='Julian Date at start of observation')

MJD = FITSKeyword(name='mjd-obs',
                  comment='Modified Julian date at start of observation')

keywords_for_all_files.append(LST)
keywords_for_all_files.append(JD)
keywords_for_all_files.append(MJD)
