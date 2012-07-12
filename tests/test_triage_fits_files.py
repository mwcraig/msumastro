from .. import image_collection as tff
import os
import numpy
import pyfits
from shutil import rmtree
import gzip
from tempfile import mkdtemp
from numpy import where
import numpy as np

_n_test = {'files': 0, 'need_object':0,
           'need_filter':0, 'bias':0,
           'compressed':0}

_test_dir = ''
_filters = []


def test_triage():
    file_info = tff.triage_fits_files(_test_dir)
    print "number of files should be %i" % _n_test['files']
    print file_info['files']['file']
    assert len(file_info['files']['file']) == _n_test['files']
    assert len(file_info['needs_pointing']) == _n_test['need_object']
    assert len(file_info['needs_filter']) == _n_test['need_filter']
    assert len(where(file_info['files']['imagetyp'] == tff.IRAF_image_type('bias'))[0]) == 2
    

def test_fits_summary():
    keywords = ['imagetyp', 'filter']
    image_collection = tff.ImageFileCollection(_test_dir,
                                               keywords=keywords)
    summary = image_collection.fits_summary(keywords=keywords)
    print summary['file']
    print summary.keys()
    assert len(summary['file']) == _n_test['files']
    for keyword in keywords:
        assert len(summary[keyword]) == _n_test['files']
    print summary['file'] == 'no_filter_no_object_bias.fit'
    print summary['filter'][summary['file'] == 'no_filter_no_object_bias.fit']
    assert summary['filter'][summary['file'] == 'no_filter_no_object_bias.fit'] == ['']



class TestImageFileCollection(object):
    
    def test_storage_dir_set(self):
        try:
            should_work = tff.ImageFileCollection(storage_dir=_test_dir)
            assert True
        except OSError:
            assert False

        try:
            should_fail = tff.ImageFileCollection(storage_dir='/')
            assert False
        except OSError:
            assert True

        img_collection = tff.ImageFileCollection(location=_test_dir, keywords=['imagetyp','filter'])
        print img_collection.filesFiltered(keywords=['imagetyp'],
                                                        values=['bias'])
        print _n_test
        assert len(img_collection.filesFiltered(keywords=['imagetyp'],
                                                        values=['bias']))==_n_test['bias']
        assert len(img_collection.files) == _n_test['files']
        assert img_collection.hasKey('filter')
        assert not img_collection.hasKey('flying monkeys')
        assert len(img_collection.values('imagetyp',unique=True))==2
    
    def test_generator_full_path(self):
        collection = tff.ImageFileCollection(location=_test_dir)
        for path, file_name in zip(collection.paths(), collection.files):
            assert path == os.path.join(_test_dir, file_name)

    def test_headers(self):
        collection = tff.ImageFileCollection(location=_test_dir)
        n_headers = 0
        for header in collection.headers():
            assert isinstance(header, pyfits.Header)
            n_headers += 1
        assert n_headers == _n_test['files']

    def test_headers_save_location(self):
        collection = tff.ImageFileCollection(location=_test_dir)
        destination = mkdtemp()
        for header in collection.headers(save_location=destination):
            pass
        new_collection = tff.ImageFileCollection(location =
                                                 destination)
        basenames = lambda paths: set([os.path.basename(file) for file in paths])

        assert (len(basenames(collection.paths())-
                   basenames(new_collection.paths())) ==
                _n_test['compressed'])
        rmtree(destination)
        
    def test_generator_headers_save_with_name(self):
        collection = tff.ImageFileCollection(location=_test_dir)
        for header in collection.headers(save_with_name='_new'):
            assert isinstance(header, pyfits.Header)
        new_collection = tff.ImageFileCollection(location=_test_dir)
        assert (len(new_collection.paths()) ==
                2*(_n_test['files'])-_n_test['compressed'])
        
    def test_generator_data(self):
        collection = tff.ImageFileCollection(location=_test_dir)
        for img in collection.data():
            assert isinstance(img, np.ndarray)
    
        
def setup_module():
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
    _n_test['bias'] += 1

    filter_no_object = pyfits.PrimaryHDU(img)
    filter_no_object.header.update('imagetyp', tff.IRAF_image_type('light'))
    filter_no_object.header.update('filter','R')
    filter_no_object.writeto('filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    filter_no_object.header.update('imagetyp', tff.IRAF_image_type('bias'))
    filter_no_object.writeto('filter_no_object_bias.fit')
    _n_test['files'] += 1
    _n_test['bias'] += 1

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
    _n_test['compressed'] += 1
    os.chdir(original_dir)

def teardown_module():
    global _n_test

    for key in _n_test.keys():
        _n_test[key] = 0
    rmtree(_test_dir)

