"""
DESCRIPTION
-----------
    For each directory provided on the command line create a table
    in that directory with one row for each FITS file in the directory.
    The columns are FITS keywords extracted from the header of each
    file.

    The list of default keywords extracted is available through the command
    line option ``--list-default``.

    .. Note::
        This feature is available only from the command line.

    For more control over the parameters see :func:`triage_fits_files`

    .. Note::
        This script is **NOT RECURSIVE**; it will not process files in
        subdirectories of the the directories supplied on the command line.


EXAMPLES
--------

    Invoking this script from the command line::

        python run_triage.py /my/folder/of/images

    Get list of default keywords included in summary table::

        python run_triage.py --list-default

    To work on the same folder from within python, do this::

        from msumastro.scripts import run_triage
        run_triage.main(['/my/folder/of/images'])
        # or...
        run_triage.main(['--list-default'])

"""

from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import os
from argparse import ArgumentParser
from sys import exit
import logging

from astropy.table import Table, Column
import numpy as np

from ..customlogger import console_handler, add_file_handlers
from ..header_processing.feder import Feder
from .. import ImageFileCollection
from . import script_helpers

logger = logging.getLogger()
screen_handler = console_handler()
logger.addHandler(screen_handler)


class DefaultFileNames(object):
    def __init__(self):
        self.object_file_name = 'NEEDS_OBJECT_NAME.txt'
        self.pointing_file_name = 'NEEDS_POINTING_INFO.txt'
        self.filter_file_name = 'NEEDS_FILTER.txt'
        self.output_table = 'Manifest.txt'
        self.astrometry_file_name = 'NEEDS_ASTROMETRY.txt'

    def as_dict(self):
        return self.__dict__


def write_list(dir, file, info, column_name=None):
    col_name = column_name or 'File'
    temp_table = Table(data=[info],
                       names=[col_name])
    temp_table.write(os.path.join(dir, file),
                     format='ascii')


def contains_maximdl_imagetype(image_collection):
    """
    Check an image file collection for MaxImDL-style image types
    """
    import re
    file_info = image_collection.summary_info

    if file_info['imagetyp'].mask.any():
        logger.warn('One or more image is missing IMAGETYP in header')

    image_types = ' '.join([typ for typ in file_info['imagetyp'].compressed()])

    if re.search('[fF]rame', image_types) is not None:
        return True
    else:
        return False


def get_column_name_case_insensitive(name, column_names):
    """
    Return the column name that matches name in a case-insensitive comparison.

    Parameters
    ----------

    name : str
        Name for which match is desired.

    column_names : list
        List of column names.

    Returns
    -------

    str or None
        name of first matching column or ``None``, if no match is found.
    """
    for cname in column_names:
        if name.lower() == cname.lower():
            return cname
    else:
        return ''


