from unittest.mock import patch


def _planet(name="Mercury", alt=10.0, mag=0.0, au=0.5, const="Vir"):
    return {"name": name, "alt": alt, "mag": mag, "au_earth": au, "const": const}


def test_visible_planets_filters_out_below_horizon(client):
    # /visiblePlanets is documented as "currently above the horizon" -- a
    # planet with alt <= 0 must never appear in the response.
    data = {"response": [_planet(name="Below", alt=-1.0), _planet(name="Above", alt=1.0)]}
    with patch("app.routes.celestial.get_planet_ephem", return_value=data):
        resp = client.get("/v1/celestial/visiblePlanets")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["Above"]


def test_visible_planets_brightness_bucket_boundaries(client):
    # REGRESSION-SHAPED: the brightness label comes from a chain of
    # magnitude thresholds -- an off-by-one on any boundary would
    # silently mislabel a planet's brightness with nothing to catch it.
    cases = [
        (6.6, "not visible to naked eye"),  # > 6.5
        (6.5, "dim"),                        # boundary: not > 6.5, and >= 2
        (2.0, "dim"),                        # boundary: >= 2
        (1.9, "average"),                    # just under 2
        (1.0, "average"),                    # boundary: >= 1
        (0.9, "bright"),                     # just under 1
        (0.0, "bright"),                     # boundary: >= 0
        (-0.1, "very bright"),               # just under 0
        (-3.0, "very bright"),               # boundary: >= -3
        (-3.1, "extremely bright"),          # just under -3
    ]
    for mag, expected in cases:
        data = {"response": [_planet(mag=mag)]}
        with patch("app.routes.celestial.get_planet_ephem", return_value=data):
            resp = client.get("/v1/celestial/visiblePlanets")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["brightness"] == expected, f"mag={mag} expected {expected}, got {body[0]['brightness']}"


def test_visible_planets_passes_through_upstream_error_shape(client):
    # When get_planet_ephem's response has no "response" key (upstream
    # error passthrough shape), the route must return that shape as-is
    # rather than crashing on `for p in None`.
    data = {"error": "upstream unavailable"}
    with patch("app.routes.celestial.get_planet_ephem", return_value=data):
        resp = client.get("/v1/celestial/visiblePlanets")
    assert resp.status_code == 200
    assert resp.json() == data


def test_visible_planets_returns_502_on_exception(client):
    with patch("app.routes.celestial.get_planet_ephem", side_effect=RuntimeError("boom")):
        resp = client.get("/v1/celestial/visiblePlanets")
    assert resp.status_code == 502
    assert "error" in resp.json()
