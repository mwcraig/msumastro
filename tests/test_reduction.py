from ..image_collection import ImageFileCollection
import numpy as np
from tempfile import mkdtemp
test_dir = ''
from ..master_bias_dark import master_bias_dark
from ..master_flat import master_flat
    
def setup():
    global test_dir
    from shutil import copytree
    from os import path
    test_dir = path.join(mkdtemp(),"data")
    copytree('data', test_dir)

def teardown():
    from shutil import rmtree

    rmtree(test_dir)

def test_bias():
    coll = ImageFileCollection(test_dir, keywords = ['imagetyp'])
    all_data = []
    for hdu in coll.hdus(imagetyp='bias',do_not_scale_image_data=False):
        all_data.append(hdu.data)
    all_data = np.array(all_data)
    admean = np.mean(all_data, axis = 0)
    admed = np.median(all_data, axis = 0)
    mbd = master_bias_dark([test_dir], type = 'bias')
    assert((mbd == admed).all())
    assert(not((mbd == admean).all()) )

def test_dark():
    coll = ImageFileCollection(test_dir, keywords = ['imagetyp', 'exptime'])
    all_data = []
    for hdu in coll.hdus(imagetyp='dark'):
        all_data.append(hdu.data)
    all_data = np.array(all_data)
    admean = np.mean(all_data, axis = 0)
    admed = np.median(all_data, axis = 0)
    mbd = master_bias_dark([test_dir], type = 'dark')
    assert(mbd == admed)
    assert(mbd != admean)

def test_flat():
    coll = ImageFileCollection(test_dir, keywords = ['imagetyp', 'exptime', 'filter'])
    all_data = []
    for hdu in coll.hdus(imagetyp='flat'):
        all_data.append(hdu.data)
    all_data = np.array(all_data)
    admean = np.mean(all_data, axis = 0)
    admed = np.median(all_data, axis = 0)
    mf = master_flat(test_dir)
    assert(mf == admed)
    assert(mf != admean)
