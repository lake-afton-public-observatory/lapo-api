from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
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

_LAT_Q = Query(None, description="Observer latitude in decimal degrees (default: LAPO 37.622°N)")
_LON_Q = Query(None, description="Observer longitude in decimal degrees (default: LAPO -97.627°W)")
_TZ_Q  = Query(None, description="IANA timezone name, e.g. `America/Chicago` (default: LAPO timezone)")
_DT_Q  = Query(None, description="ISO 8601 datetime for the position calculation (default: now)")


@router.get(
    "/iss",
    summary="ISS current position",
    description=(
        "Returns the International Space Station's current latitude, longitude, "
        "altitude, and velocity using the WhereTheISS API. "
        "Optionally accepts a datetime to compute a historical or future position."
    ),
)
async def iss(
    tz: str = _TZ_Q,
    dt: str = _DT_Q,
):
    try:
        tz_name = tz or DEFAULT_TZ
        if dt:
            timestamp = dateutil_parser.parse(dt)
        else:
            timestamp = datetime.now(tz=timezone.utc)
        return get_iss_position(timestamp, tz_name)
    except Exception as e:
        print(f"Error in /satellites/iss: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch ISS data"})


@router.get(
    "/iss-passes",
    summary="Upcoming ISS visible passes",
    description=(
        "Returns the next 2 days of visible ISS passes over the given location "
        "via the N2YO API. Each pass includes rise time, max altitude, azimuth, "
        "and set time. Requires `N2YOAPIKey` to be configured."
    ),
)
async def iss_passes(
    lat: str = _LAT_Q,
    lon: str = _LON_Q,
    tz: str = _TZ_Q,
):
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
        print(f"Error in /satellites/iss-passes: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch ISS pass data"})
