from app.services.weather_api import _reshape_weather_item


def _base_item(**overrides):
    item = {
        "main": {"temp": 20.0, "humidity": 50, "pressure": 1013},
        "wind": {"speed": 2.0, "deg": 180},
        "clouds": {"all": 10},
        "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
    }
    item.update(overrides)
    return item


def test_feels_like_omitted_when_equal_to_actual_temperature():
    # 20C / 2 m/s wind / 50% humidity is outside both the wind-chill and
    # heat-index bands, so feels_like_temp returns the input unchanged --
    # the reshaped output should not carry a redundant feels_like key.
    result = _reshape_weather_item(_base_item())
    assert "feels_like" not in result["temperature"]


def test_feels_like_included_when_it_differs_from_actual_temperature():
    # Cold + windy triggers NOAA wind chill, so feels_like_temp returns a
    # different value than the raw temperature.
    item = _base_item(main={"temp": -10.0, "humidity": 50, "pressure": 1013}, wind={"speed": 10.0, "deg": 180})
    result = _reshape_weather_item(item)
    assert "feels_like" in result["temperature"]
    assert result["temperature"]["feels_like"]["celsius"] < result["temperature"]["celsius"]


def test_min_max_omitted_when_equal():
    item = _base_item(main={"temp": 20.0, "temp_min": 20.0, "temp_max": 20.0, "humidity": 50, "pressure": 1013})
    result = _reshape_weather_item(item)
    assert "min" not in result["temperature"]
    assert "max" not in result["temperature"]


def test_min_max_included_when_different():
    item = _base_item(main={"temp": 20.0, "temp_min": 18.0, "temp_max": 23.0, "humidity": 50, "pressure": 1013})
    result = _reshape_weather_item(item)
    assert result["temperature"]["min"]["celsius"] == 18.0
    assert result["temperature"]["max"]["celsius"] == 23.0


def test_min_max_omitted_when_absent():
    result = _reshape_weather_item(_base_item())
    assert "min" not in result["temperature"]
    assert "max" not in result["temperature"]


def test_ground_level_pressure_falls_back_to_grnd_level_when_pressure_missing():
    item = _base_item(main={"temp": 20.0, "humidity": 50, "grnd_level": 987})
    result = _reshape_weather_item(item)
    assert result["groundLevelPressure"] == 987


def test_visibility_included_when_present():
    item = _base_item(visibility=16093)
    result = _reshape_weather_item(item)
    assert result["visibility"]["km"] == 16.09
    assert 9.99 <= result["visibility"]["mi"] <= 10.01


def test_visibility_omitted_when_absent():
    result = _reshape_weather_item(_base_item())
    assert "visibility" not in result


def test_dt_formatted_when_tz_name_and_dt_provided():
    item = _base_item(dt=1750000000)
    result = _reshape_weather_item(item, tz_name="America/Chicago")
    assert "dt" in result
    assert result["dt"].startswith("2025-06-15")


def test_dt_omitted_when_tz_name_not_provided():
    item = _base_item(dt=1750000000)
    result = _reshape_weather_item(item)
    assert "dt" not in result


def test_weather_array_builds_description_and_icon_url():
    result = _reshape_weather_item(_base_item())
    assert result["weather"] == [{
        "description": "Clear",
        "longDescription": "clear sky",
        "iconurl": "http://openweathermap.org/img/w/01d.png",
    }]


def test_weather_array_empty_when_no_weather_entries():
    item = _base_item(weather=[])
    result = _reshape_weather_item(item)
    assert result["weather"] == []
