MSUM Astro library
------------------

This software was developed primarily to process the files coming off the Paul P. Feder Observatory at Minnesota State University Moorhead. We needed to do several things:

+ Add in some essential meta-data (like LST, JD, AIRMASS) that isn't added by the software that grabs the images.
+ Add astrometry using http://astrometry.net
+ Rummage through a tree of directories containing images and create, for each directory, a table of user-configurable image information (e.g. file name, filter, image type, object)

Documentation is at http://msum-astro.readthedocs.org