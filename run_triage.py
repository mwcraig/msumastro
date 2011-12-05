import triage_fits_files as tff
import asciitable
import sys
import os

object_file_name = 'NEEDS_OBJECT.txt'
filter_file_name = 'NEEDS_FILTER.txt'
file_list = 'Manifest.txt'
def write_list(dir, file, info):
    out = open(os.path.join(dir,file), 'wb')
    out.write('\n'.join(info))
    out.close()

for currentDir in sys.argv[1:]:
    moo = tff.triage_fits_files(currentDir)
    need_objects = moo['needs_object']
    if need_objects:
        write_list(currentDir, object_file_name,need_objects)
    if moo['needs_filter']:
        write_list(currentDir, filter_file_name,moo['needs_filter'])
    asciitable.write(moo['files'], os.path.join(currentDir, file_list))
                     
