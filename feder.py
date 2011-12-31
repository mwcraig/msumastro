from astropysics import obstools

class FederSite(obstools.Site):
    """
    The Feder Observatory site.

    An astropysics site with the items described below pre-set.
    """
    def __init__(self):
        """
        Location/name information are set for Feder Observatory.
        
        `lat` = 46.86678 degrees
        
        `long` = -96.453278 degrees Eaast
        
        `alt` = 311.8 meters
        
        `name` = Feder Observatory
        """
        obstools.Site.__init__(self,
                               lat=46.86678,
                               long=-96.453278,
                               alt=311.8,
                               name='Feder Observatory')
