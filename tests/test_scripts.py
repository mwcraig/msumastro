import pytest
import py
from ..run_patch import patch_directories

_default_object_file_name = 'obsinfo.txt'


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

    def test_run_patch_does_not_overwite_if_destination(self, recwarn):
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
