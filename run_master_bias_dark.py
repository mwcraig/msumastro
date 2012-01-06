import triage_fits_files as tff
import ccd_characterization as ccd_char
import sys
from astropysics import ccd, pipeline
from os import path
from numpy import logical_not, median, mean

temperature_tolerance = 1 #degree C
combiner = ccd.ImageCombiner()

for currentDir in foo:
    keywords = ['imagetyp', 'exposure', 'ccd-temp']
    images = tff.ImageFileCollection(location=currentDir,
                                     keywords=keywords)
    useful = images.summary_info
    bias_files=useful.where(useful['imagetyp']=='BIAS')
    if bias_files:
        bias_data = []
        for fil in bias_files['file']:
            a_bias = ccd.FitsImage(path.join(currentDir,fil))
            bias_data.append(a_bias)

        combiner.method = 'median'
        master_bias = combiner.combineImages(bias_data)

    dark_files = useful.where(useful['imagetyp']=='DARK')
    if dark_files:
        exposure_times = set(dark_files['exposure'])
        master_dark = {}
        avg_temp = {}
        for time in exposure_times:
            these_darks=dark_files.where(dark_files['exposure']==time)
            avg_temp[time] = these_darks['ccd-temp'].mean()
            good_darks = abs(these_darks['ccd-temp'] - avg_temp[time]) < temperature_tolerance
            bad_darks = logical_not(good_darks)
            if bad_darks.any():
                raise pipeline.PipelineError('Darks with exposure time %f have a temperature problem!' % time )
            dark_data = []
            for dark in these_darks['file'][good_darks]:
                a_dark = ccd.FitsImage(path.join(currentDir,dark))
                dark_data.append(a_dark.data)

            combiner.method = 'median'
            master_dark[time] = combiner.combineImages(dark_data)
            print time, avg_temp[time], median(master_dark[time]), mean(master_dark[time])
            print ccd_char.ccd_dark_current(master_bias,dark_data,gain=1.5)/time

    light_files = useful.where(useful['imagetyp'] == 'LIGHT')
    if light_files:
        dark_subtractor = ccd.ImageBiasSubtractor()
        for light_file in light_files['file']:
            light = ccd.FitsImage(path.join(currentDir,light_file))
            header = light.fitsfile[0].header
            exposure = header['exposure']
            try:
                dark = master_dark[exposure]
            except KeyError:
                print "Holy crap, Batman, I have no dark with exposure time %f!" % exposure
                raise RuntimeError
            if abs(header['ccd-temp']-avg_temp[exposure])>temperature_tolerance:
                print "Aw damn it, the temperature of this exposure, %f, is too far" % header['ccd-temp']
                print "  from the master dark temperature, %f." % avg_temp[exposure]
                raise RuntimeError
            dark_subtractor.biasframe = dark
            calibrated_light = dark_subtractor.subtractFromImage(light)
            #calibrated_light = flatten me please!
            