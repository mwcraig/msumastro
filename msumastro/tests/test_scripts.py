import os
from tempfile import mkdtemp
import gzip
from shutil import rmtree

import astropy.io.fits as fits
from astropy.table import Table, Column
import pytest
import py
import numpy as np

from ..header_processing.patch_headers import IRAF_image_type
from ..run_patch import patch_directories
from ..run_triage import DefaultFileNames, ALWAYS_INCLUDE_KEYS
from ..run_triage import triage_directories, triage_fits_files
from ..run_astrometry import astrometry_for_directory
from ..image_collection import ImageFileCollection
from ..script_helpers import handle_destination_dir_logging_check
from ..quick_add_keys_to_file import add_keys
from data import get_data_dir

_default_object_file_name = 'obsinfo.txt'


@pytest.fixture
def triage_dict():
    default_names = DefaultFileNames()
    names_dict = default_names.as_dict()
    return names_dict


class TestScript(object):
    @pytest.fixture(autouse=True)
    def clean_data(self, tmpdir, request):
        self.test_dir = tmpdir
        test_data_dir = py.path.local(get_data_dir())
        test_data_dir.copy(self.test_dir)
        to_write = '# comment 1\n# comment 2\nobject\ney uma\nm101'
        object_path = self.test_dir.join(_default_object_file_name)
        print object_path
        object_file = object_path.open(mode='wb')
        object_file.write(to_write)
        object_file.close()

        def cleanup():
            self.test_dir.remove()
        request.addfinalizer(cleanup)

    def test_run_patch_does_not_overwite_if_destination_set(self, recwarn):
        mtimes = lambda files: [fil.mtime() for fil in files]
        fits_files = [fil for fil in self.test_dir.visit(fil='*.fit',
                                                         sort=True)]
        default_mtime = fits_files[0].mtime() - 10
        for fil in fits_files:
            fil.setmtime(default_mtime)
        original_mtimes = mtimes(fits_files)
        print original_mtimes
        destination = self.test_dir.make_numbered_dir()
        patch_directories([str(self.test_dir)], destination=str(destination))
        new_mtimes = mtimes(fits_files)
        print new_mtimes
        print destination
        print self.test_dir
        for original, new in zip(original_mtimes, new_mtimes):
            assert (original == new)
        # assertion below is to catch whether add_object_info raised a warning
        # if it did, it means object names were not added and the test wasn't
        # complete
        assert(len(recwarn.list) == 0)
        destination.remove()

    def test_run_triage_no_output_generated(self):
        list_before = self.test_dir.listdir(sort=True)
        triage_directories([self.test_dir.strpath],
                           keywords=ALWAYS_INCLUDE_KEYS,
                           object_file_name=None,
                           pointing_file_name=None,
                           filter_file_name=None,
                           output_table=None)
        list_after = self.test_dir.listdir(sort=True)
        assert(list_before == list_after)

    def _verify_triage_files_created(self, dir, triage_dict):
        for option_name, file_name in triage_dict.iteritems():
            print option_name, file_name, dir.join(file_name).check()
            assert(dir.join(file_name).check())

    def test_triage_output_file_by_keyword(self, triage_dict):
        triage_directories([self.test_dir.strpath],
                           keywords=ALWAYS_INCLUDE_KEYS,
                           **triage_dict)
        self._verify_triage_files_created(self.test_dir, triage_dict)

    def test_triage_destination_directory(self, triage_dict):
        destination = self.test_dir.make_numbered_dir()
        list_before = self.test_dir.listdir(sort=True)
        triage_directories([self.test_dir.strpath],
                           keywords=ALWAYS_INCLUDE_KEYS,
                           destination=destination.strpath,
                           **triage_dict)
        list_after = self.test_dir.listdir(sort=True)
        assert(list_before == list_after)
        self._verify_triage_files_created(destination, triage_dict)

    def test_run_astrometry_with_dest_does_not_modify_source(self):

        destination = self.test_dir.make_numbered_dir()
        list_before = self.test_dir.listdir(sort=True)
        astrometry_for_directory([self.test_dir.strpath], destination.strpath,
                                 blind=False)
        list_after = self.test_dir.listdir(sort=True)
        # nothing should change in the source directory
        assert(list_before == list_after)
        # for each light file in the destination directory we should have a
        # file with the same basename but an extension of blind
        ic = ImageFileCollection(destination.strpath,
                                 keywords=['IMAGETYP'])
        for image in ic.files_filtered(imagetyp='LIGHT'):
            image_path = destination.join(image)
            print image_path.purebasename
            blind_path = destination.join(image_path.purebasename + '.blind')
            print blind_path.strpath
            assert (blind_path.check())

    def test_quick_add_keys_records_history(self):
        ic = ImageFileCollection(self.test_dir.strpath)
        ic.summary_info.keep_columns('file')

        file_list = os.path.join(ic.location, 'files.txt')
        keyword_list = os.path.join(ic.location, 'keys.txt')

        full_paths = [os.path.join(self.test_dir.strpath, fil) for
                      fil in ic.summary_info['file']]
        print 'fill paths: %s' % ' '.join(full_paths)
        ic.summary_info['file'][:] = full_paths
        ic.summary_info.remove_column('file')
        ic.summary_info.add_column(Column(data=full_paths, name='file'))
        ic.summary_info.write(file_list, format='ascii')
        dumb_keyword = 'munkeez'.upper()
        dumb_value = 'bananaz'
        keywords = Column(data=[dumb_keyword], name='Keyword')
        vals = Column(data=[dumb_value], name='value')
        keyword_table = Table()
        keyword_table.add_columns([keywords, vals])
        keyword_table.write(keyword_list, format='ascii')
        add_keys(file_list=file_list, key_file=keyword_list)
        for header in ic.headers():
            assert (header[dumb_keyword] == dumb_value)
            history_string = ' '.join(header['history'])
            assert (dumb_keyword in history_string)
            assert (dumb_value in history_string)


