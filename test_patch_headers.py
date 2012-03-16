from patch_headers import *
from tempfile import mkdtemp
from os import path
from shutil import rmtree

test_tuple = (1,2,3.1415)
_test_dir = ''
def test_sexagesimal_string():
    assert sexagesimal_string(test_tuple) == '01:02:03.14'

def test_sexagesimal_string_with_sign():
    assert sexagesimal_string(test_tuple, sign=True) == '+01:02:03.14'

def test_sexagesimal_string_with_precision():
    assert sexagesimal_string(test_tuple, precision=3) == '01:02:03.142'

def test_sexagesimal_string_with_precision_and_sign():
    assert sexagesimal_string(test_tuple, sign=True, precision=3) == '+01:02:03.142'

def test_read_object_list():
    observer, objects = read_object_list(dir=_test_dir)
    assert len(objects) == 2
    assert objects[0] == 'ey uma'
    assert objects[1] == 'm101'
    assert observer == 'Ima Observer'
    
def setup():
    global _test_dir
    
    _test_dir = mkdtemp()
    to_write = '# comment 1\nIma Observer\n# comment 2\ney uma\nm101'
    object_file = open(path.join(_test_dir,'obsinfo.txt'),'wb')
    object_file.write(to_write)

def teardown():
    global _test_dir
    rmtree(_test_dir)
