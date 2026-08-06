import pytest

from app.services import neo_api


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def _base_neo(**overrides):
    neo = {
        "id": "1",
        "name": "(2026 AB)",
        "links": {"self": "http://example.com"},
        "is_potentially_hazardous_asteroid": False,
        "is_sentry_object": False,
        "close_approach_data": [
            {"epoch_date_close_approach": 1750000000000, "orbiting_body": "Earth"}
        ],
    }
    neo.update(overrides)
    return neo


def test_get_neo_list_raises_when_response_contains_an_error(monkeypatch):
    monkeypatch.setattr(
        neo_api.httpx, "get",
        lambda *a, **k: _FakeResponse({"error": "boom"}),
    )
    with pytest.raises(Exception, match="boom"):
        neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")


def test_get_neo_list_strips_top_level_links(monkeypatch):
    monkeypatch.setattr(
        neo_api.httpx, "get",
        lambda *a, **k: _FakeResponse({"links": {"self": "x"}, "near_earth_objects": {}}),
    )
    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    assert "links" not in result


def test_get_neo_list_strips_per_neo_fields(monkeypatch):
    data = {"near_earth_objects": {"2026-01-01": [_base_neo()]}}
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    neo = result["near_earth_objects"]["2026-01-01"][0]

    assert "links" not in neo
    assert "is_potentially_hazardous_asteroid" not in neo
    assert "is_sentry_object" not in neo


def test_get_neo_list_converts_epoch_to_localized_full_date_and_drops_epoch(monkeypatch):
    data = {"near_earth_objects": {"2026-01-01": [_base_neo()]}}
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    ca = result["near_earth_objects"]["2026-01-01"][0]["close_approach_data"][0]

    assert "epoch_date_close_approach" not in ca
    assert ca["close_approach_date_full"].startswith("2025-06-15")
    assert ca["orbiting_body"] == "Earth"


def test_get_neo_list_handles_a_neo_with_no_close_approach_data(monkeypatch):
    # REGRESSION-SHAPED: close_approach_data is only ever accessed behind a
    # truthiness check -- an empty list must not raise an IndexError trying
    # to read close_approach_data[0].
    data = {"near_earth_objects": {"2026-01-01": [_base_neo(close_approach_data=[])]}}
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")

    assert result["near_earth_objects"]["2026-01-01"][0]["close_approach_data"] == []
