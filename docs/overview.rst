.. _overview:

########
Overview
########

This package provides three related groups of functionality:

+ Command line scripts for automated updating of FITS header keywords. The
  intent with these is that they will rarely need to be used manually once the
  data preparation pipeline is set up.

+ Command lines scripts that easily automate a small number of tasks that occur
  frequently enough that it is convenient to have them available at the command
  line instead of requiring that new code to be written each time they are used.

+ The functions and classes upon which these scripts are built. Some of these,
  like :class:`ImageFileCollection` and :class:`TableTree` are useful for
  writing your own code for manipulating FITS files (e.g. for data reduction).
  Others are likely only useful for the scripts above.


