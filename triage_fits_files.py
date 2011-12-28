import fnmatch
import pyfits
from keyword_names import RA, Dec, target_object
from os import listdir, path
from numpy import array

IMAGETYPE = 'IMAGETYP'

def fits_files_in_directory(dir='.', extensions=['fit','fits'], compressed=True):
    """
    Get names of FITS files in directory, based on filename extension.

    `dir` is the directory to be searched.
    `extension` is a list of filename extensions that are FITS files.
    `compressed` should be true if compressed files should be included
    in the list (e.g. `.fits.gz`)

    Returns only the *names* of the files (with extension), not the full pathname.
    """
    # trick below is necessary to make sure we start with a clean copy of
    # extensions each time
    full_extensions = []
    full_extensions.extend(extensions)
    if compressed:
        with_gz = [extension + '.gz' for extension in extensions]
        full_extensions.extend(with_gz)

    all_files = listdir(dir)
    files = []
    for extension in full_extensions:
        files.extend(fnmatch.filter(all_files, '*'+extension))
    return files

def fits_summary(dir='.', file_list=[], keywords=['imagetyp']):
    """
    Collect information about fits files in a directory.

    `dir` is the name of the directory to search for FITS files.
    `file_list` can be set to the list of FITS files in `dir`,
    otherwise the list will be generated.
    `keywords` is the list of FITS header keywords for which
    information will be gathered.

    Returns a dictionary of arrays, with one dictionary entry for each
    of the `keywords`. Missing values are indicated by `None`
    """
    print file_list, dir
    if not file_list:
        file_list = fits_files_in_directory(dir)
    print file_list
        
    summary = {}
    summary['file'] = []
    for keyword in keywords:
        summary[keyword] = []

    for afile in file_list:
        try:
            header = pyfits.getheader(path.join(dir,afile))
        except IOError:
            print 'oops!'
            continue
        summary['file'].append(afile)
        for keyword in keywords:
            try:
                summary[keyword].append(header[keyword])
            except KeyError:
                summary[keyword].append(None)
    for key in summary.keys():
        summary[key] = array(summary[key])
    return summary
    
def triage_fits_files(dir='.'):
    """
    Check FITS files in a directory for deficient headers

    `dir` is the name of the directory to search for files; default is
    the current working directory.
    """
    files = fits_files_in_directory(dir)
    
    file_info_to_keep = ('file name', 'image type')
    file_info = {}
    for to_keep in file_info_to_keep:
        file_info[to_keep] = []
    file_needs_filter = []
    file_needs_minimal_pointing_info = []
    file_needs_object_name = []
    for fitsfile in files:
        file_with_directory = path.join(dir, fitsfile)
        try:
            hdulist = pyfits.open(file_with_directory)
        except IOError:
            print "Unable to open file %s in directory %s" % (fitsfile, dir)
            continue
        header = hdulist[0].header
        image_type =  IRAF_image_type(header[IMAGETYPE])
        file_info['file name'].append(fitsfile)
        file_info['image type'].append(image_type)
        if needs_filter(image_type) and 'FILTER' not in header.keys():
            file_needs_filter.append(fitsfile)

        object_info_present = ((set(RA.names) |
                                set(Dec.names) |
                                set(target_object.names)) &
                               (set(header.keys())))
        if image_type == IRAF_image_type('light'):
            if not object_info_present:
                file_needs_minimal_pointing_info.append(fitsfile)
            if target_object.name not in header.keys():
                file_needs_object_name.append(fitsfile)

    dir_info = {'files': file_info,
                'needs_filter': file_needs_filter,
                'needs_pointing': file_needs_minimal_pointing_info,
                'needs_object_name': file_needs_object_name}
    return dir_info
    
def IRAF_image_type(image_type):
    """Convert MaximDL default image type names to IRAF

    `image_type` is the value of the FITS header keyword IMAGETYP.
    
    MaximDL default is, e.g. 'Bias Frame', which IRAF calls
    'BIAS'. Can safely be called with an IRAF-style image_type.
    """
    return image_type.split()[0].upper()

def needs_filter(image_type):
    """Determines whether this type of image needs a FILTER keyword.

    Returns True if image is Flat or Light, False otherwise.
    """
    if image_type in (IRAF_image_type('flat'), IRAF_image_type('light')):
        return True
    else:
        return False

     
     

    
