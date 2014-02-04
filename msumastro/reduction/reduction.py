import logging

logger = logging.getLogger(__name__)


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
        if not(('oscanst' in header) and ('oscanax' in header)):
            raise RuntimeError(
                'Overscan keywords missing from header, cannot trim')

        # The conditional below IS CORRECT for selecting the case when
        # the overscan is in the first FITS axis.
        if (header['oscanax'] == 2):
            hdu.data = hdu.data[0:header['oscanst'], :]
        else:
            hdu.data = hdu.data[:, 0:header['oscanst']]
        del header['oscanst']
        del header['oscanax']
        header['oscan'] = False
        header['trimmed'] = (True, 'Has overscan been trimmed from image?')
    return hdu
