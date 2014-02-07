.. Matt's astro python toolbox documentation master file, created by
   sphinx-quickstart on Mon Dec 26 12:01:40 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MSUM python toolbox
=======================================================

.. _overview:

Overview
********

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


Contents:

.. toctree::
   :maxdepth: 2

   Installation <installation>   
   Header patching and other Feder-specific code <feder_processing>
   A tool for managing a set of images <image_processing>
   header_processing/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

..   CCD characterization <ccd_characterization>
..   Add FITS Keyword to file <quick_add_keys_to_file>
..   Image reduction <reduction>
..
   Astrometry <astrometry>
   Feder-specific items <feder> 
   FITS Keyword class <fitskeyword>
   Patch Feder FITS headers <patch_headers>
   Manage directory of images <image_collection>
   Image with WCS <image>
