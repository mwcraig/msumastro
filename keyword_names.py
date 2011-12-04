import pyfits
from fitskeyword import FITSKeyword

RA = FITSKeyword(name='RA',
                 comment='Approximate RA at EQUINOX',
                 synonyms=['OBJCTRA'])

Dec = FITSKeyword(name='DEC',
                  comment='Approximate DEC at EQUINOX',
                  synonyms=['OBJCTDEC'])
Object = FITSKeyword(name='OBJECT',
                     comment='Target of the observations')
Latitude = FITSKeyword(name="Latitude",
                       comment='[degrees] Observatory latitude',
                       synonyms=['sitelat'])
longitude = FITSKeyword(name='longitud',
                        comment='[degrees] east Observatory longitude',
                        synonyms='sitelong')
hour_angle = FITSKeyword(name='ha',
                         comment='Hour angle')
airmass = FITSKeyword(name='airmass',
                      comment='Airmass (Sec ZD) at start of observation',
                      synonyms=['secz'])
LST = FITSKeyword(name='LST',
                  comment='Local Sidereal Time at start of observation')
JD = FITSKeyword(name='JD',
                 comment='Julian Date at start of observation')

        