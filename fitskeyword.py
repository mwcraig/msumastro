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

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, keyword_name):
        if self._keyword_is_valid(keyword_name):
            self._name = keyword_name

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
                self._synonyms.append(synonym)
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



 
    