import pyfits

def image_gen(filein, data=None, fileout=None):
    hdulist = pyfits.open(filein)
    primary = hdulist[0]
    primary.data = data
    if fileout is not None:
        hdulist.writeto(fileout)

