import json
import time
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import pytz
from dateutil import parser as dateutil_parser

from app.config import (
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ,
    GOOGLE_PLACES_API_KEY, OPENWEATHERMAP_API_KEY,
)
from app.utils import get_observatory_hours
from app.services.elevation import get_elevation
from app.services.weather_api import get_weather
from app.astronomy import whatsup as wu_module
from app.astronomy.whatsup import get_location, whats_up

router = APIRouter()
_start_time = time.time()


@router.get("/")
async def root():
    return {
        "message": "Welcome to the Lake Afton Public Observatory API! "
        "To contribute, visit https://github.com/lake-afton-public-observatory/lapo-api"
    }


@router.get("/health")
async def health():
    return {"status": "ok", "uptime": time.time() - _start_time}


@router.get("/hours")
async def hours():
    now = datetime.now()
    day_anchor = 5  # Saturday
    days_ahead = (day_anchor - now.weekday()) % 7
    if days_ahead == 0 and now.weekday() != day_anchor:
        days_ahead = 7
    if days_ahead > 0:
        now = now + timedelta(days=days_ahead)
    month = now.month
    h = get_observatory_hours(month)
    return {
        "hours": {
            "prettyHours": f"{h['display']['open']} – {h['display']['close']}",
            "open": h["display"]["open"],
            "close": h["display"]["close"],
        }
    }


@router.get("/schedule")
async def schedule():
    return {
        "schedule": None,
        "message": "Viewing schedules are not available via this API. See https://www.lakeafton.com for current programs.",
    }


@router.get("/tonight")
async def tonight():
    """Aggregate endpoint: observatory status, weather, seeing conditions, and visible objects for tonight's session."""
    lat = DEFAULT_LAT
    lon = DEFAULT_LON
    tz_name = DEFAULT_TZ
    tz = pytz.timezone(tz_name)

    # Determine the next open session (Fri or Sat)
    now = datetime.now()
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    upcoming_sunday = now + timedelta(days=days_until_sunday)
    friday = upcoming_sunday - timedelta(days=2)
    saturday = upcoming_sunday - timedelta(days=1)

    month = friday.month
    obs_hours = get_observatory_hours(month)
    open_time = obs_hours["h24"]["open"]
    close_time = obs_hours["h24"]["close"]

    friday_str = friday.strftime("%Y-%m-%d")
    saturday_str = saturday.strftime("%Y-%m-%d")

    friday_close = tz.localize(dateutil_parser.parse(f"{friday_str}T{close_time}"))
    now_local = tz.localize(now)

    if friday_close > now_local:
        session_date = friday_str
    else:
        session_date = saturday_str

    open_dt = tz.localize(dateutil_parser.parse(f"{session_date}T{open_time}"))
    close_dt = tz.localize(dateutil_parser.parse(f"{session_date}T{close_time}"))

    is_open_tonight = now.weekday() in (4, 5)  # Friday=4, Saturday=5
    session_active = open_dt <= now_local <= close_dt

    result = {
        "observatory": {
            "openTonight": is_open_tonight,
            "sessionActive": session_active,
            "sessionDate": session_date,
            "hours": obs_hours["display"],
            "sessionOpen": open_dt.isoformat(),
            "sessionClose": close_dt.isoformat(),
        },
        "weather": None,
        "seeing": None,
        "objects": None,
    }

    # Weather — degrades gracefully if API key missing
    try:
        wx = get_weather(lat, lon, OPENWEATHERMAP_API_KEY, tz_name)
        clouds = wx.get("clouds") or 0
        if clouds < 20:
            conditions = "excellent"
        elif clouds < 40:
            conditions = "good"
        elif clouds < 60:
            conditions = "fair"
        elif clouds < 80:
            conditions = "poor"
        else:
            conditions = "cloudy"
        result["weather"] = wx
        result["seeing"] = {"cloudCoverPercent": clouds, "conditions": conditions}
    except Exception:
        pass

    # Sky objects — degrades gracefully if API keys missing
    try:
        wx_data = result["weather"] or {}
        pressure = wx_data.get("groundLevelPressure")
        temp = (wx_data.get("temperature") or {}).get("celsius", 25)
        elev = get_elevation(lat, lon, GOOGLE_PLACES_API_KEY)

        start_utc = open_dt.astimezone(pytz.utc)
        close_utc = close_dt.astimezone(pytz.utc)

        location = get_location(str(lat), str(lon), elev, start_utc, temp=temp, pressure=pressure)
        objects = whats_up(start_utc, close_utc, location, magnitude=6)

        wu_module.tz = tz_name
        result["objects"] = json.loads(json.dumps(objects, cls=wu_module.Encoder))
    except Exception:
        pass

    return result
