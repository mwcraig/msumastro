import pytest

from astropy.table import Table

from .. import image_grouper as ig


@pytest.fixture
def bare_group_class():
    return ig.ImageGroup


@pytest.fixture
def testing_table():
    # NEED A BETTER EXAMPLE HERE!
    a = [1, 1, 7, 5, 19]
    b = ['x', 'y', 'x', 'y', 'z']
    c = [4.1, 4.1, 4.1, 4.1, 5.2]
    index = range(0, len(a))
    tbl = Table([a, b, c, index],
                names=('a', 'b', 'c', 'index'),
                meta={'index_key': 'index',
                      'bad_group_key': 'sdafas'})
    return tbl


@pytest.fixture
def expected_tree(testing_table):
    # SO, now thinking it would be better if the leaves were always a list.
    # all assume the index is 'index'
    # if the keys are  a, b (in that order), then:
    tree_1 = { 1: {'x': [0],
                   'y': [1]},
               7: {'x': [2]},
               5: {'y': [3]},
              19: {'z': [4]}}
    # the keys are b, a (in that order) then:
    tree_2 = {'x': {1: [0],
                    7: [2]},
              'y': {1: [1],
                    5: [3]},
              'z': {19: [4]}}
    # if the keys are c (only) then:
    tree_3 = {4.1: [0, 1, 2, 3],
              5.2: [4]}
    # if keys are c and b:
    tree_4 = {4.1: {'x': [0, 2],
                    'y': [1, 3]},
              5.2: {'z': [4]}}

@pytest.fixture
def good_grouper(testing_table):
    group_keys = testing_table.colnames[0:2]
    index_key = testing_table.meta['index_key']
    grouper = ig.ImageGroup(testing_table, group_keys, index_key)
    return grouper


@pytest.fixture
def known_attributes():
    attributes = ['table', 'tree_keys', 'index_key', 'tree']
    return attributes


def test_create_grouper(bare_group_class):
    assert issubclass(bare_group_class, ig.ImageGroup)


def test_grouper_has_docstring(bare_group_class):
    assert bare_group_class.__doc__
    assert len(bare_group_class.__doc__.strip()) > 0


def test_grouper_docsting_for_sections(bare_group_class):
    required_sections = ['Parameters', 'Attributes']
    for section in required_sections:
        assert section in bare_group_class.__doc__


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


def test_grouper_tree_type(good_grouper):
    assert isinstance(good_grouper.tree, ig.RecursiveTree)


def test_grouper_tree_manual_key_addition(good_grouper):
    good_grouper.tree['one']['two']
    assert 'one' in good_grouper.tree.keys()
