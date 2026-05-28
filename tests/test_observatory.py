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


def test_legacy_redirect(client):
    response = client.get("/health", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/v1/health"
