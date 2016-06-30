from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import os
from contextlib import contextmanager

import astropy.io.fits as fits
from astropy.table import Table, Column
from astropy.extern import six

import pytest
import py
import numpy as np

from ...header_processing.patchers import IRAF_image_type
from .. import run_patch as run_patch

from .. import run_triage

from .. import run_astrometry
from .. import run_standard_header_process
from .. import sort_files
from ...image_collection import ImageFileCollection
from ..script_helpers import handle_destination_dir_logging_check
from .. import quick_add_keys_to_file
from ...tests.data import get_data_dir

_default_object_file_name = 'obsinfo.txt'
OBJECT_LIST_URL = 'https://raw.github.com/mwcraig/feder-object-list/master/feder_object_list.csv'


def set_mtimes(files, offset=10):
    """
    Set mtime of files to a time in the past

    Parameters
    ----------

    files : list of py.path.local objects
        list of files for which mtime should be set
    """
    default_mtime = files[0].mtime() - offset
    for fil in files:
        fil.setmtime(default_mtime)


def mtimes(files):
    """
    Find mtimes of files

    Parameters
    ----------

    files : list of py.path.local objects
        list of files
    """
    return [fil.mtime() for fil in files]


@pytest.fixture
def triage_dict():
    default_names = run_triage.DefaultFileNames()
    names_dict = default_names.as_dict()
    return names_dict


@pytest.fixture
def clean_data(tmpdir, request):
    test_dir = tmpdir
    test_data_dir = py.path.local(get_data_dir())
    test_data_dir.copy(test_dir)
    objs = ["ey uma, 09:02:20.76, +49:49:09.3",
            "m101,14:03:12.58,+54:20:55.50"
            ]
    to_write = '# comment 1\n# comment 2\nobject, RA, Dec\n' + '\n'.join(objs)
    object_path = test_dir.join(_default_object_file_name)
    print(object_path)
    object_file = object_path.open(mode='wt')
    print(object_file)
    object_file.write(to_write)
    object_file.close()

    def cleanup():
        test_dir.remove()
    request.addfinalizer(cleanup)
    return test_dir


