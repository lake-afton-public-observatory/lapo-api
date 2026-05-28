from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.config import DEFAULT_TZ, NASA_API_KEY
from app.services.neo_api import get_neo_list

router = APIRouter()


@router.get(
    "/neo",
    summary="Near-Earth objects",
    description=(
        "Returns all near-Earth objects (asteroids and comets) tracked by NASA "
        "that make a close approach to Earth in the next 7 days. "
        "Each entry includes the object's name, estimated diameter, close approach "
        "date and distance, relative velocity, and a flag for potentially hazardous "
        "objects (PHAs). Requires `NASAAPIKey` to be configured."
    ),
)
async def neo(
    tz: str = Query(None, description="IANA timezone name for date fields (default: LAPO timezone)"),
):
    try:
        tz_name = tz or DEFAULT_TZ
        start = datetime.now()
        end = start + timedelta(days=6)
        return get_neo_list(
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            tz_name,
            NASA_API_KEY,
        )
    except Exception as e:
        print(f"Error in /space/neo: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch near-Earth object data"})
