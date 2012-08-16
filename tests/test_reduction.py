from ..image_collection import ImageFileCollection
import numpy as np
from tempfile import mkdtemp
test_dir = ''
    
def setup():
    global test_dir
    from shutil import copytree
    from os import path
    test_dir = path.join(mkdtemp(),"data")
    copytree('data', test_dir)

def teardown():
    from shutil import rmtree

    rmtree(test_dir)
    