@pytest.mark.usefixtures('clean_data')
class TestScript(object):
    @pytest.fixture(autouse=True)
    def set_test_dir(self, clean_data):
        self.test_dir = clean_data

    @pytest.fixture
    def default_keywords(self):
        return run_triage.DEFAULT_KEYS

    def test_run_patch_does_not_overwite_fits_if_dest_set(self, recwarn):
        fits_files = [fil for fil in self.test_dir.visit(fil=str('*.fit'),
                                                         sort=False)]
        set_mtimes(fits_files)
        original_mtimes = mtimes(fits_files)
        print(original_mtimes)
        destination = self.test_dir.make_numbered_dir()
        arglist = ['--destination-dir', destination.strpath,
                   self.test_dir.strpath
                   ]
        run_patch.main(arglist)
        new_mtimes = mtimes(fits_files)
        print(new_mtimes)
        print(destination)
        print(self.test_dir)
        for original, new in zip(original_mtimes, new_mtimes):
            assert (original == new)
        # assertion below is to catch whether add_object_info raised a warning
        # if it did, it means object names were not added and the test wasn't
        # complete
        #
        # originally tested for this by looking at number of warnings
        # emitted, but changing astropy versions made it emit warnings
        # instead, do the stupid thing below...check for text of the message.
        #
        for wrn in recwarn.list:
            # Apparently message is not actually always a string, so the
            # assert below can fail for reasons unrelated to the test.
            try:
                assert 'No object list' not in wrn.message
            except TypeError:
                pass
        destination.remove()

    def test_run_patch_with_object_list_url(self, simbad_down):
        if simbad_down:
            pytest.xfail("simbad is down")
        arglist = ['-o', OBJECT_LIST_URL, self.test_dir.strpath]
        # Remove default object file just to make sure object information can
        # come only from the remote list.
        self.test_dir.join(_default_object_file_name).remove()
        run_patch.main(arglist)
        h = fits.getheader(self.test_dir.join('uint16.fit').strpath)
        assert h['object'] == 'm101'

    def test_run_patch_overscan_only(self, simbad_down):
        if simbad_down:
            pytest.xfail("simbad is down")
        arglist = ['-o', OBJECT_LIST_URL, '--overscan-only',
                   self.test_dir.strpath]
        # Remove default object file just to make sure object information can
        # come only from the remote list.
        self.test_dir.join(_default_object_file_name).remove()
        run_patch.main(arglist)
        h = fits.getheader(self.test_dir.join('uint16.fit').strpath)
        print(h)
        assert 'object' not in h

    def test_run_triage_no_output_generated(self, default_keywords):
        list_before = self.test_dir.listdir(sort=True)
        run_triage.triage_directories([self.test_dir.strpath],
                                      keywords=default_keywords,
                                      object_file_name=None,
                                      pointing_file_name=None,
                                      filter_file_name=None,
                                      output_table=None)
        list_after = self.test_dir.listdir(sort=True)
        assert(list_before == list_after)

    def _verify_triage_files_created(self, directory, triage_dict):
        for option_name, file_name in six.iteritems(triage_dict):
            print(option_name, file_name, directory.join(file_name).check())
            assert(directory.join(file_name).check())

    def test_triage_output_file_by_keyword(self, triage_dict,
                                           default_keywords):
        run_triage.triage_directories([self.test_dir.strpath],
                                      keywords=default_keywords,
                                      **triage_dict)
        self._verify_triage_files_created(self.test_dir, triage_dict)

    def test_triage_destination_directory(self, triage_dict,
                                          default_keywords):
        destination = self.test_dir.make_numbered_dir()
        list_before = self.test_dir.listdir(sort=True)
        run_triage.triage_directories([self.test_dir.strpath],
                                      keywords=default_keywords,
                                      destination=destination.strpath,
                                      **triage_dict)
        list_after = self.test_dir.listdir(sort=True)
        assert(list_before == list_after)
        self._verify_triage_files_created(destination, triage_dict)

    @pytest.mark.parametrize('extra_keys',
                             [['key1'],
                              ['key1', 'key2']])
    def test_run_triage_default_keys_and_extra(self, default_keywords,
                                               triage_dict, extra_keys):
        table_file = 'tbl.txt'
        arglist = []
        print(extra_keys)
        for key in extra_keys:
            arglist.extend(['--key', key])

        gather_keys = default_keywords[:]

        gather_keys.extend(extra_keys)
        arglist.extend(['--table-name', table_file,
                       self.test_dir.strpath])
        run_triage.main(arglist=arglist)
        print(arglist)
        print(gather_keys)
        table = Table.read(self.test_dir.join(table_file).strpath,
                           format='ascii')
        for key in gather_keys:
            assert (key in table.colnames)

    def test_run_triage_on_set_with_no_light_files(self):
        ic = ImageFileCollection(self.test_dir.strpath, keywords=['imagetyp'])
        for header in ic.headers(imagetyp='light', overwrite=True):
            header['imagetyp'] = 'BIAS'
        arglist = [self.test_dir.strpath]
        run_triage.main(arglist)
        assert 1

    def test_run_triage_on_set_with_maximdl_imagetype_fails(self):
        hdu = fits.PrimaryHDU()
        hdu.header['imagetyp'] = 'Bias Frame'
        hdu.header['exptime'] = 0.0
        hdu.data = np.random.random([100, 100])
        hdu.writeto(self.test_dir.join('maxim.fits').strpath)
        with pytest.raises(ValueError):
            run_triage.triage_fits_files(self.test_dir.strpath)

    def test_run_triage_contains_columns_with_extended_location_info(self):
        result = run_triage.triage_fits_files(self.test_dir.strpath)
        location_keys = ['Source path', 'Source directory']
        for key in location_keys:
            assert key in result['files'].colnames

    def test_run_triage_correctly_sets_extended_location_info(self):
        result = run_triage.triage_fits_files(self.test_dir.strpath)
        table = result['files']
        assert table['Source path'][0] == self.test_dir.strpath
        assert (table['Source directory'][0] ==
                os.path.basename(self.test_dir.strpath))

    def test_run_triage_with_only_list_default_keys(self):
        assert run_triage.main(arglist=['-l']) == run_triage.DEFAULT_KEYS
        assert (run_triage.main(arglist=['-l', '-k should_not_be_added']) ==
                run_triage.DEFAULT_KEYS)

    def test_run_triage_raises_error_if_no_dir_supplied(self):
        with pytest.raises(SystemExit):
            # dummy argument to ensure coverage knows the test is happening
            run_triage.main(arglist=['-k cow'])

    def test_run_triage_with_no_keywords_makes_right_keywords(self):
        result = run_triage.triage_fits_files(self.test_dir.strpath)
        expected_keys = ['imagetyp', 'object', 'filter']
        for key in expected_keys:
            assert key in result['files'].colnames

    def test_triage_grabbing_all_keywords_gets_them_all(self):
        tbl_name = 'tbl.txt'
        run_triage.main(arglist=['-a', '-t', tbl_name, self.test_dir.strpath])
        rt_table = Table.read(self.test_dir.join(tbl_name).strpath,
                              format='ascii.csv')
        lcase_columns = [c.lower() for c in rt_table.colnames]
        print(lcase_columns)
        ic = ImageFileCollection(self.test_dir.strpath,
                                 keywords='*')
        for h in ic.headers():
            for k in h:
                if k:
                    assert k.lower() in lcase_columns

    def test_run_triage_writer_makes_correct_column_names(self, tmpdir):
        dump_file = 'dumb.txt'
        run_triage.write_list(tmpdir.strpath, dump_file, range(10))
        tab = Table.read(tmpdir.join(dump_file).strpath, format='ascii')
        assert 'File' in tab.colnames

        custom_name = 'Bob'
        run_triage.write_list(tmpdir.strpath, dump_file, range(10),
                              column_name=custom_name)
        tab = Table.read(tmpdir.join(dump_file).strpath, format='ascii')
        assert custom_name in tab.colnames

    def test_triage_case_inseneistive_column_name_matching(self):
        columns = ['one', 'Two', 'THREE']
        assert (run_triage.get_column_name_case_insensitive('one', columns)
                == 'one')
        assert (run_triage.get_column_name_case_insensitive('NOT', columns)
                == '')
        assert (run_triage.get_column_name_case_insensitive('two', columns)
                == 'Two')

    def test_run_astrometry_with_dest_does_not_modify_source(self):

        destination = self.test_dir.make_numbered_dir()
        list_before = self.test_dir.listdir(sort=True)
        arglist = ['--destination-dir', destination.strpath,
                   self.test_dir.strpath
                   ]
        run_astrometry.main(arglist)
        list_after = self.test_dir.listdir(sort=True)
        # nothing should change in the source directory
        assert(list_before == list_after)
        # for each light file in the destination directory we should have a
        # file with the same basename but an extension of blind
        ic = ImageFileCollection(destination.strpath,
                                 keywords=['IMAGETYP'])
        for image in ic.files_filtered(imagetyp='LIGHT'):
            image_path = destination.join(image)
            print(image_path.purebasename)
            blind_path = destination.join(image_path.purebasename + '.blind')
            print(blind_path.strpath)
            assert (blind_path.check())

    @pytest.mark.parametrize('file_column',
                             ['file',
                              'FiLe',
                              'badd'])
    @pytest.mark.parametrize('file_arg',
                             ['--file-list',
                              ''])
    @pytest.mark.parametrize('keyword_arg',
                             ['--key-file',
                              '--key-value'])
    def test_quick_add_keys_records_history(self, keyword_arg,
                                            file_arg, file_column):
        ic = ImageFileCollection(self.test_dir.strpath,
                                 keywords=['imagetyp'])
        ic.summary_info.keep_columns('file')

        file_list = os.path.join(ic.location, 'files.txt')
        keyword_list = os.path.join(ic.location, 'keys.txt')

        full_paths = [os.path.join(self.test_dir.strpath, fil) for
                      fil in ic.summary_info['file']]
        print('fill paths: %s' % ' '.join(full_paths))
        ic.summary_info['file'][:] = full_paths
        ic.summary_info.remove_column('file')
        ic.summary_info.add_column(Column(data=full_paths, name=file_column))
        ic.summary_info.write(file_list, format='ascii')
        if file_column != 'file':
            ic.summary_info.rename_column(file_column, 'file')
        dumb_keyword = 'munkeez'.upper()
        dumb_value = 'bananaz'
        keywords = Column(data=[dumb_keyword], name='Keyword')
        vals = Column(data=[dumb_value], name='value')
        keyword_table = Table()
        keyword_table.add_columns([keywords, vals])
        keyword_table.write(keyword_list, format='ascii')
        args_for = {}
        args_for['--key-file'] = [keyword_list]
        args_for['--key-value'] = [dumb_keyword, dumb_value]
        args_for['--file-list'] = [file_list]
        args_for[''] = full_paths
        argslist = [keyword_arg]
        argslist.extend(args_for[keyword_arg])
        if file_arg:
            argslist.append(file_arg)
        argslist.extend(args_for[file_arg])
        if file_column.lower() != 'file' and file_arg:
            with pytest.raises(ValueError):
                quick_add_keys_to_file.main(argslist)
            return
        else:
            quick_add_keys_to_file.main(argslist)

