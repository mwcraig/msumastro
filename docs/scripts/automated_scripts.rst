.. _automated_scripts:

#######################################
Automated header processing
#######################################

********
Overview
********

The scripts described here are intended primarily to be run in an automated way
whenever new images are uploaded to the physics server. Each can also be run
manually, either from the command line or from python.

Both these ways of invoking the script (from the command line or from python)
is are wrappers around the python functions that do the real work. References
to those functions, which provide more control over what you can do at the
expense of taking more effort to understand, are provided below where
appropriate.

The purpose of the header processing is to:

+ Modify or add keywords to the FITS header to make working with other software
  easier:

  + Standardize names instead using the MaxIm DL defaults (e.g. ``RA`` and
    ``Dec`` instead of ``OBJCTRA`` and ``OBJCTDEC``)

  + Set ``IMAGETYP`` to IRAF default, *i.e.* "BIAS", "DARK", "FLAT" or "LIGHT"

  + Add convenient keywords that MaxImDL does not always include (e.g.
    ``AIRMASS``, ``HA``, ``LST``)

  + Add keywords indicating the overscan region, if any, in the image.

+ Add astrometry to the FITS header so that RA/Dec can be extracted/displayed
  for sources in the image.

+ Add object names to the HEADER where possible.

+ Identify images that need manual action to add any of the information above.

+ Create a table of images in each directory with columns for several FITS
  header keywords to facilitate indexing of images taken at Feder.


*****************
Intended workflow
*****************

The three primary scripts are, in the order in which they are intended (though
not *required*, necessarily) to run:

*  ``run_patch`` to do a first round of header
   patching that puts site information, LST, airmass (where
   appropriate) and RA/Dec information (where appropriate) into the files. See
   :ref:`header-patching` for details.

*  ``run_triage`` (details at :ref:`summary-table`) to:

  + generate a table summarizing properties of images in a directory. Each
    image is one row in the table and the columns are keywords from the FITS
    headers.
  + create files with lists of images missing key information.

* Fix any problems identified by ``run_triage``. The script
  ``quick_add_keys_to_file`` may be useful for this; it is an easy way to
  add/modify the values of keywords in FITS headers from the command line; see
  details at :ref:`header-quick-fix`. After fixing these problems you may need
  to re-run patch, particularly if you have added pointing information or
  changed the ``IMAGETYP`` of any of the images.

*  ``run_astrometry`` to use `astrometry.net <http://astrometry.net>`_ to add
   WCS (astrometry) information to the file. See :ref:`apply-astrometry` for
   details. **Note that this requires a local installation** of
   `astrometry.net <http://astrometry.net>`_.

* If desired, ``run_triage`` again to regenerate the table of image information.

*******************************************
The intended workflow will not work when...
*******************************************

The workflow above works great when the images that come off the telescope contain pointing information (i.e. RA/Dec), filter information and the image type in the header matches the actual image type.

Manual intervention will be required in any of these circumstances:

+ **There is no pointing information in the files.** In files that are produced at
  Feder Observatory the pointing information is contained in the FITS keywords
  ``OBJCTRA`` and ``OBJCTDEC``. If there is no pointing information, astrometry
  will not be added to the image headers. `astrometry.net
  <http://astrometry.net>`_ can actually do blind astrometry, but it is fairly
  time consuming. Alternatives are suggested below.

  * **How to identify this case**: There are two ways this problem may be noted.
    If :mod:`~msumastro.scripts.run_triage` has been run (and it *is* run in
    the standard workflow) then a file called  "NEEDS_POINTING_INFO.txt" will
    be created that lists all of the light files missing pointing information.
    In addition, one file with suffix `.blind` will be created for each light
    file which contains no pointing information.

+ **Filter information is missing for light or flat images.** All of the data
  preparation will occur if the ``FILTER`` keyword is missing   from the headers
  for light or flat images, but the filter needs to be added to   make the images
  *useful*.

  * **How to identify this case**: A file called "NEEDS_FILTER.txt" will be
    created as part of the standard workflow that lists each file that needs
    filter information.


+ **Incorrect image type set for image.** If the incorrect image type is set it
  can prevent some data preparation steps to be omitted that should actually occur
  or cause steps to be attempted that   shouldn't be. For example, if an image is
  really a ``LIGHT`` image but is   labeled in the header as a ``FLAT``, then no
  attempt will be made to calculate   an apparent position (Alt/Az) for the frame
  or to add astrometry. If the   mistake is reversed, with a ``FLAT`` image
  labeled as ``LIGHT`` an attempt   will be made to add astrometry which will
  fail.

  * **How to identify this case**: Manual inspection of affected images is the
    only reliable way to do this. A good place to start looking is at light
    files for which adding astrometry failed, file names whose name implies a
    different type than its ``IMAGETYP`` in the FITS header (e.g. a file with
    ``IMAGETYP = LIGHT`` whose name is ``flat-001R.fit``)

