from unittest.mock import patch


def _weather_response(**overrides):
    data = {
        "temperature": {"celsius": 20.0, "fahrenheit": 68.0},
        "wind": {"speed": {"metersPerSecond": 2.0, "milesPerHour": 4.47}, "direction": 180},
        "groundLevelPressure": 1013,
        "humidity": 50,
        "clouds": 10,
        "weather": [{"description": "Clear", "longDescription": "clear sky", "iconurl": "x"}],
    }
    data.update(overrides)
    return data


def test_weather_current_returns_the_reshaped_response(client):
    with patch("app.routes.weather.get_weather", return_value=_weather_response()) as mock_get:
        resp = client.get("/v1/weather/current")
    assert resp.status_code == 200
    assert resp.json()["temperature"]["fahrenheit"] == 68.0
    mock_get.assert_called_once()


def test_weather_current_returns_400_for_an_invalid_lat(client):
    # REGRESSION-SHAPED: mirrors the same fix already covered at the route
    # level for /celestial/visiblePlanets and /satellites/* -- an invalid
    # supplied lat must be rejected, not silently swapped for LAPO's own
    # default location (see resolve_lat_lon's docstring).
    resp = client.get("/v1/weather/current", params={"lat": "999"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid lat parameter"


def test_weather_current_returns_400_for_an_unparseable_lon(client):
    resp = client.get("/v1/weather/current", params={"lon": "not-a-number"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid lon parameter"


def test_weather_current_returns_502_on_exception(client):
    with patch("app.routes.weather.get_weather", side_effect=RuntimeError("boom")):
        resp = client.get("/v1/weather/current")
    assert resp.status_code == 502
    assert "error" in resp.json()


def test_weather_forecast_returns_the_reshaped_response(client):
    data = {"city": {"name": "Wichita"}, "cnt": 1, "list": [_weather_response()]}
    with patch("app.routes.weather.get_forecast", return_value=data) as mock_get:
        resp = client.get("/v1/weather/forecast")
    assert resp.status_code == 200
    assert resp.json()["cnt"] == 1
    mock_get.assert_called_once()


def test_weather_forecast_returns_400_for_an_invalid_lat(client):
    resp = client.get("/v1/weather/forecast", params={"lat": "999"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid lat parameter"


def test_weather_forecast_returns_502_on_exception(client):
    with patch("app.routes.weather.get_forecast", side_effect=RuntimeError("boom")):
        resp = client.get("/v1/weather/forecast")
    assert resp.status_code == 502
    assert "error" in resp.json()
