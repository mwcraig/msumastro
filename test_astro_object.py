import astro_object as ao

def test_lookup_from_simbad():
    ey_uma = ao.AstroObject('ey uma')
    print ey_uma.ra_dec.dec.d-49.81925, ey_uma.ra_dec.ra.d-135.5865
    assert (abs(ey_uma.ra_dec.dec.d - 49.81925) < 1e-6 and
            abs(ey_uma.ra_dec.ra.d - 135.5865) < 1e-6)

def test_init_with_ra_dec():
    ey_uma = ao.AstroObject('ey uma',ra_dec=(135.5865, 49.81925))
    assert (abs(ey_uma.ra_dec.dec.d - 49.81925) < 1e-6 and
            abs(ey_uma.ra_dec.ra.d - 135.5865) < 1e-6)
    