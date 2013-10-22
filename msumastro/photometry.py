from __future__ import division

import logging

import numpy as np

logger = logging.getLogger(__name__)


def snr(flux, ap_rad_pix, sky_per_pix, gain=1.0, read_noise=0.0):
    npix = np.pi * ap_rad_pix ** 2
    return gain * flux / np.sqrt(gain * (flux + npix * sky_per_pix) +
                                 npix * sky_per_pix)


def mag_err(flux, ap_rad_pix, sky_per_pix, gain=1.0, read_noise=0.0):
    return 1.0857 / snr(flux, ap_rad_pix, sky_per_pix, gain=gain,
                        read_noise=read_noise)


def mag(flux, exposure_time, zero_point=0):
    return -2.5 * (np.log10(flux) - np.log10(exposure_time)) + zero_point
