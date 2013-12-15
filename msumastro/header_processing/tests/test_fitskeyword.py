from astropy.io.fits.hdu import PrimaryHDU

from ..fitskeyword import FITSKeyword


class TestGoodFITSKeyword(object):

    def setup_method(self, method):
        self.keyword = FITSKeyword(name="kwd", value=12,
                                   comment='This is a comment',
                                   synonyms=['kwdalt1', 'kwdalt2'])
        self.hdu = PrimaryHDU()

    def setUp(self):
        self.name = "kwd"
        self.value = 12
        self.comment = 'This is a comment'
        self.synonyms = ['kwdalt1', 'kwdalt2']
        self.hdu = PrimaryHDU()

    def test_name_setter(self):
        assert self.keyword.name == "KWD"

    def test_synonym_setter_length(self):
        assert len(self.keyword.synonyms) == 2

    def test_synonym_setter_values(self):
        assert ((self.keyword.synonyms[0] == 'KWDALT1') and
                (self.keyword.synonyms[1] == 'KWDALT2'))

    def test_names(self):
        assert (self.keyword.names == [self.keyword.name,
                self.keyword.synonyms[0], self.keyword.synonyms[1]])

    def test_history_comment(self):
        assert (self.keyword.history_comment() ==
                "Updated keyword KWD to value 12")
        assert(self.keyword.history_comment(with_name=self.keyword.synonyms[0])
               == "Updated keyword KWDALT1 to value 12")

    def test_add_header(self):
        self.keyword.add_to_header(self.hdu)
        assert self.hdu.header[self.keyword.name] == self.keyword.value
        for synonym in self.keyword.synonyms:
            assert self.hdu.header[synonym] == self.keyword.value

    def test_add_header_history(self):
        self.keyword.add_to_header(self.hdu, history=True)
        print self.hdu.header['history']
        assert (len(self.hdu.header['history']) ==
                (1 + len(self.keyword.synonyms)))

    def test_add_header_no_synonyms(self):
        clean_hdu = PrimaryHDU()
        self.keyword.add_to_header(clean_hdu, with_synonyms=False)
        for synonym in self.keyword.synonyms:
            try:
                clean_hdu.header[synonym]
                assert False
            except KeyError:
                assert True

    def test_add_header_from_header(self):
        clean_hdu = PrimaryHDU()
        self.keyword.add_to_header(clean_hdu.header)
        for name in self.keyword.names:
            assert clean_hdu.header[name] == self.keyword.value

    def test_handling_of_duplicate_synonyms(self):
        # should fail if duplicate synonyms are not removed in initialization
        bad_synonyms = ['bad', 'bad']
        k = FITSKeyword(name='good', synonyms=bad_synonyms)
        assert(len(k.synonyms) == len(set(bad_synonyms)))

    def test_handling_of_synonym_that_duplicates_name(self):
        name = 'bob'
        k = FITSKeyword(name=name, synonyms=name)
        assert(len(k.names) == len(name))
