from __future__ import (print_function, division, absolute_import,
                        unicode_literals)

import logging
from os import path

from astropy.utils.console import _color_text

message_format = '%(message)s [%(name)s.%(funcName)s]'
console_format = '%(levelname)-18s ' + message_format
time_format = '%Y-%m-%d %H:%M:%S'
file_format = '%(asctime)s %(levelname)-8s ' + message_format

console_formatter = logging.Formatter(fmt=console_format,
                                      datefmt=time_format)


file_formatter = logging.Formatter(fmt=file_format,
                                   datefmt=time_format)


class ColorStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwd):
        super(ColorStreamHandler, self).__init__(*args, **kwd)

    def emit(self, record):
        """
        Formatter for standard output

        Taken almost verbatim from the astropy handler logic
        """
        if record.levelno < logging.DEBUG:
            colored_name = record.levelname
        elif(record.levelno < logging.INFO):
            colored_name = _color_text(record.levelname, 'magenta')
        elif(record.levelno < logging.WARN):
            colored_name = _color_text(record.levelname, 'green')
        elif(record.levelno < logging.ERROR):
            colored_name = _color_text(record.levelname, 'blue')
        else:
            colored_name = _color_text(record.levelname, 'red')

        original_levelname = record.levelname
        record.levelname = colored_name
        message = self.format(record)
        #message = message.replace('WARNING', 'MOO')
        print (message)
        record.levelname = original_levelname
        #print (dir(record))
        #print(": " + record.message)


class FormattedFileHandler(logging.FileHandler):
    """
    Standard FileHandler with a pre-set format.
    """
    def __init__(self, *args, **kwd):
        """
        Arguments are the same as for ``FileHandler``:

            filename, mode, encoding, delay
        """
        super(FormattedFileHandler, self).__init__(*args, **kwd)
        self.setFormatter(file_formatter)


def console_handler(*args, **kwd):
    """
    Return a console handler with colored level name

    All arguments are passed to the initializer of ``ColorStreamHandler``.
    """
    console = ColorStreamHandler(*args, **kwd)
    console.setFormatter(console_formatter)
    return console


def add_file_handlers(logger, directory, script_name):
    detail_log_path = path.join(directory, script_name + '.log')
    detailed_destination_log = FormattedFileHandler(detail_log_path)
    logger.addHandler(detailed_destination_log)
    error_log_path = path.join(directory,
                               script_name + '_error.log')
    error_destination_log = FormattedFileHandler(error_log_path)
    error_destination_log.setLevel(logging.WARNING)
    logger.addHandler(error_destination_log)
