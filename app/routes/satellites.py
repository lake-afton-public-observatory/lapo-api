from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from dateutil import parser as dateutil_parser

from app.config import (
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ,
    GOOGLE_PLACES_API_KEY, N2YO_API_KEY,
)
from app.services.elevation import get_elevation
from app.services.iss import get_iss_position, get_iss_passes
from app.utils import validate_lat, validate_lon

router = APIRouter()


@router.get("/iss")
async def iss(tz: str = None, dt: str = None):
    try:
        tz_name = tz or DEFAULT_TZ
        if dt:
            timestamp = dateutil_parser.parse(dt)
        else:
            timestamp = datetime.now(tz=timezone.utc)
        return get_iss_position(timestamp, tz_name)
    except Exception as e:
        print(f"Error in /iss: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch ISS data"})


@router.get("/iss-passes")
async def iss_passes(lat: str = None, lon: str = None, tz: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ
        elev = get_elevation(lat_f, lon_f, GOOGLE_PLACES_API_KEY)
        return get_iss_passes(lat_f, lon_f, elev, tz_name, N2YO_API_KEY)
    except Exception as e:
        print(f"Error in /iss-passes: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch ISS pass data"})
