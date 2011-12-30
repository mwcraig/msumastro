from numpy import random, array
from ccd_characterization import *
bias = []
dark = []
dark_current = 1.0

def test_ccd_dark_current():
    print ccd_dark_current(bias, dark, gain=1.5)
    print (ccd_dark_current(bias, dark, gain=1.5) - 1.5*dark_current)
    assert abs((ccd_dark_current(bias, dark, gain=1.5) - 1.5*dark_current).max()) < 1e-2
    assert abs(ccd_dark_current(bias, dark, gain=1.5, average_dark=True) -1.5*dark_current)<1e-2                        

def setup():
    global bias, dark, dark_current
    n_frames = 3
    shape = (1000, 1000)
    bias_level = 3000
    for i in range(1, n_frames):
        bias.append(random.normal(loc=bias_level, scale=1, size=shape))
        dark.append(random.normal(loc=dark_current,scale=0.01,size=shape)+
                    random.normal(loc=bias_level,scale=1,size=shape))
    bias = array(bias)
    dark = array(dark)