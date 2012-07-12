.. Matt's astro python toolbox documentation master file, created by
   sphinx-quickstart on Mon Dec 26 12:01:40 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MSUM python toolbox
=======================================================

This set of tools is currently a mix of routines to fix up the headers
of the FITS files generated at Feder Observatory and some more broadly
useful code.

Typical usage on a set of files from the telescope would look like
this:

*  ``python run_triage.py <directory>`` to generate a text list used
   by later stages to identify what actions are needed on the FITS files in ``<directory>``.
*  ``python run_patch.py <directory>`` to do a first round of header
   patching that puts site information, LST, airmass (where
   appropriate) and RA/Dec information (where appropriate) into the files.
*  ``python run_astrometry.py <directory>`` to use `astrometry.net
   <http://astrometry.net>`_ to add WCS information to the file; **Note
   that this requires a local installation** of astrometry.net.
* ``python run_add_object.py <directory>`` to add object information
  to appropriate files. This requires an Internet connection (for
  look-up of object coordinates from Simbad) and that there be
  pointing information in the file; adding astrometry will do that. 


Contents:

.. toctree::
   :maxdepth: 2
   
   Astrometry <astrometry>
   CCD characterization <ccd_characterization>
   Feder-specific items <feder>
   FITS Keyword class <fitskeyword>
   Add FITS Keyword to file <quick_add_keys_to_file>
   Patch Feder FITS headers <patch_headers>
   Manage directory of images <image_collection>
   Image with WCS <image>
   Image reduction <reduction>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

