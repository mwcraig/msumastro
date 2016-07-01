MSUM Astro library
------------------

.. image:: https://img.shields.io/pypi/v/msumastro.svg
    :target: https://pypi.python.org/pypi/msumastro

.. image:: https://travis-ci.org/mwcraig/msumastro.png?branch=master
    :target: https://travis-ci.org/mwcraig/msumastro


.. image:: https://coveralls.io/repos/github/mwcraig/msumastro/badge.svg?branch=master
    :target: https://coveralls.io/github/mwcraig/msumastro?branch=master


This software was developed primarily to process the files coming off the Paul
P. Feder Observatory at Minnesota State University Moorhead. We needed to do
several things:

+ Add in some essential meta-data (like LST, JD, AIRMASS) that isn't added by the software that grabs the images.
+ Add astrometry using http://astrometry.net
+ Rummage through a tree of directories containing images and create, for each directory, a table of user-configurable image information (e.g. file name, filter, image type, object)

There is one generally useful piece: image collections
++++++++++++++++++++++++++++++++++++++++++++++++++++++

``ImageFileCollection`` has been moved to `ccdproc <https://github.com/astropy/ccdproc>`_.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

It is marked as *deprecated* in
``msumastro`` version 0.9 and will be removed in the next release.

Make a collection by providing the name of a directory and a list of the FITS
keywords you want the collection to make a table of (or ``*`` for all keywords
in any of the files):

.. code::

    >>> from msumastro import ImageFileCollection
    >>> ic = ImageFileCollection('path/to/my/directory', keywords='*')

Then you can easily iterate over all of the HDUs (well, primary HDUs), headers
and/or data, filtering by FITS keyword values (``*`` represents any value):

.. code::

    >>> for hdu in ic.hdus(imagetyp='LIGHT', object='M101'):
    >>>     pass

If you don't mind a bit of hidden magic, the iterator will also automatically
save a copy of each FITS file it acts on if you tell it where you want the new
files to go:

.. code::

    >>> for hdu in ic.hdus(save_location='some/other/directory', imagetyp='LIGHT', object='M101'):
    >>>     hdu.data = 2 * hdu.data   # modified HDU automatically saved


Documentation is at http://msum-astro.readthedocs.org
