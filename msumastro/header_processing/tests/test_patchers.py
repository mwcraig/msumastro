from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from os import path, chdir, getcwd, remove
from shutil import rmtree, copy, copytree, move
from tempfile import mkdtemp
from glob import glob
import warnings
import logging
from socket import timeout

import pytest
import numpy as np
from numpy.testing import assert_almost_equal, assert_allclose
from astropy.io import fits
from astropy.coordinates import Angle, name_resolve, SkyCoord
from astropy import units as u
from astropy.table import Table
from astropy.extern import six
from astropy.time import Time

from .. import patchers as ph
from ..feder import Feder, ApogeeAltaU9, FederSite
from ...tests.data import get_data_dir
from ... import ImageFileCollection

_test_dir = ''
_default_object_file_name = 'obsinfo.txt'
_test_image_name = 'uint16.fit'
simbad_down = False
OBJECT_LIST_URL = 'https://raw.github.com/mwcraig/feder-object-list/master/feder_object_list.csv'


@pytest.mark.usefixtures('object_file_no_ra')
def test_read_object_list():
    objects, ra_dec = ph.read_object_list(directory=_test_dir,
                                          skip_lookup_from_object_name=True)
    assert len(objects) == 2
    assert objects[0] == 'ey uma'
    assert objects[1] == 'm101'
    assert not ra_dec


def test_read_object_list_ra_dec():
    temp_dir = mkdtemp()
    obj_name = 'objects_with_ra.txt'
    object_path = path.join(temp_dir, obj_name)
    object_in = 'ey uma'
    RA_in = "09:02:20.76"
    Dec_in = "+49:49:09.3"
    to_write = 'object, RA, Dec\n{},{},{}'.format(object_in, RA_in, Dec_in)
    object_file = open(object_path, 'wt')
    object_file.write(to_write)
    object_file.close()
    obj, ra_dec = ph.read_object_list(temp_dir, obj_name)
    assert(obj[0] == object_in)
    ra_dec_in = SkyCoord(RA_in, Dec_in, unit=(u.hour, u.degree), frame='fk5')
    assert ra_dec_in.separation(ra_dec[0]).arcsec < 1e-4


def test_read_object_list_from_internet():
    try:
        obj, ra_dec = ph.read_object_list(directory='',
                                          input_list=OBJECT_LIST_URL)
    except six.moves.urllib.error.URLError:
        pytest.xfail("Unable to open URL")
    assert 'ey uma' in obj


def test_read_object_list_with_skip_consistency_skip_lookup():
    # this is bad because there is an identical entry
    bad_objects = [
        "ey uma, 09:02:20.76, +49:49:09.3",
        "ey uma, 09:02:20.76, +49:49:09.3"
    ]
    object_file_with_ra_dec(_test_dir, input_objects=bad_objects)
    objects, ra_dec = ph.read_object_list(_test_dir,
                                          skip_lookup_from_object_name=True,
                                          skip_consistency_check=True)
    for obj in objects:
        assert obj == "ey uma"
    assert len(ra_dec) == 2


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
    print(files)
    n_files_after = len(glob(path.join(_test_dir, '*.fit*')))
    print(n_files_after)
    n_files_destination = len(glob(path.join(dest_dir, '*.fit*')))
    print(dest_dir)
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
    # need a header that contains IMAGETYP so that it will be processed
    a_fits_file = ''
    for h, f in ic.headers(imagetyp='*', return_fname=True):
        a_fits_file = f
        break
    a_fits_hdu = fits.open(path.join(_test_dir, a_fits_file))
    hdr = a_fits_hdu[0].header
    badname = 'Nonsense'
    hdr[badkey] = badname
    a_fits_hdu.writeto(path.join(_test_dir, a_fits_file), clobber=True)
    ph.patch_headers(_test_dir)
    patch_warnings = get_patch_header_logs(caplog)
    assert('KeyError' in patch_warnings)
    assert(badname in patch_warnings)


def test_adding_overscan_apogee_u9(make_overscan_test_files):
    original_dir = getcwd()

    apogee = ApogeeAltaU9()
    print(getcwd())
    oscan_dir, has_oscan, has_no_oscan = make_overscan_test_files
    print(getcwd())

    chdir(path.join(_test_dir, oscan_dir))
    # first, does requesting *not* adding overscan actually leave it alone?
    ph.patch_headers(dir='.', new_file_ext='', overwrite=True, purge_bad=False,
                     add_time=False, add_apparent_pos=False,
                     add_overscan=False, fix_imagetype=False)
    header_no_oscan = fits.getheader(has_no_oscan)
    assert 'biassec' not in header_no_oscan
    assert 'trimsec' not in header_no_oscan

    # Now add overscan
    ph.patch_headers(dir='.', new_file_ext='', overwrite=True, purge_bad=False,
                     add_time=False, add_apparent_pos=False,
                     add_overscan=True, fix_imagetype=False)
    print(_test_dir)
    header_no_oscan = fits.getheader(has_no_oscan)
    # This image had no overscan, so should be missing the relevant keywords.
    assert 'biassec' not in header_no_oscan
    assert 'trimsec' not in header_no_oscan
    header_yes_oscan = fits.getheader(has_oscan)
    # This one as overscan, so should include both of the overscan keywords.
    assert header_yes_oscan['biassec'] == apogee.useful_overscan
    assert header_yes_oscan['trimsec'] == apogee.trim_region
    print(getcwd())
    chdir(original_dir)
    print(getcwd())


