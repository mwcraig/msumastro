Processing Feder Image Files
=============================

Introduction
-------------

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

*  ``python run_patch.py <directory>`` to do a first round of header
   patching that puts site information, LST, airmass (where
   appropriate) and RA/Dec information (where appropriate) into the files.
*  ``python run_triage.py <directory>`` to:

  + generate a text list used by later stages to identify what actions are needed on the FITS files in ``<directory>``.
  + create files with lists of images missing key information.

*  ``python run_astrometry.py <directory>`` to use `astrometry.net
   <http://astrometry.net>`_ to add WCS (astrometry) information to the file. **Note
   that this requires a local installation** of `astrometry.net
   <http://astrometry.net>`_.
* ``python run_add_object.py <directory>`` to add object information
  to appropriate files. This requires an Internet connection (for
  look-up of object coordinates from Simbad) and that there be
  pointing information in the file; adding astrometry will do that. 
* If desired run ``python run_triage.py <directory>`` again to regenerate the table of image information.
