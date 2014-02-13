from os import path, chdir, getcwd, remove
from shutil import rmtree, copy, copytree, move
from tempfile import mkdtemp
from glob import glob
import warnings
import logging
from socket import timeout

import pytest
pytest_plugins = "capturelog"
import numpy as np
from numpy.testing import assert_almost_equal
from astropy.io import fits
from astropy.coordinates import Angle, FK5, name_resolve
from astropy import units as u

#from ..patch_headers import *
from .. import patchers as ph
from ..feder import Feder, FederSite, ApogeeAltaU9
from ...reduction.tests.utilities import make_overscan_test_files
from ...tests.data import get_data_dir
from ... import ImageFileCollection

_test_dir = ''
_default_object_file_name = 'obsinfo.txt'
_test_image_name = 'uint16.fit'
simbad_down = False


@pytest.mark.usefixtures('object_file_no_ra')
def test_read_object_list():
    objects, RA, Dec = ph.read_object_list(dir=_test_dir)
    assert len(objects) == 2
    assert objects[0] == 'ey uma'
    assert objects[1] == 'm101'
    assert not (RA or Dec)


def test_read_object_list_ra_dec():
    temp_dir = mkdtemp()
    obj_name = 'objects_with_ra.txt'
    object_path = path.join(temp_dir, obj_name)
    object_in = 'ey uma'
    RA_in = "09:02:20.76"
    Dec_in = "+49:49:09.3"
    to_write = 'object, RA, Dec\n{},{},{}'.format(object_in, RA_in, Dec_in)
    object_file = open(object_path, 'wb')
    object_file.write(to_write)
    object_file.close()
    obj, RA, Dec = ph.read_object_list(temp_dir, obj_name)
    assert(obj[0] == object_in)
    assert(RA[0] == RA_in)
    assert(Dec[0] == Dec_in)


def test_history_bad_mode():
    with pytest.raises(ValueError):
        ph.history(test_history_bad_mode, mode='not a mode')


def test_history_begin():
    hist = ph.history(test_history_begin, mode='begin')
    assert hist.find('BEGIN') > 0
    assert hist.endswith('+')


def test_history_end():
    hist = ph.history(test_history_end, mode='end')
    assert hist.find('END') > 0
    assert hist.endswith('-')


def test_history_function_name():
    hist = ph.history(test_history_function_name, mode='begin')
    assert hist.find('test_history_function_name') > 0


def test_data_is_unmodified_by_patch_headers():
    """No changes should be made to the data."""
    new_ext = '_new'
    ph.patch_headers(_test_dir, new_file_ext=new_ext)
    test_file_basename = path.splitext(_test_image_name)[0]
    fname = path.join(_test_dir, test_file_basename)
    fname_new = fname + new_ext
    orig = fits.open(fname + '.fit',
                     do_not_scale_image_data=True)
    modified = fits.open(fname_new + '.fit',
                         do_not_scale_image_data=True)
    assert np.all(orig[0].data == modified[0].data)


def test_writing_patched_files_to_directory():
    files = glob(path.join(_test_dir, '*.fit*'))
    n_files_init = len(glob(path.join(_test_dir, '*.fit*')))
    dest_dir = mkdtemp()
    ph.patch_headers(_test_dir, new_file_ext='', save_location=dest_dir)
    print files
    n_files_after = len(glob(path.join(_test_dir, '*.fit*')))
    print n_files_after
    n_files_destination = len(glob(path.join(dest_dir, '*.fit*')))
    print dest_dir
    rmtree(dest_dir)
    assert ((n_files_init == n_files_after) &
            (n_files_init == n_files_destination))


@pytest.mark.parametrize('data_source',
                         ['maximdl_5_21_header.fit',
                          'maximdl_5_23_header.fit'])
def test_purging_maximdl5_keywords(data_source):

    feder = Feder()
    mdl5_name = data_source
    copy(path.join(get_data_dir(), mdl5_name), _test_dir)
    hdr5 = fits.getheader(path.join(_test_dir, mdl5_name))

    software = ph.get_software_name(hdr5, use_observatory=feder)
    ph.purge_bad_keywords(hdr5, history=True, force=False)

    keyword_present = False
    for keyword in software.bad_keywords:
        keyword_present = (keyword_present or (keyword in hdr5))
    assert not keyword_present


