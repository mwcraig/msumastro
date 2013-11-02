import logging
from os import path

from astropysics import ccd, pipeline
import numpy as np

from ..image_collection import ImageFileCollection

logger = logging.getLogger(__name__)


def reduce(files, source_dir, destination=None,
           reduced_name='_reduced', overwrite=False):
    """
    Reduce light files by applying darks and flats.

    `files` is a list of files to be reduced.

    `source_dir` is the directory containing those files and master
    darks/flats.

    `destination` is the directory to which reduced files should be
    written.

    `reduced_name` is the text to be added to the name of the reduced
    file (before the extension)

    `overwrite` must be set to `True` and the destination set to none
    for the original files to be overwritten. If you care about your
    data you won't do that, but if you want to hang yourself, use this
    rope.
    """
    if destination is not None:
        dest_dir = destination
    else:
        if overwrite:
            dest_dir = source_dir
        else:
            dest_dir = None

    dark_subtractor = ccd.ImageBiasSubtractor()
    flattener = ccd.ImageFlattener()
    flattener.combine = 'median'
    pipe = pipeline.Pipeline([dark_subtractor, flattener])

    image_info = ImageFileCollection(location=source_dir,
                                     info_file=None,
                                     keywords=['imagetyp',
                                               'exptime', 'filter'])
    images = image_info.summary_info

    master_darks = load_masters(images, source_dir=source_dir,
                                type='dark', index_by='exptime')

    master_flats = load_masters(images, source_dir=source_dir,
                                type='flat', index_by='filter')
    file_idx = []
    for fil in files:
        file_idx.append(np.where(images['file'] == fil)[0])

    file_info = images.rows(file_idx)
    file_info.sort(['exptime', 'filter'])
    exposure_times = set(file_info['exptime'].reshape(len(file_info)))
    filters = set(file_info['filter'].reshape(len(file_info)))
    for time in exposure_times:
        files_this_exposure = file_info[file_info['exptime'] == time]
        dark_subtractor.biasframe = master_darks[time].data
        for filter_band in filters:
            files_this_filter = files_this_exposure[
                files_this_exposure['filter'] == filter_band]
            flattener.flatfield = master_flats[filter_band].data
            for img in files_this_filter['file']:
                pipe.feed(ccd.FitsImage(path.join(source_dir, img)))
                pipe.process()
                result = pipe.extract()
                if dest_dir is not None:
                    base, ext = path.splitext(img)
                    result.save(path.join(dest_dir, base + reduced_name + ext))


def load_masters(images, source_dir='.', type='', index_by=''):
    """Return master calibration file(s)

    `images` should be a an image information table.

    `source_dir` should be the directory containing the files.

    `type` should be 'bias', 'dark' or 'flat'

    `index_by` is the keyword by which masters should be indexed
    (e.g. 'exptime' is a sensible choice for darks, `filter` for
    flats) and forces the return value to be a dictionary of masters.
    An empty string means return a single master.
    """
    if not set(['BIAS', 'DARK', 'FLAT']).issuperset(set([type.upper()])):
        raise ValueError('Read the docstring, chump! You gave me a bad type.')

    masters = images[images['imagetyp'] == 'MASTER ' + type.upper()]
    if not masters:
        raise ValueError('Sorry, no master files of that type are present')

    if not index_by:
        if len(masters) != 1:
            raise RuntimeError('Do not know how to group these masters')
        master_images = ccd.FitsImage(path.join(dir, masters['file'][0]))
    else:
        master_images = {}
        for val in masters[index_by]:
            this_master = masters[masters[index_by] == val]
            if len(this_master) != 1:
                raise RuntimeError('Do not know how to group these masters')

            master_images[val] = ccd.FitsImage(
                path.join(source_dir, this_master['file'][0]))

    return master_images


def trim(hdu):
    """
    Trim the overscan region from an image.

    Parameters

    hdu: FITS hdu
    """
    header = hdu.header

    try:
        overscan = header['oscan']
    except KeyError:
        return

    if overscan:
        # The conditional below IS CORRECT for selecting the case when
        # the overscan is in the first FITS axis.
        if not(('oscanst' in header) and ('oscanax' in header)):
            raise RuntimeError(
                'Overscan keywords missing from header, cannot trim')

        if (header['oscanax'] == 2):
            hdu.data = hdu.data[0:header['oscanst'], :]
        else:
            hdu.data = hdu.data[:, 0:header['oscanst']]
        del header['oscanst']
        del header['oscanax']
        header['oscan'] = False
        header['trimmed'] = (True, 'Has overscan been trimmed from image?')
    return hdu
