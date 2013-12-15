import logging

from astropy.io.fits import Header
from astropy.io.fits import PrimaryHDU

logger = logging.getLogger(__name__)


class FITSKeyword(object):

    """
    Represents a FITS keyword.

    Useful if one logical keyword (e.g. `airmass`) has several
    often-used synonyms (e.g. secz and `airmass`).

    Checks whether the keyword is a valid FITS keyword when initialized.
    """

    def __init__(self, name=None, value=None, comment=None, synonyms=None):
        """
        All inputs are optional.
        """
        self._hdr = Header()
        self.name = name
        self.value = value
        self.comment = comment
        if synonyms is None:
            self.synonyms = []
        else:
            self.synonyms = synonyms
        return

    def __str__(self):
        if self.value is None:
            value_string = ''
        else:
            value_string = str(self.value)
        return ("%s = %s    / %s \n with synonyms: %s" %
                (self.name.upper(), value_string, self.comment,
                 ",".join(str(syn).upper() for syn in self.synonyms)))

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
            return []
        if isinstance(inp_synonyms, basestring):
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
        Method to add HISTORY line to header.
        Use `with_name` to override the name of the keyword object.
        """
        if with_name is None:
            with_name = self.name
        return "Updated keyword %s to value %s" % (with_name.upper(),
                                                   self.value)

    def add_to_header(self, hdu_or_header, with_synonyms=True, history=False):
        """
        Method to add keyword to FITS header.

        `hdu_or_header` can be either a astropy.io.fits `PrimaryHDU` or a
        pytfits `Header` object.
        `with_synonyms` determines whether the keyword's synonynms are
        also added to the header.j
        `history` determines whether a history comment is added when
        the keyword is added to the header.
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
        Determine value of keyword from FITS header.

        `hdu_or_header` can be either an astropy.io.fits `PrimaryHDU` or a
        astropy.fits `Header` object.

        If both the primary name of the keyword and its synonyms are
        present in the FITS header, checks whether the values are
        identical, and if they aren't, raises an error.
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
                                 (','.join(self.names), ','.join(values)))
            self.value = values[0]
        else:
            raise ValueError('Keyword not found in header: %s' % self)
