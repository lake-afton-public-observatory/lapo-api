import httpx
from cachetools import TTLCache, cached
from datetime import datetime, timezone
import pytz
from app.utils import (
    celsius_to_fahrenheit,
    mps_to_mph,
    meters_to_miles,
    round_off,
    feels_like_temp,
)

_weather_cache = TTLCache(maxsize=64, ttl=60)
_forecast_cache = TTLCache(maxsize=64, ttl=300)


def _format_dt(epoch: int, tz_name: str) -> str:
    try:
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        return dt.astimezone(pytz.timezone(tz_name)).isoformat()
    except Exception:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _reshape_weather_item(item: dict, tz_name: str = None) -> dict:
    temp_c = item["main"]["temp"]
    wind_speed = item["wind"]["speed"]
    humidity = item["main"]["humidity"]
    fl = feels_like_temp(temp_c, wind_speed, humidity)

    temp_obj = {
        "celsius": temp_c,
        "fahrenheit": round_off(celsius_to_fahrenheit(temp_c), 2),
    }
    if fl != temp_c:
        temp_obj["feels_like"] = {
            "celsius": round_off(fl, 2),
            "fahrenheit": round_off(celsius_to_fahrenheit(fl), 2),
        }

    temp_min = item["main"].get("temp_min")
    temp_max = item["main"].get("temp_max")
    if temp_min is not None and temp_max is not None and temp_min != temp_max:
        temp_obj["min"] = {
            "celsius": temp_min,
            "fahrenheit": round_off(celsius_to_fahrenheit(temp_min), 2),
        }
        temp_obj["max"] = {
            "celsius": temp_max,
            "fahrenheit": round_off(celsius_to_fahrenheit(temp_max), 2),
        }

    result = {
        "temperature": temp_obj,
        "wind": {
            "speed": {
                "metersPerSecond": wind_speed,
                "milesPerHour": round_off(mps_to_mph(wind_speed), 2),
            },
            "direction": item["wind"].get("deg"),
        },
        "groundLevelPressure": item["main"].get("pressure") or item["main"].get("grnd_level"),
        "humidity": humidity,
        "clouds": item.get("clouds", {}).get("all"),
        "weather": [],
    }

    for w in item.get("weather", []):
        result["weather"].append({
            "description": w.get("main", ""),
            "longDescription": w.get("description", ""),
            "iconurl": f"http://openweathermap.org/img/w/{w.get('icon', '')}.png",
        })

    if "visibility" in item:
        vis = item["visibility"]
        result["visibility"] = {
            "km": round_off(vis / 1000, 2),
            "mi": round_off(meters_to_miles(vis), 2),
        }

    if tz_name and "dt" in item:
        result["dt"] = _format_dt(item["dt"], tz_name)

    return result


@cached(cache=_weather_cache, key=lambda lat, lon, key, tz=None: (lat, lon, tz))
def get_weather(lat: float, lon: float, key: str, tz: str = None) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&units=metric&APPID={key}"
    )
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return _reshape_weather_item(data, tz)


@cached(cache=_forecast_cache, key=lambda lat, lon, key, tz=None: (lat, lon, tz))
def get_forecast(lat: float, lon: float, key: str, tz: str = None) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&units=metric&APPID={key}"
    )
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    forecasts = []
    for item in data.get("list", []):
        reshaped = _reshape_weather_item(item, tz)
        reshaped["seaLevelPressure"] = item["main"].get("sea_level")
        reshaped["groundLevelPressure"] = item["main"].get("grnd_level")
        forecasts.append(reshaped)

    return {
        "city": data.get("city"),
        "cnt": data.get("cnt"),
        "list": forecasts,
    }
