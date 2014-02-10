import fnmatch
from os import listdir, path
import logging

import numpy as np
import numpy.ma as ma

from astropy.table import Table
import astropy.io.fits as fits

logger = logging.getLogger(__name__)


class ImageFileCollection(object):

    """
    Representation of a collection of image files.

    The class offers a table summarizing values of
    keywords in the FITS headers of the files in the collection and offers
    convenient methods for iterating over the files in the collection. The
    generator methods use simple filtering syntax and can automate storage
    of any FITS files modified in the loop using the generator.

    Parameters
    ----------
    location : str, optional
        path to directory containing FITS files
    keywords : list of str, optional
        Keywords that should be used as column headings in the summary table.
    info_file : str, optional
        Path to file that contains a table of information about FITS files.

    Attributes
    ----------
    location
    keywords
    files
    summary_info
    """

    def __init__(self, location=None, keywords=None, info_file=None):
        self._location = location
        self._files = []
        if location:
            self._files = self._fits_files_in_directory()
        self._summary_info = {}
        if keywords is None:
            keywords = []
        if info_file is not None:
            try:
                info_path = path.join(self.location, info_file)
            except AttributeError:
                info_path = info_file
            try:
                self._summary_info = Table.read(info_path,
                                                format='ascii',
                                                delimiter=',')
                self._summary_info = Table(self._summary_info,
                                           masked=True)
            except IOError:
                if location:
                    logger.warning('Unable to open table file %s, will try '
                                   'initializing from location instead',
                                   info_path)
                else:
                    raise
        if keywords:
            self.keywords = keywords

    @property
    def summary_info(self):
        """
        astropy.table.Table of values of FITS keywords for files in the collection.

        Each keyword is a column heading. In addition, there is a column
        called 'file' that contains the name of the FITS file. The directory
        is not included as part of that name.
        """
        return self._summary_info

    @property
    def location(self):
        """
        str, Path name to directory containing FITS files
        """
        return self._location

    @property
    def keywords(self):
        """
        list of str, Keywords currently in the summary table.

        Setting the keywords causes the summary table to be regenerated unless
        the new keywords are a subset of the old.
        """
        if self.summary_info:
            return self.summary_info.keys()
        else:
            return []

    @keywords.setter
    def keywords(self, keywords=None):
        # since keywords are drawn from self.summary_info, setting
        # summary_info sets the keywords.
        if keywords is None:
            self._summary_info = []
            return

        logging.debug('keywords in setter before pruning: %s', keywords)

        # remove duplicates and force a copy
        new_keys = list(set(keywords))
        logging.debug('keywords after pruning %s', new_keys)

        full_new_keys = list(set(new_keys))
        full_new_keys.append('file')
        full_new_set = set(full_new_keys)
        current_set = set(self.keywords)
        if full_new_set.issubset(current_set):
            logging.debug('table columns before trimming: %s',
                          ' '.join(current_set))
            cut_keys = current_set.difference(full_new_set)
            logging.debug('will try removing columns: %s',
                          ' '.join(cut_keys))
            for key in cut_keys:
                self._summary_info.remove_column(key)
            logging.debug('after removal column names are: %s',
                          ' '.join(self.keywords))
        else:
            logging.debug('should be building new table...')
            self._summary_info = self._fits_summary(header_keywords=new_keys)

    @property
    def files(self):
        """
        list of str, Unfiltered list of FITS files in location.
        """
        return self._files

    def values(self, keyword, unique=False):
        """
        List of values for a keyword.

        Parameters
        ----------
        keyword : str
            Keyword (i.e. table column) for which values are desired.

        unique : bool, optional
            If True, return only the unique values for the keyword.

        Returns
        -------
        list
            Values as a list.
        """
        if keyword not in self.keywords:
            raise ValueError(
                'keyword %s is not in the current summary' % keyword)

        if unique:
            return list(set(self.summary_info[keyword]))
        else:
            return list(self.summary_info[keyword])

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
        # force a copy by explicitly converting to a list
        current_file_mask = list(self.summary_info['file'].mask)
        self._find_keywords_by_values(**kwd)
        filtered_files = self.summary_info['file'].compressed()
        self.summary_info['file'].mask = current_file_mask
        return filtered_files

    def _fits_summary(self, header_keywords=None):
        """

        """
        from collections import OrderedDict
        from astropy.table import MaskedColumn

        if not self.files:
            return None

        dummy_value = -123  # Used as fill value before masked array is created
        summary = OrderedDict()
        missing_values = OrderedDict()
        data_type = {}
        header_keys = list(set(header_keywords))
        keywords = list(set(header_keys))
        if 'file' not in keywords:
            keywords.insert(0, 'file')
        else:
            # the file column should be populated from file name, not header
            header_keys.remove('file')
        for keyword in keywords:
            summary[keyword] = []
            missing_values[keyword] = []

        for afile in self.files:
            file_path = path.join(self.location, afile)
            summary['file'].append(afile)
            missing_values['file'].append(False)
            data_type['file'] = type('string')
            if not header_keys:
                continue
            try:
                header = fits.getheader(file_path)
            except IOError as e:
                logger.warning('Unable to get FITS header for file %s: %s',
                               file_path, e)
                # remove this bad file from list
                summary['file'].pop()
                missing_values['file'].pop()
                continue
            for keyword in header_keys:
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
                    summary[keyword].append(dummy_value)
                    missing_values[keyword].append(True)

        summary_table = Table(masked=True)

        for key in summary.keys():
            if key not in data_type:
                data_type[key] = type('str')
                summary[key] = [str(val) for val in summary[key]]

            new_column = MaskedColumn(name=key, data=summary[key],
                                      mask=missing_values[key])
            summary_table.add_column(new_column)

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

        if (set(keywords).issubset(set(self.keywords))):
            # we already have the information in memory
            use_info = self.summary_info
        else:
            # we need to load information about these keywords.
            use_info = self._fits_summary(header_keywords=keywords)

        matches = np.array([True] * len(use_info))
        for key, value in zip(keywords, values):
            logger.debug('Key %s, value %s', key, value)
            logger.debug('Value in table %s', use_info[key])
            value_missing = use_info[key].mask
            logger.debug('Value missing: %s', value_missing)
            value_not_missing = np.logical_not(value_missing)
            if value == '*':
                have_this_value = value_not_missing
            elif value is not None:
                if isinstance(value, basestring):
                    # need to loop explicitly over array rather than using
                    # where to correctly do string comparison.
                    have_this_value = np.array([False] * len(use_info))
                    for idx, file_key_value in enumerate(use_info[key]):
                        if value_not_missing[idx]:
                            value_matches = (file_key_value.lower() ==
                                             value.lower())
                        else:
                            value_matches = False

                        have_this_value[idx] = (value_not_missing[idx] &
                                                value_matches)
                else:
                    have_this_value = value_not_missing
                    tmp = (use_info[key][value_not_missing] == value)
                    have_this_value[value_not_missing] = tmp
                    have_this_value &= value_not_missing
            else:
                # this case--when value==None--is asking for the files which
                # are missing a value for this keyword
                have_this_value = value_missing

            matches &= have_this_value

        # the numpy convention is that the mask is True for values to
        # be omitted, hence use ~matches.
        logger.debug('Matches: %s', matches)
        self.summary_info['file'].mask = ma.nomask
        self.summary_info['file'][~matches] = ma.masked

    def _fits_files_in_directory(self, extensions=None,
                                 compressed=True):
        """
        Get names of FITS files in directory, based on filename extension.

        Parameters
        ----------
        extension : list of str, optional
            List of filename extensions that are FITS files. Default is
            ``['fit', 'fits']``

        compressed : bool, optional
            If ``True``, compressed files should be included in the list
            (e.g. `.fits.gz`)

        Returns
        -------
        list
            *Names* of the files (with extension), not the full pathname.
        """
        full_extensions = extensions or ['fit', 'fits']
        if compressed:
            with_gz = [extension + '.gz' for extension in full_extensions]
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
        """
        Generator that yields each {name} in the collection.

        If any of the parameters ``save_with_name``, ``save_location`` or
        ``clobber`` evaluates to ``True`` the generator will write a copy of
        each FITS file it is iterating over. In other words, if
        ``save_with_name`` and/or ``save_location`` is a string with non-zero
        length, and/or ``clobber`` is ``True``, a copy of each FITS file will
        be made.


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
            copy a directory of files--loop over the {name} with
            `save_location` set.

        clobber : bool
            If ``True``, overwrite input FITS files.

        do_not_scale_image_data : bool
            If ``True``, prevents fits from scaling images. Default is
            ``{default_scaling}``.

        return_fname : bool, default is False
            If True, return the tuple (header, file_name) instead of just
            header.

        kwd : dict
            Any additional keywords are used to filter the items returned; see
            Examples for details.

        Returns
        -------
        {return_type}
            If ``return_fname`` is ``False``, yield the next {name} in the
            collection

        ({return_type}, str)
            If ``return_fname`` is ``True``, yield a tuple of
            ({name}, `file path`) for next the  item in the collection.

        """
        # store mask so we can reset at end--must COPY, otherwise
        # current_mask just points to the mask of summary_info
        if self.summary_info is None:
            return

        current_mask = {}
        for col in self.summary_info.columns:
            current_mask[col] = self.summary_info[col].mask

        if kwd:
            self._find_keywords_by_values(**kwd)

        for full_path in self._paths():
            no_scale = do_not_scale_image_data
            hdulist = fits.open(full_path,
                                do_not_scale_image_data=no_scale)

            return_options = {'header': hdulist[0].header,
                              'hdu': hdulist[0],
                              'data': hdulist[0].data}

            try:
                yield (return_options[return_type]  # pragma: no branch
                       if (not return_fname) else
                       (return_options[return_type], full_path))
            except KeyError:
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
                    logger.error('Error writing file %s', new_path)
                    raise
            hdulist.close()

        # reset mask
        for col in self.summary_info.columns:
            self.summary_info[col].mask = current_mask[col]

    def _paths(self):
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
        return self._generator('header', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               return_fname=return_fname,
                               **kwd)
    headers.__doc__ = _generator.__doc__.format(name='header',
                            default_scaling='True',
                            return_type='astropy.io.fits.Header')

    def hdus(self, save_with_name='',
             save_location='', clobber=False,
             do_not_scale_image_data=False,
             **kwd):

        return self._generator('hdu', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               **kwd)
    hdus.__doc__ = _generator.__doc__.format(name='HDU',
                                             default_scaling='False',
                                             return_type='astropy.io.fits.HDU')

    def data(self, hdulist=None, save_with_name="", save_location='',
             do_not_scale_image_data=False,
             clobber=False, **kwd):
        return self._generator('data', save_with_name=save_with_name,
                               save_location=save_location, clobber=clobber,
                               do_not_scale_image_data=do_not_scale_image_data,
                               **kwd)
    data.__doc__ = _generator.__doc__.format(name='image',
                                             default_scaling='False',
                                             return_type='numpy.ndarray')
