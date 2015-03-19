from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from ..feder import Feder, ApogeeAltaU9


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
