from fitskeyword import FITSKeyword

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
        