def triage_fits_files(dir=None, file_info_to_keep=None):
    """
    Check FITS files in a directory for deficient headers

    `dir` is the name of the directory to search for files.

    `file_info_to_keep` is a list of the FITS keywords to get values
    for for each FITS file in `dir`.
    """
    dir = dir or '.'
    all_file_info = file_info_to_keep or ['imagetyp', 'object',
                                          'filter', 'wcsaxes']
    feder = Feder()
    RA = feder.RA
    if ((not (set(RA.names) <= set(all_file_info))) and
       (all_file_info != '*')):
        all_file_info.extend(RA.names)

    images = ImageFileCollection(dir, keywords=all_file_info)
    file_info = images.summary_info

    # check for bad image type and halt until that is fixed.
    if contains_maximdl_imagetype(images):
        raise ValueError(
            'Correct MaxImDL-style image types before proceeding.')

    file_needs_filter = \
        list(images.files_filtered(imagetyp='light',
                                   filter=None))
    file_needs_filter += \
        list(images.files_filtered(imagetyp='flat',
                                   filter=None))

    file_needs_object_name = \
        list(images.files_filtered(imagetyp='light',
                                   object=None))

    lights = file_info[file_info['imagetyp'] == 'LIGHT']
    file_needs_pointing = []
    file_needs_astrometry = []
    if lights:
        has_no_ra = np.array([True] * len(lights))
        has_no_ha = np.array([True] * len(lights))
        for ra_name in RA.names:
            col_name = \
                get_column_name_case_insensitive(ra_name, lights.colnames)
            try:
                has_no_ra &= (lights[col_name].mask)
            except KeyError:
                pass
        for ha_name in feder.HA.names:
            col_name = \
                get_column_name_case_insensitive(ha_name, lights.colnames)
            try:
                has_no_ha &= lights[col_name].mask
            except KeyError:
                pass

        file_needs_astrometry = list(lights['file'][lights['wcsaxes'].mask])
        needs_minimal_pointing = has_no_ha | has_no_ra
        file_needs_pointing = list(lights['file'][needs_minimal_pointing])

    full_path = os.path.abspath(dir)
    path_column = Column(data=[full_path] * len(file_info), name='Source path')
    containing_dir = os.path.basename(full_path)
    containing_dir_col = Column(data=[containing_dir] * len(file_info),
                                name='Source directory')
    file_info.add_columns([path_column, containing_dir_col])

    dir_info = {'files': file_info,
                'needs_filter': file_needs_filter,
                'needs_pointing': file_needs_pointing,
                'needs_object_name': file_needs_object_name,
                'needs_astrometry': file_needs_astrometry}

    return dir_info


def triage_directories(directories,
                       keywords=None,
                       all_keywords=False,
                       object_file_name=None,
                       pointing_file_name=None,
                       filter_file_name=None,
                       astrometry_file_name=None,
                       output_table=None,
                       destination=None,
                       no_log_destination=False):

    for currentDir in directories:
        if destination is not None:
            target_dir = destination
        else:
            target_dir = currentDir
        if (not no_log_destination) and (destination is not None):
            add_file_handlers(logger, destination, 'run_triage')
        logger.info('Examining directory %s', currentDir)
        if keywords:
            # force a copy...
            use_keys = list(keywords)
        else:
            use_keys = []

        if all_keywords:
            try:
                use_keys += ['*']
            except TypeError:
                use_keys = '*'

        result = triage_fits_files(currentDir, file_info_to_keep=use_keys)
        outfiles = [pointing_file_name, filter_file_name,
                    object_file_name, output_table, astrometry_file_name]
        for fil in [outfile for outfile in outfiles if outfile is not None]:
            try:
                os.remove(os.path.join(currentDir, fil))
            except OSError:
                pass

        need_pointing = result['needs_pointing']
        need_filter = result['needs_filter']
        need_object_name = result['needs_object_name']
        need_astrometry = result['needs_astrometry']

        if need_pointing and pointing_file_name is not None:
            write_list(target_dir, pointing_file_name, need_pointing)
        if need_filter and filter_file_name is not None:
            write_list(target_dir, filter_file_name, need_filter)
        if need_object_name and object_file_name is not None:
            write_list(target_dir, object_file_name,
                       need_object_name)
        if need_astrometry and astrometry_file_name is not None:
            write_list(target_dir, astrometry_file_name, need_astrometry)

        tbl = result['files']
        if ((len(tbl) > 0) and (output_table is not None)):
            tbl.write(os.path.join(target_dir, output_table),
                      format='ascii', delimiter=',')


def construct_parser():

    parser = ArgumentParser()
    script_helpers.setup_parser_help(parser, __doc__)
    # allow for no directories below so that -l option
    # can be used without needing to specify a directory
    script_helpers.add_directories(parser, '*')
    script_helpers.add_debug(parser)
    script_helpers.add_verbose(parser)
    script_helpers.add_destination_directory(parser)
    script_helpers.add_no_log_destination(parser)
    script_helpers.add_console_output_args(parser)

    key_help = 'FITS keyword to add to table in addition to the defaults; '
    key_help += 'for multiple keywords use this option multiple times.'
    parser.add_argument('-k', '--key', action='append',
                        help=key_help, default=[])

