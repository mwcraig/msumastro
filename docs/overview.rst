.. _overview:

########
Overview
########

This package provides three related groups of functionality:

***************************
Automated header processing
***************************

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

***********************************
Manual header or image manipulation
***********************************

Command lines scripts that easily automate a small number of tasks that occur
frequently enough that it is convenient to have them available at the command
line instead of requiring that new code to be written each time they are used.

The only example of this currently is
:mod:`~msumastro.scripts.quick_add_keys_to_file`.

All of these scripts can also be run from your python code if desired.

***********************
Building your own tools
***********************

The functions and classes upon which the scripts above are built may be useful
in writing your own software for working with images. Of these,
:class:`ImageFileCollection` and :class:`TableTree` are most likely to be of
interest.
