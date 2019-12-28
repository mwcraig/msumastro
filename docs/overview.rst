.. _overview:

########
Overview
########

This package provides two types of functionality; only the first is likely to be of general interest.

***********************************************
Classes for managing a collection of FITS files
***********************************************


The :class:`~msumastro.table_tree.TableTree` constructs, from the summary table of an :class:`~ccdproc.ImageFileCollection`, a tree organized by values in the FITS headers of the collection.

******************************************************
Header processing of images from the Feder Observatory
******************************************************

===============================
Semi-automatic image processing
===============================

Command line scripts for automated updating of FITS header keywords. The
intent with these is that they will rarely need to be used manually once a
data preparation pipeline is set up.

The simplest option here is to use
:mod:`~msumastro.scripts.run_standard_header_process` which will chain together
all of the steps in data preparation for you. When using
:mod:`~msumastro.scripts.run_standard_header_process` consider using the
``--scripts-only`` option, which generates `bash` scripts to carry out the data
preparation. This gives you a complete record of the commands run in addition to
the log files that are always generated.

All of these scripts can also be run from your python code if desired.

===================================
Manual header or image manipulation
===================================

Command lines scripts that easily automate a small number of tasks that occur
frequently enough that it is convenient to have them available at the command
line instead of requiring that new code to be written each time they are used.

There are currently two examples of this:

+ :mod:`~msumastro.scripts.quick_add_keys_to_file`, for modifying the values of
  FITS header keywords with minimal effort.
+ :mod:`~msumastro.scripts.sort_files` for :ref:`sort_files`


All of these scripts can also be run from your python code if desired.
