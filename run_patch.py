from patch_headers import patch_headers
import sys

for currentDir in sys.argv[1:]:
    patch_headers(currentDir, overwrite=True)