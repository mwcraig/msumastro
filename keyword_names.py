from fitskeyword import FITSKeyword

all_files = []
light_files = []

RA = FITSKeyword(name='ra',
                 comment='Approximate RA at EQUINOX',
                 synonyms=['objctra'])
light_files.append(RA)

Dec = FITSKeyword(name='DEC',
                  comment='Approximate DEC at EQUINOX',
                  synonyms=['objctdec'])
light_files.append(Dec)

target_object = FITSKeyword(name='object',
                     comment='Target of the observations')
light_files.append(target_object)

latitude = FITSKeyword(name="latitude",
                       comment='[degrees] Observatory latitude',
                       synonyms=['sitelat'])

longitude = FITSKeyword(name='longitud',
                        comment='[degrees] east Observatory longitude',
                        synonyms='sitelong')
all_files.append(latitude)
all_files.append(longitude)

hour_angle = FITSKeyword(name='ha',
                         comment='Hour angle')

airmass = FITSKeyword(name='airmass',
                      comment='Airmass (Sec ZD) at start of observation',
                      synonyms=['secz'])

alitude = FITSKeyword(name='alt',
                      comment='[degrees] Altitude of object above the horizon')
azimuth = FITSKeyword(name='azimuth',
                      comment='[degrees] Azimuth of object')

light_files.append(hour_angle)
light_files.append(airmass)
light_files.append(altitude)
light_files.append(azimuth)

LST = FITSKeyword(name='LST',
                  comment='Local Sidereal Time at start of observation')

JD = FITSKeyword(name='jd-obs',
                 comment='Julian Date at start of observation')

MJD = FITSKeyword(name='mjd-obs',
                  comment='Modified Julian date at start of observation')

all_files.append(LST)
all_files.append(JD)
all_files.append(MJD)
        