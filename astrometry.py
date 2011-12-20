import subprocess
from os import path, remove, rename

def call_astrometry(filename, sextractor=False, feder_settings=True,
                   no_plots=True, minimal_output=True,
                   ra_dec=None):
    """Wrapper around astrometry.net solve-field.

    Provides several groups of options that work well with images from
    the Feder telescope.
    """
    solve_field = ["solve-field"]
    option_list = []

    option_list.append("--obj 20 --depth 20")
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

    options = " ".join(option_list)

    solve_field.extend(options.split())
    solve_field.extend([filename])
    print solve_field
    return subprocess.call(solve_field)
        
def add_astrometry(filename, overwrite=False, ra_dec=None):
    """Add WCS headers to FITS file using astrometry.net

    Boolean, returns True on success.
    
    Tries a couple strategies before giving up: first sextractor,
    then, if that fails, astrometry.net's built-in soure extractor.

    It also cleans up after astrometry.net, keeping only the new FITS
    file it generates and the .solved file.

    overwrite should be True to overwrite the original file. If False,
    the file astrometry.net generates is kept.

    ra_dec is a list or tuple (RA, Dec) in either decimal or
    sexagesimal form.
    """
    solved_field = (call_astrometry(filename,
                                    sextractor='/opt/local/bin/sex',ra_dec=ra_dec)
                    == 0)

    if not solved_field:
            solved_field = (call_astrometry(filename ,ra_dec=ra_dec)
                            == 0)

    if not solved_field:
        return False

    # we solved, time to clean up:
    base, ext = path.splitext(filename)
    if overwrite:
        try:
            rename(base+'.new', filename)
        except OSError:
            return False
    remove(base+'.axy')
    remove(base+'-indx.xyls')
    return True
    
        