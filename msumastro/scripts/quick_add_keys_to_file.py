"""
Add/modify keywords in FITS files.

DESCRIPTION
-----------

    Add each of the keywords in either the ``key_file`` or specified on the
    command line to each of the files either listed in the file ``file_list`` or
    specified on the command line. If the keyword is already present its value
    is updated to the value in ``key_file``. A HISTORY comment is added to the
    header for each keyword indicating which keyword was modified.

    .. WARNING::
        This script OVERWRITES the image files in the list specified on the
        command line. There is NO WAY to override this behavior.
"""
from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from argparse import ArgumentParser
import logging

import astropy.io.fits as fits
from astropy.table import Table
from astropy.extern import six

from . import script_helpers
from ..header_processing.fitskeyword import FITSKeyword

logger = logging.getLogger(__name__)


def add_keys(*files, **kwd):
    """
    Add keywords to a list of FITS files.

    At least one source of files must be provided and at least one source of
    keywords.

    Parameters
    ----------

    files : str, optional
        Zero or more file names, as positional arguments.

    file_list : str, optional
        Path to file which contains a list of files whose FITS keywords are to
        be modified.

    key_file : str
        Path to file which contains list of key-value pairs for FITS keywords.

    kwd : dict
        All remaining keyword arguments are interpreted as key-value pairs to
        be added as FITS keywords.

    Notes
    -----

    `file_list` should have one file per line with a header line
    at the top. A sample file list looks like this::

        File
        MyFirstFile.fits
        another_fits_file.fits
        /or/even/the/full/path/to/a/fits/file.fits

    `key_file` can be in any ASCII format easily readable by
    astropy.Table (e.g. CSV, or tab-delimited text). There needs
    to be a header line followed by, on each line, a FITS keyword
    and its value.

    All keywords in the `key_file` file are added to all of the files
    in `file_list` or the values are modified if they are already
    present in the FITS file.

    A sample `key_file` file is::

        Keyword   Value
        OBJCTDEC '+49 49 14'
        OBJCTRA '09 02 21'

    """
    file_list = kwd.pop('file_list', None)
    if file_list:
        files = Table.read(file_list, format='ascii')
        if files.colnames[0].lower() != 'file':
            raise ValueError('File list must have column named "file"')
        files.keep_columns([files.colnames[0]])
        files = [f[0] for f in files]
    key_file = kwd.pop('key_file', None)
    if key_file:
        key_table = Table.read(key_file, format='ascii')
    else:
        key_table = [(key, value) for key, value in six.iteritems(kwd)]
    for fil in files:
        logger.info('Adding keys to file %s', fil)
        fil_fits = fits.open(fil, mode='update')
        hdr = fil_fits[0].header
        for key, val in key_table:
            keyword = FITSKeyword(name=key, value=val)
            keyword.add_to_header(hdr, history=True)
            hdr[key] = val
        fil_fits.close()

#__doc__ += add_keys.__doc__


def construct_parser():
    """Add arguments to parser for this script
    """
    parser = ArgumentParser()
    script_helpers.setup_parser_help(parser, __doc__)

    file_help = 'File with list of files in which keywords are to be changed'
    parser.add_argument('--file-list', help=file_help)
    parser.add_argument('files', nargs='*',
                        help='Files in which to add/change keywords')

    key_group = parser.add_mutually_exclusive_group(required=True)

    key_group.add_argument('--key-file',
                           help='File with keywords and values to be set')

    key_group.add_argument('--key-value', nargs=2,
                           help='Keyword to add/change',)
    return parser


def main(arglist=None):
    """
    Wrapper for invoking add_keys from the command line

    Parameters
    ----------

    arglist : list of strings, optional
        If set, use this arglist instead of `sys.argv` for parsing command
        line arguments. Primarily useful for testing.
    """
    parser = construct_parser()
    args = parser.parse_args(arglist)

    if len(args.files) == 0 and args.file_list is None:
        parser.error('Must provide either files or a --file-list')
    key_dict = {}
    if args.key_value:
        key_dict[args.key_value[0]] = args.key_value[1]
    add_keys(*args.files, file_list=args.file_list, key_file=args.key_file,
             **key_dict)