@pytest.fixture(params=['run_patch', 'run_triage', 'run_astrometry'])
def a_parser(request):
    from ..run_patch import construct_parser as ph_parser
    from ..run_astrometry import construct_parser as as_parser
    from ..run_triage import construct_parser as tr_parser
    parsers = {'run_patch': ph_parser,
               'run_astrometry': as_parser,
               'run_triage': tr_parser
               }
    the_parser = parsers[request.param]
    return the_parser()


class TestScriptHelper(object):
    """Test functions in script_helpers"""

    @pytest.mark.parametrize("argstring,expected", [
        (['--no-log-destination', '--destination-dir', '.', '.'], 'exception'),
        (['--no-log-destination', os.getcwd()], 'exception'),
        (['--no-log-destination', '--destination-dir', '/tmp', os.getcwd()], True),
        (['--destination-dir', '/tmp', '.'], False)])
    def test_handle_destination_dir_logging_check(self, argstring, expected,
                                                  a_parser):
        args = a_parser.parse_args(argstring)
        print argstring, expected
        print type(expected)
        if expected == 'exception':
            with pytest.raises(RuntimeError):
                handle_destination_dir_logging_check(args)
        else:
            assert (handle_destination_dir_logging_check(args) == expected)


_n_test = {'files': 0, 'need_object': 0,
           'need_filter': 0, 'bias': 0,
           'compressed': 0, 'light': 0,
           'need_pointing': 0}

_test_dir = ''
_filters = []


@pytest.fixture
def triage_setup(request):
    global _n_test
    global _test_dir

    for key in _n_test.keys():
        _n_test[key] = 0

    _test_dir = mkdtemp()
    original_dir = os.getcwd()
    os.chdir(_test_dir)
    img = np.uint16(np.arange(100))

    no_filter_no_object = fits.PrimaryHDU(img)
    no_filter_no_object.header['imagetyp'] = IRAF_image_type('light')
    no_filter_no_object.writeto('no_filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    _n_test['need_filter'] += 1
    _n_test['light'] += 1
    _n_test['need_pointing'] += 1

    no_filter_no_object.header['imagetyp'] = IRAF_image_type('bias')
    no_filter_no_object.writeto('no_filter_no_object_bias.fit')
    _n_test['files'] += 1
    _n_test['bias'] += 1

    filter_no_object = fits.PrimaryHDU(img)
    filter_no_object.header['imagetyp'] = IRAF_image_type('light')
    filter_no_object.header['filter'] = 'R'
    filter_no_object.writeto('filter_no_object_light.fit')
    _n_test['files'] += 1
    _n_test['need_object'] += 1
    _n_test['light'] += 1
    _n_test['need_pointing'] += 1

    filter_no_object.header['imagetyp'] = IRAF_image_type('bias')
    filter_no_object.writeto('filter_no_object_bias.fit')
    _n_test['files'] += 1
    _n_test['bias'] += 1

    filter_object = fits.PrimaryHDU(img)
    filter_object.header['imagetyp'] = IRAF_image_type('light')
    filter_object.header['filter'] = 'R'
    filter_object.header['OBJCTRA'] = '00:00:00'
    filter_object.header['OBJCTDEC'] = '00:00:00'
    filter_object.writeto('filter_object_light.fit')
    _n_test['files'] += 1
    _n_test['light'] += 1
    _n_test['need_object'] += 1
    filter_file = open('filter_object_light.fit', 'rb')
    fzipped = gzip.open('filter_object_light.fit.gz', 'wb')
    fzipped.writelines(filter_file)
    fzipped.close()
    _n_test['files'] += 1
    _n_test['compressed'] += 1
    _n_test['light'] += 1
    _n_test['need_object'] += 1

    def teardown():
        global _n_test

        for key in _n_test.keys():
            _n_test[key] = 0
        rmtree(_test_dir)
        os.chdir(original_dir)
    request.addfinalizer(teardown)


@pytest.mark.usefixtures("triage_setup")
def test_triage():
    file_info = triage_fits_files(_test_dir)
    print "number of files should be %i" % _n_test['files']
    print file_info['files']['file']
    assert len(file_info['files']['file']) == _n_test['files']
    assert len(file_info['needs_pointing']) == _n_test['need_pointing']
    assert len(file_info['needs_object_name']) == _n_test['need_object']
    assert len(file_info['needs_filter']) == _n_test['need_filter']
    bias_check = np.where(file_info['files']['imagetyp'] ==
                          IRAF_image_type('bias'))
    assert (len(bias_check[0]) == 2)
