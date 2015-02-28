from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import logging

from astropy.io.fits import Header
from astropy.io.fits import PrimaryHDU
from astropy.extern import six

logger = logging.getLogger(__name__)

__all__ = ['FITSKeyword']


class FITSKeyword(object):

    """
    Represents a FITS keyword, which may have several synonyms.

    Parameters
    ----------

    name : str, optional
        Name of the keyword; case insensitive

    value : str or numeric type, optional
        Value of the keyword; this class imposes no constraints on the type of
        the keyword but if you intend to save the value in a FITS header you
        should be aware of the restrictions the FITS standard places on keyword
        values.

    comment : str, optional
        Description of the keyword.

    synonyms : str or list of str, optional
        Synonyms for this keyword. Synonyms are to look for a value in a FITS
        header and to set multiple keywords to the same value in a FITS header.
    """

    def __init__(self, name=None, value=None, comment=None, synonyms=None):
        self._hdr = Header()
        self.name = name
        self.value = value
        self.comment = comment
        if synonyms is None:
            self.synonyms = []
        else:
            self.synonyms = synonyms

    def __str__(self):
        if self.value is None:
            value_string = ''
        else:
            value_string = str(self.value)
        return ("%s = %s    / %s \n with synonyms: %s" %
                (self.name.upper(), value_string, self.comment,
                 ",".join([str(syn).upper() for syn in self.synonyms])))

    def _set_keyword_case(self, keyword):
        return keyword.upper()

    @property
    def name(self):
        """
        Primary name of the keyword.
        """
        return self._name

    @name.setter
    def name(self, keyword_name):
        self._name = self._set_keyword_case(keyword_name)
        # set synonyms again in case the new name matches one the synonyms
        self.synonyms = self.synonyms

    @property
    def synonyms(self):
        """
        List of synonyms for the keyword.
        """
        try:
            return self._synonyms
        except AttributeError:
            return None

    @synonyms.setter
    def synonyms(self, inp_synonyms):
        if not inp_synonyms:
            self._synonyms = []
            return
        if isinstance(inp_synonyms, six.string_types):
            synonym_list = [inp_synonyms]
        elif isinstance(inp_synonyms, list):
            synonym_list = set(inp_synonyms)
        else:
            raise ValueError(
                'Synonyms must either be a string or a list of strings')
        synonym_list = [self._set_keyword_case(syn) for syn in synonym_list]
        self._synonyms = [synonym for synonym in synonym_list
                          if synonym != self.name]
        return

    @property
    def names(self):
        """
        All names, including synonyms, for this keyword, as a list.
        """
        all_names = [self.name]
        if self.synonyms:
            all_names.extend(self.synonyms)
        return all_names

    def history_comment(self, with_name=None):
        """
        Produce a string describing changes to the keyword value.

        Parameters
        ----------

        with_name : str, optional
            Name to use for the keyword in the history comment. Default is the
            `name` attribute of the `Keyword`.
        """
        if with_name is None:
            with_name = self.name
        return "Updated keyword %s to value %s" % (with_name.upper(),
                                                   self.value)

    def add_to_header(self, hdu_or_header, with_synonyms=True, history=False):
        """
        Add keyword to FITS header.

        Parameters
        ----------

        hdu_or_header : astropy.io.fits.Header or astropy.io.fits.PrimaryHDU
            Header/HDU to which the keyword is to be added.

        with_synonyms : bool, optional
            Control whether a keyword is added for each of the synonyms for the
            keyword. Default is True.

        history : bool, optional
            Control whether a history comment is added to the header; if True
            a history comment is added for *each* of the keyword names added
            to the header, including synonyms.
        """
        if isinstance(hdu_or_header, PrimaryHDU):
            header = hdu_or_header.header
        elif isinstance(hdu_or_header, Header):
            header = hdu_or_header
        else:
            raise ValueError('argument must be a fits Primary HDU or header')

        header[self.name] = (self.value, self.comment)
        if history:
            header.add_history(self.history_comment())
        if with_synonyms and self.synonyms:
            for synonym in self.synonyms:
                header[synonym] = (self.value, self.comment)
                if history:
                    header.add_history(self.history_comment(with_name=synonym))

    def set_value_from_header(self, hdu_or_header):
        """
        Set value of keyword from FITS header.

        Values are obtained from the header by looking for the keyword by its
        primary name and any synonyms. If multiple values are found they are
        checked for consistency.

        Parameters
        ----------

        hdu_or_header: astropy.io.fits.Header or astrop.io.fits.PrimaryHDU
            Header from which the keyword value should be taken.

        Raises
        ------

        ValueError
            If `hdu_or_header` is of the wrong type, or the keyword
            (or synonyms) are not found in the header, or multiple
            non-identical values are found.
        """
        if isinstance(hdu_or_header, PrimaryHDU):
            header = hdu_or_header.header
        elif isinstance(hdu_or_header, Header):
            header = hdu_or_header
        else:
            raise ValueError('argument must be a fits Primary HDU or header')
        values = []
        for name in self.names:
            try:
                values.append(header[name])
            except KeyError:
                continue
        if values:
            if len(set(values)) > 1:
                error_msg = 'Found multiple values for keyword %s:\nValues: %s'
                raise ValueError(error_msg %
                                 (','.join(self.names),
                                  ','.join([str(v) for v in values])))
            self.value = values[0]
        else:
            raise ValueError('Keyword not found in header: %s' % self)
