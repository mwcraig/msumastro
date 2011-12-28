import triage_fits_files as tff
import os
import numpy
import pyfits
from shutil import rmtree
import gzip
from tempfile import mkdtemp

_n_test = {'files': 0, 'need_object':0, 'need_filter':0}
_test_dir = ''
_filters = []

def test_IRAF_image_type_with_maximDL_name():
    maximDL_name = 'Bias Frame'
    assert tff.IRAF_image_type(maximDL_name) == 'BIAS'

def test_IRAF_image_type_with_IRAF_name():
    IRAF_name = 'BIAS'
    assert tff.IRAF_image_type(IRAF_name) == 'BIAS'

def test_needs_filter():
    assert tff.needs_filter(tff.IRAF_image_type('light'))
    assert tff.needs_filter(tff.IRAF_image_type('flat'))
    assert not tff.needs_filter(tff.IRAF_image_type('bias'))
    assert not tff.needs_filter(tff.IRAF_image_type('dark'))

def test_triage():
    file_info = tff.triage_fits_files(_test_dir)
    print "number of files should be %i" % _n_test['files']
    print file_info['files']
    assert len(file_info['files']['file name']) == _n_test['files']
    assert len(file_info['needs_pointing']) == _n_test['need_object']
    assert len(file_info['needs_filter']) == _n_test['need_filter']
    
def test_fits_files_in_directory():
    assert (len(tff.fits_files_in_directory(_test_dir)) == _n_test['files'])

def test_fits_summary():
    keywords = ['imagetyp', 'filter']
    summary = tff.fits_summary(_test_dir,
                               keywords=keywords)
    print summary['file']
    print summary.keys()
    assert len(summary['file']) == _n_test['files']
    for keyword in keywords:
        assert len(summary[keyword]) == _n_test['files']
    print summary['file'] == 'no_filter_no_object_bias.fit'
    print summary['filter'][summary['file'] == 'no_filter_no_object_bias.fit']
    assert summary['filter'][summary['file'] == 'no_filter_no_object_bias.fit'] == [None]
    
    
def setup():
    global _n_test
    global _test_dir
    
    for key in _n_test.keys():
        _n_test[key] = 0
    
    original_dir = os.getcwd()
    _test_dir = mkdtemp()
    os.chdir(_test_dir)
    img = numpy.arange(100)

    no_filter_no_object = pyfits.PrimaryHDU(img)
    no_filter_no_object.header.update('imagetyp', tff.IRAF_image_type('light'))
    no_filter_no_object.writeto('no_filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    _n_test['need_filter'] += 1
    
    no_filter_no_object.header.update('imagetyp', tff.IRAF_image_type('bias'))
    no_filter_no_object.writeto('no_filter_no_object_bias.fit')
    _n_test['files'] += 1


    filter_no_object = pyfits.PrimaryHDU(img)
    filter_no_object.header.update('imagetyp', tff.IRAF_image_type('light'))
    filter_no_object.header.update('filter','R')
    filter_no_object.writeto('filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    filter_no_object.header.update('imagetyp', tff.IRAF_image_type('bias'))
    filter_no_object.writeto('filter_no_object_bias.fit')
    _n_test['files'] += 1

    filter_object = pyfits.PrimaryHDU(img)
    filter_object.header.update('imagetyp', tff.IRAF_image_type('light'))
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

def teardown():
    global _n_test

    for key in _n_test.keys():
        _n_test[key] = 0
    #rmtree(_test_dir)
    

#test_triage.setUp = triage_setup
#test_triage.tearDown = triage_teardown
