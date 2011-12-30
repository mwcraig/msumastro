from numpy import random, array, sqrt, log
from ccd_characterization import *
bias = []
dark = []
dark_current = 1.0
bias_level = 3000.
bias_width = 1.

def test_ccd_dark_current():
    print ccd_dark_current(bias, dark, gain=1.5)
    print (ccd_dark_current(bias, dark, gain=1.5) - 1.5*dark_current)
    assert abs((ccd_dark_current(bias, dark, gain=1.5) - 1.5*dark_current).max()) < 1e-2
    assert abs(ccd_dark_current(bias, dark, gain=1.5, average_dark=True) -1.5*dark_current)<1e-2                        
def test_ccd_bias():
    gaussian = ccd_bias(bias[0])
    fwhm_expected = 2*sqrt(2*log(2))*bias_width
    assert abs(round((gaussian.pos.val-bias_level)/bias_level,3)) == 0
    assert abs(round((gaussian.fwhm.val-fwhm_expected)/fwhm_expected,1)) == 0
    
def setup():
    global bias, dark, dark_current
    n_frames = 3
    shape = (1000, 1000)
    for i in range(1, n_frames):
        bias.append(random.normal(loc=bias_level, scale=bias_width, size=shape))
        dark.append(random.normal(loc=dark_current,scale=0.01,size=shape)+
                    random.normal(loc=bias_level,scale=bias_width,size=shape))
    bias = array(bias)
    dark = array(dark)