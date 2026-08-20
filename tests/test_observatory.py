from datetime import datetime as real_datetime
from unittest.mock import patch

from app.config import DEFAULT_TZ


def test_hours_uses_observatory_local_time_not_server_time(client):
    # Regression test: /hours previously called datetime.now() with no
    # timezone, which on a server running in UTC (e.g. Heroku) does not
    # represent Lake Afton's local wall-clock time. That could make the
    # endpoint compute the wrong "next Saturday" / month around day
    # boundaries. Assert it now anchors on the observatory's local time zone.
    with patch("app.routes.observatory.datetime") as mock_dt:
        mock_dt.now.side_effect = lambda *a, **kw: real_datetime.now(*a, **kw)
        client.get("/v1/hours")
        assert mock_dt.now.called
        args, kwargs = mock_dt.now.call_args
        tz_arg = args[0] if args else kwargs.get("tz")
        assert tz_arg is not None
        assert str(tz_arg) == DEFAULT_TZ


def test_tonight_uses_observatory_local_time_not_server_time(client):
    with patch("app.routes.observatory.datetime") as mock_dt:
        mock_dt.now.side_effect = lambda *a, **kw: real_datetime.now(*a, **kw)
        client.get("/v1/tonight")
        assert mock_dt.now.called
        args, kwargs = mock_dt.now.call_args
        tz_arg = args[0] if args else kwargs.get("tz")
        assert tz_arg is not None
        assert str(tz_arg) == DEFAULT_TZ


def test_root(client):
    response = client.get("/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome" in data["message"]


def test_health(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data


def test_hours(client):
    response = client.get("/v1/hours")
    assert response.status_code == 200
    data = response.json()
    assert "hours" in data
    hours = data["hours"]
    assert "prettyHours" in hours
    assert "open" in hours
    assert "close" in hours


def test_schedule(client):
    response = client.get("/v1/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
    assert "message" in data
    assert "lakeafton.com" in data["message"]


def test_tonight(client):
    response = client.get("/v1/tonight")
    assert response.status_code == 200
    data = response.json()
    assert "observatory" in data
    obs = data["observatory"]
    assert "openTonight" in obs
    assert "sessionActive" in obs
    assert "sessionDate" in obs
    assert "hours" in obs
    # weather/seeing/objects may be None without API keys — that's acceptable
    assert "weather" in data
    assert "seeing" in data
    assert "objects" in data


def test_legacy_redirect(client):
    # Root-level paths still redirect to /v1/ observatory routes
    response = client.get("/health", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/v1/health"

    # Old flat /v1/ paths redirect to namespaced routes
    response = client.get("/v1/planets", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/v1/celestial/planets"

    response = client.get("/v1/weather", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/v1/weather/current"

    response = client.get("/v1/iss", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/v1/satellites/iss"
