from triage_fits_files import ImageFileCollection
from  ccd_characterization import ccd_gain, ccd_read_noise
from numpy import array
from astropysics import ccd

def as_images(tbl, src_dir):
    from os import path
    img = []
    for tb in tbl:
        img.append(ccd.FitsImage(path.join(src_dir, tb['file'])).data[1:,:])
    return img
        
def calc_gain_read(src_dir):
     """Calculate gain and read noise from images in `src_dir`

     Uses biases and any R band flats that are present.
     """
     img_col = ImageFileCollection(location=src_dir,
                                   keywords=['imagetyp', 'filter'],
                                   info_file=None)
     img_tbl = img_col.summary_info
     bias_tbl = img_tbl.where(img_tbl['imagetyp']=='BIAS')
     biases = as_images(bias_tbl, src_dir)
     r_flat_tbl = img_tbl.where((img_tbl['imagetyp']=='FLAT') &
                                (img_tbl['filter']=='R'))
     r_flats = as_images(r_flat_tbl, src_dir)
     n_files = len(biases)
     n_pairs = int(n_files/2)
     gain = []
     read_noise = []
     for i in range(0,n_files,2):
         print biases[i].shape
         gain.append(ccd_gain(biases[i:i+2], r_flats[i:i+2]))
         read_noise.append(ccd_read_noise(biases[i:i+2],gain=gain[-1]))
     return (array(gain),array(read_noise))
     