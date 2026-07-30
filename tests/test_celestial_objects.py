import pytest

from app.astronomy.celestial_objects import (
    _parse_ra,
    _parse_dec,
    _parse_pm,
    _parse_xephem_line,
)


def test_parse_ra_full_hms():
    assert _parse_ra("12:30:00") == pytest.approx(12.5)


def test_parse_ra_hours_minutes_only():
    # H:MM.m form -- no seconds field at all.
    assert _parse_ra("12:30.5") == pytest.approx(12 + 30.5 / 60)


def test_parse_ra_hours_only():
    assert _parse_ra("12") == pytest.approx(12.0)


def test_parse_ra_strips_proper_motion_suffix():
    # The |pm suffix must never leak into the RA value itself.
    assert _parse_ra("12:30:00|5.2") == pytest.approx(12.5)


def test_parse_dec_positive():
    assert _parse_dec("+45:30:00") == pytest.approx(45.5)


def test_parse_dec_negative():
    assert _parse_dec("-45:30:00") == pytest.approx(-45.5)


def test_parse_dec_no_sign_defaults_positive():
    # REGRESSION-SHAPED: only a leading '-' flips the sign; a bare
    # unsigned value must not be silently treated as negative.
    assert _parse_dec("45:30:00") == pytest.approx(45.5)


def test_parse_dec_strips_proper_motion_suffix():
    assert _parse_dec("+45:30:00|3.1") == pytest.approx(45.5)


def test_parse_pm_present():
    assert _parse_pm("12:30:00|5.2") == pytest.approx(5.2)


def test_parse_pm_absent_defaults_zero():
    assert _parse_pm("12:30:00") == 0.0


def test_parse_pm_invalid_value_defaults_zero():
    # A malformed pm segment shouldn't raise -- just fall back to 0.
    assert _parse_pm("12:30:00|not-a-number") == 0.0


def test_parse_xephem_line_ignores_blank_lines():
    assert _parse_xephem_line("", "star") is None
    assert _parse_xephem_line("   ", "star") is None


def test_parse_xephem_line_ignores_comments():
    assert _parse_xephem_line("# a comment", "star") is None


def test_parse_xephem_line_rejects_too_few_fields():
    assert _parse_xephem_line("Polaris,f", "star") is None


def test_parse_xephem_line_parses_a_valid_star():
    line = "Polaris|Alpha UMi,f,2:31:49.09,89:15:50.8,1.98"
    entry = _parse_xephem_line(line, "star")

    assert entry is not None
    assert entry["key"] == "polaris"
    assert entry["names"] == ["Polaris", "Alpha UMi"]
    assert entry["type"] == "star"
    assert entry["magnitude"] == pytest.approx(1.98)
    assert entry["skyfield"] is not None


def test_parse_xephem_line_missing_magnitude_is_none():
    line = "Polaris|Alpha UMi,f,2:31:49.09,89:15:50.8"
    entry = _parse_xephem_line(line, "star")

    assert entry is not None
    assert entry["magnitude"] is None


def test_parse_xephem_line_rejects_unparseable_ra_dec():
    line = "Bogus,f,not-a-coordinate,also-bad,1.0"
    assert _parse_xephem_line(line, "star") is None


def test_parse_xephem_line_rejects_empty_names_field():
    line = "|| ,f,2:31:49.09,89:15:50.8,1.98"
    assert _parse_xephem_line(line, "star") is None
