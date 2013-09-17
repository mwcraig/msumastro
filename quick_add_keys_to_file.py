import asciitable as at
import astropy.io.fits as fits


def add_keys(file_list, keys=''):
    """Add keywords to a list of FITS files.

    `file_list` should have one file per line.

    `keylist` can be in any format easily readable by
    asciitable. There needs to be a header line followed by, on each
    line, a FITS keyword and its value.

    All keywords in the `keylist` file are added to all of the files
    in `file_list`.

    A sample `keylist` file is:
        Keyword   Value
        OBJCTDEC '+49 49 14'
        OBJCTRA '09 02 21'

    """
    files = at.read(file_list)
    key_table = at.read(keys)
    for fil in files:
        fil_fits = fits.open(fil[0], mode='update')
        hdr = fil_fits[0].header
        for key, val in key_table:
            print key, val
            hdr[key] = val
        fil_fits.close()
