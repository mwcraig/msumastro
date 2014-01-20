import pytest

from astropy.table import Table

from .. import image_grouper as ig


@pytest.fixture
def empty_group():
    return ig.ImageGroup


@pytest.fixture
def testing_table():
    a = [1, 1, 2, 3, 4]
    b = ['x', 'y', 'x', 'y', 'z']
    c = [4.1, 4.1, 4.1, 4.1, 5.2]
    index = range(0, len(a))
    tbl = Table([a, b, c, index],
                names=('a', 'b', 'c', 'index'),
                meta={'index_key': 'index',
                      'bad_group_key': 'sdafas'})
    return tbl


@pytest.fixture
def good_grouper(testing_table):
    group_keys = testing_table.colnames[0:2]
    index_key = testing_table.meta['index_key']
    grouper = ig.ImageGroup(testing_table, group_keys, index_key)
    return grouper


@pytest.fixture
def known_attributes():
    attributes = ['table', 'tree_keys', 'index_key']
    return attributes


def test_create_grouper(empty_group):
    assert issubclass(empty_group, ig.ImageGroup)


def test_grouper_has_docstring(empty_group):
    assert empty_group.__doc__
    assert len(empty_group.__doc__.strip()) > 0


def test_grouper_docsting_for_sections(empty_group):
    required_sections = ['Parameters', 'Attributes']
    for section in required_sections:
        assert section in empty_group.__doc__


def test_grouper_initializer_number_arguments(good_grouper):
    assert isinstance(good_grouper, ig.ImageGroup)


def test_group_initialization_with_bad_group_key(testing_table):
    group_keys = [testing_table.colnames[0],
                  testing_table.meta['bad_group_key']]
    index_key = testing_table.meta['index_key']
    with pytest.raises(KeyError):
        bad_grouper = ig.ImageGroup(testing_table, group_keys, index_key)


def test_group_initialization_checks_input_types(testing_table):
    group_keys = testing_table.colnames[0:2]
    index_key = testing_table.meta['index_key']
    # should error because first argument is not a table
    with pytest.raises(TypeError):
        bad_grouper = ig.ImageGroup(group_keys, group_keys, index_key)
    # should error because second argument is a string, which is iterable but
    # not a list
    with pytest.raises(TypeError):
        bad_grouper = ig.ImageGroup(testing_table, index_key, index_key)
    # should error because second argument is not iterable
    with pytest.raises(TypeError):
        bad_grouper = ig.ImageGroup(testing_table, 5, index_key)
    # should error because third argument is not a string
    with pytest.raises(TypeError):
        bad_grouper = ig.ImageGroup(testing_table, group_keys, [1, 2])
    # should error because third argument is not a column in the table
    with pytest.raises(KeyError):
        bad_grouper = ig.ImageGroup(testing_table, group_keys,
                                    testing_table.meta['bad_group_key'])
    # should error because third argument has values that are not unique
    with pytest.raises(ValueError):
        bad_grouper = ig.ImageGroup(testing_table, group_keys,
                                    testing_table.colnames[0])


def test_grouper_has_attributes(good_grouper, known_attributes):
    for attribute in known_attributes:
        assert hasattr(good_grouper, attribute)


def test_grouper_attributes_are_not_settable(good_grouper, known_attributes):
    dummy_value = 5
    for attribute in known_attributes:
        with pytest.raises(AttributeError):
            setattr(good_grouper, attribute, dummy_value)
