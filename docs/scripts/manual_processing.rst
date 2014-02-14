.. _manual_processing:

########################
Manual header processing
########################

********
Overview
********

Sometimes the standard data preparation will fail at one stage or another,
most often because pointing information is missing for an image or because no
object was found matching the RA/Dec of the image. Your tool of choice in such
cases, either to add pointing information or to add object names is
:mod:`~msumastro.scripts.quick_add_keys_to_file`. A broad discussion of using
it is at :ref:`how_to_fix`.

This document provides some examples of using
:mod:`~msumastro.scripts.quick_add_keys_to_file` from the command line. See the
documentation for :func:`add_keys` for use from python scripts.


********
Examples
********

Command line only
=================

Add the keyword "OBJECT", with value "EY UMa", to the file ``image.fit``::

    quick_add_keys_to_file.py --key-value object "EY UMa" image.fits

The same, but for all of the files that match the pattern ``ey-uma*.fit``::

    quick_add_keys_to_file.py --key-value object "EY UMa" ey-uma*.fits

The rest of the command line examples you have created a file called
``keys.txt`` with a list of keyword/value pairs and a list of files called
``files.txt`` (you can call the files whatever you want, of course)

Command line and supporting files
=================================

Format of the keyword file
--------------------------

A keyword file looks like this (you need the header line)::

    Keyword,Value
    OBJECT,"EY UMa"
    RA,"09:02:20.79"
    DEC,"+49:49:09.7"

You can include as many keywords as you want, and they can have numerical values
instead of string values in appropriate. If the value has two words, like the
value for the keyword "OBJECT" above, it must be in quotes, like "EY UMa".

Keyword names are case insensitive because keywords in the FITS standard are
case insensitive.

Format of the file list
-----------------------

A file list looks like this (yes, you need the header line)::

    File
    MyFirstFile.fit
    another_fits_file.fits
    /or/even/the/full/path/to/a/fits/file.fit

Examples using keyword file/file list
-------------------------------------

Add all of the keywords in ``keys.txt`` to all of the files in ``files.txt``::

    quick_add_keys_to_file.py --key-file keys.txt --file-list files.txt

Add all of the keywords in ``keys.txt`` to the files ``image1.fit`` and
``image2.fit``::

    quick_add_keys_to_file.py --key-file keys.txt image1.fit image2.fit

Add keywords from the command line to all of the files in ``files.txt``::

    quick_add_keys_to_file.py --key-value my_key "some value" --file-list files.txt
