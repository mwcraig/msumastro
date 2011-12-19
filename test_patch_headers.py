from patch_headers import *

test_tuple = (1,2,3.1415)
def test_sexagesimal_string():
    assert sexagesimal_string(test_tuple) == '01:02:03.14'

def test_sexagesimal_string_with_sign():
    assert sexagesimal_string(test_tuple, sign=True) == '+01:02:03.14'

def test_sexagesimal_string_with_precision():
    assert sexagesimal_string(test_tuple, precision=3) == '01:02:03.142'

def test_sexagesimal_string_with_precision_and_sign():
    assert sexagesimal_string(test_tuple, sign=True, precision=3) == '+01:02:03.142'
    