import image_collection as tff
from astropysics import ccd
from os import path
import astropy.io.fits as fits
import numpy as np
from master_bias_dark import master_frame, add_files_info
import logging

logger = logging.getLogger(__name__)

combiner = ccd.ImageCombiner()


def master_flat(directories):
    """
    Construct master flats by combining individual flats.

    :param directories: List of directories.

    Each directory must contain master darks whose exposure time
    matches the flats in the directory. A separate master flat will be
    constructed for each filter band for which there are flats in the
    directory.
    """
    for currentDir in directories:
        keywords = ['imagetyp', 'exptime', 'filter', 'ccd-temp',
                    'calstat', 'master']
        image_collection = tff.ImageFileCollection(location=currentDir,
                                                   keywords=keywords,
                                                   info_file=None)
        images = image_collection.summary_info
        master_dark_files = images[((images['imagetyp'] == 'DARK') &
                                    ('M' in images['calstat']))]
        all_flats = images[(((images['imagetyp'] == 'FLAT') |
                             (images['imagetyp'] == 'Flat Field')) &
                            (images['master'] != 'Y'))]
        exposure_times = set(all_flats['exptime'])
        print exposure_times
        for time in exposure_times:
            flats_time = all_flats[(all_flats['exptime'] == time)]
            filters = np.unique(flats_time['filter'])
            for flat_filter in filters:
                these_flats = flats_time[(flats_time['filter'] == flat_filter)]
                same_filter = (these_flats['filter'] == flat_filter)
                if not same_filter.all():
                    raise RuntimeError(
                        'Holy crap, my flats have mixed filters!')
                master_dark = master_dark_files[
                    (master_dark_files['exptime'] == time)]
                if not master_dark:
                    print 'Sorry, no dark for the exposure %f, skipping' % time
                    continue
                master_dark = ccd.FitsImage(
                    path.join(currentDir, master_dark['file'][0]))
                flats = []
                for flat_file in these_flats['file']:
                    flat = ccd.FitsImage(path.join(currentDir, flat_file))
                    flats.append(flat.data - master_dark.data)
                combiner.method = "median"
                master_flat = combiner.combineImages(flats)
                avg_temp = these_flats['ccd-temp'].mean()
                temp_dev = these_flats['ccd-temp'].std()
                sample = fits.open(
                    path.join(currentDir, these_flats['file'][0]))
                flat_im = master_frame(master_flat, avg_temp,
                                       temp_dev, sample=sample[0].header,
                                       combiner=combiner)
                flat_fn = 'Master_Flat_%s_band.fit' % flat_filter
                add_files_info(flat_im, these_flats['file'])
                flat_im.save(path.join(currentDir, flat_fn))

if __name__ == "__main__":
    from sys import argv
    master_flat(argv[1:])
