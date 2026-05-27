from app.utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    mps_to_mph,
    meters_to_miles,
    round_off,
    feels_like_temp,
    get_observatory_hours,
    validate_lat,
    validate_lon,
)


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(-40) == -40
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212


def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(-40) == -40
    assert fahrenheit_to_celsius(32) == 0
    assert fahrenheit_to_celsius(212) == 100


def test_mps_to_mph():
    assert mps_to_mph(0) == 0
    assert mps_to_mph(13.4112) == 30
    assert mps_to_mph(33.528) == 75


def test_meters_to_miles():
    assert meters_to_miles(16093.44) == 10
    result = meters_to_miles(10000)
    assert 6.21 < result < 6.22


def test_round_off():
    assert round_off(3.14159, 2) == 3.14
    assert round_off(123.456789, 3) == 123.457


def test_wind_chill():
    result = feels_like_temp(5, 3, 0)
    assert 2.50 <= result <= 2.51
    result = feels_like_temp(0, 10, 0)
    assert -7.04 <= result <= -7.03
    result = feels_like_temp(11, 10, 0)
    assert 10.99 <= result <= 11.01


def test_heat_index():
    result = feels_like_temp(27, 0, 15)
    assert 26.98 <= result <= 27.99
    result = feels_like_temp(30, 0, 50)
    assert 31.04 <= result <= 31.05
    result = feels_like_temp(40, 0, 40)
    assert 48.26 <= result <= 48.27
    result = feels_like_temp(50, 0, 75)
    assert 49.99 <= result <= 50.01


def test_observatory_hours_summer():
    h = get_observatory_hours(6)
    assert h["display"]["open"] == "9:00pm"
    assert h["h24"]["open"] == "21:00"


def test_observatory_hours_winter():
    h = get_observatory_hours(12)
    assert h["display"]["open"] == "7:30pm"
    assert h["h24"]["close"] == "21:30"


def test_observatory_hours_spring():
    h = get_observatory_hours(3)
    assert h["display"]["open"] == "8:30pm"


def test_validate_lat():
    assert validate_lat("37.6") == 37.6
    assert validate_lat("91") is None
    assert validate_lat(None) is None


def test_validate_lon():
    assert validate_lon("-97.6") == -97.6
    assert validate_lon("181") is None
    assert validate_lon(None) is None
