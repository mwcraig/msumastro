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
    from ...header_processing.feder import ApogeeAltaU9, MaximDL5
    from os import path, mkdir
    import astropy.io.fits as fits
    import numpy as np

    oscan_names = ['yes_scan', 'no_scan']
    oscan = {'yes_scan': True,
             'no_scan': False}
    apogee = ApogeeAltaU9()
    working_dir = 'overscan_test'
    working_path = path.join(test_dir, working_dir)
    mkdir(working_path)
    add_instrument = lambda hdr: hdr.set('instrume', 'Apogee Alta')
    name_fits = lambda name: name + '.fit'
    for name in oscan_names:
        if oscan[name]:
            data = np.zeros([apogee.rows, apogee.columns])
            has_oscan = name
        else:
            data = np.zeros([apogee.rows, apogee.overscan_start])
            no_oscan = name
        hdu = fits.PrimaryHDU(data)
        hdr = hdu.header
        add_instrument(hdu.header)
        mdl5 = MaximDL5()
        # all headers need a software name
        hdr[mdl5.fits_keyword] = mdl5.fits_name[0]
        hdr['imagetyp'] = 'LIGHT'
        hdu.writeto(path.join(working_path, name_fits(name)))

    return (working_dir, name_fits(has_oscan), name_fits(no_oscan))
