################
Image Processing
################

Much of the header processing software relies on a class for managing a collection of images that includes the ability to filter by keyword values (e.g. ``OBJECT == 'EY UMa'`` or ``IMAGETYP == 'DARK'``), iterators to loop over image files (or just headers or data), and automated saving of copies of modified FITS files.

That class is :class:`ImageCollection <msumastro.image_collection.ImageFileCollection>`...and for now you just have to read its documentation.
