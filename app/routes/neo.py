from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import DEFAULT_TZ, NASA_API_KEY
from app.services.neo_api import get_neo_list

router = APIRouter()


@router.get("/neo")
async def neo(tz: str = None):
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
        print(f"Error in /neo: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch near-Earth object data"})
