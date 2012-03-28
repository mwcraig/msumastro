from patch_headers import patch_headers, add_object_info
import sys

for currentDir in sys.argv[1:]:
    print "working on directory: %s" % currentDir
    patch_headers(currentDir, overwrite=True)
    add_object_info(currentDir)
    