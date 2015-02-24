from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

from os import path


def get_data_dir():
    """
    Return the absolute path to the directory containing the data for testing

    This is assumed to be the subdirectory named `data` of the directory
    containing this file.

    Returns
    -------
    str
        Name of path
    """
    data_name = 'data'
    this_dir = path.dirname(path.abspath(__file__))
    data_dir = path.join(this_dir, data_name)
    if not path.isdir(data_dir):
        raise RuntimeError('No data file found in {0}'.format(this_dir))
    return data_dir
