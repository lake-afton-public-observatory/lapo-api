from app.services import astropical


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_get_planet_ephem_requests_https(monkeypatch):
    # REGRESSION: this previously called astropical.space over plain HTTP
    # while every other external API in this repo (Celestrak, wheretheiss.at,
    # NASA) uses HTTPS -- lat/lon and the returned ephemeris data were sent
    # unencrypted for no reason, since the site supports HTTPS.
    astropical._cache.clear()
    captured_url = {}

    def fake_get(url, timeout=None):
        captured_url["url"] = url
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(astropical.httpx, "get", fake_get)

    astropical.get_planet_ephem(37.5, -97.6)

    assert captured_url["url"].startswith("https://astropical.space/")


def test_get_planet_ephem_returns_response_json(monkeypatch):
    astropical._cache.clear()
    monkeypatch.setattr(astropical.httpx, "get", lambda url, timeout=None: _FakeResponse({"sun": {"alt": 12.3}}))

    result = astropical.get_planet_ephem(1.0, 2.0)

    assert result == {"sun": {"alt": 12.3}}
