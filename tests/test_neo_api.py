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
        "is_potentially_hazardous_asteroid": True,
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


def test_get_neo_list_strips_per_neo_links_and_sentry_flag_but_preserves_pha_flag(monkeypatch):
    # REGRESSION: is_potentially_hazardous_asteroid was previously stripped
    # alongside links/is_sentry_object, contradicting the /space/neo route's
    # own docstring promise of "a flag for potentially hazardous objects
    # (PHAs)" -- the PHA flag is the actual headline value of a near-earth
    # object endpoint and must survive the reshape.
    data = {"near_earth_objects": {"2026-01-01": [_base_neo()]}}
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    neo = result["near_earth_objects"]["2026-01-01"][0]

    assert "links" not in neo
    assert "is_sentry_object" not in neo
    assert neo["is_potentially_hazardous_asteroid"] is True


def test_get_neo_list_converts_epoch_to_localized_full_date_and_drops_epoch(monkeypatch):
    data = {"near_earth_objects": {"2026-01-01": [_base_neo()]}}
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    ca = result["near_earth_objects"]["2026-01-01"][0]["close_approach_data"][0]

    assert "epoch_date_close_approach" not in ca
    assert "close_approach_date_full" in ca


def test_get_neo_list_handles_a_neo_with_no_close_approach_data(monkeypatch):
    data = {
        "near_earth_objects": {
            "2026-01-01": [_base_neo(close_approach_data=[])]
        }
    }
    monkeypatch.setattr(neo_api.httpx, "get", lambda *a, **k: _FakeResponse(data))

    result = neo_api.get_neo_list("2026-01-01", "2026-01-02", "America/Chicago", "key")
    neo = result["near_earth_objects"]["2026-01-01"][0]

    assert neo["close_approach_data"] == []
