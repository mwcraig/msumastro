def make_overscan_test_files(test_dir):
    """
    Creates two files, one with overscan, one without for Alta U9

    Parameters

    test_dir: str
        Directory in which to create the overscan files.

    Returns

    info: list
        (working_dir, has_oscan, has_no_oscan)
        working_dir: str
            subdirectory of test_dir in which files are created
        has_oscan: str
            Name of FITS file that has overscan region
        has_no_oscan: str
            Name of FITS file that has no overscan region
    """
    from ...header_processing.feder import ApogeeAltaU9
    from os import path, mkdir, chdir, getcwd
    import astropy.io.fits as fits
    import numpy as np

    has_oscan = 'yes_oscan.fit'
    has_no_oscan = 'no_oscan.fit'
    apogee = ApogeeAltaU9()
    working_dir = 'overscan_test'
    original_dir = getcwd()
    mkdir(path.join(test_dir, working_dir))
    chdir(path.join(test_dir, working_dir))
    no_oscan = np.zeros([apogee.rows, apogee.overscan_start])
    add_instrument = lambda hdr: hdr.set('instrume', 'Apogee Alta')
    hdu = fits.PrimaryHDU(no_oscan)
    add_instrument(hdu.header)
    hdu.writeto(has_no_oscan)
    yes_oscan = np.zeros([apogee.rows, apogee.columns])
    hdu = fits.PrimaryHDU(yes_oscan)
    add_instrument(hdu.header)
    hdu.writeto(has_oscan)
    chdir(test_dir)
    chdir(original_dir)
    return (working_dir, has_oscan, has_no_oscan)
