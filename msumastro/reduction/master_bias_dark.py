import image_collection as tff
from astropysics import ccd
from os import path
from numpy import median, mean
from datetime import datetime
# from fits import Header
import astropy.io.fits as fits
import logging

logger = logging.getLogger(__name__)


temperature_tolerance = 2  # degree C
combiner = ccd.ImageCombiner()


def combine_from_list(dir, fnames, combiner):
    data = []
    for fn in fnames:
        a_data = ccd.FitsImage(path.join(dir, fn))
        data.append(a_data)
    return combiner.combineImages(data)


def master_frame(data, T, Terr, sample=None, combiner=None, img_type=''):
    copy_from_sample = ['imagetyp', 'xbinning', 'ybinning',
                        'xpixsz', 'ypixsz', 'exptime']
    img = ccd.FitsImage(data)
    hdr = img.fitsfile[0].header

    try:
        calstat = hdr['calstat']
        calstat += 'M'
    except KeyError:
        calstat = 'M'
    hdr['calstat'] = (calstat,
                      'Calibrations applied, MaximDL style')
    hdr['master'] = ('Y', 'Is this a master frame?')

    now = datetime.utcnow()
    now = now.replace(microsecond=0)
    hdr['date'] = (now.isoformat(),
                   'Creation date of file')
    hdr['ccd-temp'] = (T, 'Average temperature of CCD')
    hdr['temp-dev'] = (Terr,
                       'Standard deviation of CCD temperature')
    if combiner is not None:
        hdr['cmbn-mth'] = (combiner.method,
                           'Combination method for producing master')

    if sample is not None:
        if not isinstance(sample, fits.Header):
            raise TypeError
        for key in copy_from_sample:
            hdr[key] = (sample[key], sample.comments[key])
    else:
        if img_type:
            hdr['imagetyp'] = img_type

    return img


def add_files_info(fits_image, files):
    hdr = fits_image.fitsfile[0].header
    hdr['n-files'] = (len(files),
                      'Number of files combined to make master')
    hdr.add_comment('This master produced by combining the files below:')
    for fil in files:
        hdr.add_comment('    ' + fil)


def master_bias_dark(directories):
    for currentDir in directories:
        print 'Directory %s' % currentDir
        keywords = ['imagetyp', 'exptime', 'ccd-temp', 'calstat', 'master']
        images = tff.ImageFileCollection(location=currentDir,
                                         keywords=keywords)
        useful = images.summary_info
        # print useful.data
        bias_files = useful[(((useful['imagetyp'] == 'BIAS') |
                              (useful['imagetyp'] == 'Bias Frame')) &
                            (useful['master'] != 'Y'))]
        if bias_files:
            combiner.method = 'median'
            master_bias = combine_from_list(currentDir,
                                            bias_files['file'], combiner)
            avg_temp = bias_files['ccd-temp'].mean()
            temp_dev = bias_files['ccd-temp'].std()
            sample = fits.open(path.join(currentDir, bias_files['file'][0]))
            bias_im = master_frame(master_bias, avg_temp,
                                   temp_dev, sample=sample[0].header,
                                   combiner=combiner)
            add_files_info(bias_im, bias_files['file'])
            bias_im.save(path.join(currentDir, 'Master_Bias.fit'))

        dark_files = useful[(((useful['imagetyp'] == 'DARK') |
                              (useful['imagetyp'] == 'Dark Frame'))
                             &
                             (useful['master'] != 'Y'))]
        if dark_files:
            exposure_times = set(dark_files['exptime'])
            master_dark = {}
            avg_temp = {}
            for time in exposure_times:
                these_darks = dark_files[(dark_files['exptime'] == time)]
                avg_temp[time] = these_darks['ccd-temp'].mean()
                temp_dev = these_darks['ccd-temp'].std()
                good_darks = (abs(these_darks['ccd-temp'] - avg_temp[time]) <
                              temperature_tolerance)
                if not good_darks.all():
                    dark_message = 'Darks with exposure time %f '
                    dark_message += 'have a temperature problem!'
                    raise RuntimeError(dark_message % time)
                combiner.method = 'median'
                master_dark = combine_from_list(currentDir,
                                                these_darks['file'], combiner)
                sample = fits.open(
                    path.join(currentDir, these_darks['file'][0]))
                dark_im = master_frame(master_dark, avg_temp[time],
                                       temp_dev, sample=sample[0].header,
                                       combiner=combiner)
                dark_fn_base = 'Master_Dark_{:.2f}_sec_{:.2f}_degC.fit'
                dark_fn = dark_fn_base.format(round(time, 2),
                                              round(avg_temp[time], 2))
                add_files_info(dark_im, these_darks['file'])
                dark_im.save(path.join(currentDir, dark_fn))

                print (time, avg_temp[time], median(master_dark[time]),
                       mean(master_dark[time]))
# print ccd_char.ccd_dark_current(master_bias,dark_data,gain=1.5)/time

if __name__ == "__main__":
    from sys import argv
    master_bias_dark(argv[1:])
