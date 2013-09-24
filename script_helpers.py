"""A set of functions to standardize some options for python scripts."""


def setup_parser_help(parser, additional_docs=None):
    """
    Set formatting for parser to raw and add docstring to help output

    Parameters
    ----------

    parser : `ArgumentParser`
        The parser to be modified.

    additional_docs: str
        Any documentation to be added to the documentation produced by
        `argparse`

    """
    from argparse import RawDescriptionHelpFormatter

    parser.formatter_class = RawDescriptionHelpFormatter
    if additional_docs is not None:
        parser.epilog = additional_docs


def add_verbose(parser):
    """
    Add a verbose option (--verbose or -v) to parser.

    Parameters:
    -----------

    parser : `ArgumentParser`

    """

    verbose_help = "provide more information during processing"
    parser.add_argument("-v", "--verbose", help=verbose_help,
                        action="store_true")


def add_directories(parser):
    """
    Add a positional argument that is one or more directories.

    Parameters
    ----------

    parser : `ArgumentParser`

    """

    parser.add_argument("dir", metavar='dir', nargs='+',
                        help="Directory to process")


def construct_default_parser(docstring=None):
    #import script_helpers
    import argparse

    parser = argparse.ArgumentParser()
    if docstring is not None:
        setup_parser_help(parser, docstring)
    add_verbose(parser)
    add_directories(parser)

    return parser