from fitskeyword import FITSKeyword

class TestGoodFITSKeyword(FITSKeyword):
    def setUp(self):
        self.name = "kwd"
        self.value = 12
        self.comment = 'This is a comment'
        self.synonyms = ['kwdalt1', 'kwdalt2']
        
    def test_name_setter(self):
        assert self.name == "kwd"

    def test_synonym_setter_length(self):
        assert len(self.synonyms) == 2

    def test_synonym_setter_values(self):
        assert ((self.synonyms[0] == 'kwdalt1') and
                (self.synonyms[1] == 'kwdalt2'))
