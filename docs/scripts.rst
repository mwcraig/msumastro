.. _script-documentation:

Command-line scripts for processing Feder files
===============================================

Each of the command-line scripts described below is also callable from python. The details of how you call it from python are described below. 

Both these ways of invoking the script (from the command line or from python) is are wrappers around the python functions that do the real work. References to those functions, which tend to provide more control over what you can do at the expense of taking more effort to understand, are provided below where appropriate.

-------------

.. _header-patching:

Header processing
+++++++++++++++++

For a detailed description of which header keywords are modified see :ref:`header-patch-detail`.

.. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

Usage summary
-------------

.. argparse::
    :module: run_patch
    :func: construct_parser
    :prog: python run_patch.py
    

.. automodule:: run_patch

-------------

.. _apply-astrometry:

Astrometry
+++++++++++

.. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

Usage summary
-------------

.. argparse::
    :module: run_astrometry
    :func: construct_parser
    :prog: python run_astrometry.py

.. automodule:: run_astrometry

-------------

.. _summary-table:

Summary table
+++++++++++++

Usage summary
-------------

.. argparse::
    :module: run_triage
    :func: construct_parser
    :prog: python run_triage.py

.. automodule:: run_triage

-------------

.. _header-quick-fix:

Quickly modify FITS headers
+++++++++++++++++++++++++++

.. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line.

Usage summary
-------------

.. argparse::
    :module: quick_add_keys_to_file
    :func: construct_parser
    :prog: python quick_add_keys_to_file.py

.. automodule:: quick_add_keys_to_file
