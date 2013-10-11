import pytest
import py
from ..run_patch import patch_directories
from ..run_triage import DefaultFileNames, always_include_keys
from ..run_triage import triage_directories
from ..run_astrometry import astrometry_for_directory

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
        test_data_dir = py.path.local('data')
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
                           keywords=always_include_keys,
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
                           keywords=always_include_keys,
                           **triage_dict)
        self._verify_triage_files_created(self.test_dir, triage_dict)

    def test_triage_destination_directory(self, triage_dict):
        destination = self.test_dir.make_numbered_dir()
        list_before = self.test_dir.listdir(sort=True)
        triage_directories([self.test_dir.strpath],
                           keywords=always_include_keys,
                           destination=destination.strpath,
                           **triage_dict)
        list_after = self.test_dir.listdir(sort=True)
        assert(list_before == list_after)
        self._verify_triage_files_created(destination, triage_dict)

    def test_run_astrometry_with_dest_does_not_modify_source(self):
        from ..image_collection import ImageFileCollection

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
