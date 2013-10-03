import fnmatch
import astropy.io.fits as fits
from os import listdir, path
from numpy import array
import numpy.ma as ma
from astropy.table import Table


class ImageFileCollection(object):

    """
    Representation of a collection (usually a directory) of image
    files.

    :attrib summary_info: An ATpy table of information about the FITS files in
    the direction.

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

    def __init__(self, location='.', storage_dir=None, keywords=[],
                 missing=-999, info_file='Manifest.txt'):
        self._location = location
        self.storage_dir = storage_dir
        self._files = self._fits_files_in_directory()
        self.summary_info = {}

        if info_file is not None:
            try:
                self.summary_info = Table(path.join(self.location, info_file),
                                          type='ascii',
                                          delimiter=',')
            except IOError:
                pass

        if keywords:
            if not set(keywords).issubset(set(self.keywords)):
                pass
                #print ('Regenerating information summary table for %s' %
                #       location)

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

        `None` or `False` means it is not stored on disk; `True` means the
        storage is in the same place as `self.location`; a `string` is
        interpreted as the full path name of the directory where information
        should be stored.

        The storage location must be writeable by the user; this is
        automatically checked when the property is set.

        """
        return self._storage

    @storage_dir.setter
    def storage_dir(self, loc):
        """
        On setting, check that `loc` is writable.
        """
        from tempfile import TemporaryFile

        if ((isinstance(loc, bool) and not loc) or
                (loc is None)):
            self._storage = loc
            return

        if isinstance(loc, basestring):
            temp_storage = loc
        else:
            temp_storage = self.location

        # try writing a file to this location...
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
        if not self.has_key(keyword):
            raise ValueError(
                'keyword %s is not in the current summary' % keyword)

        if unique:
            return list(set(self.summary_info[keyword]))
        else:
            return list(self.summary_info[keyword])

    def has_key(self, keyword):
        """True if keyword is in current summary."""
        return keyword in self.keywords

    def files_filtered(self, **kwd):
        """Determine files whose keywords have listed values.

        `**kwd` is list of keywords and values the files must have.

        The value '*' represents any value.
         A missing keyword is indicated by value ''

        Example:
        >>> keys = ['imagetyp','filter']
        >>> collection = ImageFileCollection('test/data', keywords=keys)
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

        Returns an Astropy table.
        """
        from collections import OrderedDict
        from astropy.table import MaskedColumn

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
                header = fits.getheader(path.join(self.location, afile))
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
                            raise ValueError(
                                'Different data types found for keyword %s' %
                                keyword)
                    else:
                        data_type[keyword] = type(header[keyword])
                else:
                    summary[keyword].append(missing)
                    missing_values[keyword].append(True)

        summary_table = Table(masked=True)

        for key in summary.keys():
            if key not in data_type:
                data_type[key] = type('str')
                summary[key] = [str(val) for val in summary[key]]

            new_column = MaskedColumn(name=key, data=summary[key],
                                      mask=missing_values[key])
            summary_table.add_column(new_column)

            if data_type[key] == type('str'):
                summary_table[key][array(missing_values[key])] = ''

        return summary_table

    def _find_keywords_by_values(self, **kwd):
        """
        Find files whose keywords have given values.

        `**kwd` is list of keywords and values the files must have.

        The value '*' represents any value.
         A missing keyword is indicated by value ''

        Example:
        >>> keys = ['imagetyp','filter']
        >>> collection = ImageFileCollection('test/data', keywords=keys)
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
                        have_this_value[idx] = (
                            file_key_value.lower() == value.lower())
                else:
                    have_this_value = (use_info[key] == value)
            matches &= have_this_value

        # the numpy convention is that the mask is True for values to
        # be omitted, hence use ~matches.
        self.summary_info['file'].mask = ma.nomask
        self.summary_info['file'][~matches] = ma.masked

    def _fits_files_in_directory(self, extensions=['fit', 'fits'],
                                 compressed=True):
        """
        Get names of FITS files in directory, based on filename extension.

        `extension` is a list of filename extensions that are FITS files.

        `compressed` should be true if compressed files should be included
        in the list (e.g. `.fits.gz`)

        Returns only the *names* of the files (with extension), not the full
        pathname.
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
            files.extend(fnmatch.filter(all_files, '*' + extension))

        return files

    def _generator(self, return_type,
                   save_with_name="", save_location='',
                   clobber=False,
                   do_not_scale_image_data=True,
                   return_fname=False,
                   **kwd):

        # store mask so we can reset at end--must COPY, otherwise
        # current_mask just points to the mask of summary_info
        current_mask = {}
        for col in self.summary_info.columns:
            current_mask[col] = self.summary_info[col].mask

        if kwd:
            self._find_keywords_by_values(**kwd)

        for full_path in self.paths():
            no_scale = do_not_scale_image_data
            hdulist = fits.open(full_path,
                                do_not_scale_image_data=no_scale)

            return_options = {'header': hdulist[0].header,
                              'hdu': hdulist[0],
                              'data': hdulist[0].data}

            try:
                yield (return_options[return_type] if (not return_fname) else
                       (return_options[return_type], full_path))
            except ValueError:
                raise ValueError('No generator for {}'.format(return_type))

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

        # reset mask
        for col in self.summary_info.columns:
            self.summary_info[col].mask = current_mask[col]

    def paths(self):
        """
        Full path to each file.
        """
        unmasked_files = self.summary_info['file'].compressed()
        return [path.join(self.location, file_) for file_ in unmasked_files]

    def headers(self, save_with_name='',
                save_location='', clobber=False,
                do_not_scale_image_data=True,
                return_fname=False,
                **kwd):
        """
        Generator for headers in the collection including writing of
        FITS file before moving to next item.

        Parameters
        ----------

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
            If true, prevents fits from scaling images (useful for
            preserving unsigned int images unmodified)

        return_fname : bool, default is False
            If True, return the list (header, file_name) instead of just
            header.

        kwd : dict
            Any additional keywords are passed to `fits.open`
        """
        #self.headers.__func__.__doc__ += self._generator.__doc__
        return self._generator('header', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               return_fname=return_fname,
                               **kwd)

    def hdus(self, save_with_name='',
             save_location='', clobber=False,
             do_not_scale_image_data=False,
             **kwd):

        return self._generator('hdu', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               **kwd)

    def data(self, hdulist=None, save_with_name="", save_location='',
             do_not_scale_image_data=False,
             clobber=False, **kwd):
        return self._generator('data', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               **kwd)
