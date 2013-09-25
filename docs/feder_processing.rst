Processing Feder Image Files
=============================

Overview
--------

How header processing occurs
+++++++++++++++++++++++++++++

The intent is that this processing will happen automatically within 24 hours of the data being uploaded to ``physics.mnstate.edu``. The actual processing will be done on a OSX-based machine (currently ``esne-bide.mnstate.edu``) with the results passed back up to ``physics.mnstate.edu``.

After processing, the raw data files will be compressed and will remain on the physics server.

Purpose of the header processing
+++++++++++++++++++++++++++++++++

The purpose of the header processing is to:

+ Modify or add keywords to the FITS header to make working with other software easier:

  + Standardize names instead using the MaxIm DL defaults (e.g. ``RA`` and ``Dec`` instead of ``OBJCTRA`` and ``OBJCTDEC``)
  + Add convenient keywords that MaxImDL does not always include (e.g. ``AIRMASS``, ``HA``, ``LST``)
  + Add keywords indicating the overscan region, if any, in the image.

+ Add astrometry to the FITS header so that RA/Dec can be extracted/displayed for sources in the image.
+ Add object names to the HEADER where possible.
+ Identify images that need manual action to add any of the information above.
+ Create a table of images in each directory with columns for several FITS header keywords to facilitate indexing of images taken at Feder.

Running the software
+++++++++++++++++++++

The underlying python functions are run with a few convenience scripts to accomplish each of the steps above. They would typically be run in this order:

*  ``run_patch`` to do a first round of header
   patching that puts site information, LST, airmass (where
   appropriate) and RA/Dec information (where appropriate) into the files. See :ref:`header-patching` for details.
*  ``run_triage`` (details at :ref:`summary-table`) to:

  + generate a table summarizing properties of images in a directory. Each image is one row in the table and the columns are keywords from the FITS headers.
  + create files with lists of images missing key information.
* Fix any problems identified by ``run_triage``. The script ``quick_add_keys_to_file`` may be useful for this; it is an easy way to add/modify the values of keywords in FITS headers from the command line; see details at :ref:`header-quick-fix`. After fixing these problems you may need to re-run patch, particularly if you have added pointing information or changed the ``IMAGETYP`` of any of the images.
*  ``run_astrometry`` to use `astrometry.net
   <http://astrometry.net>`_ to add WCS (astrometry) information to the file. See :ref:`apply-astrometry` for details. **Note
   that this requires a local installation** of `astrometry.net
   <http://astrometry.net>`_.

* If desired, ``run_triage`` again to regenerate the table of image information.

Detailed documentation of the individual scripts is :doc:`available here. <scripts>`

Details
-------

.. _header-patch-detail:

Header patching
++++++++++++++++

The keywords that are currently added/modified by ``patch_headers``  for **all files** are::

  LATITUDE: [degrees] Observatory latitude
  LONGITUD: [degrees east] Observatory longitude
  ALTITUDE: [meters] Observatory altitude
  LST: Local Sidereal Time at start of observation
  JD-OBS: Julian Date at start of observation
  MJD-OBS: Modified Julian date at start of observation
  OSCAN: True if image has overscan region
  OSCANAX: Overscan axis, 1 is NAXIS1, 2 is NAXIS 2
  OSCANST: Starting pixel of overscan region

The keywords that are currently added/modified by ``patch_header`` for **light files only** are::

  RA: Approximate RA at EQUINOX
  DEC: Approximate DEC at EQUINOX
  OBJECT: Target of the observations
  HA: Hour angle
  AIRMASS: Airmass (Sec(Z)) at start of observation
  ALT-OBJ: [degrees] Altitude of object, no refraction
  AZ-OBJ: [degrees] Azimuth of object, no refraction

Some **keywords are purged** from the original headers because I don't trust the values that MaxImDL v5 puts in::

  OBJECT
  JD
  JD-HELIO
  OBJCTALT
  OBJCTAZ
  OBJCTHA
  AIRMASS

