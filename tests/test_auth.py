"""Tests for optional API key authentication."""

import pytest
from fastapi.testclient import TestClient


def test_open_mode_no_key_required(client):
    """Without LAPO_API_KEYS set, all requests pass through."""
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_auth_enforced_when_keys_configured(monkeypatch):
    """When LAPO_API_KEYS is set, missing key returns 401."""
    import app.config as cfg
    import app.auth as auth_mod

    monkeypatch.setattr(cfg, "LAPO_API_KEYS", {"secret-key-123"})
    monkeypatch.setattr(cfg, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(auth_mod, "LAPO_API_KEYS", {"secret-key-123"})
    monkeypatch.setattr(auth_mod, "API_AUTH_ENABLED", True)

    from app.main import app
    c = TestClient(app, follow_redirects=True)

    # No key → 401
    response = c.get("/v1/health")
    assert response.status_code == 401

    # Wrong key → 401
    response = c.get("/v1/health", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401

    # Correct key → 200
    response = c.get("/v1/health", headers={"X-API-Key": "secret-key-123"})
    assert response.status_code == 200
