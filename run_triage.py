"""
DESCRIPTION
-----------
    For each directory provided on the command line create a table
    in that directory with one row for each FITS file in the directory.
    The columns are FITS keywords extracted from the header of each
    file.

    By default, astrometry is added only for those files with pointing
    information in the header (specifically, RA and Dec) because blind
    astrometry is fairly slow. It may be faster to insert RA/Dec into
    those files before doing astrometry.

    The functions called by this script set the WCS reference pixel
    to the center of the image, which turns out to make aligning images
    a little easier.

    For more control over the parameters see :func:`add_astrometry`
    and for even more control, :func:`call_astrometry`.

    .. Note::
        This script is **NOT RECURSIVE**; it will not process files in
        subdirectories of the the directories supplied on the command line.

    .. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

EXAMPLES
--------

    Invoking this script from the command line::

        python run_astrometry.py /my/folder/of/images

    To work on the same folder from within python, do this::

        from run_astrometry import astrometry_for_directory
        astrometry_for_directory('/my/folder/of/images')


"""
import image_collection as tff
import os

object_name_file_name = 'NEEDS_OBJECT_NAME.txt'
pointing_file_name = 'NEEDS_POINTING_INFO.txt'
filter_file_name = 'NEEDS_FILTER.txt'
file_list = 'Manifest.txt'


def write_list(dir, file, info):
    out = open(os.path.join(dir, file), 'wb')
    out.write('\n'.join(info))
    out.close()


def triage_directories(directories,
                       extra_keywords=None):
    if extra_keywords is not None:
        more_keys = extra_keywords

    for currentDir in directories:
        all_keywords = ['imagetyp', 'filter', 'exptime', 'ccd-temp']
        all_keywords.extend(more_keys)
        moo = tff.triage_fits_files(currentDir,
                                    file_info_to_keep=all_keywords)
        for fil in [pointing_file_name, filter_file_name,
                    object_name_file_name, file_list]:
            try:
                os.remove(os.path.join(currentDir, fil))
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
            tbl.write(os.path.join(currentDir, file_list),
                      format='ascii', delimiter=',')

from script_helpers import construct_default_parser


def construct_parser():
    parser = construct_default_parser(__doc__)

    key_help = 'FITS keyword to add to table; for multiple keywords use '
    key_help += 'this option multiple times.'
    parser.add_argument('-k', '--key', action='append',
                        help=key_help)

    return parser

if __name__ == "__main__":
    parser = construct_parser()
    args = parser.parse_args()
    always_include_keys = ['object', 'observer', 'airmass', 'instrument']

    try:
        always_include_keys.extend(args.key)
    except TypeError as e:
        pass

    triage_directories(args.dir, extra_keywords=always_include_keys)
