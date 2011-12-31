import triage_fits_files as tff
import asciitable
import sys
import os

#import pdb 

object_name_file_name = 'NEEDS_OBJECT_NAME.txt'
pointing_file_name = 'NEEDS_POINTING_INFO.txt'
filter_file_name = 'NEEDS_FILTER.txt'
file_list = 'Manifest.txt'
def write_list(dir, file, info):
    out = open(os.path.join(dir,file), 'wb')
    out.write('\n'.join(info))
    out.close()

for currentDir in sys.argv[1:]:
#    pdb.set_trace()
    moo = tff.triage_fits_files(currentDir,
                                file_info_to_keep=['imagetyp', 'filter'])
    need_pointing = moo['needs_pointing']
    if need_pointing:
        write_list(currentDir, pointing_file_name, need_pointing)
    if moo['needs_filter']:
        write_list(currentDir, filter_file_name, moo['needs_filter'])
    if moo['needs_object_name']:
        write_list(currentDir, object_name_file_name,
                   moo['needs_object_name'])
    asciitable.write(moo['files'],
                     os.path.join(currentDir, file_list),
                     delimiter=',')
                 
                     
