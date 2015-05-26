############
Installation
############

*************
This software
*************

Users
=====

This software requires a python distribution that includes `numpy`_ and other
packages that support scientific work with python. The easiest way to get these
is to download and install the `Anaconda python distribution`_. Note that the
Anaconda distribution includes ``astropy``.

Install the way you install most python software::

    pip install msumastro

followed (optionally) by::

    pip install astropysics

only if you need the Feder Observatory stuff. You do *not* need `astropysics`_
for the image management features likely to be of broadest interest.

Developers
==========

Install this software by downloading a copy from the `github page for the code
<https://github.com/mwcraig/msumastro>`_. On Mac/Linux do this by typing, in a
terminal in the directory in which you want to run the code::

    git clone https://github.com/mwcraig/msumastro.git

Navigate to the directory in which you downloaded it and run::

    python setup.py develop

With this setup any changes you make to the source code will be immediately
available to you without additional steps.

************
Dependencies
************

Python
======

This software has only been tested in python 2.7.x. It does **not** work in
3.x.

.. note::
    Most of the requirements below will be taken care of automatically
    if you install `msumastro` with ``pip`` or ``setup.py`` as described above.
    The exceptions are `numpy`_ and `scipy`_

Python packages
===============

Required
--------

Nothing will work without these:

+ `numpy`_ (*included with anaconda*): If you need to install it, please see the
  instructions at the `SciPy download site
  <http://www.scipy.org/scipylib/download.html>`_. Some functionality may
  require SciPy.

+ `astropy`_ (*included with anaconda*): If you need to install it, do so with::

    pip install astropy

Required for some features
--------------------------

Most of the header patching functionality requires `astropysics`_:

+ `astropysics`_: Install with::

    pip install astropysics

Very strongly recommended if you want to test your install
----------------------------------------------------------

+ `pytest_capturelog`_: Install with::

    pip install pytest-capturelog

Required to build documentation
-------------------------------

You only need to install the packages below if you want to build the
documentation yourself:

+ `numpydoc`_: Install using either ``pip``, or, if you have the `Anaconda
  python distribution`_, like this::

    conda install numpydoc

+ `sphinx_argparse`_: Install it this way::

    pip install sphinx-argparse


(mostly) Non-python software: astrometry.net
============================================

.. note::
    There is one piece of python software you need for `astrometry.net
    <http://astrometry.net>`_ and for now you need to install it manually::

        pip install pyfits

If you want to be able to use the script :ref:`apply-astrometry` you need a
local installation of `astrometry.net <http://astrometry.net>`_ and
`sextractor`_ (the latter works better than the source detection built into
astrometry.net) The easiest way to do that (on a Mac) is with `homebrew`_. Once
you have installed `homebrew`_ the rest is easy (unless it fails, of course...):

+ ``brew tap homebrew/science`` (only needs to be done once; connects the set of
  `homebrew`_ science formulae)

+ ``brew install sextractor`` (note this can take a a few minutes)

+ ``brew install --env=std astrometry.net`` [Note the option ``--env=std``. It
  is necessary to ensure `homebrew`_ sees your python installation.]

.. _Anaconda python distribution: http://www.continuum.io/downloads
.. _astropy: http://www.astropy.org/
.. _astropysics: http://pythonhosted.org/Astropysics/
.. _sphinx_argparse: https://github.com/ribozz/sphinx-argparse
.. _homebrew: http://brew.sh/
.. _numpy: http://www.numpy.org/
.. _numpydoc: https://github.com/numpy/numpydoc
.. _scipy: http://www.scipy.org/
.. _pytest_capturelog: http://bitbucket.org/memedough/pytest-capturelog/overview
.. _sextractor: http://www.astromatic.net/software/sextractor
