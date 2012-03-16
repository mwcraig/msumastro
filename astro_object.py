from astropysics import coords

class AstroObject(object):
    """
    An astronomical object, with only a few basic properties.
    """
    def __init__(self, name, ra_dec=None):
        from coatpy import Sesame
        from urllib import quote_plus

        if ra_dec is None:
            simbad = Sesame(opt='S')
            try:
                ra_dec = simbad.resolve(quote_plus(name,safe='+'))
            except:
                raise RuntimeError('Object %s not found by simbad.' % name)
            
        self._name = name
        self._ra_dec = coords.coordsys.FK5Coordinates(ra_dec)

    @property
    def name(self):
        return self._name

    @property
    def ra_dec(self):
        return self._ra_dec
            