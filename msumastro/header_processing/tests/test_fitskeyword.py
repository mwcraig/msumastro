from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import pytest
from astropy.io.fits.hdu import PrimaryHDU
from astropy.io.fits import Header

from ..fitskeyword import FITSKeyword


class TestGoodFITSKeyword(object):

    def setup_method(self, method):
        self.name = "kwd"
        self.value = 12
        self.comment = 'This is a comment'
        self.synonyms = ['kwdalt1', 'kwdalt2']
        self.keyword = FITSKeyword(name=self.name, value=self.value,
                                   comment=self.comment,
                                   synonyms=self.synonyms)
        self.hdu = PrimaryHDU()

    def test_name_setter(self):
        assert self.keyword.name == self.name.upper()

    def test_synonym_setter_length(self):
        assert len(self.keyword.synonyms) == 2

    def test_synonym_setter_values(self):
        synonyms_should_be = set([syn.upper() for syn in self.synonyms])
        assert(not synonyms_should_be.difference(self.keyword.synonyms))

    def test_names(self):
        assert (self.keyword.names == [self.keyword.name,
                self.keyword.synonyms[0], self.keyword.synonyms[1]])

    def test_history_comment(self):
        assert (self.keyword.history_comment() ==
                "Updated keyword KWD to value 12")
        assert(self.keyword.history_comment(with_name=self.synonyms[0])
               == "Updated keyword KWDALT1 to value 12")

    def test_add_header(self):
        self.keyword.add_to_header(self.hdu)
        assert self.hdu.header[self.keyword.name] == self.keyword.value
        for synonym in self.keyword.synonyms:
            assert self.hdu.header[synonym] == self.keyword.value

    def test_add_header_history(self):
        self.keyword.add_to_header(self.hdu, history=True)
        print(self.hdu.header['history'])
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
        assert(len(k.names) == 1)
        good_synonyms = ['bobby', 'robert']
        k = FITSKeyword(name=name, synonyms=[name] + good_synonyms)
        assert(len(k.names) == len(good_synonyms) + 1)

    def test_setting_name_to_one_of_synonyms(self):
        # doing so should remove that new name as a synonym
        k = FITSKeyword(name=self.name,
                        synonyms=self.synonyms)
        k.name = self.synonyms[0]
        assert(len(k.synonyms) == len(self.synonyms) - 1)

    def test_string_repesentation(self):
        # If I have no value does my string contain only my name and comment?
        k = FITSKeyword(name=self.name, comment=self.comment)
        string_k = str(k)
        assert self.name.upper() in string_k
        assert self.comment in string_k
        # Does value and synonyms appear in string?
        k = FITSKeyword(name=self.name, comment=self.comment, value=self.value,
                        synonyms=self.synonyms)
        string_k = str(k)
        assert str(self.value) in string_k
        for syn in self.synonyms:
            assert syn.upper() in string_k

    def test_error_raised_if_invalid_synonym(self):
        # Does synonym which is neither string nor list raise error?
        with pytest.raises(ValueError):
            FITSKeyword(name='adfa', synonyms=12)

    def test_bad_hdu_or_header_arg_raises_error(self):
        hdu_or_header = 'Not a header or hdu'
        with pytest.raises(ValueError):
            self.keyword.add_to_header(hdu_or_header)
        with pytest.raises(ValueError):
            self.keyword.set_value_from_header(hdu_or_header)

    def test_set_value_from_header(self):
        # Do I raise a value error if the keyword isn't found?
        with pytest.raises(ValueError):
            self.keyword.set_value_from_header(self.hdu.header)
        new_value = 3 * self.value
        self.hdu.header[self.name] = new_value
        # Did I get the new value from the hdu?
        self.keyword.set_value_from_header(self.hdu)
        assert self.keyword.value == new_value
        # reset to original value
        self.keyword.value = self.value
        # Can I get the value from the header?
        self.keyword.set_value_from_header(self.hdu.header)
        assert self.keyword.value == new_value
        # Do multiple (non-identical) values raise a value error?
        self.hdu.header[self.synonyms[0]] = 7 * new_value
        with pytest.raises(ValueError):
            self.keyword.set_value_from_header(self.hdu.header)
