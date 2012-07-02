from astropysics import obstools
from fitskeyword import FITSKeyword

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
    def __init__(self, name, fits_name=None,
                 rows=0, columns=0,
                 overscan_start=None,
                 overscan_axis=None ):
        self.name = name
        self.fits_name = fits_name
        self.rows = rows
        self.columns = columns
        self.overscan_start = overscan_start
        self.overscan_axis = overscan_axis

class ApogeeAltaU9(Instrument):
    def __init__(self):
        Instrument.__init__(self, "Apogee Alta U9",
                            fits_name="Apogee Alta",
                            rows=2048, columns=3085,
                            overscan_start=3073,
                            overscan_axis=1)
                
class Feder(object):
    def __init__(self):
        self.site = FederSite()
        self.instrument = { ApogeeAltaU9().fits_name: ApogeeAltaU9() }
        
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
