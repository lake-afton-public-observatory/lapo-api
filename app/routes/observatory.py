import json
import time
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import pytz
from dateutil import parser as dateutil_parser

from app.config import (
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ,
    OPENWEATHERMAP_API_KEY,
)
from app.utils import get_observatory_hours
from app.services.elevation import get_elevation
from app.services.weather_api import get_weather
from app.astronomy import whatsup as wu_module
from app.astronomy.whatsup import get_location, whats_up

router = APIRouter()
_start_time = time.time()


@router.get(
    "/",
    summary="API root",
    description="Returns a welcome message and link to the source repository.",
)
async def root():
    return {
        "message": "Welcome to the Lake Afton Public Observatory API! "
        "To contribute, visit https://github.com/lake-afton-public-observatory/lapo-api"
    }


@router.get(
    "/health",
    summary="Health check",
    description="Returns API status and uptime in seconds.",
)
async def health():
    return {"status": "ok", "uptime": time.time() - _start_time}


@router.get(
    "/hours",
    summary="Observatory hours",
    description=(
        "Returns the operating hours for the upcoming Saturday session at Lake Afton "
        "Public Observatory. Hours shift seasonally with sunset times."
    ),
)
async def hours():
    # Use the observatory's local wall-clock time, not the server's local time
    # (which is UTC in production, e.g. on Heroku). Using datetime.now() directly
    # would make "today"/"this weekday" wrong by several hours, which can flip
    # which day (and therefore which month's hours) this endpoint reports.
    now = datetime.now(pytz.timezone(DEFAULT_TZ)).replace(tzinfo=None)
    day_anchor = 5  # Saturday
    # (day_anchor - now.weekday()) % 7 is 0 exactly when today already is
    # day_anchor, so today's own hours are used (not next Saturday's) when
    # the check falls on a Saturday.
    days_ahead = (day_anchor - now.weekday()) % 7
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


@router.get(
    "/schedule",
    summary="Viewing schedule",
    description=(
        "Weekly viewing program description. Live schedules are managed on "
        "the observatory website — see the `message` field for a direct link."
    ),
)
async def schedule():
    return {
        "schedule": None,
        "message": "Viewing schedules are not available via this API. See https://www.lakeafton.com for current programs.",
    }


@router.get(
    "/tonight",
    summary="Tonight's session snapshot",
    description=(
        "Aggregate endpoint that returns everything needed for tonight's viewing session "
        "in a single call: observatory open/close status, current weather, seeing conditions "
        "classified by cloud cover, and all celestial objects visible during open hours. "
        "Weather and sky-object sections degrade gracefully to null if API keys are absent. "
        "Defaults to the Lake Afton Public Observatory location."
    ),
)
async def tonight():
    lat = DEFAULT_LAT
    lon = DEFAULT_LON
    tz_name = DEFAULT_TZ
    tz = pytz.timezone(tz_name)

    # Use the observatory's local wall-clock time, not the server's local time
    # (which is UTC in production). Otherwise "now" can land on the wrong
    # weekday, which flips whether tonight's session is open/active and which
    # date (Friday vs. Saturday) is reported.
    now = datetime.now(tz).replace(tzinfo=None)
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

    is_open_tonight = now.weekday() in (4, 5)
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

    try:
        wx_data = result["weather"] or {}
        pressure = wx_data.get("groundLevelPressure")
        temp = (wx_data.get("temperature") or {}).get("celsius", 25)
        elev = get_elevation(lat, lon)

        session_secs = (close_dt - open_dt).total_seconds()
        mid_dt = open_dt + timedelta(seconds=session_secs / 2)
        mid_utc = mid_dt.astimezone(pytz.utc)

        location = get_location(str(lat), str(lon), elev, mid_utc, temp=temp, pressure=pressure)
        objects = whats_up(mid_utc, mid_utc + timedelta(minutes=1), location, magnitude=6)

        wu_module.tz = tz_name
        result["objects"] = json.loads(json.dumps(objects, cls=wu_module.Encoder))
    except Exception:
        pass

    return result
