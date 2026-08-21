from datetime import datetime, timezone


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_iss_treats_offsetless_dt_as_utc(client, monkeypatch):
    # REGRESSION: a `dt` query param with no UTC offset (e.g.
    # "2024-06-15T12:00:00") parses to a naive datetime via dateutil. Naive
    # datetime.timestamp() is interpreted in the *server's* local timezone,
    # not UTC -- unlike the no-dt default path, which is explicitly
    # `datetime.now(tz=timezone.utc)`. Confirm the epoch sent to
    # WhereTheISS matches the UTC interpretation of the given wall-clock
    # time, not some other timezone's interpretation of it.
    from app.services import iss as iss_service

    captured = {}

    def fake_get(url, timeout=None):
        captured["url"] = url
        return _FakeResponse({
            "timestamp": 1718452800,
            "altitude": 400.0,
            "velocity": 27000.0,
            "latitude": 0,
            "longitude": 0,
            "units": "kilometers",
            "footprint": 1,
            "daynum": 1,
            "solar_lat": 1,
            "solar_lon": 1,
        })

    monkeypatch.setattr(iss_service.httpx, "get", fake_get)

    resp = client.get("/v1/satellites/iss", params={"dt": "2024-06-15T12:00:00"})
    assert resp.status_code == 200

    expected_epoch = int(datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    assert f"timestamp={expected_epoch}" in captured["url"]
