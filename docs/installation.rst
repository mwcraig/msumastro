Installation
=============

This software
*************

Install this software by downloading a copy from the `github page for the code <https://github.com/mwcraig/msumastro>`_. On Mac/Linux do this by typing, in a terminal in the directory in which you want to run the code::

    git clone https://github.com/mwcraig/msumastro.git

Dependencies
************

Python
------

This software has only been tested in python 2.7.x. It probably does not work in 3.x.

This software requires a python distribution that includes numpy and other packages that support scientific work with python. The easiest way to get these is to download and install the `Anaconda python distribution`_. Note that the Anaconda distribution includes ``astropy``.


Python packages
----------------

All of the python packages are installed with ``pip``, which is run from the command line (not in a python or ipython session). If you don't have ``pip`` you can almost certainly install it like this::

    easy_install pip

Required
+++++++++

Nothing will work without these:

+ `numpy`_ (*included with anaconda*): If you need to install it, do so with::

    pip install numpy

+ `astropy`_ (*included with anaconda*): If you need to install it, do so with:: 

    pip install astropy

+ `astropysics`_: Install with::

    pip install --pre astropysics``


Required to build documentation
+++++++++++++++++++++++++++++++

You only need to install the package below if you want to build the documentation yourself:

+ `sphinx_argparse`_: Install it this way::

    pip install sphinx-argparse

Non-python software: astrometry.net
------------------------------------


If you want to be able to use the script :ref:`apply-astrometry` you need a local installation of `astrometry.net <http://astrometry.net>`_. The easiest way to do that (on a Mac) is with `homebrew`_; instructions are below.

+ *Sorry, the homebrew installation of astrometry.net does not seem to be working right now...*

.. _Anaconda python distribution: http://www.continuum.io/downloads
.. _astropy: http://www.astropy.org/
.. _astropysics: http://pythonhosted.org/Astropysics/
.. _sphinx_argparse: https://github.com/ribozz/sphinx-argparse 
.. _homebrew: http://brew.sh/
.. _numpy: http://www.numpy.org/
