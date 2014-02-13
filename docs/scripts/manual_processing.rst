.. _manual_processing:

########################
Manual header processing
########################

********
Overview
********

Sometimes the standard data preparation will fail at one stage or another, most often because pointing information is missing for an image or because no object was found matching the RA/Dec of the image. Your tool of choice in such cases, either to add pointing information or to add object names is :mod:`~msumastro.scripts.quick_add_keys_to_file`. A broad discussion of using it is at :ref:`how_to_fix`. 

This document provides some detailed examples, both of using :mod:`~msumastro.scripts.quick_add_keys_to_file` and from within python.


********
Examples
********

