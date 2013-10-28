"""A set of functions to standardize some options for python scripts"""
import logging

logger = logging.getLogger(__name__)


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


def add_directories(parser, nargs_in='+'):
    """
    Add a positional argument that is one or more directories.

    Parameters
    ----------

    parser : `ArgumentParser`

    """

    parser.add_argument("dir", metavar='dir', nargs=nargs_in,
                        help="Directory to process")


def add_destination_directory(parser):
    """
    Add a destination directory option

    Parameters
    ----------

    parser : `ArgumentParser`

    """
    arg_help = 'Directory in which output from this script will be stored'
    parser.add_argument("-d", "--destination-dir",
                        help=arg_help,
                        default=None)


def add_debug(parser):
    """
    Add a debug option to produce very verbose output

    Parameters
    ----------

    parser : `ArgumentParser`
    """
    arg_help = 'Turn on very detailed logging output'
    parser.add_argument('--debug', help=arg_help, action='store_true')


def add_no_log_destination(parser):
    """
    Add option to suppress logging to files in destination directory
    """
    arg_help = 'Do not write log files to destination directory'
    parser.add_argument('-n', '--no-log-destination',
                        help=arg_help, action='store_true')


def add_console_output_args(parser):
    parser.add_argument('--quiet-console',
                        help=('Log only errors (or worse) to console '
                              'while running scripts'),
                        action='store_true')
    parser.add_argument('--silent-console',
                        help=('Turn off all logging output to console'),
                        action='store_true')


def construct_default_parser(docstring=None):
    #import script_helpers
    import argparse

    parser = argparse.ArgumentParser()
    if docstring is not None:
        setup_parser_help(parser, docstring)
    add_verbose(parser)
    add_directories(parser)
    add_destination_directory(parser)
    add_debug(parser)
    add_no_log_destination(parser)
    add_console_output_args(parser)

    return parser


def setup_logging(logger, args, screen_handler):
    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.quiet_console:
        screen_handler.setLevel(logging.WARNING)

    if args.silent_console:
        logger.removeHandler(screen_handler)


def handle_destination_dir_logging_check(args):
    """
    Perform error checking for command line arguments
    """
    from os import getcwd, path

    do_not_log_in_destination = args.no_log_destination
    # turn off destination logging if we are running in the destination
    # directory because we always create logs in the working directory...
    if args.dir:
        dir_abs = [path.abspath(d) for d in args.dir]
    else:
        dir_abs = None

    if args.destination_dir:
        dest_abs = path.abspath(args.destination_dir)
    else:
        dest_abs = None

    effective_destination = dest_abs or dir_abs or None

    cwd = getcwd()
    if effective_destination and (path.abspath(cwd) in effective_destination):
        if do_not_log_in_destination:
            raise RuntimeError('option --no-log-destination cannot be used '
                               'when running in the destination directory '
                               'because a log is always made in the '
                               'directory in which the script is run')
        do_not_log_in_destination = True
    return do_not_log_in_destination
