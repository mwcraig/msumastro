from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import pytest

from ..feder import Feder, ApogeeAltaU9, ApogeeAspenCG16


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
