from reduction import trim
from image_collection import ImageFileCollection


def trim_the_buggers(dir):
    """
    Trim overscan from images without removing bias

    This is, arguably, stupid, since the whole point of overscan is to
    remove bias.
    """
    from os import path

    trimmed = path.join(dir, 'trimmed')

    imgs = ImageFileCollection(dir)
    for img in imgs.hdus(save_location=trimmed, do_not_scale_image_data=True):
        trim(img)


if __name__ == '__main__':
    from sys import argv
    trim_the_buggers(argv[1])
