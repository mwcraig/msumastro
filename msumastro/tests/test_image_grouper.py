from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import pytest

from astropy.table import Table
from astropy.extern import six

from .. import table_tree as tt


@pytest.fixture
def bare_group_class():
    return tt.TableTree


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
    # the decimal entries in the table are subject to rounding, so use those
    # entries rather than hand entering them below.
    # if the keys are c (only) then:
    tree_3 = {testing_table['c'][0]: [0, 1, 2, 3],
              testing_table['c'][4]: [4]}
    # if keys are c and b:
    tree_4 = {testing_table['c'][0]: {'x': [0, 2],
                    'y': [1, 3]},
              testing_table['c'][4]: {'z': [4]}}
    tree_for_keys = {'a,b': tree_1,
                     'b,a': tree_2,
                     'c': tree_3,
                     'c,b': tree_4}
    return tree_for_keys


@pytest.fixture
def good_grouper(testing_table):
    group_keys = testing_table.colnames[0:2]
    index_key = testing_table.meta['index_key']
    grouper = tt.TableTree(testing_table, group_keys, index_key)
    return grouper


@pytest.fixture
def known_attributes():
    attributes = ['table', 'tree_keys', 'index_key']
    return attributes


def test_create_grouper(bare_group_class):
    assert issubclass(bare_group_class, tt.TableTree)


def test_grouper_has_docstring(bare_group_class):
    assert bare_group_class.__doc__
    assert len(bare_group_class.__doc__.strip()) > 0


def test_grouper_docsting_for_sections(bare_group_class):
    required_sections = ['Parameters', 'Attributes']
    for section in required_sections:
        assert section in bare_group_class.__doc__


def test_grouper_initializer_number_arguments(good_grouper, testing_table):
    assert isinstance(good_grouper, tt.TableTree)
    # should fail because too few arguments
    with pytest.raises(TypeError):
        print(tt.TableTree(['a']))
    # should fail because too many arguments
    with pytest.raises(TypeError):
        print(tt.TableTree(testing_table, testing_table.colnames[0:2],
                            testing_table.meta['index_key'], 5))


def test_group_initialization_with_bad_group_key(testing_table):
    group_keys = [testing_table.colnames[0],
                  testing_table.meta['bad_group_key']]
    index_key = testing_table.meta['index_key']
    with pytest.raises(KeyError):
        bad_grouper = tt.TableTree(testing_table, group_keys, index_key)


def test_group_initialization_checks_input_types(testing_table):
    group_keys = testing_table.colnames[0:2]
    index_key = testing_table.meta['index_key']
    # should error because first argument is not a table
    with pytest.raises(TypeError):
        bad_grouper = tt.TableTree(group_keys, group_keys, index_key)
    # should error because second argument is a string, which is iterable but
    # not a list
    with pytest.raises(TypeError):
        bad_grouper = tt.TableTree(testing_table, index_key, index_key)
    # should error because second argument is not iterable
    with pytest.raises(TypeError):
        bad_grouper = tt.TableTree(testing_table, 5, index_key)
    # should error because third argument is not a string
    with pytest.raises(TypeError):
        bad_grouper = tt.TableTree(testing_table, group_keys, [1, 2])
    # should error because third argument is not a column in the table
    with pytest.raises(KeyError):
        bad_grouper = tt.TableTree(testing_table, group_keys,
                                    testing_table.meta['bad_group_key'])
    # should error because third argument has values that are not unique
    with pytest.raises(ValueError):
        bad_grouper = tt.TableTree(testing_table, group_keys,
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
    assert isinstance(good_grouper, tt.RecursiveTree)


def test_grouper_tree_manual_key_addition(good_grouper):
    good_grouper['one']['two']
    assert 'one' in good_grouper.keys()
    assert 'two' in good_grouper['one'].keys()
    new_keys = range(4)
    good_grouper.add_keys(new_keys)
    for key in new_keys:
        assert key in good_grouper.keys()
        good_grouper = good_grouper[key]


def compare_trees(tree1, tree2):
    """
    Recursively compare two trees

    This only terminates if the leaves of the trees are instances of a list. In
    other words, it works fine for testing the trees created by TableTree but
    isn't really a general tree comparer.
    """
    for key in tree1.keys():
        print(key)
        assert key in tree2.keys()
        if isinstance(tree1[key], list):
            print(tree1[key])
            assert tree1[key] == tree2[key]
        else:
            print('Calling compare_trees recursively')
            compare_trees(tree1[key], tree2[key])


def test_grouper_with_expected_trees(testing_table, expected_tree):
    index_with = testing_table.meta['index_key']
    for grouping_string, good_tree in six.iteritems(expected_tree):
        grouping_keys = grouping_string.split(',')
        grouper = tt.TableTree(testing_table, grouping_keys, index_with)
        compare_trees(grouper, good_tree)


def validate_walk(grouper, good_tree):
    for parents, children, index in grouper.walk():
        working_tree = dict(good_tree)
        # walk the comparison tree down to the same level as the grouper tree
        print(parents)
        for parent in parents:
            print(parent)
            working_tree = working_tree[parent]
        if children:
            assert set(children) == set(working_tree.keys())
        if index:
            assert set(index) == set(working_tree)


def test_grouper_walk(testing_table, expected_tree):
    index_with = testing_table.meta['index_key']
    for grouping_string, good_tree in six.iteritems(expected_tree):
        grouping_keys = grouping_string.split(',')
        grouper = tt.TableTree(testing_table, grouping_keys, index_with)
        validate_walk(grouper, good_tree)
