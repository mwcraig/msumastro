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

    run_patch.py /my/folder/of/images

To work on the same folder from within python, do this::

    from msumastro.scripts import run_patch
    run_patch.main(['/my/folder/of/images'])

To use the same object list for several different directories do this::

    run_patch.py --object-list path/to/list.txt dir1 dir2 dir3

where ``path/to/list.txt`` is the path to your object list and ``dir1``,
``dir2``, etc. are the directories you want to process.

From within python this would be::

    from msumastro.scripts import run_patch
    run_patch.main(['--object-list', 'path/to/list.txt',
                   'dir1', 'dir2', 'dir3'])
"""
from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from os import getcwd
from os import path
import warnings
import logging

from ..header_processing import patch_headers, add_object_info, list_name_is_url
from ..customlogger import console_handler, add_file_handlers
from .script_helpers import (setup_logging, construct_default_parser,
                             handle_destination_dir_logging_check,
                             _main_function_docstring)

logger = logging.getLogger()
screen_handler = console_handler()
logger.addHandler(screen_handler)

DEFAULT_OBJ_LIST = 'obsinfo.txt'
DEFAULT_OBJECT_URL = ('https://raw.github.com/mwcraig/feder-object-list'
                      '/master/feder_object_list.csv')


def patch_directories(directories, verbose=False, object_list=None,
                      destination=None,
                      no_log_destination=False,
                      overscan_only=False,
                      script_name='run_patch'):
    """
    Patch all of the files in each of a list of directories.

    Parameters
    ----------

    directories : str or list of str
        Directory or directories whose FITS files are to be processed.

    verbose : bool, optional
        Control amount of logging output.

    object_list : str, optional
        Path to or URL of a file containing a list of objects that
        might be in the files in `directory`. If not provided it defaults
        to looking for a file called `obsinfo.txt` in the directory being
        processed.

    destination : str, optional
        Path to directory in which patched images will be stored. Default
        value is None, which means that **files will be overwritten** in
        the directory being processed.
    """
    no_explicit_object_list = (object_list is None)
    if not no_explicit_object_list:
        if list_name_is_url(object_list):
            obj_dir = None
            obj_name = object_list
        else:
            full_path = path.abspath(object_list)
            obj_dir, obj_name = path.split(full_path)

    for currentDir in directories:
        if destination is not None:
            working_dir = destination
        else:
            working_dir = currentDir

        if (not no_log_destination) and (destination is not None):
            add_file_handlers(logger, working_dir, 'run_patch')

        logger.info("Working on directory: %s", currentDir)

        with warnings.catch_warnings():
            # suppress warning from overwriting FITS files
            ignore_from = 'astropy.io.fits.hdu.hdulist'
            warnings.filterwarnings('ignore', module=ignore_from)
            if overscan_only:
                patch_headers(currentDir, new_file_ext='', overwrite=True,
                              save_location=destination,
                              purge_bad=False,
                              add_time=False,
                              add_apparent_pos=False,
                              add_overscan=True,
                              fix_imagetype=False,
                              add_unit=False)

            else:
                patch_headers(currentDir, new_file_ext='', overwrite=True,
                              save_location=destination)

                default_object_list_present = path.exists(path.join(currentDir,
                                                          DEFAULT_OBJ_LIST))
                if (default_object_list_present and no_explicit_object_list):
                    obj_dir = currentDir
                    obj_name = DEFAULT_OBJ_LIST
                add_object_info(working_dir, new_file_ext='', overwrite=True,
                                save_location=destination,
                                object_list_dir=obj_dir, object_list=obj_name)


def construct_parser():
    parser = construct_default_parser(__doc__)

    object_list_help = ('Path to or URL of file containing list (and '
                        'optionally coordinates of) objects that might be in '
                        'these files. If not provided it defaults to looking '
                        'for a file called obsinfo.txt in the directory '
                        'being processed')
    parser.add_argument('-o', '--object-list',
                        help=object_list_help,
                        default=DEFAULT_OBJECT_URL)
    parser.add_argument('--overscan-only', action='store_true',
                        help='Only add appropriate overscan keywords')
    return parser


def main(arglist=None):
    """See script_helpers._main_function_docstring for actual documentation
    """
    parser = construct_parser()
    args = parser.parse_args(arglist)

    setup_logging(logger, args, screen_handler)

    add_file_handlers(logger, getcwd(), 'run_patch')

    do_not_log_in_destination = handle_destination_dir_logging_check(args)

    patch_directories(args.dir, verbose=args.verbose,
                      object_list=args.object_list,
                      destination=args.destination_dir,
                      no_log_destination=do_not_log_in_destination,
                      overscan_only=args.overscan_only)

main.__doc__ = _main_function_docstring(__name__)
