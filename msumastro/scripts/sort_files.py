"""
DESCRIPTION
-----------
    For the directory provided on the command line sort the FITS files in this
    way::

        destination
            |
            |
            |
            |---'BIAS'
            |
            |---'DARK'
            |     |---exposure_time_1
            |     |---exposure_time_2, etc.
            |
            |---'FLAT'
            |      |---filter_1
            |      |    |---exposure_time_1
            |      |    |---exposure_time_2, etc.
            |      |
            |      |---filter_2, etc.
            |
            |---'LIGHT'
                    |---object_1
                    |       |---filter_1
                    |       |    |---exposure_time_1
                    |       |    |---exposure_time_2, etc.
                    |       |
                    |       |---filter_2, etc.
                    |
                    |---object_2
                    |       |---filter_1
                    |       |---filter_2, etc.
                    |
                    |---object_3, etc.
                    |
                    |---'no_object'
                            |---filter_1
                            |---filter_2, etc.

    The names in single quotes, like `'bias'`, appear exactly as written in the
    directory tree created. Names like `exposure_time_1` are replaced with a
    value, for example 30.0 if the first dark exposure time is 30.0 seconds.

    The directory ``destination/calibration/flat/R`` will contain all of the
    FITS files that are R-band flats.

    .. Note::
        This script is **NOT RECURSIVE**; it will not process files in
        subdirectories of the the directories supplied on the command line.

    .. Warning::
        Unless you explicitly supply a destination using the --destination-dir
        option the files will be copied/moved in the directory in which they
        currently exist. While this *should not* lead to information loss,
        since files are moved or copied but never deleted, you have been
        warned.

EXAMPLES
--------


"""

from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import os
import logging
import shutil

from astropy.extern.six.moves import zip as izip

from ..customlogger import console_handler, add_file_handlers
from .. import ImageFileCollection
from .. import TableTree
from . import script_helpers

UNSORTED_DIR = 'unsorted'

logger = logging.getLogger()
screen_handler = console_handler()
logger.addHandler(screen_handler)


def copy_files(files, dest, copy_or_move):
    """
    Copy a list of files to a directory

    Parameters
    ----------
    files : list of str
        List of paths of files to be copied
    dest : str
        Name of dirctory to which files should be copied
    """
    for f in files:
        copy_or_move(f, dest)


def sort_directory(directory, verbose=False,
                   destination=None,
                   no_log_destination=False,
                   script_name=None,
                   move=False):
    """
    Sort files in a directory into a tree

    Parameters
    ----------
    directory : str
        Directory whose files are to be sorted
    verbose : bool
        If True, increase logging verbosity
    destination : str, optional
        Directory into which the sorted files/directories should be placed. If
        omitted, sorting is done in the source ``directory``.
    no_log_destination : bool, optional
        Suppress logging in the destination directory. Logging cannot be
        suppressed if you are running in the destination directory.
    script_name : str, optional, default is 'sort_files'
        Name of the script calling this function; used to set the name of the
        log file in the destination.
    """
    script_name = script_name or 'sort_files'
    if destination is not None:
        working_dir = destination
        if not os.path.exists(destination):
            os.makedirs(destination)
    else:
        working_dir = directory

    if (not no_log_destination) and (destination is not None):
        add_file_handlers(logger, working_dir, script_name)

    if move:
        copy_or_move = shutil.move
    else:
        copy_or_move = shutil.copy2

    logger.info("Working on directory: %s", directory)
    logger.info("Destination directory is: %s", destination)

    default_keys = ['imagetyp', 'exptime', 'filter', 'object']
    images = ImageFileCollection(directory, keywords=default_keys)
    if not images.files:
        return
    full_table = images.summary_info
    bias = 'BIAS'
    dark = 'DARK'
    flat = 'FLAT'
    light = 'LIGHT'
    image_types = {bias: None,
                   dark: ['exptime'],
                   flat: ['filter', 'exptime'],
                   light: ['object', 'filter', 'exptime']}
    table_by_type = full_table.group_by('imagetyp')
    prepend_path = lambda path, file_list: \
                        [os.path.join(path, f) for f in file_list]
    for im_type, table in izip(table_by_type.groups.keys,
                               table_by_type.groups):
        image_type = im_type['imagetyp']
        tree_keys = image_types[image_type]
        dest_dir = os.path.join(working_dir, image_type)
        if not tree_keys:
            # bias
            source_files = prepend_path(directory, table['file'])
            this_dest = os.makedirs(dest_dir)
            copy_files(source_files, dest_dir, copy_or_move)
            continue
        mask = [False] * len(table)
        for key in tree_keys:
            mask |= table[key].mask
        if any(mask):
            source_files = prepend_path(directory, table['file'][mask])
            this_dest = os.path.join(dest_dir, UNSORTED_DIR)
            os.makedirs(this_dest)
            copy_files(source_files, this_dest, copy_or_move)
        clean_table = table[~mask]
        try:
            tree = TableTree(clean_table, tree_keys, 'file')
        except IndexError:
            continue
        for parents, children, files in tree.walk():
            if files:
                str_parents = [str(p) for p in parents]
                this_dest = os.path.join(dest_dir, *str_parents)
                os.makedirs(this_dest)
                source_files = prepend_path(directory, files)
                copy_files(source_files, this_dest, copy_or_move)


def construct_parser():
    parser = script_helpers.construct_default_parser(__doc__)
    parser.add_argument('--move', '-m', action='store_true',
                        help='Move files instead of copying them.')
    return parser


def main(arglist=None):
    """See script_helpers._main_function_docstring for actual documentation
    """
    parser = construct_parser()
    args = parser.parse_args(arglist)
    logger.debug('args are %s', vars(args))

    script_helpers.setup_logging(logger, args, screen_handler)

    add_file_handlers(logger, os.getcwd(), 'sort_files')

    # coverage misses the line below, which is actually tested..
    if not args.dir:    # pragma: no cover
        parser.error('No directory specified')

    do_not_log_in_destination = \
        script_helpers.handle_destination_dir_logging_check(args)

    sort_directory(args.dir[0],
                   verbose=args.verbose,
                   destination=args.destination_dir,
                   no_log_destination=do_not_log_in_destination,
                   move=args.move)

main.__doc__ = script_helpers._main_function_docstring(__name__)
