from datetime import datetime
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


def test_hours_uses_todays_own_month_when_today_is_saturday(client, monkeypatch):
    # REGRESSION-SHAPED: the route used to have an unreachable dead-code
    # branch (`days_ahead == 0 and now.weekday() != day_anchor`, which can
    # never be true since days_ahead is only 0 when weekday() == day_anchor)
    # that made it look like Saturday was special-cased to force a jump to
    # *next* Saturday. It wasn't reachable, so the real behavior -- use
    # today's own hours when today already is the anchor day -- was
    # completely unverified. 2026-08-22 is a Saturday.
    import app.routes.observatory as observatory

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 22)

    monkeypatch.setattr(observatory, "datetime", _FixedDatetime)
    captured_month = {}

    def fake_get_observatory_hours(month):
        captured_month["month"] = month
        return {"display": {"open": "x", "close": "y"}}

    monkeypatch.setattr(observatory, "get_observatory_hours", fake_get_observatory_hours)

    response = client.get("/v1/hours")

    assert response.status_code == 200
    assert captured_month["month"] == 8


def test_hours_advances_across_a_month_boundary_to_the_next_saturday(client, monkeypatch):
    # 2026-08-31 is a Monday; the next Saturday is 2026-09-05, crossing into
    # September. If the day-advance math regressed, this would still report
    # August's hours instead of September's.
    import app.routes.observatory as observatory

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 31)

    monkeypatch.setattr(observatory, "datetime", _FixedDatetime)
    captured_month = {}

    def fake_get_observatory_hours(month):
        captured_month["month"] = month
        return {"display": {"open": "x", "close": "y"}}

    monkeypatch.setattr(observatory, "get_observatory_hours", fake_get_observatory_hours)

    response = client.get("/v1/hours")

    assert response.status_code == 200
    assert captured_month["month"] == 9


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
