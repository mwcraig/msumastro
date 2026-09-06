import pytest

from ..feder import (Feder, ApogeeAltaU9, ApogeeAspenCG16, ImageSoftware,
                     MaximDL5, MaximDL6, MaximDL7)


def test_apogee_alta_has_overscan():
    feder_obj = Feder()
    apogee_alta = feder_obj.instruments["Apogee Alta"]
    assert (apogee_alta.has_overscan([3085, 2048]))
    assert not (apogee_alta.has_overscan([3073, 2048]))


def test_apogee_alta_fits_names():
    feder_obj = Feder()
    assert isinstance(feder_obj.instruments["Apogee Alta"],
                      ApogeeAltaU9)
    assert isinstance(feder_obj.instruments["Apogee USB/Net"],
                      ApogeeAltaU9)


def test_apogee_aspen_has_overscan():
    feder_obj = Feder()
    apogee_aspen = feder_obj.instruments['Apogee Aspen CG16M']
    assert apogee_aspen.has_overscan([4109, 4096])
    assert not apogee_aspen.has_overscan([4096, 4096])


def test_apogee_aspen_fits_names():
    feder_obj = Feder()
    assert isinstance(feder_obj.instruments["Apogee Aspen CG16M"],
                      ApogeeAspenCG16)


@pytest.mark.parametrize('instrument',
                         ["SBIG ST-7", "Celestron Nightscape 10100"])
def test_sbig_celestron_has_no_overscan(instrument):
    feder_obj = Feder()
    assert not feder_obj.instruments[instrument].has_overscan([])


def test_all_image_software_subclasses_are_registered():
    feder_obj = Feder()
    for cls in ImageSoftware.__subclasses__():
        instance = cls()
        for name in instance.fits_name:
            assert name in feder_obj.software
            assert isinstance(feder_obj.software[name], cls)


def test_maximdl7_registered():
    feder_obj = Feder()
    swname = 'MaxIm DL Version 7.1.4.0 260709 07593'
    assert isinstance(feder_obj.software[swname], MaximDL7)


@pytest.mark.parametrize('swname,cls', [
    ('MaxIm DL Version 5.14', MaximDL5),
    ('MaxIm DL Version 6.50 240628 2HVXS', MaximDL6),
])
def test_maximdl_versions_seen_at_feder_registered(swname, cls):
    feder_obj = Feder()
    assert isinstance(feder_obj.software[swname], cls)
