from pyfits import Header

class FITSKeyword(object):
    def __init__(self, name=None, value=None, comment=None, synonyms=None):
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
        return self._name

    @name.setter
    def name(self, keyword_name):
        if self._keyword_is_valid(keyword_name):
            self._name = self._set_keyword_case(keyword_name)

    @property
    def synonyms(self):
        return self._synonyms

    @synonyms.setter
    def synonyms(self, inp_synonyms):
        self._synonyms = []
        if isinstance(inp_synonyms, basestring):
            synonym_list = [inp_synonyms]
        elif isinstance(inp_synonyms, list):
            synonym_list = inp_synonyms
        else:
            raise ValueError(
                'Synonyms must either be a string or a list of strings')
        for synonym in synonym_list:
            if self._keyword_is_valid(synonym):
                self._synonyms.append(self._set_keyword_case(synonym))
        return

    def _keyword_is_valid(self, keyword_name):
        if keyword_name is not None:
            dummy_value = 0
            try:
                self._hdr.update(keyword_name,dummy_value)
            except ValueError:
                raise
            return True
        else:
            return False

    @property
    def names(self):
        """Return all names, including synonyms, for this keyword.
        """
        all_names = [self.name]
        if self.synonyms:
            all_names.extend(self.synonyms)
        return all_names

    def history_comment(self, with_name=None):
        if with_name is None: with_name = self.name
        return "Updated keyword %s to value %s" % (with_name.upper(), self.value)

    def add_to_header(self, hdu, with_synonyms=True, history=False):
        header = hdu.header
        header.update(self.name, self.value, self.comment)
        if history:
            header.add_history(self.history_comment())
        if with_synonyms and self.synonyms:
            for synonym in self.synonyms:
                header.update(synonym, self.value, self.comment)
                if history:
                    header.add_history(self.history_comment(with_name=synonym))
