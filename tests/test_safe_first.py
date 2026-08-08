import datetime

import numpy as np

from app.astronomy.whatsup import _safe_first


class _FakeTime:
    """Stand-in for a Skyfield Time object exposing only .utc_datetime()."""

    def __init__(self, value):
        self._value = value

    def utc_datetime(self):
        return self._value


def test_returns_none_for_none_input():
    assert _safe_first(None) is None


def test_returns_none_for_empty_array():
    assert _safe_first([]) is None
    assert _safe_first(np.array([])) is None


def test_returns_datetime_from_scalar_time_with_no_len():
    dt = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    assert _safe_first(_FakeTime(dt)) == dt


def test_returns_datetime_from_first_element_of_array():
    dt = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    other = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    assert _safe_first([_FakeTime(dt), _FakeTime(other)]) == dt


def test_unwraps_a_list_result_from_utc_datetime_to_its_first_element():
    # REGRESSION: a vectorized Skyfield Time can return a list/ndarray from
    # utc_datetime() even for what looks like a single element -- the
    # function must unwrap that to a plain datetime, not leak the array out.
    dt = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    other = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    assert _safe_first(_FakeTime([dt, other])) == dt
    assert _safe_first(_FakeTime(np.array([dt, other]))) == dt


def test_returns_none_when_utc_datetime_raises():
    class _BrokenTime:
        def utc_datetime(self):
            raise RuntimeError("boom")

    assert _safe_first(_BrokenTime()) is None
