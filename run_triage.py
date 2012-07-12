import image_collection as tff
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

def triage_directories(directories,
                       extra_keywords=[]):
    for currentDir in directories:
#    pdb.set_trace()
        moo = tff.triage_fits_files(currentDir,
                                    file_info_to_keep=['imagetyp',
                                                       'filter',
                                                       'exptime',
                                                       'ccd-temp']+extra_keywords)
        for fil in [pointing_file_name, filter_file_name,
                       object_name_file_name, file_list]:
            try:
                os.remove(os.path.join(currentDir,fil))
            except OSError:
                pass
            
        need_pointing = moo['needs_pointing']
        if need_pointing:
            write_list(currentDir, pointing_file_name, need_pointing)
        if moo['needs_filter']:
            write_list(currentDir, filter_file_name, moo['needs_filter'])
        if moo['needs_object_name']:
            write_list(currentDir, object_name_file_name,
                       moo['needs_object_name'])
        tbl = moo['files']
        if len(tbl) > 0:
            tbl.write(os.path.join(currentDir, file_list), type='ascii', delimiter=',')
                 
if __name__ == "__main__":
    dirs = sys.argv[1:]
    triage_directories(dirs, extra_keywords=['object'])
