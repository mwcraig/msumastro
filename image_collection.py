import fnmatch
import pyfits
from feder import RA, Dec, target_object
from os import listdir, path
from numpy import array, where
import numpy.ma as ma
from string import lower
import atpy
import functools

def contains_maximdl_imagetype(image_collection):
    """
    Check an image file collection for MaxImDL-style image types
    """
    import re
    file_info = image_collection.summary_info
    image_types = ' '.join([typ for typ in file_info['imagetyp']])
    if re.search('[fF]rame', image_types) is not None:
        return True
    else:
        return False
    
def triage_fits_files(dir='.', file_info_to_keep=['imagetyp',
                                                  'object',
                                                  'filter']):
    """
    Check FITS files in a directory for deficient headers

    `dir` is the name of the directory to search for files.

    `file_info_to_keep` is a list of the FITS keywords to get values
    for for each FITS file in `dir`.
    """

    all_file_info = file_info_to_keep
    all_file_info.extend(RA.names)
    
    images = ImageFileCollection(dir, keywords=all_file_info)
    file_info = images.fits_summary(keywords=all_file_info)

    # check for bad image type and halt until that is fixed.
    if contains_maximdl_imagetype(images):
        raise ValueError('Correct MaxImDL-style image types before proceeding.')
        
    file_needs_filter = \
        list(images.files_filtered(imagetyp='light',
                                   filter=''))
    file_needs_filter += \
        list(images.files_filtered(imagetyp='flat',
                                   filter=''))

    file_needs_object_name = \
        list(images.files_filtered(imagetyp='light',
                                   object=''))

    lights = file_info.where(file_info['imagetyp']=='LIGHT')
    has_no_ra = array([True]*len(lights))
    for ra_name in RA.names:
        has_no_ra &= (lights[ra_name] == '')
    needs_minimal_pointing = (lights['object'] == '') & has_no_ra    
    
    dir_info = {'files': file_info,
                'needs_filter': file_needs_filter,
                'needs_pointing': list(lights['file'][needs_minimal_pointing]),
                'needs_object_name': file_needs_object_name}
    return dir_info
    
def IRAF_image_type(image_type):
    """Convert MaximDL default image type names to IRAF

    `image_type` is the value of the FITS header keyword IMAGETYP.
    
    MaximDL default is, e.g. 'Bias Frame', which IRAF calls
    'BIAS'. Can safely be called with an IRAF-style image_type.
    """
    return image_type.split()[0].upper()
    
from tempfile import TemporaryFile
def iterate_files(func):
    @functools.wraps(func)
    def wrapper(self, save_with_name="", save_location='',
                clobber=False, hdulist=None,
                do_not_scale_image_data=True,
                **kwd):

        if kwd:
            self._find_keywords_by_values(**kwd)
            
        for full_path in self.paths():
            hdulist = pyfits.open(full_path,
                                  do_not_scale_image_data=do_not_scale_image_data)
            yield func(self, save_with_name=save_with_name,
                       save_location='', clobber=clobber, hdulist=hdulist)
            if save_location:
                destination_dir = save_location
            else:
                destination_dir = path.dirname(full_path)
            basename = path.basename(full_path)
            if save_with_name:
                base, ext = path.splitext(basename)
                basename = base + save_with_name + ext

            new_path = path.join(destination_dir, basename)

            if (new_path != full_path) or clobber:
                try:
                    hdulist.writeto(new_path, clobber=clobber)
                except IOError:
                    pass
            hdulist.close()
    return wrapper
    
