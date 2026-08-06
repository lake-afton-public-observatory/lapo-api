import pytest

from app.astronomy import whatsup


class _FakeAngle:
    """Stand-in for skyfield's Angle, whatsup.get_phase_name only reads .degrees."""

    def __init__(self, degrees):
        self.degrees = degrees


@pytest.mark.parametrize("degrees,expected", [
    (0, "new moon"),
    (5, "new moon"),
    (355, "new moon"),
    (10, "waxing crescent"),
    (79, "waxing crescent"),
    (90, "first quarter moon"),
    (95, "first quarter moon"),
    (100.0001, "waxing gibbous"),
    (169, "waxing gibbous"),
    (180, "full moon"),
    (185, "full moon"),
    (190.0001, "waning gibbous"),
    (259, "waning gibbous"),
    (270, "last quarter moon"),
    (275, "last quarter moon"),
    (280.0001, "waning crescent"),
    (350, "waning crescent"),
])
def test_get_phase_name(monkeypatch, degrees, expected):
    # get_phase_name calls _get_ephemeris() first (loads real Skyfield data),
    # then almanac.moon_phase(eph, t) -- stub the latter so the branching
    # logic on phase_ang is tested in isolation, independent of the actual
    # moon position on any given date.
    monkeypatch.setattr(
        whatsup.almanac, "moon_phase",
        lambda eph, t: _FakeAngle(degrees),
    )

    assert whatsup.get_phase_name(t=None) == expected


@pytest.mark.parametrize("degrees,expected", [
    (9.999, "new moon"),
    (10.0001, "waxing crescent"),
    (349.9999, "waning crescent"),
    (350.0001, "new moon"),
])
def test_get_phase_name_boundaries_favor_named_phases(monkeypatch, degrees, expected):
    # The four named-phase windows (new/first-quarter/full/last-quarter) take
    # priority in the if/elif chain over the waxing/waning bands they'd
    # otherwise also fall inside of, so these boundary values pin down the
    # exact cutoffs rather than just the middle of each range.
    monkeypatch.setattr(
        whatsup.almanac, "moon_phase",
        lambda eph, t: _FakeAngle(degrees),
    )

    assert whatsup.get_phase_name(t=None) == expected