#    no_default_help = ('Do not include default list of keywords in table'
#                       '**EXCEPT** for `file` and `imagetyp`, which are'
#                       'always included')
#    parser.add_argument('--no-default', action='store_true',
#                        help=no_default_help)

    list_help = 'Print default list keywords put into table and exit'
    parser.add_argument('-l', '--list-default', action='store_true',
                        help=list_help)

    all_keys_help = ('Construct table from all FITS keywords present in '
                     'headers and the list of default keywords.')
    parser.add_argument('-a', '--all', action='store_true',
                        help=all_keys_help)

    default_names = DefaultFileNames()
    output_file_help = 'Name of file in which table is saved; default is '
    output_file_help += default_names.output_table
    parser.add_argument('-t', '--table-name',
                        default=default_names.output_table,
                        help=output_file_help)

    needs_object_help = 'Name of file to which list of files that need '
    needs_object_help += 'object name is saved; default is '
    needs_object_help += default_names.object_file_name
    parser.add_argument('-o', '--object-needed-list',
                        default=default_names.object_file_name,
                        help=needs_object_help)

    needs_pointing_help = 'Name of file to which list of files that need '
    needs_pointing_help += 'pointing name is saved; default is '
    needs_pointing_help += default_names.pointing_file_name
    parser.add_argument('-p', '--pointing-needed-list',
                        default=default_names.pointing_file_name,
                        help=needs_pointing_help)

    needs_filter_help = 'Name of file to which list of files that need '
    needs_filter_help += 'filter is saved; default is '
    needs_filter_help += default_names.filter_file_name
    parser.add_argument('-f', '--filter-needed-list',
                        default=default_names.filter_file_name,
                        help=needs_filter_help)

    needs_astrometry_help = 'Name of file to which list of files that need '
    needs_astrometry_help += 'astrometry is saved; default is '
    needs_astrometry_help += default_names.astrometry_file_name
    parser.add_argument('-y', '--astrometry-needed-list',
                        default=default_names.astrometry_file_name,
                        help=needs_astrometry_help)

    return parser

DEFAULT_KEYS = ['imagetyp', 'filter', 'exptime', 'ccd-temp',
                'object', 'observer', 'airmass', 'instrume',
                'RA', 'Dec', 'date-obs', 'jd', 'wcsaxes']


def main(arglist=None):
    """See script_helpers._main_function_docstring for actual documentation
    """
    parser = construct_parser()
    args = parser.parse_args(arglist)
    logger.debug('args are %s', vars(args))

    script_helpers.setup_logging(logger, args, screen_handler)

    add_file_handlers(logger, os.getcwd(), 'run_triage')

    use_keys = list(DEFAULT_KEYS)  # force a copy so DEFAULT_KEYS not modified

    if args.list_default:
        print('Keys included by default are:\n')
        keys_print = [key.upper() for key in use_keys]
        print(', '.join(keys_print))
        return use_keys

    use_keys.extend(args.key)

    if not args.dir:
        parser.error('No directory specified')

    logger.debug('use_keys are %s', use_keys)
    do_not_log_in_destination = \
        script_helpers.handle_destination_dir_logging_check(args)
    triage_directories(args.dir, keywords=use_keys,
                       all_keywords=args.all,
                       object_file_name=args.object_needed_list,
                       pointing_file_name=args.pointing_needed_list,
                       filter_file_name=args.filter_needed_list,
                       astrometry_file_name=args.astrometry_needed_list,
                       output_table=args.table_name,
                       destination=args.destination_dir,
                       no_log_destination=do_not_log_in_destination)

main.__doc__ = script_helpers._main_function_docstring(__name__)
