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
        raise ValueError('bias and flat must each be two element tuple or list')

    b1 = bias[0]
    b2 = bias[1]
    f1 = flat[0]
    f2 = flat[1]

    flat_diff = f1 - f2
    bias_diff = b1 - b2

    gain = (((f1.mean() + f2.mean()) - (b1.mean() + b2.mean())) /
            ((f1-f2).var() - (b1-b2).var()))
    return gain

    