class ImageFileCollection(object):
    """
    Representation of a collection (usually a directory) of image
    files.

    :attrib summary_info: An ATpy table of information about the FITS files in the direction.

    :param missing: Value to be used for missing entries.
    
    To extract a desired set of files::
    
        import image_collection as tff
        my_files = tff.ImageFileCollection('my_directory',keywords=['object'])
        summary = my_files.summary_info
        m101 = (summary['object'] == 'm101')
        m101_files = summary['file'][m101]
    
    *TODO:* Correctly handle case when keywords is a single value
    instead of a list.
    """
    def __init__(self,location='.', storage_dir=None, keywords=[],
                 missing=-999, info_file='Manifest.txt'):
        self._location = location
        self.storage_dir = storage_dir
        self._files = self._fits_files_in_directory()
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

        self.summary_info = self.fits_summary(keywords=keywords,
                                              missing=missing)

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
        # since keywords are drawn from self.summary_info, setting
        # summary_info sets the keywords.
        if keywords:
            self.summary_info = self.fits_summary(keywords=keywords)

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
        return keyword in self.keywords
        
    def files_filtered(self, **kwd):
        """Determine files whose keywords have listed values.

        `**kwd` is list of keywords and values the files must have.

        The value '*' represents any value.
         A missing keyword is indicated by value ''
        
        Example:
        >>> collection = ImageFileCollection('test/data', keywords=['imagetyp','filter'])
        >>> collection.files_filtered(imagetyp='LIGHT', filter='R')
        >>> collection.files_filtered(imagetyp='*', filter='')
        
        NOTE: Value comparison is case *insensitive* for strings.
        """

        self._find_keywords_by_values(**kwd)
        return self.summary_info['file'].compressed()
        
    def fits_summary(self, 
                     keywords=['imagetyp'], missing=-999):
        """
        Collect information about fits files in a directory.

        `file_list` can be set to the list of FITS files in `dir`,
        otherwise the list will be generated.

        `keywords` is the list of FITS header keywords for which
        information will be gathered.


        `missing` is the numerical value to be substituted if a particular file
        doesn't have a keyword. =
        
        Returns an ATpy table.
        """
        from collections import OrderedDict

        missing = float(missing)
        
        summary = OrderedDict()
        summary['file'] = []
        missing_values = OrderedDict()
        missing_values['file'] = []
        data_type = {}
        for keyword in keywords:
            summary[keyword] = []
            missing_values[keyword] = []

        for afile in self.files:
            try:
                header = pyfits.getheader(path.join(self.location,afile))
            except IOError:
                continue
            summary['file'].append(afile)
            missing_values['file'].append(False)
            data_type['file'] = type('string')
            for keyword in keywords:
                if keyword in header:
                    summary[keyword].append(header[keyword])
                    missing_values[keyword].append(False)
                    if (keyword in data_type): 
                        if (type(header[keyword]) != data_type[keyword]):
                            raise ValueError('Different data types found for keyword %s' % keyword)
                    else:
                        data_type[keyword] = type(header[keyword])
                else:
                    summary[keyword].append(missing)
                    missing_values[keyword].append(True)
                                                  
        summary_table = atpy.Table(masked=True)

        for key in summary.keys():
            if key not in data_type:
                data_type[key] = type('str')
                summary[key] = [str(val) for val in summary[key]]
            if data_type[key] == type('str'):
                summary_table.add_column(key, summary[key], mask=missing_values[key])
                summary_table[key][array(missing_values[key])] = ''
            else:
                summary_table.add_column(key, summary[key],
                                         mask=missing_values[key])


        return summary_table

    def _find_keywords_by_values(self, **kwd):
        """
        Find files whose keywords have given values.

        `**kwd` is list of keywords and values the files must have.

        The value '*' represents any value.
         A missing keyword is indicated by value ''
        
        Example:
        >>> collection = ImageFileCollection('test/data', keywords=['imagetyp','filter'])
        >>> collection.files_filtered(imagetyp='LIGHT', filter='R')
        >>> collection.files_filtered(imagetyp='*', filter='')
        
        NOTE: Value comparison is case *insensitive* for strings.
        """
        keywords = kwd.keys()
        values = kwd.values()
        
        if (set(keywords) & set(self.keywords)):
            # we already have the information in memory
            use_info = self.summary_info
        else:
            # we need to load information about these keywords.
            use_info = self.fits_summary(keywords=keywords)
            
        matches = array([True] * len(use_info))
        for key, value in zip(keywords, values):
            if value == '*':
                have_this_value = (use_info[key] != '')
            else:
                if isinstance(value, basestring):
                    # need to loop explicitly over array rather than using
                    # where to correctly do string comparison.
                    have_this_value = array([False] * len(use_info))
                    for idx, file_key_value in enumerate(use_info[key]):
                        have_this_value[idx] = (file_key_value.lower() == value.lower())
                else:
                    have_this_value = (use_info[key] == value)
            matches &= have_this_value
            
        # the numpy convention is that the mask is True for values to
        # be omitted, hence use ~matches.
        self.summary_info['file'][~matches] = ma.masked
        
    def _fits_files_in_directory(self, extensions=['fit','fits'], compressed=True):
        """
        Get names of FITS files in directory, based on filename extension.
        
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
            
            all_files = listdir(self.location)
            files = []
            for extension in full_extensions:
                files.extend(fnmatch.filter(all_files, '*'+extension))
                
            return files

    def paths(self):
        """
        Full path to each file.
        """
        return [path.join(self.location, file_) for file_ in self.summary_info['file'].compressed()]

    @iterate_files
    def headers(self, save_with_name='',
                save_location='', clobber=False,
                hdulist=None, do_not_scale_image_data=True,
                **kwd):
        """
        Generator for headers in the collection including writing of
        FITS file before moving to next item.

        Parameters

        save_with_name : str
            string added to end of file name (before extension) if
            FITS file should be saved after iteration. Unless
            `save_location` is set, files will be saved to location of
            the source files `self.location`
        
        save_location : str
            Directory in which to save FITS files; implies that FITS
            files will be saved. Note this provides an easy way to
            copy a directory of files--loop over the headers with
            `save_location` set.

        clobber : bool
            If True, overwrite input FITS files.

        do_not_scale_image_data : bool
            If true, prevents pyfits from scaling images (useful for
            preserving unsigned int images unmodified)
        
        **kwd : dict
            Any additional keywords are passed to `pyfits.open`
        """
        
        return hdulist[0].header

    @iterate_files    
    def hdus(self, save_with_name='',
                save_location='', clobber=False,
                hdulist=None, do_not_scale_image_data=False,
                **kwd):
        return hdulist[0]

    @iterate_files
    def data(self, hdulist=None, save_with_name="", save_location='', clobber=False):
        return hdulist[0].data