#        add_keys(file_list=file_list, key_file=keyword_list)
        for header in ic.headers():
            assert (header[dumb_keyword] == dumb_value)
            history_string = ' '.join(header['history'])
            assert (dumb_keyword in history_string)
            assert (dumb_value in history_string)

    def test_quick_add_keys_raises_error_if_no_files(self):
        with pytest.raises(SystemExit):
            quick_add_keys_to_file.main(['--key-value', 'key', 'value'])


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

## snippet below is from http://stackoverflow.com/a/13847807


@contextmanager
def pushd(newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)


class TestScriptHelper(object):
    """Test functions in script_helpers"""

    @pytest.mark.parametrize("argstring,run_in,expected", [
        (['--no-log-destination', '--destination-dir', '.', '.'], '.', 'exception'),
        (['--no-log-destination', os.getcwd()], '.', 'exception'),
        (['--no-log-destination', '--destination-dir', '/tmp', os.getcwd()], '.', True),
        (['--destination-dir', '/tmp', '.'], '.', False),
        (['--destination-dir', os.getcwd(), os.getcwd()], '..', False)])
    def test_handle_destination_dir_logging_check(self, argstring, run_in,
                                                  expected, a_parser):
        with pushd(run_in):
            args = a_parser.parse_args(argstring)
            print(argstring, expected)
            print(type(expected))
            if expected == 'exception':
                with pytest.raises(RuntimeError):
                    handle_destination_dir_logging_check(args)
            else:
                assert (handle_destination_dir_logging_check(args) == expected)


