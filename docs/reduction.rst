Image Reduction
====================

The three steps involved in reducing images are:

* Construct master bias and dark frames (`master_bias_dark`)
* Construct master flat (`master_flat`)
* Calibrate images by applying bias, dark and flats.

These steps are accomplished like this::

    import master_bias_dark
    import master_flat
    import reduction
    directories = ['path/to/a/directory']
    master_bias_dark(directories)
    master_flat(directories)
    for directory in directories:
        list_of_files = [ list of names of files you want to calibrate]
        reduction.reduce(list_of_files, directory)

`directories` must be a list, so you can process several directories
at once.

For an example of easily generating a list of files, see
:mod:`triage_fits_files`


Contents:

.. automodule:: master_flat
   :members:
   :undoc-members:

.. automodule:: reduction
   :members:
   :undoc-members:


