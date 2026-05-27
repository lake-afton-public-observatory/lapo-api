import json
import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import pytz
from dateutil import parser as dateutil_parser

from app.config import (
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ,
    GOOGLE_PLACES_API_KEY, OPENWEATHERMAP_API_KEY,
)
from app.services.elevation import get_elevation
from app.services.weather_api import get_weather
from app.services.astropical import get_planet_ephem
from app.astronomy import whatsup as wu
from app.astronomy.whatsup import get_location, get_data, whats_up, OBJECT_DICT
from app.utils import validate_lat, validate_lon, parse_date, get_observatory_hours

router = APIRouter()


def _build_location(lat, lon, tz_name, dt_str=None):
    """Build an ephem Observer with weather-based pressure/temp."""
    elev = get_elevation(lat, lon, GOOGLE_PLACES_API_KEY)
    weather_data = get_weather(lat, lon, OPENWEATHERMAP_API_KEY)
    pressure = weather_data.get("groundLevelPressure")
    temp = weather_data.get("temperature", {}).get("celsius", 25)

    date = datetime.datetime.now()
    if dt_str:
        date = dateutil_parser.parse(dt_str)
    if date.tzinfo is None:
        date = pytz.timezone(tz_name).localize(date)
    date = date.astimezone(pytz.utc)

    return get_location(str(lat), str(lon), elev, date, temp=temp, pressure=pressure), date


def _serialize(data, tz_name):
    """Serialize response with datetime handling via the Encoder class."""
    wu.tz = tz_name
    return json.loads(json.dumps(data, cls=wu.Encoder))


@router.get("/visiblePlanets")
async def visible_planets(lat: str = None, lon: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON

        data = get_planet_ephem(lat_f, lon_f)
        planets = data.get("response")
        if planets is None:
            return data

        visible = []
        for p in planets:
            if p["alt"] > 0:
                mag = p["mag"]
                if mag > 6.5:
                    brightness = "not visible to naked eye"
                elif mag >= 2:
                    brightness = "dim"
                elif mag >= 1:
                    brightness = "average"
                elif mag >= 0:
                    brightness = "bright"
                elif mag >= -3:
                    brightness = "very bright"
                else:
                    brightness = "extremely bright"

                visible.append({
                    "name": p["name"],
                    "altitudeDegrees": p["alt"],
                    "distanceFromEarthAU": p["au_earth"],
                    "distanceFromEarthMiles": (p["au_earth"] * 149597870700) / 1609.344,
                    "magnitude": mag,
                    "brightness": brightness,
                    "constellation": p["const"],
                })
        return visible
    except Exception as e:
        print(f"Error in /visiblePlanets: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch planet data"})


@router.get("/planets")
async def planets(lat: str = None, lon: str = None, tz: str = None, dt: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ

        location, _ = _build_location(lat_f, lon_f, tz_name, dt)
        bodies = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
        query_set = set(bodies) & set(OBJECT_DICT.keys())
        query_list = [OBJECT_DICT[k] for k in query_set]
        result = get_data(query_list, location)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /planets: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch planet data"})


@router.get("/sun")
async def sun(lat: str = None, lon: str = None, tz: str = None, dt: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ

        location, _ = _build_location(lat_f, lon_f, tz_name, dt)
        query_list = [OBJECT_DICT["sun"]]
        result = get_data(query_list, location)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /sun: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch sun data"})


@router.get("/moon")
async def moon(lat: str = None, lon: str = None, tz: str = None, dt: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ

        location, _ = _build_location(lat_f, lon_f, tz_name, dt)
        query_list = [OBJECT_DICT["moon"]]
        result = get_data(query_list, location)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /moon: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch moon data"})


@router.get("/whatsup")
async def whatsup(lat: str = None, lon: str = None, tz: str = None, start: str = None, end: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ

        location, date = _build_location(lat_f, lon_f, tz_name, start)

        end_dt = parse_date(end, tz_name)
        if end_dt:
            end_dt = end_dt.astimezone(pytz.utc)
        if end_dt is None or end_dt < date:
            end_dt = date

        result = whats_up(date, end_dt, location, magnitude=6)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /whatsup: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch sky data"})


@router.get("/whatsup-next")
@router.get("/whatsup_next")
async def whatsup_next():
    try:
        lat = DEFAULT_LAT
        lon = DEFAULT_LON
        tz_name = DEFAULT_TZ

        now = datetime.datetime.now()
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        upcoming_sunday = now + datetime.timedelta(days=days_until_sunday)
        friday = upcoming_sunday - datetime.timedelta(days=2)
        saturday = upcoming_sunday - datetime.timedelta(days=1)

        month = friday.month
        hours = get_observatory_hours(month)
        open_time = hours["h24"]["open"]
        close_time = hours["h24"]["close"]

        friday_str = friday.strftime("%Y-%m-%d")
        saturday_str = saturday.strftime("%Y-%m-%d")

        close_dt = dateutil_parser.parse(f"{friday_str}T{close_time}")
        close_dt = pytz.timezone(tz_name).localize(close_dt)

        if close_dt > pytz.timezone(tz_name).localize(now):
            open_str = f"{friday_str}T{open_time}"
            close_str = f"{friday_str}T{close_time}"
        else:
            open_str = f"{saturday_str}T{open_time}"
            close_str = f"{saturday_str}T{close_time}"

        location, start_dt = _build_location(lat, lon, tz_name, open_str)
        end_dt = dateutil_parser.parse(close_str)
        if end_dt.tzinfo is None:
            end_dt = pytz.timezone(tz_name).localize(end_dt)
        end_dt = end_dt.astimezone(pytz.utc)

        result = whats_up(start_dt, end_dt, location, magnitude=6)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /whatsup-next: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch sky data"})