def test_fix_imagetype():
    imagetypes_to_check = {'Bias Frame': 'BIAS',
                           'Dark Frame': 'DARK',
                           'Light Frame': 'LIGHT',
                           'Flat Frame': 'FLAT'}
    for im_type in imagetypes_to_check:
        header = fits.Header()

        header['imagetyp'] = im_type
        # first run SHOULD change imagetyp
        print(header)
        ph.change_imagetype_to_IRAF(header, history=False)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        # second call should NOT change imagetyp
        print(header)
        ph.change_imagetype_to_IRAF(header, history=True)
        assert(header['imagetyp'] == imagetypes_to_check[im_type])
        with pytest.raises(KeyError):
            print(header['history'])
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
    print('add object name: %s' % fname)
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


@pytest.mark.usefixtures('object_file_ra_change_col_case')
def test_adding_object_name_does_not_depend_on_column_name_case():
    test_adding_object_name()


def test_add_object_name_warns_if_no_match(caplog):
    test_adding_object_name()
    patch_header_warnings = get_patch_header_logs(caplog)
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
    print('add object name: %s' % fname)
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
    object_file = open(obj_path, 'wt')
    object_file.write(to_write)
    object_file.close()
    with pytest.raises(RuntimeError):
        test_adding_object_name(use_list=obj_name, use_obj_dir=a_temp_dir)


def test_missing_object_file_issues_warning(caplog):
    remove(path.join(_test_dir, _default_object_file_name))
    ph.add_object_info(_test_dir)
    patch_header_warnings = get_patch_header_logs(caplog)
    assert 'No object list in directory' in patch_header_warnings


def test_no_object_match_for_image_warning_includes_file_name(caplog):
    remove(path.join(_test_dir, _default_object_file_name))
    to_write = ('# comment 1\n# comment 2\nobject,RA,Dec\n'
                'sz lyn,8:09:35.75,+44:28:17.59')
    object_file = open(path.join(_test_dir, _default_object_file_name), 'wt')
    object_file.write(to_write)
    object_file.close()
    ph.patch_headers(_test_dir, new_file_ext='', overwrite=True)
    ph.add_object_info(_test_dir)
    patch_header_warnings = get_patch_header_logs(caplog)
    assert 'No object found' in patch_header_warnings
    assert _test_image_name in patch_header_warnings


def test_missing_object_column_raises_error():
    object_path = path.join(_test_dir, _default_object_file_name)
    object_table = Table.read(object_path, format='ascii')
    object_table.rename_column('object', 'BADBADBAD')
    object_table.write(object_path, format='ascii')
    with pytest.raises(RuntimeError):
        ph.read_object_list(directory=_test_dir,
                            input_list=_default_object_file_name)


@pytest.mark.usefixtures('object_file_no_ra')
def test_read_object_list_logs_error_if_object_on_list_not_found(caplog):
    if simbad_down:
        pytest.xfail('Simbad is down')
    object_path = path.join(_test_dir, _default_object_file_name)
    object_table = Table.read(object_path, format='ascii',
                              comment='#', delimiter=',')
    object_table.add_row(['not_a_simbad_object'])
    object_table.write(object_path, format='ascii')
    with pytest.raises(name_resolve.NameResolveError):
        ph.read_object_list(_test_dir)
    errs = get_patch_header_logs(caplog, level=logging.ERROR)
    assert 'Unable to do lookup' in errs
    ph.add_object_info(_test_dir)
    errs = get_patch_header_logs(caplog, level=logging.ERROR)
    assert 'Unable to add objects--name resolve error' in errs


def test_add_object_name_logic_when_all_images_have_matching_object(caplog):
    ic = ImageFileCollection(_test_dir, keywords=['imagetyp'])
    for h in ic.headers(imagetyp='light', overwrite=True):
        h['imagetyp'] = 'FLAT'
    ph.add_object_info(_test_dir)
    infos = get_patch_header_logs(caplog, level=logging.INFO)
    assert 'NO OBJECTS MATCHED' in infos


