import subprocess
from os import path, remove, rename

def call_astrometry(filename, sextractor=False, feder_settings=True,
                    no_plots=True, minimal_output=True,
                    ra_dec=None, overwrite=False,
                    wcs_reference_image_center=True):
    
    """Wrapper around astrometry.net solve-field.
    
    :param sextractor:
        True to use `sextractor`, or a string with the
        path to sextractor.
    :param feder_settings:
        Set True if you want to use plate scale appropriate for Feder
        Observatory Apogee Alta U9 camera.
    :param no_plots:
        True to suppress astrometry.net generation of
        plots (pngs showing object location and more)
    :param minimal_output:
        Suppress, as separate files, output of: WCS
        header, RA/Dec object list, matching objects list.
    :param ra_dec:
        List or tuple of RA and Dec; also limits search
        radius to 1 degree.
    :param overwrite:
        If True, write the WCS header to the input FITS
        file.
    :param wcs_reference_image_center:
        If True, force the WCS reference point in the image to be the
        image center.
    """
    solve_field = ["solve-field"]
    option_list = []

    option_list.append("--obj 40 --depth 20,40")
    if feder_settings:
        option_list.append("--scale-low 0.4 --scale-high 0.56 --scale-units arcsecperpix")

    if isinstance(sextractor, basestring):
        option_list.append("--sextractor-path "+sextractor)
    elif sextractor:
        option_list.append("--use-sextractor")

    if no_plots:
        option_list.append("--no-plot")

    if minimal_output:
        option_list.append("--wcs none --corr none --rdls none --match none")

    if ra_dec is not None:
        option_list.append("--ra %s --dec %s --radius 1" % ra_dec)
        
    if overwrite:
        option_list.append("--overwrite")

    if wcs_reference_image_center:
        option_list.append("--crpix-center")
        
    options = " ".join(option_list)

    solve_field.extend(options.split())
    solve_field.extend([filename])
    print solve_field
    return subprocess.call(solve_field)
        
def add_astrometry(filename, overwrite=False, ra_dec=None, note_failure=False):
    """Add WCS headers to FITS file using astrometry.net

    `overwrite` should be `True` to overwrite the original file. If `False`,
    the file astrometry.net generates is kept.

    `ra_dec` is a list or tuple (RA, Dec) in either decimal or
    sexagesimal form.

    Set `note_failure` to True if you want a file created with
    extension "failed" if astrometry.net fails.
    
    Returns `True` on success.
    
    Tries a couple strategies before giving up: first sextractor,
    then, if that fails, astrometry.net's built-in soure extractor.

    It also cleans up after astrometry.net, keeping only the new FITS
    file it generates and the .solved file.

    For more flexible invocation of astrometry.net, see :func:`call_astrometry`
    """
    base, ext = path.splitext(filename)

    solved_field = (call_astrometry(filename,
                                    sextractor='/opt/local/bin/sex',
                                    ra_dec=ra_dec)
                    == 0)

    if not solved_field:
            solved_field = (call_astrometry(filename, ra_dec=ra_dec,
                                            overwrite=True)
                            == 0)

    if overwrite and solved_field:
        try:
            rename(base+'.new', filename)
        except OSError:
            return False

    # whether we succeeded or failed, clean up
    try:
        remove(base+'.axy')
    except OSError:
        pass
        
    if solved_field:
        try:
            remove(base+'-indx.xyls')
        except OSError:
            pass
        
    if note_failure and not solved_field:
        try:
            f = open(base + '.failed', 'wb')
            f.close()
        except IOError:
            pass
            
    return solved_field
    
        