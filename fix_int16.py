from os import listdir, path
import numpy as np

from patch_headers import fix_int16_images, compare_data_in_fits
from image_collection import ImageFileCollection

fix_vol = '/Volumes/FULL BACKUP/processed'
#fix_vol = 'foo'
raw_vol = '/Volumes/feder_data_originals/ast390/raw'

dirs_to_fix = listdir(fix_vol)

begin_dir = '----------------- processing directory %s -----------------------'
bad_end = '================>>>>>> One or more failures in directory %s'
good_end = '++++++++++++++++++ success in directory %s +++++++++++++++++++++++'

for current_dir in dirs_to_fix:
    current_proc = path.join(fix_vol, current_dir)
    current_raw = path.join(raw_vol, current_dir)
    print begin_dir % current_proc
    try:
        test = open(path.join(current_proc, 'FIXED_YAY'), 'rb')
        print '    >>>>>>>>>>>>>>>>>>skipping this directory, already done.'
        continue
    except IOError:
        pass

    fix_int16_images(current_proc)
    files_to_check = ImageFileCollection(current_proc, keywords=['imagetyp'])
    files_to_check = files_to_check.summary_info['file']
    files_match = np.zeros(len(files_to_check), dtype=np.bool)
    for nfil, fil in enumerate(files_to_check):
        fixed_name = path.join(current_proc, fil)
        raw_name = path.join(current_raw, fil)
        files_match[nfil] = compare_data_in_fits(fixed_name, raw_name)
        if not files_match[nfil]:
            print '****************-------> FAIL on file %s' % fixed_name

    if not files_match.all():
        print bad_end % current_proc
        crap = open(path.join(current_proc, 'FAILED'), 'wb')
    else:
        print good_end % current_proc
        crap = open(path.join(current_proc, 'FIXED_YAY'), 'wb')

    crap.close()