@pytest.mark.usefixtures('clean_data')
class TestRunStandardHeaderProcess(object):
    @pytest.fixture(autouse=True)
    def set_test_dir(self, clean_data):
        self.test_dir = clean_data

    @pytest.fixture()
    def scratch_destination(self):
        dest = self.test_dir.mkdtemp()
        return dest

    def test_source_not_modified_if_dest_set(self, scratch_destination):
        arglist = ['--dest-root', scratch_destination.strpath]
        arglist += [self.test_dir.strpath]
        fits_files = [fil for fil in self.test_dir.visit(fil=str('*.fit'),
                                                         sort=True)]
        set_mtimes(fits_files)
        original_mtimes = mtimes(fits_files)
        run_standard_header_process.main(arglist)
        new_mtimes = mtimes(fits_files)
        for original, new in zip(original_mtimes, new_mtimes):
            assert(original == new)


class TestSortFiles(object):
    """docstring for TestSortFiles"""
    @pytest.fixture(autouse=True)
    def set_test_dir(self, tmpdir):
        self.test_dir = tmpdir

    def write_names(self, hdu, names):
        for name in names:
            hdu.writeto(self.test_dir.join(name).strpath)

    def make_filter_exp(self, hdu, filter_dict, extra_name=None):
        add_to_name = extra_name or ''
        hdr = hdu.header
        make_base = lambda hdr, band: \
            hdr['imagetyp'] + add_to_name + band + str(hdr['exptime'])
        for band, num_or_exp_dict in six.iteritems(filter_dict):
            hdr['filter'] = band
            if isinstance(num_or_exp_dict, dict):
                for exp, number in six.iteritems(num_or_exp_dict):
                    hdr['exptime'] = exp
                    base = make_base(hdr, band)
                    print(base)
                    self.write_names(hdu, [base + str(i) + '.fit' for i in range(number)])
            else:
                hdr['exptime'] = 17.0
                base = make_base(hdr, band)
                print(base)
                print(hdr['imagetyp'])
                self.write_names(hdu, [base + str(i) + '.fit' for i in range(num_or_exp_dict)])

    @pytest.fixture
    def set_test_files(self):
        """
        A set of file is created from the dictionary below; the number
        of files of each type is set by the 'number' key.
        """
        bias = 'BIAS'
        dark = 'DARK'
        flat = 'FLAT'
        light = 'LIGHT'
        files = {bias: 5,
                 dark: {20.0: 5,
                        30.0: 5},
                 flat: {'R': {17.0: 3},
                        'V': {15.0: 2,
                              25.0: 2},
                        'I': {17.0: 5}},
                 light: {'m81': {'R': {17.0: 3},
                                 'V': {17.0: 2}},
                         'm101': {'I': {17.0: 5}},
                         None: {'I': {17.0: 2},
                                'R': {17.0: 3},
                                'V': {17.0: 4}}}
                 }
        data = np.random.random([100, 100])
        make_hdu = lambda im_type: \
            fits.PrimaryHDU(data,
                            fits.Header.fromkeys(['imagetyp'], value=im_type))
        make_file_names = lambda base, number: \
            [base + str(i) + '.fit' for i in range(number)]
        bias_names = make_file_names(bias, files[bias])
        bias_hdu = make_hdu(bias)
        self.write_names(bias_hdu, bias_names)
        for exp, number in six.iteritems(files[dark]):
            dark_hdu = make_hdu(dark)
            dark_hdu.header['exptime'] = exp
            dark_names = make_file_names(dark + str(exp), number)
            self.write_names(dark_hdu, dark_names)
        flat_hdu = make_hdu(flat)
        self.make_filter_exp(flat_hdu, files[flat])
        light_hdu = make_hdu(light)
        for obj, filter_dict in six.iteritems(files[light]):
            if not obj:
                try:
                    del light_hdu.header['object']
                except KeyError:
                    pass
            else:
                light_hdu.header['object'] = obj
            obj_name = obj or None
            self.make_filter_exp(light_hdu, filter_dict, extra_name=obj_name)

        return files

    def test_sort_files_can_be_called(self):
        sort_files.main([self.test_dir.strpath])

    def test_sort_called_with_no_directory_raises_error(self):
        with pytest.raises(SystemExit):
            sort_files.main(arglist=['-v', '-n'])

    def _walk_dict_string_keys(self, d, parent=None):
        if parent is None:
            parent = []
        for key, val in six.iteritems(d):
            new_parent = list(parent) + [str(key)]
            if isinstance(val, dict):
                for d in self._walk_dict_string_keys(val, parent=new_parent):
                    yield d
            else:
                yield new_parent, val

    @pytest.mark.parametrize('dest,move',
                             [('tmp', False),
                              (None, False),
                              ('tmp', True),
                              (None, True)])
    def test_sort_called_with_destination(self, set_test_files, dest, move):
        print(set_test_files)
        if dest:
            dest_path = self.test_dir.mkdtemp().strpath
            args = ['-d', dest_path, self.test_dir.strpath]
        else:
            dest_path = self.test_dir.strpath
            args = [self.test_dir.strpath]
        if move:
            args.insert(0, '--move')
        files_before_sort = os.listdir(self.test_dir.strpath)
        sort_files.main(arglist=args)
        files_after_sort = os.listdir(self.test_dir.strpath)
        if dest and not move:
            assert files_before_sort == files_after_sort
        if move:
            for f in files_after_sort:
                print(f)
                assert os.path.isdir(os.path.join(self.test_dir.strpath, f))
        expected_unsorted = 0
        for key in set_test_files['LIGHT'][None]:
            expected_unsorted += set_test_files['LIGHT'][None][key][17.0]
        for parents, num_files in self._walk_dict_string_keys(set_test_files):
            print(parents)
            if 'None' in parents:
                path = os.path.join(dest_path, parents[0],
                                    sort_files.UNSORTED_DIR)
                assert len(os.listdir(path)) == expected_unsorted
            else:
                path = os.path.join(dest_path, *parents)
                assert len(os.listdir(path)) == num_files

    def test_sort_creates_destination_if_needed(self, set_test_files):
        dest = self.test_dir.mkdtemp()
        dest = dest.join('crazy_dir')
        args = ['-d', dest.strpath, self.test_dir.strpath]
        sort_files.main(arglist=args)
        assert os.path.isdir(dest.strpath)

    def test_sort_handles_cannot_form_tree(self, set_test_files):
        # the object keyword is stripped from all headers, which means
        # you cannot for a tree for the light files. As a result, all
        # light files should end up in "unsorted" and no error should
        # be raised.
        images = ImageFileCollection(self.test_dir.strpath,
                                     keywords=['imagetyp', 'object'])
        n_light = 0
        for header in images.headers(overwrite=True, imagetyp='LIGHT'):
            try:
                del header['object']
            except KeyError:
                pass
            n_light += 1
        dest = self.test_dir.mkdtemp()
        sort_files.main(['-d', dest.strpath, self.test_dir.strpath])
        unsorted_path = os.path.join(dest.strpath,
                                     'LIGHT', sort_files.UNSORTED_DIR)
        assert len(os.listdir(unsorted_path)) == n_light


