import pytest

from app.services.iss import _az_compass


@pytest.mark.parametrize("az,expected", [
    (0, "N"),
    (22.4, "N"),
    (44.9, "NE"),
    (67.5, "E"),
    (90, "E"),
    (180, "S"),
    (337.5, "N"),
    (359, "N"),
])
def test_az_compass(az, expected):
    assert _az_compass(az) == expected


def test_az_compass_wraps_at_360():
    # REGRESSION-SHAPED: round(360/45) % 8 == 8 % 8 == 0 -- the modulo is what
    # keeps a full-circle azimuth landing back on "N" instead of indexing past
    # the end of COMPASS.
    assert _az_compass(360) == "N"


def test_az_compass_uses_bankers_rounding_at_exact_half_points():
    # REGRESSION-SHAPED: Python's round() rounds half-to-even, not
    # half-away-from-zero. At exactly 22.5deg (az/45 == 0.5), that rounds
    # down to 0 ("N"), not up to 1 ("NE") -- worth pinning down explicitly
    # since it's a common source of off-by-one compass labels.
    assert _az_compass(22.5) == "N"
    assert _az_compass(67.5) == "E"
