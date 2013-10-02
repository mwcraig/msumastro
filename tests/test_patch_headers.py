from ..patch_headers import *
from tempfile import mkdtemp
from os import path, chdir, getcwd
from shutil import rmtree
import numpy as np
import pytest

test_tuple = (1, 2, 3.1415)
_test_dir = ''
_default_object_file_name = 'obsinfo.txt'


def test_sexagesimal_string():
    assert sexagesimal_string(test_tuple) == '01:02:03.14'


def test_sexagesimal_string_with_sign():
    assert sexagesimal_string(test_tuple, sign=True) == '+01:02:03.14'


def test_sexagesimal_string_with_precision():
    assert sexagesimal_string(test_tuple, precision=3) == '01:02:03.142'


def test_sexagesimal_string_with_precision_and_sign():
    assert (sexagesimal_string(test_tuple, sign=True, precision=3) ==
            '+01:02:03.142')


def test_read_object_list():
    objects = read_object_list(dir=_test_dir)
    assert len(objects) == 2
    assert objects[0] == 'ey uma'
    assert objects[1] == 'm101'


def test_history_bad_mode():
    with pytest.raises(ValueError):
        history(test_history_bad_mode, mode='not a mode')


def test_history_begin():
    hist = history(test_history_begin, mode='begin')
    assert hist.find('BEGIN') > 0
    assert hist.endswith('+')


def test_history_end():
    hist = history(test_history_end, mode='end')
    assert hist.find('END') > 0
    assert hist.endswith('-')


def test_history_function_name():
    hist = history(test_history_function_name, mode='begin')
    assert hist.find('test_history_function_name') > 0


def test_data_is_unmodified_by_patch_headers():
    """No changes should be made to the data."""
    new_ext = '_new'
    patch_headers(_test_dir, new_file_ext=new_ext)
    fname = path.join(_test_dir, 'uint16')
    fname_new = fname + new_ext
    orig = fits.open(fname + '.fit',
                     do_not_scale_image_data=True)
    modified = fits.open(fname_new + '.fit',
                         do_not_scale_image_data=True)
    assert np.all(orig[0].data == modified[0].data)


def test_data_is_unmodified_by_adding_object():
    new_ext = '_obj'
    patch_headers(_test_dir, new_file_ext=new_ext)
    add_object_info(_test_dir, new_file_ext=new_ext)
    fname = path.join(_test_dir, 'uint16')
    fname_new = fname + new_ext + new_ext
    orig = fits.open(fname + '.fit',
                     do_not_scale_image_data=True)
    modified = fits.open(fname_new + '.fit',
                         do_not_scale_image_data=True)
    assert np.all(orig[0].data == modified[0].data)


def test_adding_object_name(use_list=None):
    new_ext = '_obj_name_test'
    patch_headers(_test_dir, new_file_ext=new_ext)
    add_object_info(_test_dir, new_file_ext=new_ext, object_list=use_list)
    fname = path.join(_test_dir, 'uint16')
    fname += new_ext + new_ext
    with_name = fits.open(fname + '.fit')
    print 'add object name: %s' % fname
    assert (with_name[0].header['object'] == 'm101')
    return with_name


def test_writing_patched_files_to_directory():
    from glob import glob
    files = glob(path.join(_test_dir, '*.fit*'))
    n_files_init = len(glob(path.join(_test_dir, '*.fit*')))
    dest_dir = mkdtemp()
    patch_headers(_test_dir, new_file_ext=None, save_location=dest_dir)
    print files
    n_files_after = len(glob(path.join(_test_dir, '*.fit*')))
    print n_files_after
    n_files_destination = len(glob(path.join(dest_dir, '*.fit*')))
    print dest_dir
    rmtree(dest_dir)
    assert ((n_files_init == n_files_after) &
            (n_files_init == n_files_destination))


def test_purging_maximdl5_keywords():
    from ..feder import Feder
    from shutil import copy

    feder = Feder()
    mdl5_name = 'maximdl5_header.fit'
    copy(path.join('data', mdl5_name), _test_dir)
    hdr5 = fits.getheader(path.join(_test_dir, mdl5_name))
    purge_bad_keywords(hdr5, history=True, force=False)
    for software in feder.software:
        if software.created_this(hdr5[software.fits_keyword]):
            break
    keyword_present = False
    for keyword in software.bad_keywords:
        keyword_present = (keyword_present or (keyword in hdr5))
    assert not keyword_present


def test_adding_overscan_apogee_u9():
    from ..feder import ApogeeAltaU9
    from utilities import make_overscan_test_files

    original_dir = getcwd()

    apogee = ApogeeAltaU9()
    print getcwd()
    oscan_dir, has_oscan, has_no_oscan = make_overscan_test_files(_test_dir)
    print "POOOP"
    print getcwd()
    print "PEE"

    chdir(path.join(_test_dir, oscan_dir))
    patch_headers(dir='.', new_file_ext='', overwrite=True, purge_bad=False,
                  add_time=False, add_apparent_pos=False,
                  add_overscan=True, fix_imagetype=False)
    print _test_dir
    header_no_oscan = fits.getheader(has_no_oscan)
    assert not header_no_oscan['oscan']
    header_yes_oscan = fits.getheader(has_oscan)
    assert header_yes_oscan['oscan']
    assert header_yes_oscan['oscanax'] == apogee.overscan_axis
    assert header_yes_oscan['oscanst'] == apogee.overscan_start
    print getcwd()
    chdir(original_dir)
    print getcwd()
    assert (True)


def test_fix_imagetype():
    imagetypes_to_check = {'Bias Frame': 'BIAS',
                           'Dark Frame': 'DARK',
                           'Light Frame': 'LIGHT',
                           'Flat Frame': 'FLAT'}
    for im_type in imagetypes_to_check:
        header = fits.Header()

        header['imagetyp'] = im_type
        # first run SHOULD change imagetyp
        print header
        change_imagetype_to_IRAF(header, history=False)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        # second call should NOT change imagetyp
        print header
        change_imagetype_to_IRAF(header, history=True)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        with pytest.raises(KeyError):
            print header['history']
        # change imagetype back to non-IRAF
        header['imagetyp'] = im_type
        # change with history
        change_imagetype_to_IRAF(header, history=True)
        assert('history' in header)


def test_add_object_name_uses_object_list_name():
    from shutil import move

    custom_object_name = 'my_object_list.txt'
    old_object_path = path.join(_test_dir, _default_object_file_name)
    new_path = path.join(_test_dir, custom_object_name)
    move(old_object_path, new_path)
    fits_with_obj_name = test_adding_object_name(use_list=custom_object_name)
    # The line below is probably not really necessary since the same test
    # is done in test_adding_object_name but it doesn't hurt to test it
    # here too
    assert (fits_with_obj_name[0].header['object'] == 'm101')


def setup():
    global _test_dir
    from shutil import copy

    _test_dir = mkdtemp()
    to_write = '# comment 1\n# comment 2\nobject\ney uma\nm101'
    object_file = open(path.join(_test_dir, _default_object_file_name), 'wb')
    object_file.write(to_write)
    copy(path.join('data', 'uint16.fit'), _test_dir)


def teardown():
    global _test_dir
    rmtree(_test_dir)
