"""
SYNOPSIS

    python run_patch.py dir1 [dir2 dir3 ...]

DESCRIPTION

    For each directory dir1, dir2, ... provided on the command line the
    headers all of the FITS files in that directory are modified
    to add information like LST, apparent object position, and more.
    See the full documentation for a list of the specific keywords
    that are modified.

    This is basically a wrapper around the function `patch_headers` with
    the options set so that:

        + "Bad" keywords written by MaxImDL 5 are purged.
        + Additional useful times like LST, JD are added to the header.
        + Apparent position (Alt/Az, hour angle) are added to the header.
        + Information about overscan is added to the header.
        + Files are overwritten.

    For more control over what is patched and where the patched files are saved
    see the documentation for ``patch_headers`` at
    :func:`patch_headers.patch_headers`.

    .. Note::
        This script is **NOT RECURSIVE**; it will not process files in
        subdirectories of the the directories supplied on the command line.

    .. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

EXAMPLES

    Invoking this script from the command line::

        python run_patch.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from run_patch import patch_directories
        patch_directories('/my/folder/of/images')
"""

from patch_headers import patch_headers, add_object_info


def patch_directories(directories):
    for currentDir in directories:
        print "working on directory: %s" % currentDir
        patch_headers(currentDir, new_file_ext='', overwrite=True)
        add_object_info(currentDir, new_file_ext='', overwrite=True)

if __name__ == "__main__":
    import argparse
    raw_help_format = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(epilog=__doc__,
                                     formatter_class=raw_help_format)
    parser.add_argument("directories", metavar='dir', nargs='+')
    parser.parse_args()

    args = parser.parse_args()
    patch_directories(args.directories)
