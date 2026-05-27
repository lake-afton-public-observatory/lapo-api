import time
from datetime import datetime, timedelta
from fastapi import APIRouter
from app.utils import get_observatory_hours
from app.viewing_schedule import VIEWING_SCHEDULE

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
    # Advance to upcoming Saturday if not already Saturday
    day_anchor = 5  # Python: Monday=0, Saturday=5
    days_ahead = (day_anchor - now.weekday()) % 7
    if days_ahead == 0 and now.weekday() != day_anchor:
        days_ahead = 7
    if days_ahead > 0:
        now = now + timedelta(days=days_ahead)
    month = now.month
    h = get_observatory_hours(month)
    return {
        "hours": {
            "prettyHours": f"{h['display']['open']} \u2013 {h['display']['close']}",
            "open": h["display"]["open"],
            "close": h["display"]["close"],
        }
    }


@router.get("/schedule")
async def schedule():
    now = datetime.now()
    # Get upcoming Sunday
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    upcoming_sunday = now + timedelta(days=days_until_sunday)
    relevant_friday = upcoming_sunday - timedelta(days=2)
    key = relevant_friday.strftime("%m-%d-%Y")
    return {"schedule": VIEWING_SCHEDULE.get(key)}
