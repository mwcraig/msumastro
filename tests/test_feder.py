from ..feder import *
from astropysics.obstools import calendar_to_jd

# def test_localSiderialTime():
#    feder_site = FederSite()
#    feder_site.currentobsjd = calendar_to_jd((2000, 1, 1, 5, 13, 0.4))
#    lst = feder_site.localSiderialTime(returntype='datetime')
#    assert 1


def test_apogee_has_overscan():
    feder_obj = Feder()
    assert (feder_obj.instrument["Apogee Alta"].has_overscan([3085, 2048]))
    assert not (feder_obj.instrument["Apogee Alta"].has_overscan([3073, 2048]))


def test_apogee_fits_names():
    feder_obj = Feder()
    assert isinstance(feder_obj.instrument["Apogee Alta"],
                      ApogeeAltaU9)
    assert isinstance(feder_obj.instrument["Apogee USB/Net"],
                      ApogeeAltaU9)