+ **The object being observed is not in the master object list.** The standard
  workflow has run but object names have not been add to all of the
  light files. This occurs when the object of the image was not in the list of
  objects used by ``run_patch.py`` or the object's RA/Dec was too far from the
  center of the image to be matched.

  * **How to identify this case**: The script ``run_triage.py``, part of the
    standard workflow, will produce a file called "NEEDS_OBJECT.txt" with a
    list of light files for which there is no object.

.. _how_to_fix:

*****************************************
Fixes for cases that require intervention
*****************************************

The discussion below is deliberately broad. For some concrete examples see
:ref:`manual_processing`

+ **Adding pointing information**: There are a few options here:

    * Use :mod:`~msumastro.scripts.quick_add_keys_to_file` to add the ``OBJECT``
      keyword to the header, then
      :func:`~msumastro.header_patching.patchers.add_ra_dec_from_object_name` to
      add pointing information, then :mod:`~msumastro.scripts.run_astrometry` to
      add astrometry to the images.

    * Use :mod:`~msumastro.scripts.quick_add_keys_to_file` to add the
      ``OBJECT``, ``RA``, ``DEC``, ``OBJCTRA`` and ``OBJCTDEC`` to the headers, then
      :mod:`~msumastro.scripts.run_astrometry` to       add astrometry to the images.
      This route is **not recommended** because it is easy to use a format for RA/Dec
      that isn't understood (or is misinterpreted) by the code that adds astrometry.

    * Do blind astrometry to add pointing information, then use
      :func:`~msumastro.header_patching.patchers.add_object_info` to add object
      names. There are no inherent with with this approach, though it may be
      simpler to add the astrometry then re-run the standard processing workflow
      to add any missing keywords than it is to manually use
      :func:`~msumastro.header_patching.patchers.add_object_info`

+ **Adding filter information**: The hard part here is not adding the filter
  keyword, it is figuring out what filter was used when the image was taken.
  You are on your own in figuring out that piece. Once you know what the
  filter should be, use :mod:`~msumastro.scripts.quick_add_keys_to_file` to
  add the keyword ``FILTER`` to the relevant files.

+ **Adding filter information**: As with adding filter information, the hard
  part is figuring out what the image type *should* be. In practice most cases
  of this are light images misidentified as flat and *vice versa* and it ought
  to be easy to determine which of those an image is at a glance (arguably, if
  you can't tell at a glance then the image is probably useful as neither a
  light nor a flat image). Once you know what the image type should be, use
  :mod:`~msumastro.scripts.quick_add_keys_to_file` to set the keyword
  ``IMAGETYP`` to the appropriate value in the relevant files. Allowed values
  for ``IMAGETYP`` are "BIAS", "DARK", "FLAT" or "LIGHT".

+ **Adding object information**: Assuming pointing information is already in the
  header for the images that need object information this is fairly
  straightforward. One way to do it is to add the object to the master object list
  and run :func:`~msumastro.header_patching.patchers.add_object_info` (or even
  just re-run :mod:`~msumastro.scripts.run_patch`, which will end up re-doing some
  of the keyword-patching work). Another way to approach is to use
  :mod:`~msumastro.scripts.quick_add_keys_to_file` to set the ``OBJECT`` keyword
  directly. **Either way you are encouraged to upadte the master object list.**

*********************************
Detailed list of keywords changed
*********************************

.. _header-patch-detail:

Keywords purged before further processing
-----------------------------------------

Some **keywords are purged** from the original headers because I don't trust
the values that MaxImDL v5 puts in::

  OBJECT
  JD
  JD-HELIO
  OBJCTALT
  OBJCTAZ
  OBJCTHA
  AIRMASS


Keywords modified for all files
-------------------------------

The keywords that are currently added/modified by ``patch_headers`` for
**all files** are::

  IMAGETYP: Type of image
  LATITUDE: [degrees] Observatory latitude
  LONGITUD: [degrees east] Observatory longitude
  ALTITUDE: [meters] Observatory altitude
  LST: Local Sidereal Time at start of observation
  JD-OBS: Julian Date at start of observation
  MJD-OBS: Modified Julian date at start of observation
  BIASSEC: Region of the image useful for subtracting overscan
  TRIMSEC: Region to which the image should be trimmed after removing overscan

Keywords modified only for light files
--------------------------------------

The keywords that are currently added/modified by ``patch_header`` for
**light files only** are::

  RA: Approximate RA at EQUINOX
  DEC: Approximate DEC at EQUINOX
  OBJECT: Target of the observations
  HA: Hour angle
  AIRMASS: Airmass (Sec(Z)) at start of observation
  ALT-OBJ: [degrees] Altitude of object, no refraction
  AZ-OBJ: [degrees] Azimuth of object, no refraction



*************
Reference/API
*************

.. toctree::
    :maxdepth: 2

    scripts
