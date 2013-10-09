Installation
=============

Python
------

This software requires a python distribution that includes numpy other packages vthat support scientific work with python. The easiest way to get this is to download and install the `Anaconda python distribution`_. Note that the Anaconda distribution includes ``astropy``.

Additional external packages
----------------------------

Required
+++++++++

Nothing will work without these:

+ `astropy`_: Note that this is *included* with the `Anaconda python distribution`_. If you need to install it, do so with ``pip install --pre astropy``. Note that you need to use the ``--pre`` argument to make this work.
+ `astropysics`_: Install with: ``pip install --pre astropysics``. Note that you need to use the ``--pre`` argument to make this work.

Required for some scripts
+++++++++++++++++++++++++

If you want to be able to use the script :ref:`apply-astrometry` you need a local installation of `astrometry.net <http://astrometry.net>`_. The easiest way to do that (on a Mac) is with `homebrew`_; instructions are below.

+ *Sorry, the homebrew installation of astrometry.net does not seem to be working right now...*


Required only to build documentation
+++++++++++++++++++++++++++++++++++++

+ If you want to be able to build the documentation you will need `sphinx_argparse`_: Install it this way: ``pip install sphinx-argparse``


.. _Anaconda python distribution: http://www.continuum.io/downloads
.. _astropy: http://www.astropy.org/
.. _astropysics: http://pythonhosted.org/Astropysics/
.. _sphinx_argparse: https://github.com/ribozz/sphinx-argparse 
.. _homebrew: http://brew.sh/