@pytest.mark.parametrize('new_file_ext',
                         ['', None])
def test_add_ra_dec_from_object_name(new_file_ext):
    if simbad_down:
        pytest.xfail("Simbad is down")
    full_path = path.join(_test_dir, _test_image_name)
    f = fits.open(full_path, do_not_scale_image_data=True)
    h = f[0].header

    try:
        del h['OBJCTRA']
        del h['OBJCTDEC']
    except KeyError:
        pass

    h['OBJECT'] = 'M101'
    with warnings.catch_warnings():
        ignore_from = 'astropy.io.fits.hdu.hdulist'
        warnings.filterwarnings('ignore', module=ignore_from)
        f.writeto(full_path, clobber=True)
    f.close()

    try:
        ph.add_ra_dec_from_object_name(_test_dir, new_file_ext=new_file_ext,
                                       object_list_dir=_test_dir)
    except (name_resolve.NameResolveError, timeout):
        pytest.xfail("Simbad is down")

    base, ext = path.splitext(full_path)
    if new_file_ext is None:
        new_ext = 'new'  # this is the default value...
    else:
        new_ext = new_file_ext
    new_path = base + new_ext + ext
    f = fits.open(new_path, do_not_scale_image_data=True)
    h = f[0].header
    m101_ra_dec_correct = SkyCoord('14h03m12.58s +54d20m55.50s', frame='icrs')
    header_m101 = SkyCoord(ra=h['ra'], dec=h['dec'],
                           unit=(u.hour, u.degree), frame='icrs')

    assert_allclose(m101_ra_dec_correct.ra.hour,
                    header_m101.ra.hour, rtol=1e-5)
    assert_allclose(m101_ra_dec_correct.dec.degree,
                    header_m101.dec.degree, rtol=1e-5)


def test_add_ra_dec_from_object_name_edge_cases(caplog):
    # add a 'dec' keyword to every light file so that none need RA/Dec
    ic = ImageFileCollection(_test_dir, keywords=['imagetyp'])
    for h in ic.headers(imagetyp='light', overwrite=True):
        h['dec'] = '+17:42:00'
        h['ra'] = '03:45:06'
        h['object'] = 'm101'
    # does this succeed without errors?
    ph.add_ra_dec_from_object_name(_test_dir)

    # add name that will fail as object of one image
    image_path = path.join(_test_dir, _test_image_name)
    f = fits.open(image_path)
    h = f[0].header

    try:
        del h['RA']
        del h['dec']
    except KeyError:
        pass

    h['object'] = 'i am a fake object'
    f.writeto(image_path, clobber=True)
    ph.add_ra_dec_from_object_name(_test_dir)
    warns = get_patch_header_logs(caplog, level=logging.WARN)
    assert 'Unable to lookup' in warns


def get_patch_header_logs(log, level=logging.WARN):
    patch_header_warnings = []
    for record in log.records():
        if (('patchers' in record.name) and (record.levelno ==
                                             level)):

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
    RA_2012_5 = 14.061475336  # hours, from astropy
    Dec_correct = 54.351111111  # degrees
    Dec_2012_5 = 54.29181012  # degrees, from astropy
    # Got the "correct" LST from astropy
    LST = 14.78635133  # hours

    HA_correct = LST - RA_correct

    ph.patch_headers(_test_dir, new_file_ext='', overwrite=True)
    header = fits.getheader(path.join(_test_dir, _test_image_name))

    # check Julian Date
    assert_almost_equal(header['JD-OBS'], JD_correct)

    # calculate then check LST
    h, m, s = header['LST'].split(':')
    header_lst = int(h) + int(m)/60. + float(s)/3600.

    assert_almost_equal(header_lst, LST, decimal=7)

    # calculate then check HA
    h, m, s = header['HA'].split(':')
    header_HA = int(h) + int(m)/60. + float(s)/3600.

    assert_almost_equal(HA_correct, header_HA, decimal=7)

    print(header['MJD-OBS'])
    # calculate, then check, altitude
    f = FederSite()
    latitude = f.latitude.radian
    Dec_a = Angle(Dec_2012_5, unit=u.degree)
    HA_a = Angle(LST - RA_2012_5, unit=u.hour)
    sin_alt = (np.sin(latitude) * np.sin(Dec_a.radian) +
               (np.cos(latitude) * np.cos(Dec_a.radian) *
                np.cos(HA_a.radian)))
    alt = Angle(np.arcsin(sin_alt), unit=u.radian)
    header_alt = header['alt-obj']

    # ONLY CHECKING TWO DECIMAL PLACES SEEMS AWFUL!!!
    assert_almost_equal(alt.degree, header_alt, decimal=2)

    # calculate, then check, airmass
    zenith_angle = Angle(90 - alt.degree, unit=u.degree)
    airmass_correct = 1/np.cos(zenith_angle.radian)
    assert_almost_equal(airmass_correct, header['airmass'], decimal=3)


