from tempfile import mkdtemp
import os
from shutil import rmtree
import gzip

import numpy as np
import pytest
from astropy.io import fits

from .header_processing.patchers import IRAF_image_type


@pytest.fixture
def triage_setup(request):
    n_test = {'files': 0, 'need_object': 0,
              'need_filter': 0, 'bias': 0,
              'compressed': 0, 'light': 0,
              'need_pointing': 0}

    test_dir = ''

    for key in n_test.keys():
        n_test[key] = 0

    test_dir = mkdtemp()
    original_dir = os.getcwd()
    os.chdir(test_dir)
    img = np.uint16(np.arange(100))

    no_filter_no_object = fits.PrimaryHDU(img)
    no_filter_no_object.header['imagetyp'] = IRAF_image_type('light')
    no_filter_no_object.writeto('no_filter_no_object_light.fit')
    n_test['files'] += 1
    n_test['need_object'] += 1
    n_test['need_filter'] += 1
    n_test['light'] += 1
    n_test['need_pointing'] += 1

    no_filter_no_object.header['imagetyp'] = IRAF_image_type('bias')
    no_filter_no_object.writeto('no_filter_no_object_bias.fit')
    n_test['files'] += 1
    n_test['bias'] += 1

    filter_no_object = fits.PrimaryHDU(img)
    filter_no_object.header['imagetyp'] = IRAF_image_type('light')
    filter_no_object.header['filter'] = 'R'
    filter_no_object.writeto('filter_no_object_light.fit')
    n_test['files'] += 1
    n_test['need_object'] += 1
    n_test['light'] += 1
    n_test['need_pointing'] += 1

    filter_no_object.header['imagetyp'] = IRAF_image_type('bias')
    filter_no_object.writeto('filter_no_object_bias.fit')
    n_test['files'] += 1
    n_test['bias'] += 1

    filter_object = fits.PrimaryHDU(img)
    filter_object.header['imagetyp'] = IRAF_image_type('light')
    filter_object.header['filter'] = 'R'
    filter_object.header['OBJCTRA'] = '00:00:00'
    filter_object.header['OBJCTDEC'] = '00:00:00'
    filter_object.writeto('filter_object_light.fit')
    n_test['files'] += 1
    n_test['light'] += 1
    n_test['need_object'] += 1
    filter_file = open('filter_object_light.fit', 'rb')
    fzipped = gzip.open('filter_object_light.fit.gz', 'wb')
    fzipped.writelines(filter_file)
    fzipped.close()
    n_test['files'] += 1
    n_test['compressed'] += 1
    n_test['light'] += 1
    n_test['need_object'] += 1

    filter_object.header['RA'] = filter_object.header['OBJCTRA']
    filter_object.header['Dec'] = filter_object.header['OBJCTDEC']
    filter_object.writeto('filter_object_RA_keyword_light.fit')
    n_test['files'] += 1
    n_test['light'] += 1
    n_test['need_object'] += 1

    def teardown():
        for key in n_test.keys():
            n_test[key] = 0
        rmtree(test_dir)
        os.chdir(original_dir)
    request.addfinalizer(teardown)

    class Result(object):
        def __init__(self, n, directory):
            self.n_test = n
            self.test_dir = directory
    return Result(n_test, test_dir)


@pytest.fixture
def make_overscan_test_files(request, tmpdir):
    """
    Creates two files, one with overscan, one without for Alta U9

    Parameters

    test_dir: str
        Directory in which to create the overscan files.

    Returns

    info: list
        (working_dir, has_oscan, has_no_oscan)
        working_dir: str
            subdirectory of test_dir in which files are created
        has_oscan: str
            Name of FITS file that has overscan region
        has_no_oscan: str
            Name of FITS file that has no overscan region
    """
    from .header_processing.feder import ApogeeAltaU9, MaximDL5
    from os import path, mkdir
    import astropy.io.fits as fits
    import numpy as np

    test_dir = tmpdir
    oscan_names = ['yes_scan', 'no_scan']
    oscan = {'yes_scan': True,
             'no_scan': False}
    apogee = ApogeeAltaU9()
    working_dir = 'overscan_test'
    working_path = test_dir.mkdir(working_dir)
    add_instrument = lambda hdr: hdr.set('instrume', 'Apogee Alta')
    name_fits = lambda name: name + '.fit'
    for name in oscan_names:
        if oscan[name]:
            data = np.zeros([apogee.rows, apogee.columns])
            has_oscan = name
        else:
            data = np.zeros([apogee.rows, apogee.overscan_start])
            no_oscan = name
        hdu = fits.PrimaryHDU(data)
        hdr = hdu.header
        add_instrument(hdu.header)
        mdl5 = MaximDL5()
        # all headers need a software name
        hdr[mdl5.fits_keyword] = mdl5.fits_name[0]
        hdr['imagetyp'] = 'LIGHT'
        hdu.writeto(path.join(working_path.strpath, name_fits(name)))

    return (working_path.strpath, name_fits(has_oscan), name_fits(no_oscan))
