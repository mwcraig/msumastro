import triage_fits_files as tff
import os
import numpy
import pyfits
from shutil import rmtree
import gzip

TEST_DIR = 'monkeezs'
_n_test = {'files': 0, 'need_object':0, 'need_filter':0}

def test_IRAF_image_type_with_maximDL_name():
    maximDL_name = 'Bias Frame'
    assert tff.IRAF_image_type(maximDL_name) == 'BIAS'

def test_IRAF_image_type_with_IRAF_name():
    IRAF_name = 'BIAS'
    assert tff.IRAF_image_type(IRAF_name) == 'BIAS'

def test_needs_filter():
    assert tff.needs_filter(tff.IRAF['light'])
    assert tff.needs_filter(tff.IRAF['flat'])
    assert not tff.needs_filter(tff.IRAF['bias'])
    assert not tff.needs_filter(tff.IRAF['dark'])

def test_triage():
    file_info = tff.triage_fits_files(TEST_DIR)
    print "number of files should be %i" % _n_test['files']
    print file_info['files']
    assert len(file_info['files']['file name']) == _n_test['files']
    assert len(file_info['needs_object']) == _n_test['need_object']
    assert len(file_info['needs_filter']) == _n_test['need_filter']

def triage_setup():
    global _n_test

    for key in _n_test.keys():
        _n_test[key] = 0
    
    original_dir = os.getcwd()
    os.mkdir(TEST_DIR)
    os.chdir(TEST_DIR)
    img = numpy.arange(100)

    no_filter_no_object = pyfits.PrimaryHDU(img)
    no_filter_no_object.header.update('imagetyp', tff.IRAF['light'])
    no_filter_no_object.writeto('no_filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    _n_test['need_filter'] += 1
    no_filter_no_object.header.update('imagetyp', tff.IRAF['bias'])
    no_filter_no_object.writeto('no_filter_no_object_bias.fit')
    _n_test['files'] += 1


    filter_no_object = pyfits.PrimaryHDU(img)
    filter_no_object.header.update('imagetyp', tff.IRAF['light'])
    filter_no_object.header.update('filter','R')
    filter_no_object.writeto('filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    filter_no_object.header.update('imagetyp', tff.IRAF['bias'])
    filter_no_object.writeto('filter_no_object_bias.fit')
    _n_test['files'] += 1

    filter_object = pyfits.PrimaryHDU(img)
    filter_object.header.update('imagetyp', tff.IRAF['light'])
    filter_object.header.update('filter','R')
    filter_object.header.update('OBJCTRA','00:00:00')
    filter_object.header.update('OBJCTDEC','00:00:00')
    filter_object.writeto('filter_object_light.fit')
    _n_test['files'] += 1
    filter_file = open('filter_object_light.fit', 'rb')
    fzipped = gzip.open('filter_object_light.fit.gz', 'wb')
    fzipped.writelines(filter_file)
    fzipped.close()
    _n_test['files'] += 1
    os.chdir(original_dir)

def triage_teardown():
    global _n_test

    for key in _n_test.keys():
        _n_test[key] = 0
    rmtree(TEST_DIR)
    

test_triage.setUp = triage_setup
test_triage.tearDown = triage_teardown
