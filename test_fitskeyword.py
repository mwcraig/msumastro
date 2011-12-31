from fitskeyword import FITSKeyword
from pyfits.hdu import PrimaryHDU

class TestGoodFITSKeyword(FITSKeyword):
    def setUp(self):
        self.name = "kwd"
        self.value = 12
        self.comment = 'This is a comment'
        self.synonyms = ['kwdalt1', 'kwdalt2']
        self.hdu = PrimaryHDU()
        
    def test_name_setter(self):
        assert self.name == "KWD"

    def test_synonym_setter_length(self):
        assert len(self.synonyms) == 2

    def test_synonym_setter_values(self):
        assert ((self.synonyms[0] == 'KWDALT1') and
                (self.synonyms[1] == 'KWDALT2'))

    def test_names(self):
        assert self.names == [self.name, self.synonyms[0], self.synonyms[1]]

    def test_history_comment(self):
        assert self.history_comment() == "Updated keyword KWD to value 12"
        assert self.history_comment(with_name=self.synonyms[0]) ==\
            "Updated keyword KWDALT1 to value 12"

    def test_add_header(self):
        self.add_to_header(self.hdu)
        assert self.hdu.header[self.name] == self.value
        for synonym in self.synonyms:
            assert self.hdu.header[synonym] == self.value
            
    def test_add_header_history(self):
        self.add_to_header(self.hdu, history=True)
        print self.hdu.header.get_history()
        assert len(self.hdu.header.get_history()) == (1+len(self.synonyms))

    def test_add_header_no_synonyms(self):
        clean_hdu = PrimaryHDU()
        self.add_to_header(clean_hdu, with_synonyms=False)
        for synonym in self.synonyms:
            try:
                clean_hdu.header[synonym]
                assert False
            except KeyError:
                assert True
                
    def test_add_header_from_header(self):
        clean_hdu = PrimaryHDU()
        self.add_to_header(clean_hdu.header)
        for name in self.names:
            assert clean_hdu.header[name] == self.value
    


            

