from os import path, walk


def get_data_dir():
    """
    Return the absolute path to the directory containing the data for testing

    This is assumed to be the only subdirectory of the directory containing
    this file.

    Returns
    -------
    str
        Name of path
    """
    this_dir = path.dirname(path.abspath(__file__))
    for root, dirs, files in walk(this_dir):
        try:
            return path.join(root, dirs[0])
        except IndexError:
            raise RuntimeError('No data file found in {0}'.format(this_dir))