@pytest.mark.parametrize('badkey', ['swcreate', 'instrume'])
def test_patch_headers_stops_if_instrument_or_software_not_found(badkey,
                                                                 caplog):
    ic = ImageFileCollection(_test_dir, keywords=['imagetyp'])
    a_fits_file = ic.files[0]
    a_fits_hdu = fits.open(path.join(_test_dir, a_fits_file))
    hdr = a_fits_hdu[0].header
    badname = 'Nonsense'
    hdr[badkey] = badname
    a_fits_hdu.writeto(path.join(_test_dir, a_fits_file), clobber=True)
    ph.patch_headers(_test_dir)
    patch_warnings = get_patch_header_warnings(caplog)
    assert('KeyError' in patch_warnings)
    assert(badname in patch_warnings)


def test_adding_overscan_apogee_u9():
    original_dir = getcwd()

    apogee = ApogeeAltaU9()
    print getcwd()
    oscan_dir, has_oscan, has_no_oscan = make_overscan_test_files(_test_dir)
    print getcwd()

    chdir(path.join(_test_dir, oscan_dir))
    ph.patch_headers(dir='.', new_file_ext='', overwrite=True, purge_bad=False,
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
        ph.change_imagetype_to_IRAF(header, history=False)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        # second call should NOT change imagetyp
        print header
        ph.change_imagetype_to_IRAF(header, history=True)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        with pytest.raises(KeyError):
            print header['history']
        # change imagetype back to non-IRAF
        header['imagetyp'] = im_type
        # change with history
        ph.change_imagetype_to_IRAF(header, history=True)
        assert('history' in header)


def test_data_is_unmodified_by_adding_object():
    new_ext = '_obj'
    ph.patch_headers(_test_dir, new_file_ext=new_ext)
    ph.add_object_info(_test_dir, new_file_ext=new_ext)
    test_file_basename = path.splitext(_test_image_name)[0]
    fname = path.join(_test_dir, test_file_basename)
    fname_new = fname + new_ext + new_ext
    orig = fits.open(fname + '.fit',
                     do_not_scale_image_data=True)
    modified = fits.open(fname_new + '.fit',
                         do_not_scale_image_data=True)
    assert np.all(orig[0].data == modified[0].data)


def test_adding_object_name(use_list=None,
                            use_obj_dir=None,
                            check_fits_file=None):
    """
    Test adding object name

    Provide `use_list` to override the default object file name.
    Provide `use_obj_dir` to specify directory in which the object file
    is found. Defaults to directory in which the images reside if
    `use_obj_dir` is None.
    """
    new_ext = '_obj_name_test'
    check_file = check_fits_file or path.splitext(_test_image_name)[0]
    ph.patch_headers(_test_dir, new_file_ext=new_ext)
    ph.add_object_info(_test_dir, new_file_ext=new_ext,
                       object_list=use_list, object_list_dir=use_obj_dir)
    fname = path.join(_test_dir, check_file)
    fname += new_ext + new_ext
    with_name = fits.open(fname + '.fit')
    print 'add object name: %s' % fname
    assert (with_name[0].header['object'] == 'm101')
    return with_name


@pytest.mark.usefixtures('object_file_no_ra')
def test_adding_object_from_name_only():
    if simbad_down:
        pytest.xfail("Simbad is down")
    try:
        test_adding_object_name()
    except (name_resolve.NameResolveError, timeout):
        pytest.xfail("Simbad is down")


def test_add_object_name_warns_if_no_match(caplog):
    test_adding_object_name()
    patch_header_warnings = get_patch_header_warnings(caplog)
    assert('No object found for image ' in patch_header_warnings)


def test_adding_object_name_to_different_directory(use_list=None,
                                                   use_obj_dir=None):
    new_ext = '_obj_name_test'
    ph.patch_headers(_test_dir, new_file_ext=new_ext)
    destination_dir = mkdtemp()
    ph.add_object_info(_test_dir, new_file_ext=new_ext,
                       save_location=destination_dir,
                       object_list=use_list, object_list_dir=use_obj_dir)
    test_file_basename = path.splitext(_test_image_name)[0]
    fname = path.join(destination_dir, test_file_basename)
    fname += new_ext + new_ext
    with_name = fits.open(fname + '.fit')
    print 'add object name: %s' % fname
    assert (with_name[0].header['object'] == 'm101')
    return with_name


def test_add_object_name_uses_object_list_name():

    custom_object_name = 'my_object_list.txt'
    old_object_path = path.join(_test_dir, _default_object_file_name)
    new_path = path.join(_test_dir, custom_object_name)
    move(old_object_path, new_path)
    fits_with_obj_name = test_adding_object_name(use_list=custom_object_name)
    # The line below is probably not really necessary since the same test
    # is done in test_adding_object_name but it doesn't hurt to test it
    # here too
    assert (fits_with_obj_name[0].header['object'] == 'm101')


def test_add_object_name_with_custom_dir_standard_name():

    a_temp_dir = mkdtemp()

    old_object_path = path.join(_test_dir, _default_object_file_name)
    new_path = path.join(a_temp_dir, _default_object_file_name)
    move(old_object_path, new_path)
    test_adding_object_name(use_obj_dir=a_temp_dir)


def test_add_object_name_uses_object_list_dir():

    a_temp_dir = mkdtemp()

    custom_object_name = 'my_object_list.txt'
    old_object_path = path.join(_test_dir, _default_object_file_name)
    new_path = path.join(a_temp_dir, custom_object_name)
    move(old_object_path, new_path)
    # first make sure object name isn't added if object list can't be found
    with pytest.raises(IOError):
        test_adding_object_name(use_list=custom_object_name)

    # Now make sure it works when we specify the directory; need to redo
    # setup to clear out files made in pass above
    setup_function(test_add_object_name_uses_object_list_dir)
    test_adding_object_name(use_list=custom_object_name,
                            use_obj_dir=a_temp_dir)


def test_ambiguous_object_file_raises_error():
    a_temp_dir = mkdtemp()
    obj_name = 'bad_list.txt'
    obj_path = path.join(a_temp_dir, obj_name)
    object_in = 'ey uma'
    RA_in = "09:02:20.76"
    Dec_in = "+49:49:09.3"
    to_write = 'object, RA, Dec\n{},{},{}\n'.format(object_in, RA_in, Dec_in)
    to_write += '{},{},{}\n'.format('crap', RA_in, Dec_in)
    object_file = open(obj_path, 'wb')
    object_file.write(to_write)
    object_file.close()
    with pytest.raises(RuntimeError):
        test_adding_object_name(use_list=obj_name, use_obj_dir=a_temp_dir)


def test_missing_object_file_issues_warning(caplog):
    remove(path.join(_test_dir, _default_object_file_name))
    ph.add_object_info(_test_dir)
    patch_header_warnings = get_patch_header_warnings(caplog)
    assert 'No object list in directory' in patch_header_warnings


def test_no_object_match_for_image_warning_includes_file_name(caplog):
    remove(path.join(_test_dir, _default_object_file_name))
    to_write = '# comment 1\n# comment 2\nobject,RA,Dec\nsz lyn,8:09:35.75,+44:28:17.59'
    object_file = open(path.join(_test_dir, _default_object_file_name), 'wb')
    object_file.write(to_write)
    object_file.close()
    ph.patch_headers(_test_dir, new_file_ext='', overwrite=True)
    ph.add_object_info(_test_dir)
    patch_header_warnings = get_patch_header_warnings(caplog)
    assert 'No object found' in patch_header_warnings
    assert _test_image_name in patch_header_warnings


def test_add_ra_dec_from_object_name():
    if simbad_down:
        pytest.xfail("Simbad is down")
    full_path = path.join(_test_dir, _test_image_name)
    f = fits.open(full_path, do_not_scale_image_data=True)
    h = f[0].header
    del h['OBJCTRA']
    del h['OBJCTDEC']
    h['OBJECT'] = 'M101'
    with warnings.catch_warnings():
        ignore_from = 'astropy.io.fits.hdu.hdulist'
        warnings.filterwarnings('ignore', module=ignore_from)
        f.writeto(full_path, clobber=True)
    f.close()

    try:
        ph.add_ra_dec_from_object_name(_test_dir, new_file_ext='')
    except (name_resolve.NameResolveError, timeout):
        pytest.xfail("Simbad is down")

    f = fits.open(full_path, do_not_scale_image_data=True)
    h = f[0].header
    m101_ra_dec_correct = FK5('14h03m12.58s +54d20m55.50s')
    header_m101 = FK5(ra=h['ra'], dec=h['dec'],
                      unit=(u.hour, u.degree))

    assert_almost_equal(m101_ra_dec_correct.ra.hour,
                        header_m101.ra.hour)
    assert_almost_equal(m101_ra_dec_correct.dec.degree,
                        header_m101.dec.degree)


def get_patch_header_warnings(log):
    patch_header_warnings = []
    for record in log.records():
        if (('patchers' in record.name) and (record.levelno ==
                                             logging.WARN)):

            patch_header_warnings.append(record.message)

    patch_headers_message_text = '\n'.join(patch_header_warnings)
    return patch_headers_message_text


def test_times_apparent_pos_added():
    # the correct value below is from the USNO JD calculator using the UT
    # of the start of the observation in the file uint16.fit, which is
    # 2012-06-05T04:17:00
    JD_correct = 2456083.678472222
    # The "correct" values below are from converting the RA/Dec in uint16 to
    # decimal hours/degrees
    RA_correct = 14.054166667  # hours
    Dec_correct = 54.351111111  # degrees

    # Get the "correct" LST from astropysics and assume that that is correct
    f = FederSite()
    f.currentobsjd = JD_correct
    LST_astropysics = f.localSiderialTime()

    HA_correct = LST_astropysics - RA_correct

    ph.patch_headers(_test_dir, new_file_ext='', overwrite=True)
    header = fits.getheader(path.join(_test_dir, _test_image_name))

    # check Julian Date
    assert_almost_equal(header['JD-OBS'], JD_correct)

    # calculate then check LST
    h, m, s = header['LST'].split(':')
    header_lst = int(h) + int(m)/60. + float(s)/3600.

    assert_almost_equal(header_lst, LST_astropysics, decimal=5)

    # calculate then check HA
    h, m, s = header['HA'].split(':')
    header_HA = int(h) + int(m)/60. + float(s)/3600.

    assert_almost_equal(HA_correct, header_HA)

    # calculate, then check, altitude
    latitude = f.latitude.radians  # this is an astropysics object--has radians
    Dec_a = Angle(Dec_correct, unit=u.degree)
    HA_a = Angle(HA_correct, unit=u.hour)
    sin_alt = (np.sin(latitude) * np.sin(Dec_a.radian) +
               (np.cos(latitude) * np.cos(Dec_a.radian) *
                np.cos(HA_a.radian)))
    alt = Angle(np.arcsin(sin_alt), unit=u.radian)
    header_alt = header['alt-obj']
    assert_almost_equal(alt.degree, header_alt, decimal=5)

    # calculate, then check, airmass
    zenith_angle = Angle(90 - alt.degree, unit=u.degree)
    airmass_correct = 1/np.cos(zenith_angle.radian)
    assert_almost_equal(airmass_correct, header['airmass'], decimal=3)


@pytest.fixture(params=['object', 'OBJECT', 'Object'])
def object_file_no_ra(request):
    to_write = '# comment 1\n# comment 2\n' + request.param + '\ney uma\nm101'
    object_file = open(path.join(_test_dir, _default_object_file_name), 'wb')
    object_file.write(to_write)
    object_file.close()


def object_file_with_ra_dec(dir):
    objs = ["ey uma, 09:02:20.76, +49:49:09.3",
            "m101,14:03:12.58,+54:20:55.50"
    ]
    to_write = '# comment 1\n# comment 2\nobject, RA, Dec\n' + '\n'.join(objs)
    object_file = open(path.join(dir, _default_object_file_name), 'wb')
    object_file.write(to_write)
    object_file.close()


def setup_module(module):
    global simbad_down

    try:
        foo = FK5.from_name("m101")
    except (name_resolve.NameResolveError, timeout):
        simbad_down = True


def setup_function(function):
    global _test_dir
    global _test_image_name

    _test_dir = path.join(mkdtemp(), 'data')
    data_source = get_data_dir()
    print data_source
    copytree(data_source, _test_dir)
    object_file_with_ra_dec(_test_dir)


def teardown_function(function):
    global _test_dir
    rmtree(_test_dir)
