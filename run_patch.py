"""
DESCRIPTION
-----------

For each directory provided on the command line the
headers all of the FITS files in that directory are modified
to add information like LST, apparent object position, and more.
See the full documentation for a list of the specific keywords
that are modified.

Header patching
^^^^^^^^^^^^^^^

This is basically a wrapper around the function
:func:`patch_headers.patch_headers` with the options set so that:

    + "Bad" keywords written by MaxImDL 5 are purged.
    + ``IMAGETYP`` keyword is changed from default MaxIM DL style
      to IRAF style (e.g. "Bias Frame" to "BIAS")
    + Additional useful times like LST, JD are added to the header.
    + Apparent position (Alt/Az, hour angle) are added to the header.
    + Information about overscan is added to the header.
    + Files are overwritten.

For more control over what is patched and where the patched files are saved
see the documentation for ``patch_headers`` at
:func:`patch_headers.patch_headers`.

Adding OBJECT keyword
^^^^^^^^^^^^^^^^^^^^^

``run_patch`` also adds the name of the object being observed when
appropriate (i.e. only for light files) and possible. It needs to be
given a list of objects; looking up the coordinates for those objects
requires an Internet connection. See

For a detailed description of the object list file see
:func:`Object file format <patch_headers.read_object_list>`.

for a detailed description of the function that actually adds the object name
see :func:`patch_headers.add_object_info`.

If no object list is specified or present in the directory being processed
the `OBJECT` keyword is simply not added to the FITS header.

.. Note::
    This script is **NOT RECURSIVE**; it will not process files in
    subdirectories of the the directories supplied on the command line.

.. WARNING::
    This script OVERWRITES the image files in the directories
    specified on the command line unless you use the --destination-dir
    option.

EXAMPLES
--------

Invoking this script from the command line::

    python run_patch.py /my/folder/of/images

To work on the same folder from within python, do this::

    from run_patch import patch_directories
    patch_directories('/my/folder/of/images')

To use the same object list for several different directories do this::

    python run_patch.py --object-list path/to/list.txt dir1 dir2 dir3

where ``path/to/list.txt`` is the path to your object list and ``dir1``,
``dir2``, etc. are the directories you want to process.

"""

# The import below
# MUST happen before any logging...oddly, setting the VALUE
# doesn't change anything. True story.

from astropy.logger import LOG_WARNINGS
import logging
from customlogger import console_handler, FormattedFileHandler

logger = logging.getLogger()
logger.addHandler(console_handler())

from patch_headers import patch_headers, add_object_info
default_obj_list = 'obsinfo.txt'


def patch_directories(directories, verbose=False, object_list=None,
                      destination=None):
    """
    Patch all of the files in each of a list of directories.

    Parameters
    ----------

    directories : str or list of str
        Directory or directories whose FITS files are to be processed.

    verbose : bool, optional
        Control amount of logging output.

    object_list : str, optional
        Path to the name of a file containing a list of objects that
        might be in the files in `directory`. If not provided it defaults
        to looking for a file called `obsinfo.txt` in the directory being
        processed.

    destination : str, optional
        Path to directory in which patched images will be stored. Default
        value is None, which means that **files will be overwritten** in
        the directory being processed.
    """
    from os import path
    import warnings

    if object_list is not None:
        full_path = path.abspath(object_list)

    for currentDir in directories:
        if verbose:
            print "working on directory: %s" % currentDir
        obj_dir = None
        obj_name = None
        if object_list is not None:
            obj_dir, obj_name = path.split(full_path)
        with warnings.catch_warnings():
            # suppress warning from overwriting FITS files
            ignore_from = 'astropy.io.fits.hdu.hdulist'
            warnings.filterwarnings('ignore', module=ignore_from)
            patch_headers(currentDir, new_file_ext='', overwrite=True,
                          save_location=destination)
            if destination is not None:
                working_dir = destination
            else:
                working_dir = currentDir

            default_object_list_present = path.exists(path.join(currentDir,
                                                      default_obj_list))
            no_explicit_object_list = (object_list is None)
            if (default_object_list_present and no_explicit_object_list):
                obj_dir = currentDir
                obj_name = default_obj_list
            add_object_info(working_dir, new_file_ext='', overwrite=True,
                            save_location=destination,
                            object_list_dir=obj_dir, object_list=obj_name)

from script_helpers import construct_default_parser


def construct_parser():
    parser = construct_default_parser(__doc__)

    object_list_help = 'Path to file containing list (and optionally '
    object_list_help += 'coordinates of) objects that might be in these files.'
    object_list_help += ' If not provided it defaults to looking for a file '
    object_list_help += 'called obsinfo.txt in the directory being processed'
    parser.add_argument('-o', '--object-list',
                        help=object_list_help,
                        default=None)
    return parser

if __name__ == "__main__":
    parser = construct_parser()
    args = parser.parse_args()

    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    patch_directories(args.dir, verbose=args.verbose,
                      object_list=args.object_list,
                      destination=args.destination_dir)
