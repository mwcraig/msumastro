from patch_headers import patch_headers, add_object_info
import sys

for currentDir in sys.argv[1:]:
    print "working on directory: %s" % currentDir
    patch_headers(currentDir, new_file_ext='', overwrite=True)
    add_object_info(currentDir, new_file_ext='', overwrite=True)
    #add_overscan(currentDir, new_file_ext='', overwrite=True)
