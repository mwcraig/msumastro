from ..feder import Feder, ApogeeAltaU9

# def test_localSiderialTime():
#    feder_site = FederSite()
#    feder_site.currentobsjd = calendar_to_jd((2000, 1, 1, 5, 13, 0.4))
#    lst = feder_site.localSiderialTime(returntype='datetime')
#    assert 1


def test_apogee_has_overscan():
    feder_obj = Feder()
    apogee_alta = feder_obj.instruments["Apogee Alta"]
    assert (apogee_alta.has_overscan([3085, 2048]))
    assert not (apogee_alta.has_overscan([3073, 2048]))


def test_apogee_fits_names():
    feder_obj = Feder()
    assert isinstance(feder_obj.instruments["Apogee Alta"],
                      ApogeeAltaU9)
    assert isinstance(feder_obj.instruments["Apogee USB/Net"],
                      ApogeeAltaU9)
