import triage_fits_files as tff
import ccd_characterization as ccd_char
from astropysics import ccd
from os import path
import pyfits

combiner = ccd.ImageCombiner()

def master_frame(data, img_type, T, Terr, sample=None,combiner=None):
    copy_from_sample = ['xbinning', 'ybinning',
                        'xpixsz', 'ypixsz', 'exptime','filter']
    img = ccd.FitsImage(data)
    hdr = img.fitsfile[0].header
    hdr.update('imagetyp',img_type)
    now = datetime.utcnow()
    now = now.replace(microsecond=0)
    hdr.update('date', now.isoformat(),
               'Creation date of file')
    hdr.update('ccd-temp', T, 'Average temperature of CCD')
    hdr.update('temp-dev', Terr,
               'Standard deviation of CCD temperature')
    if combiner is not None:
        hdr.update('cmbn-mth',combiner.method,
                   'Combination method for producing master')
        
    if sample is not None:
        if not isinstance(sample, Header):
            raise TypeError
        cards = sample.ascard
        for key in copy_from_sample:
            hdr.update(key,cards[key].value,cards[key].comment)
    return img
    
for currentDir in foo:
    keywords = ['imagetyp', 'exptime', 'filter', 'ccd-temp']
    image_collection = tff.ImageFileCollection(location=currentDir,
                                               keywords=keywords,
                                               info_file=None)
    images = image_collection.summary_info
    master_dark_files = images.where(images['imagetyp'] == 'MASTER DARK')
    all_flats = images.where(images['imagetyp'] == 'FLAT')
    exposure_times = set(all_flats['exptime'])
    print exposure_times
    for time in exposure_times:
        these_flats = all_flats.where(all_flats['exptime'] == time)
        flat_filter = these_flats['filter'][0]
        master_dark = master_dark_files.where(master_dark_files['exptime']==time)
        if not master_dark:
            print 'Sorry, no dark for the exposure %f, skipping....' %time
            continue
        master_dark = ccd.FitsImage(path.join(currentDir,master_dark['file'][0]))
        flats = []
        for flat_file in these_flats['file']:
            flat = ccd.FitsImage(path.join(currentDir,flat_file))
            flats.append(flat.data - master_dark.data)
        master_flat = combiner.combineImages(flats)
        avg_temp = these_flats['ccd-temp'].mean()
        temp_dev = these_flats['ccd-temp'].std()
        sample = pyfits.open(path.join(currentDir,these_flats['file'][0]))
        flat_im = master_frame(master_flat, 'MASTER FLAT', avg_temp,
                               temp_dev, sample=sample[0].header,
                               combiner=combiner)
        flat_fn = 'Master_Flat_%s_band.fit' % flat_filter
        flat_im.save(path.join(currentDir,flat_fn))
