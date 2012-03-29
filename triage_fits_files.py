import fnmatch
import pyfits
from feder import RA, Dec, target_object
from os import listdir, path
from numpy import array, where
from string import lower
import atpy

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

    
def triage_fits_files(dir='.', file_info_to_keep=['imagetyp']):
    """
    Check FITS files in a directory for deficient headers

    `dir` is the name of the directory to search for files.

    `file_info_to_keep` is a list of the FITS keywords to get values
    for for each FITS file in `dir`.
    """
    files = fits_files_in_directory(dir)
    
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
        image_type =  IRAF_image_type(header['imagetyp'])

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

    img_collection = ImageFileCollection(dir, keywords=file_info_to_keep)
    file_info = img_collection.fits_summary(dir, keywords=file_info_to_keep)
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

from tempfile import TemporaryFile
class ImageFileCollection(object):
    """
    Representation of a collection (usually a directory) of image
    files.

    :attrib summary_info: An ATpy table of information about the FITS files in the direction.

    To extract a desired set of files::
    
        import triage_fits_files as tff
        my_files = tff.ImageFileCollection('my_directory',keywords=['object'])
        summary = my_files.summary_info
        m101 = (summary['object'] == 'm101')
        m101_files = summary['file'][m101]
    
    *TODO:* Correctly handle case when keywords is a single value
    instead of a list.
    """
    def __init__(self,location='.', storage_dir=None, keywords=[], info_file='Manifest.txt'):
        self._location = location
        self.storage_dir = storage_dir
        self._files = fits_files_in_directory(self.location)
        self.summary_info = {}

        if info_file is not None:
            try:
                self.summary_info = atpy.Table(path.join(self.location,info_file),
                                               type='ascii',
                                               delimiter=',')
            except Exception:
                print 'Unable to read file %s, will regenerate table' % info_file

        if keywords:
            if not set(keywords).issubset(set(self.keywords)):
                print 'Regenerating information summary table for %s' % location
                self.summary_info = self.fits_summary(self.location,
                                                      file_list=self._files,
                                                      keywords=keywords)
            
    @property
    def location(self):
        """
        Location of the collection.

        Path name to directory if it is a directory.
        """
        return self._location

    @property
    def storage_dir(self):
        """
        Directory information about this collection should be stored.

        `None` or `False` means it is not stored on disk; `True` means the storage is
        in the same place as `self.location`; a `string` is interpreted as the
        full path name of the directory where information should be
        stored.

        The storage location must be writeable by the user; this is
        automatically checked when the property is set.

        """
        return self._storage

    @storage_dir.setter
    def storage_dir(self, loc):
        """
        On setting, check that `loc` is writable.
        """
        if ((isinstance(loc, bool) and not loc) or
            (loc is None)):
            self._storage = loc
            return

        if isinstance(loc, basestring):
            temp_storage = loc
        else:
            temp_storage = self.location
            
        #try writing a file to this location...
        try:
            tmpfile = TemporaryFile(dir=temp_storage)
        except OSError:
            raise
        tmpfile.close()
        self._storage = temp_storage

    @property
    def keywords(self):
        """
        List of keywords from FITS files about which you want
        information.
        """
        if self.summary_info:
            return self.summary_info.keys()
        else:
            return []
            
    @keywords.setter
    def keywords(self, keywords=[]):
        if keywords:
            self.summary_info = self.fits_summary(self.location,
                                              file_list=self._files,
                                              keywords=keywords)

    @property
    def files(self):
        """List of FITS files in location.
        """
        return self._files

    def values(self, keyword, unique=False):
        """Return list of values for a particular keyword.

        Values for `keyword` are returned.

        If `unique` is `True` then only the unique values are returned.
        """
        if not self.hasKey(keyword):
            raise ValueError('keyword %s is not in the current summary' % keyword)

        if unique:
            return list(set(self.summary_info[keyword]))
        else:
            return list(self.summary_info[keyword])

    def hasKey(self, keyword):
        """True if keyword is in current summary."""
        for key in self.keywords:
            if keyword == key:
                return True
        return False
        
    def filesFiltered(self, keywords=[], values=[]):
        """Determine files whose keywords have listed values.

        `keywords` should be a list of keywords.

        `values` should be a list of their values or the string '*' if
        only the presence of the `keyword` matters.

        The two lists must have the same length.

        NOTE: Value comparison is case *insensitive* for strings.
        """
        if len(keywords) != len(values):
            raise ValueError('keywords and values must have same length.')

        return self._find_keywords_by_values(keywords, values)

    def fits_summary(self, dir='.', file_list=[], keywords=['imagetyp']):
        """
        Collect information about fits files in a directory.

        `dir` is the name of the directory to search for FITS files.

        `file_list` can be set to the list of FITS files in `dir`,
        otherwise the list will be generated.

        `keywords` is the list of FITS header keywords for which
        information will be gathered.

        Returns an ATpy table.
        """
        from collections import OrderedDict

        if not file_list:
            file_list = fits_files_in_directory(dir)

        summary = OrderedDict()
        summary['file'] = []
        for keyword in keywords:
            summary[keyword] = []

        for afile in file_list:
            try:
                header = pyfits.getheader(path.join(dir,afile))
            except IOError:
                continue
            summary['file'].append(afile)
            for keyword in keywords:
                try:
                    summary[keyword].append(header[keyword])
                except KeyError:
                    summary[keyword].append('')

        summary_table = atpy.Table()

        for key in summary.keys():        
            summary_table.add_column(key, summary[key])

        return summary_table

    def _find_keywords_by_values(self, keywords=[],
                                            values=[]):
        """Find files whose keywords have given values.

        `keywords` is a list of keyword names.
        
        `values` should be a list desired values as strings or '*' to match any
        value. The latter simply checks whether the keyword is present
        in the file with a non-trivial value.
        """
        if values == '*':
            use_values = [values] * len(keywords)
        else:
            use_values = values
            
        if (set(keywords) & set(self.keywords)):
            # we already have the information in memory
            use_info = self.summary_info
        else:
            # we need to load information about these keywords.
            use_info = self.fits_summary(self.location,
                                         file_list=self.files,
                                         keywords=keywords)
            
        have_all = set(range(0, len(self._files)))
        for key, value in zip(keywords, use_values):
            if value == '*':
                have_this_value = set(where(use_info[key] != '')[0])
            else:
                if isinstance(value, basestring):
                    # need to loop explicitly over array rather than using
                    # where to correctly do string comparison.
                    have_this_value = []
                    for idx, file_key_value in enumerate(use_info[key]):
                        if file_key_value.lower() == value.lower():
                            have_this_value.append(idx)
                    have_this_value = set(have_this_value)
                else:
                    have_this_value = set(where(use_info[key] == value)[0])
            have_all &= have_this_value
            
        # we need to convert the list of files to a numpy array to be
        # able to index it, but it is easier to work with an ordinary
        # list for the files.
        return list(array(self._files)[list(have_all)])
       
        