"""
DESCRIPTION
-----------

    Add each of the keywords in the ``key_file`` to each of the files
    listed in the ``file_list``. If the keyword is already present its
    value is updated to the value in ``key_file``.
"""


import astropy.io.fits as fits
from astropy.table import Table


def add_keys(*files, **kwd):
    """
    Add keywords to a list of FITS files.

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
    key_file = kwd.pop('key_file', None)
    files = Table.read(file_list, format='ascii')
    key_table = Table.read(key_file, format='ascii')
    for fil in files:
        fil_fits = fits.open(fil[0], mode='update')
        hdr = fil_fits[0].header
        for key, val in key_table:
            print key, val
            hdr[key] = val
        fil_fits.close()

__doc__ += add_keys.__doc__


def construct_parser():
    from argparse import ArgumentParser
    import script_helpers

    parser = ArgumentParser()
    script_helpers.setup_parser_help(parser, __doc__)

    parser.add_argument('-k', '--key-file',
                        help='File with keywords and values to be set',
                        required=True)

    file_help = 'File with list of files in which keywords are to be changed'
    parser.add_argument('-f', '--file-list',
                        help=file_help,
                        required=True)

    return parser


if __name__ == '__main__':
    parser = construct_parser()
    args = parser.parse_args()

    add_keys(file_list=args.file_list, key_file=args.key_file)