def test_add_object_pos_airmass_raises_error_when_it_should():
    feder = Feder()
    header = fits.Header()
    # make sure the JD_OBS really has the desired value for this test...
    assert feder.JD_OBS.value is None
    # have not set JD_OBS, do we raise the appropriate error?
    with pytest.raises(ValueError):
        ph.add_object_pos_airmass(header)
    # No significance to the value below, but need to set it to something...
    feder.JD_OBS.value = 2456490
    with pytest.raises(ValueError):
        ph.add_object_pos_airmass(header)


def test_purge_handles_all_software():
    ic = ImageFileCollection(_test_dir, keywords=['imagetyp'])
    for h in ic.headers():
        ph.purge_bad_keywords(h)
        assert 'purged' in h


def test_purge_bad_keywords_logic_for_conditionals(caplog):
    ic = ImageFileCollection(_test_dir, keywords=['imagetyp'])
    headers = [h for h in ic.headers()]
    a_header = headers[0]
    # should be no warnings the first time...
    ph.purge_bad_keywords(a_header)
    purge_warnings = get_patch_header_logs(caplog)
    assert not purge_warnings
    # re-purging should generate warnings...
    ph.purge_bad_keywords(a_header)
    purge_warnings = get_patch_header_logs(caplog)
    assert 'force' in purge_warnings
    assert 'removing' in purge_warnings
    # grab a clean header
    # want to get to a header with more than one bad keyword so that a
    # history is generated...
    for a_header in headers[1:]:
        software = ph.get_software_name(a_header)
        if len(software.bad_keywords) <= 1:
            continue
        else:
            break
    # delete one of the purge keywords for this software, which should ensure
    # that their is no history added to the header that contains the name of
    # this keyword
    key_to_delete = software.bad_keywords[0]
    print(software.bad_keywords)
    try:
        del a_header[key_to_delete]
    except KeyError:
        pass

    print(a_header)
    ph.purge_bad_keywords(a_header, history=True)
    print(a_header)
    assert all(key_to_delete.lower() not in h.lower()
               for h in a_header['HISTORY'])


def test_unit_is_added():
    # patch in _test_dir, overwriting existing files
    ph.patch_headers(_test_dir, overwrite=True, new_file_ext='')
    ic = ImageFileCollection(_test_dir, keywords='*')
    feder = Feder()
    print(_test_dir)
    for h, f in ic.headers(return_fname=True):
        instrument = feder.instruments[h['instrume']]
        if instrument.image_unit is not None:
            print(str(instrument.image_unit), f)
            # If the instrument has a unit, the header should too.
            assert h['BUNIT'] == str(instrument.image_unit)


def test_lst_in_future():
    header = fits.Header()
    future = Time.now() + 1 * u.year
    header['date-obs'] = future.isot
    ph.add_time_info(header)


@pytest.fixture(params=['object', 'OBJECT', 'Object'])
def object_file_ra_change_col_case(request):
    object_file_with_ra_dec(_test_dir, object_col_name=request.param)


@pytest.fixture
def object_file_no_ra(request):
    try:
        object_col_name = request.param
    except AttributeError:
        object_col_name = 'object'
    to_write = ('# comment 1\n# comment 2\n' + object_col_name +
                '\ney uma\nm101\n')
    object_file = open(path.join(_test_dir, _default_object_file_name), 'wt')
    object_file.write(to_write)
    object_file.close()


def object_file_with_ra_dec(dir, object_col_name='object',
                            input_objects=None):
    if input_objects is None:
        objs = ["ey uma, 09:02:20.76, +49:49:09.3",
                "m101,14:03:12.58,+54:20:55.50"
                ]
    else:
        objs = list(input_objects)

    to_write = ('# comment 1\n# comment 2\n' + object_col_name +
                ', RA, Dec\n' + '\n'.join(objs))
    object_file = open(path.join(dir, _default_object_file_name), 'wt')
    object_file.write(to_write)
    object_file.close()


def setup_module(module):
    global simbad_down

    try:
        foo = SkyCoord.from_name("m101")
    except (name_resolve.NameResolveError, timeout):
        simbad_down = True


def setup_function(function):
    global _test_dir
    global _test_image_name

    _test_dir = path.join(mkdtemp(), 'data')
    data_source = get_data_dir()
    print(data_source)
    copytree(data_source, _test_dir)
    object_file_with_ra_dec(_test_dir)


def teardown_function(function):
    global _test_dir
    rmtree(_test_dir)
