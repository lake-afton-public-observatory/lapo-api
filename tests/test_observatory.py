def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome" in data["message"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data


def test_hours(client):
    response = client.get("/hours")
    assert response.status_code == 200
    data = response.json()
    assert "hours" in data
    hours = data["hours"]
    assert "prettyHours" in hours
    assert "open" in hours
    assert "close" in hours


def test_schedule(client):
    response = client.get("/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
