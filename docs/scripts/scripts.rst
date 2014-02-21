.. _script-documentation:

###############################################
Command-line scripts
###############################################

Each of the command-line scripts described below is also callable from python. The details of how you call it from python are described below. 

Both these ways of invoking the script (from the command line or from python) is are wrappers around the python functions that do the real work. References to those functions, which tend to provide more control over what you can do at the expense of taking more effort to understand, are provided below where appropriate.

-------------

.. _script_wrapper:

**************************************************************************
Running the complete standard workflow: ``run_standard_header_process.py``
**************************************************************************

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.run_standard_header_process
    :func: construct_parser
    :prog: run_standard_header_process.py

.. automodule:: msumastro.scripts.run_standard_header_process

-------------

.. _header-patching:

*********************************
Header patching: ``run_patch.py``
*********************************

For a detailed description of which header keywords are modified see :ref:`header-patch-detail`.

.. WARNING::
    This script OVERWRITES the image files in the directories
    specified on the command line unless you use the --destination-dir
    option.

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.run_patch
    :func: construct_parser
    :prog: run_patch.py
    

.. automodule:: msumastro.scripts.run_patch

-------------

.. _apply-astrometry:

****************************************
Adding astrometry: ``run_astromtery.py``
****************************************

.. WARNING::
    This script OVERWRITES the image files in the directories
    specified on the command line unless you use the --destination-dir
    option.

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.run_astrometry
    :func: construct_parser
    :prog: run_astrometry.py

.. automodule:: msumastro.scripts.run_astrometry

-------------

.. _summary-table:

***************************************************
Find problems and create summary: ``run_triage.py``
***************************************************

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.run_triage
    :func: construct_parser
    :prog: run_triage.py

.. automodule:: msumastro.scripts.run_triage

-------------

.. _header-quick-fix:

**************************************************
Manual intervention: ``quick_add_keys_to_file.py``
**************************************************

.. WARNING::
        This script OVERWRITES the image files in the directories
        specified on the command line. There is NO WAY TO DISABLE
        this behavior.

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.quick_add_keys_to_file
    :func: construct_parser
    :prog: quick_add_keys_to_file.py

.. automodule:: msumastro.scripts.quick_add_keys_to_file

-------------

.. _sort_files:

***************************************
Sorting files based on image properties
***************************************

.. note::
    By default this script makes a copy of the images being sorted. There is
    an option for moving the files instead.

    This type of sorting is handy for working with images in GUI software like
    AstroImageJ or MaxImDL, but will make it harder to process the data
    programmatically in python.

Usage summary
=============

.. argparse::
    :module: msumastro.scripts.sort_files
    :func: construct_parser
    :prog: sort_files.py

.. automodule:: msumastro.scripts.sort_files
