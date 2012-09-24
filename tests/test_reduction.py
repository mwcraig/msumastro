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

    #rmtree(test_dir)

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
    coll = ImageFileCollection(test_dir, keywords = ['imagetyp'])
    all_data = []
    current = 300.0 #setting dark current
    expotime = 30.0 #setting exposure time
    for hdu in coll.hdus(imagetyp='bias', do_not_scale_image_data=False, save_with_name = 'dark'):
        hdu.header['exptime'] = expotime
        hdu.header['exposure'] = expotime
        hdu.header['imagetyp'] = 'DARK'
        hdu.data += current*expotime #dark current multiplied by exposure time added to bias frame
        all_data.append(hdu.data)
    all_data = np.array(all_data)
    admean = np.mean(all_data, axis = 0)
    admed = np.median(all_data, axis = 0)
    mbd = master_bias_dark([test_dir], type = 'dark')
    mb = master_bias_dark([test_dir], type = 'bias')
    assert((mbd == admed).all())
    assert(not((mbd == admean).all()) )
    assert((mbd == mb + current*expotime).all())

def nottest_flat():
    coll = ImageFileCollection(test_dir, keywords = ['imagetyp'])
    all_data = []
    flt = np.linspace(0.95,1.05,10000) #creates an array of values from 0.95 to 1.05
    np.reshape(flt,[100,100]) #reshapes the array to 100x100 to match other frames
    for hdu in coll.hdus(imagetyp='dark', do_not_scale_image_data = False, save_with_name = 'flat'):
        hdu.header['imagetyp'] = 'FLAT'
        hdu.data *= flt
        all_data.append(hdu.data)
    all_data = np.array(all_data)
    admean = np.mean(all_data, axis = 0)
    admed = np.median(all_data, axis = 0)
    mf = master_flat([test_dir])
    assert((mf == admed).all())
    assert((not(mf == admean).all()) )
