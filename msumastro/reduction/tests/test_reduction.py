from tempfile import mkdtemp
from os import path, chdir, getcwd
from shutil import rmtree

import astropy.io.fits as fits
import pytest

from utilities import make_overscan_test_files
from ...header_processing.feder import ApogeeAltaU9
from ..reduction import trim
from ...header_processing.patchers import patch_headers

test_dir = ''
original_dir = ''


def setup():
    global test_dir
    global original_dir

    original_dir = getcwd()
    test_dir = mkdtemp()


def test_trim():
    global test_dir

    oscan_dir, has_oscan, has_no_oscan = make_overscan_test_files(test_dir)
    chdir(path.join(test_dir, oscan_dir))
    patch_headers('.', new_file_ext='', overwrite=True,
                  add_time=False, purge_bad=False, add_apparent_pos=False,
                  add_overscan=True, fix_imagetype=False)
    apogee = ApogeeAltaU9()
    # files without overscan should not be changed by trim
    hdus = fits.open(has_no_oscan)
    hdu = hdus[0]
    hdr = hdu.header
    assert(hdr['NAXIS' + str(apogee.overscan_axis)] == apogee.overscan_start)
    trim(hdu)
    assert(hdr['NAXIS' + str(apogee.overscan_axis)] == apogee.overscan_start)
    # files with overscan should have overscan region removed
    hdus = fits.open(has_oscan)
    hdu = hdus[0]
    hdr = hdu.header
    assert(hdr['NAXIS' + str(apogee.overscan_axis)] == apogee.columns)
    trim(hdu)
    assert(hdr['NAXIS' + str(apogee.overscan_axis)] == apogee.overscan_start)
    with pytest.raises(RuntimeError):
        hdus = fits.open(has_oscan)
        hdu = hdus[0]
        hdr = hdu.header
        try:
            del hdr['oscanax']
            del hdr['oscanst']
        except KeyError:
            pass
        trim(hdu)


def teardown():
    chdir(original_dir)
    rmtree(test_dir)
