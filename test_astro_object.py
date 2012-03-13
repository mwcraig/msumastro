import astro_object as ao

def test_lookup():
    ey_uma = ao.AstroObject('ey uma')
    print ey_uma.ra_dec.dec.d-49.81925, ey_uma.ra_dec.ra.d-135.5865
    assert (abs(ey_uma.ra_dec.dec.d - 49.81925) < 1e-6 and
            abs(ey_uma.ra_dec.ra.d - 135.5865) < 1e-6)