def test_triage_via_triage_fits_files(triage_setup):
    file_info = run_triage.triage_fits_files(triage_setup.test_dir)
    print("number of files should be %i" % triage_setup.n_test['files'])
    print(file_info['files']['file'])
    assert len(file_info['files']['file']) == triage_setup.n_test['files']
    assert len(file_info['needs_pointing']) == \
        triage_setup.n_test['need_pointing']
    assert len(file_info['needs_object_name']) == \
        triage_setup.n_test['need_object']
    assert len(file_info['needs_filter']) == triage_setup.n_test['need_filter']
    assert len(file_info['needs_astrometry']) == triage_setup.n_test['light']
    bias_check = np.where(file_info['files']['imagetyp'] ==
                          IRAF_image_type('bias'))
    assert (len(bias_check[0]) == 2)


def test_triage_via_run_triage(triage_setup, triage_dict):
    run_triage.main(['-a', triage_setup.test_dir])
    n_test_names = ['need_pointing', 'need_object', 'need_filter']
    file_name_keys = ['pointing_file_name', 'object_file_name',
                      'filter_file_name']
    for n_name, fname in zip(n_test_names, file_name_keys):
        file_path = os.path.join(triage_setup.test_dir,
                                 triage_dict[fname])
        dump = Table.read(file_path, format='ascii')
        assert len(dump) == triage_setup.n_test[n_name]
