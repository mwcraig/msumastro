"""
DESCRIPTION
-----------

    For each directory provided on the command line the
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
--------

    Invoking this script from the command line::

        python run_patch.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from run_patch import patch_directories
        patch_directories('/my/folder/of/images')


"""

from patch_headers import patch_headers, add_object_info


def patch_directories(directories, verbose=False):
    for currentDir in directories:
        if verbose:
            print "working on directory: %s" % currentDir
        patch_headers(currentDir, new_file_ext='', overwrite=True)
        add_object_info(currentDir, new_file_ext='', overwrite=True)


def construct_parser():
    import script_helpers
    import argparse

    parser = argparse.ArgumentParser()
    script_helpers.setup_parser_help(parser, __doc__)
    script_helpers.add_verbose(parser)
    script_helpers.add_directories(parser)

    return parser

if __name__ == "__main__":
    parser = construct_parser()
    parser.parse_args()
    args = parser.parse_args()

    patch_directories(args.dir, verbose=args.verbose)
