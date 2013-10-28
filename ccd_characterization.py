import logging

import numpy as np
try:
    import sherpa.ui as ui
except ImportError:
    pass

logger = logging.getLogger(__name__)


def ccd_dark_current(bias, dark, gain=1.0, average_dark=False):
    """
    Calculate the average dark current given bias and dark frames.

    `bias` should be either a single bias array or a numpy array of arrays. A
    list will be combined before subtraction from the dark.
    `dark` should be either a single dark array or a numpy array of arrays.
    `gain` is the gain of the CCD.
    `average_dark` should be `True` if the return value should be the
    average of the dark currents form the individual frames.

    Returns the current in electrons/pixel
    """
    if len(bias.shape) == 3:
        average_bias = bias.mean(axis=0)
    else:
        average_bias = bias

    if not isinstance(dark, np.ndarray):
        dark = np.array(dark)
    if len(dark.shape) == 2:
        dark_array = np.array([dark])
    else:
        dark_array = dark

    working_dark = np.zeros(dark_array.shape[1:2])
    dark_current = np.zeros(dark_array.shape[0])
    for i in range(0, dark_array.shape[0]):
        working_dark = dark_array[i, :, :] - average_bias
        dark_current[i] = gain * working_dark.mean()

    if average_dark:
        dark_current = dark_current.mean()
    return dark_current


def ccd_bias(bias):
    """
    Calculate the mean and width of a gaussian fit to the bias
    histogram.

    `bias` is a numpy array.
    """
    values, bins = np.histogram(bias,
                                bins=np.arange(bias.min(), bias.max() + 1))
    ui.load_arrays(1, bins[:-1], values)
    ui.set_model(ui.gauss1d.g1)
    g1.pos = bias.mean()
    g1.fwhm = bias.std()
    ui.fit()
    return g1


def ccd_read_noise(bias, gain=None, flat=None):
    """
    Calculate CCD read noise.

    `bias` is a tuple or list of bias frames as numpy arrays.
    `gain` should be set to CCD gain.
    `flat`, if set, should be a pair of flat frames. It is used only
    to calculate the gain, and is ignored if `gain` is set.

    Either `gain` or `flat` *must* be set.

    Returns the read noise, calculated using the formula on p. 73 of the
    *Handbook of CCD Astronomy* by Steve Howell.
    """
    if gain is None:
        if flat is None:
            raise ValueError('Must specify either gain or flat frames.')
        gain = ccd_gain(bias, flat)

    return gain / np.sqrt(2) * (bias[0] - bias[1]).std()


def ccd_gain(bias, flat):
    """
    Calculate CCD gain from pair of bias and pair of flat frames.

    `bias` is a tuple or list of two bias frames as arrays.

    `flat` is a tuple or list of tywo flat frams as arrays.

    `bias` and `flat` should have the same shape.

    Returns the gain, calculated using the formula on p. 73 of the
    *Handbook of CCD Astronomy* by Steve Howell.
    """

    if len(bias) != 2 or len(flat) != 2:
        raise ValueError(
            'bias and flat must each be two element tuple or list')

    b1 = bias[0]
    b2 = bias[1]
    f1 = flat[0]
    f2 = flat[1]

    gain = (((f1.mean() + f2.mean()) - (b1.mean() + b2.mean())) /
            ((f1 - f2).var() - (b1 - b2).var()))
    return gain
