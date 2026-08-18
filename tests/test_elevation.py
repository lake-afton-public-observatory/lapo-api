import pytest

from app.services import elevation


class _FakeSRTM:
    def __init__(self, value=None, raises=None):
        self._value = value
        self._raises = raises
        self.call_count = 0

    def get_elevation(self, lat, lon):
        self.call_count += 1
        if self._raises is not None:
            raise self._raises
        return self._value


@pytest.fixture(autouse=True)
def clear_elevation_cache():
    # get_elevation is wrapped in a module-level TTLCache -- without
    # clearing it, whichever test runs first would poison the cache for
    # every test after it that reuses the same (lat, lon) pair.
    elevation._elevation_cache.clear()
    yield
    elevation._elevation_cache.clear()


def test_get_elevation_returns_srtm_value_as_float(monkeypatch):
    fake = _FakeSRTM(value=412)
    monkeypatch.setattr(elevation, "_get_srtm", lambda: fake)

    result = elevation.get_elevation(37.5, -97.6)

    assert result == 412.0
    assert isinstance(result, float)


def test_get_elevation_returns_zero_when_srtm_has_no_data(monkeypatch):
    # REGRESSION-SHAPED: srtm.py returns None for coordinates outside its
    # coverage (e.g. open ocean) -- this must not propagate None to callers
    # that expect a float.
    fake = _FakeSRTM(value=None)
    monkeypatch.setattr(elevation, "_get_srtm", lambda: fake)

    result = elevation.get_elevation(0.0, 0.0)

    assert result == 0.0


def test_get_elevation_returns_zero_and_does_not_raise_on_srtm_error(monkeypatch):
    # REGRESSION-SHAPED: a corrupt/missing SRTM tile download must not crash
    # the request -- the function explicitly swallows and falls back to 0.0.
    fake = _FakeSRTM(raises=OSError("tile download failed"))
    monkeypatch.setattr(elevation, "_get_srtm", lambda: fake)

    result = elevation.get_elevation(51.5, -0.1)

    assert result == 0.0


def test_get_elevation_caches_repeated_calls_for_the_same_coordinates(monkeypatch):
    fake = _FakeSRTM(value=100)
    monkeypatch.setattr(elevation, "_get_srtm", lambda: fake)

    elevation.get_elevation(10.0, 20.0)
    elevation.get_elevation(10.0, 20.0)

    assert fake.call_count == 1


def test_get_elevation_does_not_share_cache_across_different_coordinates(monkeypatch):
    fake = _FakeSRTM(value=100)
    monkeypatch.setattr(elevation, "_get_srtm", lambda: fake)

    elevation.get_elevation(10.0, 20.0)
    elevation.get_elevation(30.0, 40.0)

    assert fake.call_count == 2
