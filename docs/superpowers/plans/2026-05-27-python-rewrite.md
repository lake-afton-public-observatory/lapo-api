# Python Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Node.js/Express API with a pure Python FastAPI application, eliminating the python-shell bridge and simplifying the stack to a single language.

**Architecture:** FastAPI app with route modules split by domain (observatory, celestial, weather, satellites, neo). Existing `whatsup.py` and `celestial_objects.py` are imported directly instead of spawned as subprocesses. External API calls use `httpx` with `cachetools` TTL caches matching the current memoization behavior. Response shapes are preserved exactly for backwards compatibility.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx, cachetools, slowapi (rate limiting), ephem, pytz, python-dateutil

---

## File Structure

```
lapo-api/
├── app/
│   ├── __init__.py              # empty
│   ├── main.py                  # FastAPI app, middleware, startup
│   ├── config.py                # env vars, constants (LAPO coords, default tz)
│   ├── routes/
│   │   ├── __init__.py          # empty
│   │   ├── observatory.py       # GET /, /health, /hours, /schedule
│   │   ├── celestial.py         # GET /planets, /visiblePlanets, /sun, /moon, /whatsup, /whatsup-next
│   │   ├── weather.py           # GET /weather, /forecast, /mars-weather
│   │   ├── satellites.py        # GET /iss, /iss-passes
│   │   └── neo.py               # GET /neo
│   ├── services/
│   │   ├── __init__.py          # empty
│   │   ├── elevation.py         # Google Elevation API client
│   │   ├── weather_api.py       # OpenWeatherMap client + response reshaping
│   │   ├── astropical.py        # astropical.space client
│   │   ├── iss.py               # WhereTheISS + N2YO clients
│   │   ├── neo_api.py           # NASA NEO client
│   │   └── mars_weather.py      # MAAS Mars weather client
│   ├── astronomy/
│   │   ├── __init__.py          # empty
│   │   ├── whatsup.py           # existing whatsup.py refactored (remove stdin/main)
│   │   └── celestial_objects.py # existing celestial_objects.py (fix paths)
│   └── utils.py                 # unit conversions, feels-like temp, query parsing
├── data/
│   ├── messier.txt              # moved from lib/
│   ├── caldwell.txt             # moved from lib/
│   ├── stars.txt                # moved from lib/
│   └── others.txt               # moved from lib/
├── tests/
│   ├── __init__.py
│   ├── test_utils.py            # unit conversion tests (ported from helpers test)
│   ├── test_observatory.py      # /health, /hours, /schedule tests
│   └── conftest.py              # FastAPI test client fixture
├── requirements.txt             # updated
├── Procfile                     # updated for uvicorn
├── runtime.txt                  # Python version for Heroku
├── README.md                    # updated
└── viewing_schedule.py          # ported from viewingSchedule.js
```

---

### Task 1: Project scaffolding and config

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/main.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Modify: `requirements.txt`
- Modify: `Procfile`
- Create: `runtime.txt`

- [ ] **Step 1: Update requirements.txt**

```
ephem>=4.1,<5
python-dateutil>=2.9,<3
pytz>=2024.1
requests>=2.32,<3
requests-cache>=1.2,<2
fastapi>=0.115,<1
uvicorn[standard]>=0.34,<1
httpx>=0.28,<1
cachetools>=5.5,<6
slowapi>=0.1.9,<1
python-dotenv>=1.0,<2
pytest>=8.0,<9
pytest-asyncio>=0.24,<1
httpx  # also used by TestClient
```

- [ ] **Step 2: Install dependencies**

Run: `. .venv/bin/activate && pip install -r requirements.txt`
Expected: All packages install successfully

- [ ] **Step 3: Create app/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# LAPO default coordinates
DEFAULT_LAT = 37.62218579135644
DEFAULT_LON = -97.62695789337158
DEFAULT_TZ = "America/Chicago"

# API keys
GOOGLE_PLACES_API_KEY = os.getenv("GooglePlacesAPIKey", "")
OPENWEATHERMAP_API_KEY = os.getenv("OpenWeatherMapAPIKey", "")
NASA_API_KEY = os.getenv("NASAAPIKey", "")
N2YO_API_KEY = os.getenv("N2YOAPIKey", "")

# Server
PORT = int(os.getenv("PORT", "3000"))
```

- [ ] **Step 4: Create app/__init__.py**

```python
# empty
```

- [ ] **Step 5: Create app/main.py (minimal, just health check)**

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Lake Afton API")

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests, please try again later"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 6: Create tests/__init__.py and tests/conftest.py**

```python
# tests/__init__.py — empty
```

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 7: Update Procfile**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 8: Create runtime.txt**

```
python-3.11.9
```

- [ ] **Step 9: Verify the app starts**

Run: `. .venv/bin/activate && uvicorn app.main:app --port 3333 &`
Run: `curl -s http://localhost:3333/docs`
Expected: FastAPI auto-generated docs page (HTML)
Kill the server.

- [ ] **Step 10: Commit**

```bash
git add app/ tests/ requirements.txt Procfile runtime.txt
git commit -m "feat: scaffold FastAPI app with config, rate limiting, CORS"
```

---

### Task 2: Utils and unit conversion tests

**Files:**
- Create: `app/utils.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write failing tests for unit conversions**

```python
# tests/test_utils.py
from app.utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    mps_to_mph,
    meters_to_miles,
    round_off,
    feels_like_temp,
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
    # temp too high for wind chill, returns input
    result = feels_like_temp(11, 10, 0)
    assert 10.99 <= result <= 11.01

def test_heat_index():
    result = feels_like_temp(27, 0, 15)
    assert 26.98 <= result <= 27.99
    result = feels_like_temp(30, 0, 50)
    assert 31.04 <= result <= 31.05
    result = feels_like_temp(40, 0, 40)
    assert 48.26 <= result <= 48.27
    # absurd RH, returns original
    result = feels_like_temp(50, 0, 75)
    assert 49.99 <= result <= 50.01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `. .venv/bin/activate && python -m pytest tests/test_utils.py -v`
Expected: FAIL — `ImportError: cannot import name 'celsius_to_fahrenheit' from 'app.utils'`

- [ ] **Step 3: Implement app/utils.py**

```python
import math
from datetime import datetime
from typing import Optional
import pytz
from dateutil import parser as dateutil_parser


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9


def mps_to_mph(meters_per_second: float) -> float:
    return meters_per_second / 0.44704


def meters_to_miles(meters: float) -> float:
    return meters / 1609.344


def round_off(number: float, digits: int = 0) -> float:
    factor = 10 ** digits
    return round(number * factor) / factor


def feels_like_temp(
    temp_celsius: float,
    wind_mps: float,
    relative_humidity: float,
) -> float:
    T = celsius_to_fahrenheit(temp_celsius)
    W = mps_to_mph(wind_mps)
    RH = relative_humidity

    if T <= 50 and W >= 3:
        wc = (
            35.74
            + (0.6215 * T)
            - (35.75 * W**0.16)
            + (0.4275 * T * W**0.16)
        )
        return fahrenheit_to_celsius(wc)

    if T > 80 and (245 - (T * 5 / 3)) >= RH:
        HI = 0.5 * (T + 61 + ((T - 68) * 1.2) + RH * 0.094)
        if (HI + T) / 2 >= 80:
            HI = (
                -42.379
                + 2.04901523 * T
                + 10.14333127 * RH
                - 0.22475541 * T * RH
                - 0.00683783 * T * T
                - 0.05481717 * RH * RH
                + 0.00122874 * T * T * RH
                + 0.00085282 * T * RH * RH
                - 0.00000199 * T * T * RH * RH
            )
            ADJ = 0.0
            if RH < 13 and 80 <= T <= 112:
                ADJ = -(
                    ((13 - RH) / 4)
                    * math.sqrt((17 - abs(T - 95)) / 17)
                )
            elif RH > 85 and 80 <= T <= 87:
                ADJ = ((RH - 85) / 10) * ((87 - T) / 5)
            HI += ADJ
            return fahrenheit_to_celsius(HI)

    return fahrenheit_to_celsius(T)


def get_observatory_hours(month: int) -> dict:
    if month in (3, 4, 9, 10):
        return {
            "display": {"open": "8:30pm", "close": "10:30pm"},
            "h24": {"open": "20:30", "close": "22:30"},
        }
    elif month in (5, 6, 7, 8):
        return {
            "display": {"open": "9:00pm", "close": "11:30pm"},
            "h24": {"open": "21:00", "close": "23:30"},
        }
    else:  # 11, 12, 1, 2
        return {
            "display": {"open": "7:30pm", "close": "9:30pm"},
            "h24": {"open": "19:30", "close": "21:30"},
        }


def parse_date(value: Optional[str], tz_name: str = "America/Chicago") -> Optional[datetime]:
    if value is None:
        return None
    try:
        dt = dateutil_parser.parse(value)
        if dt.tzinfo is None:
            dt = pytz.timezone(tz_name).localize(dt)
        return dt
    except (ValueError, TypeError):
        return None


def validate_lat(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        lat = float(value)
        return lat if -90 <= lat <= 90 else None
    except (ValueError, TypeError):
        return None


def validate_lon(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        lon = float(value)
        return lon if -180 <= lon <= 180 else None
    except (ValueError, TypeError):
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `. .venv/bin/activate && python -m pytest tests/test_utils.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/utils.py tests/test_utils.py
git commit -m "feat: add utility functions with unit conversion, feels-like temp, observatory hours"
```

---

### Task 3: Observatory routes (/, /health, /hours, /schedule)

**Files:**
- Create: `app/routes/__init__.py`
- Create: `app/routes/observatory.py`
- Create: `app/viewing_schedule.py`
- Create: `tests/test_observatory.py`
- Modify: `app/main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_observatory.py
from tests.conftest import client  # noqa: F401


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome" in data["message"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data


def test_hours(client):
    response = client.get("/hours")
    assert response.status_code == 200
    data = response.json()
    assert "hours" in data
    hours = data["hours"]
    assert "prettyHours" in hours
    assert "open" in hours
    assert "close" in hours


def test_schedule(client):
    response = client.get("/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `. .venv/bin/activate && python -m pytest tests/test_observatory.py -v`
Expected: FAIL — 404 for all routes

- [ ] **Step 3: Port viewing_schedule.js to Python**

```python
# app/viewing_schedule.py
VIEWING_SCHEDULE = {
    "12-21-2018": "This weekend is all about Winter Splendors. We will be viewing Mars, Neptune, the Blue Snowball, the Andromeda Galaxy, and much more.",
    "12-28-2018": "We will be viewing Mars, Neptune, Uranus, the pleiades, the Orion Nebula, and more",
    "01-04-2019": "This weekend is all about Winter Splendors. We will be viewing Mars, Neptune, the Blue Snowball, the Andromeda Galaxy, and much more.",
    "01-18-2019": "This weekend features a Big Moon and Binary Stars. We will be viewing the Moon, Garnet Star, Neptune, and Mars",
    "01-25-2019": "The Messier Medley, featuring Mars, Blue Snowball, The Andromeda Galaxy, the ET Cluster and the Pinwheel Galaxy",
    "02-01-2019": "We will be viewing Mars, the Andromeda Galaxy, the ET Cluster, the Little Dumbbell and the Pinwheel Galaxy",
    "02-08-2019": "From the closest to the farthest, we will view the Moon, Mars, Polaris, M110, and the Andromeda Galaxy",
    "02-15-2019": "Over the moon, we will look at Alpha Centauri, Mars, the Moon, Polaris, and maybe the Andromeda Galaxy",
    "02-22-2019": "The winter deep sky splendors will be out tonight, featuring Mars, the Blue Snowball, M110, and the Andromeda Galaxy",
    "03-01-2019": "A star's life, we will view η Persei, the Pleiades, the ET cluster, and the Orion Nebula",
    "03-08-2019": "We will be viewing the Great Orion Nebula, Mars, the ET Cluster, and more",
    "03-15-2019": "The moon, up close and personal tonight. We will also look at Alpha Centauri, Mars, and γ¹ Leonis",
    "03-22-2019": "A tour of the universe, starting with Mars, then on to M108, the Owl Nebula, and the Andromeda Galaxy",
    "03-29-2019": "Tonight is all about deep sky splendors, including M108, the Owl Nebula, the ET cluster, η Persei, and M38",
    "04-05-2019": "A tour of the universe, starting with Mars, then on to M108, the Owl Nebula, and the Andromeda Galaxy",
    "04-12-2019": "The moon, up close and personal tonight. We will also look at Alpha Centauri, Mars, and γ¹ Leonis",
    "04-19-2019": "A nearly full moon will grace our skies, and we'll also be looking at Mars, M31, M44, the Double Cluster, M47, and M41",
    "04-26-2019": "This week is the Hyades cluster, Mizar, M31, M44, and the Double Cluster",
    "05-03-2019": "",
    "05-10-2019": "Viewing the mountains and valleys of the moon",
    "05-17-2019": "More views of the moon as well as binary stars",
    "05-24-2019": "Galaxies of the Universe",
    "05-31-2019": "Spring Galaxy tour",
    "06-07-2019": "Dancing star pairs, double stars, binary stars",
    "06-14-2019": "Jupiter",
    "06-21-2019": "Galaxy Quest and Jupiter",
    "06-28-2019": "Enjoying Jupiter",
    "07-05-2019": "Jupiter, Moon, and Galaxies, Oh My!",
    "07-12-2019": "Saturn, Jupiter and the Moon",
    "07-19-2019": "Solar System and the Universe",
    "07-26-2019": "Sizing up our solar system",
    "08-02-2019": "Summer splendors",
    "08-09-2019": "Astrofest! Best of the solar system",
    "08-16-2019": "Planets and explosions",
    "08-23-2019": "Must See Saturn!",
    "08-30-2019": "Planets and our Milky Way",
    "09-06-2019": "A stroll through our Solar System",
    "09-13-2019": "Last Call for Jupiter",
    "09-20-2019": "Very Last Call for Jupiter!",
    "09-27-2019": "Don't Miss Saturn this year!",
    "10-04-2019": "Voyager's Grand Tour",
    "10-11-2019": "Full Moon Fever",
    "10-18-2019": "Saturn and Stellar Death",
    "10-25-2019": "Don't Miss Saturn!",
    "11-01-2019": "The Moon and Outer Planets",
    "11-08-2019": "Galactic Medley",
    "11-15-2019": "Messier Marvels",
    "11-22-2019": "Tour of the Universe",
    "11-29-2019": "The Best of Dark Skies",
    "12-06-2019": "The Moon and Outer Planets",
    "12-13-2019": "Winter Splendors",
    "12-20-2019": "Galactic Medley, all sorts...",
    "12-27-2019": "End of Year Messier Medley",
}
```

- [ ] **Step 4: Create app/routes/__init__.py (empty) and app/routes/observatory.py**

```python
# app/routes/__init__.py — empty
```

```python
# app/routes/observatory.py
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
    if now.weekday() != day_anchor:
        days_ahead = (day_anchor - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
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
    # Relevant Friday = Sunday - 2
    relevant_friday = upcoming_sunday - timedelta(days=2)
    key = relevant_friday.strftime("%m-%d-%Y")
    return {"schedule": VIEWING_SCHEDULE.get(key)}
```

- [ ] **Step 5: Register the router in app/main.py**

Add to the end of `app/main.py`:

```python
from app.routes import observatory

app.include_router(observatory.router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `. .venv/bin/activate && python -m pytest tests/test_observatory.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add app/routes/ app/viewing_schedule.py tests/test_observatory.py
git commit -m "feat: add observatory routes (root, health, hours, schedule)"
```

---

### Task 4: External API services (elevation, weather, forecast, mars)

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/elevation.py`
- Create: `app/services/weather_api.py`
- Create: `app/services/mars_weather.py`

- [ ] **Step 1: Create app/services/__init__.py (empty)**

- [ ] **Step 2: Create app/services/elevation.py**

```python
import httpx
from cachetools import TTLCache, cached

_elevation_cache = TTLCache(maxsize=256, ttl=3600)


@cached(cache=_elevation_cache)
def get_elevation(lat: float, lon: float, api_key: str) -> float:
    url = (
        f"https://maps.googleapis.com/maps/api/elevation/json"
        f"?locations={lat},{lon}&key={api_key}"
    )
    try:
        resp = httpx.get(url, timeout=10)
        data = resp.json()
        return data["results"][0]["elevation"]
    except Exception as e:
        print(f"Error in Elevation API: {e}")
        return 0.0
```

- [ ] **Step 3: Create app/services/weather_api.py**

This is the most complex service — it reshapes the OpenWeatherMap response to match the existing API output exactly.

```python
import httpx
from cachetools import TTLCache, cached
from datetime import datetime, timezone
import pytz
from app.utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
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
        "groundLevelPressure": item["main"].get("pressure")
            or item["main"].get("grnd_level"),
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


@cached(cache=_weather_cache, key=lambda lat, lon, key, tz=None: (lat, lon))
def get_weather(lat: float, lon: float, key: str, tz: str = None) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&units=metric&APPID={key}"
    )
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return _reshape_weather_item(data, tz)


@cached(cache=_forecast_cache, key=lambda lat, lon, key, tz=None: (lat, lon))
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
```

- [ ] **Step 4: Create app/services/mars_weather.py**

```python
import httpx


def get_mars_weather() -> dict:
    resp = httpx.get("https://api.maas2.apollorion.com/", timeout=10)
    resp.raise_for_status()
    return resp.json()
```

- [ ] **Step 5: Commit**

```bash
git add app/services/
git commit -m "feat: add elevation, weather, forecast, mars weather services"
```

---

### Task 5: Weather routes

**Files:**
- Create: `app/routes/weather.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create app/routes/weather.py**

```python
from fastapi import APIRouter, Request
from app.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ, OPENWEATHERMAP_API_KEY
from app.services.weather_api import get_weather, get_forecast
from app.services.mars_weather import get_mars_weather
from app.utils import validate_lat, validate_lon

router = APIRouter()


@router.get("/weather")
async def weather(
    lat: str = None, lon: str = None, tz: str = None,
):
    lat_f = validate_lat(lat) if lat else DEFAULT_LAT
    lon_f = validate_lon(lon) if lon else DEFAULT_LON
    if lat_f is None:
        lat_f = DEFAULT_LAT
    if lon_f is None:
        lon_f = DEFAULT_LON
    tz_name = tz or DEFAULT_TZ
    return get_weather(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)


@router.get("/forecast")
async def forecast(
    lat: str = None, lon: str = None, tz: str = None,
):
    lat_f = validate_lat(lat) if lat else DEFAULT_LAT
    lon_f = validate_lon(lon) if lon else DEFAULT_LON
    if lat_f is None:
        lat_f = DEFAULT_LAT
    if lon_f is None:
        lon_f = DEFAULT_LON
    tz_name = tz or DEFAULT_TZ
    return get_forecast(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)


@router.get("/mars-weather")
async def mars_weather():
    return get_mars_weather()
```

- [ ] **Step 2: Register in app/main.py**

Add:
```python
from app.routes import weather
app.include_router(weather.router)
```

- [ ] **Step 3: Commit**

```bash
git add app/routes/weather.py app/main.py
git commit -m "feat: add weather, forecast, mars-weather routes"
```

---

### Task 6: Move astronomy code and data files

**Files:**
- Create: `app/astronomy/__init__.py`
- Move: `lib/whatsup.py` → `app/astronomy/whatsup.py` (refactored)
- Move: `lib/celestial_objects.py` → `app/astronomy/celestial_objects.py`
- Move: `lib/messier.txt`, `lib/caldwell.txt`, `lib/stars.txt`, `lib/others.txt` → `data/`

- [ ] **Step 1: Create data/ directory and move catalog files**

```bash
mkdir -p data
cp lib/messier.txt lib/caldwell.txt lib/stars.txt lib/others.txt data/
```

- [ ] **Step 2: Create app/astronomy/__init__.py (empty)**

- [ ] **Step 3: Copy and refactor celestial_objects.py**

Copy `lib/celestial_objects.py` to `app/astronomy/celestial_objects.py`. Update the file paths in `get_objects` calls — the catalog file paths will be passed in from the caller rather than hardcoded. No other changes needed; the module is used as-is.

```python
# app/astronomy/celestial_objects.py
# Same as lib/celestial_objects.py — no changes needed,
# paths are passed in by the caller
```

(Copy the file verbatim from `lib/celestial_objects.py`)

- [ ] **Step 4: Copy and refactor whatsup.py**

Copy `lib/whatsup.py` to `app/astronomy/whatsup.py`. Remove the `main()` function, `read_in()`, the `if __name__ == '__main__'` block, and the `Encoder` class (FastAPI handles JSON serialization). Update the import of `celestial_objects` to a relative import. Update catalog paths to use `data/` directory. Export `get_location`, `get_data`, `whats_up`, `get_phase_name`, `format_angle`, `format_ra`, and `OBJECT_DICT`.

Key changes:
```python
# Change this import:
import celestial_objects
# To:
from app.astronomy import celestial_objects

# Change catalog paths:
OBJECT_DICT = celestial_objects.get_objects([
    ('./data/messier.txt', None),
    ('./data/caldwell.txt', None),
    ('./data/stars.txt', 'star'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Bright/2018/Soft03Bright.txt', 'solar_system'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt', 'solar_system'),
    ('http://celestrak.com/NORAD/elements/visual.txt', 'satellite')
])

# Remove: read_in(), main(), Encoder class, if __name__ block
# Keep everything else
```

- [ ] **Step 5: Verify the astronomy module imports**

Run: `. .venv/bin/activate && python -c "from app.astronomy.whatsup import OBJECT_DICT; print(f'Loaded {len(OBJECT_DICT)} objects')"`
Expected: `Loaded <N> objects` (should be 29+ depending on external catalog availability)

- [ ] **Step 6: Commit**

```bash
git add app/astronomy/ data/
git commit -m "feat: move astronomy code and catalogs, refactor for direct import"
```

---

### Task 7: Celestial routes (/planets, /visiblePlanets, /sun, /moon, /whatsup, /whatsup-next)

**Files:**
- Create: `app/services/astropical.py`
- Create: `app/routes/celestial.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create app/services/astropical.py**

```python
import httpx
from cachetools import TTLCache, cached

_cache = TTLCache(maxsize=64, ttl=300)


@cached(cache=_cache)
def get_planet_ephem(lat: float, lon: float) -> dict:
    url = f"http://astropical.space/api-ephem.php?lat={lat}&lon={lon}"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
```

- [ ] **Step 2: Create app/routes/celestial.py**

```python
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
from app.astronomy.whatsup import get_location, get_data, whats_up, OBJECT_DICT, Encoder
from app.utils import (
    validate_lat, validate_lon, parse_date, get_observatory_hours,
)

router = APIRouter()

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


def _build_location(lat, lon, tz, dt_str=None):
    """Build an ephem Observer with weather-based pressure/temp."""
    elev = get_elevation(lat, lon, GOOGLE_PLACES_API_KEY)
    weather_data = get_weather(lat, lon, OPENWEATHERMAP_API_KEY)
    pressure = weather_data.get("groundLevelPressure")
    temp = weather_data.get("temperature", {}).get("celsius", 25)

    date = datetime.datetime.now()
    if dt_str:
        date = dateutil_parser.parse(dt_str)
    if date.tzinfo is None:
        date = pytz.timezone(tz).localize(date)
    date = date.astimezone(pytz.utc)

    return get_location(
        str(lat), str(lon), elev, date, temp=temp, pressure=pressure
    ), date


def _serialize(data: dict, tz_name: str) -> dict:
    """Serialize datetime objects in nested dicts to ISO strings."""
    import json
    # Reuse the Encoder from whatsup but we need to set the tz global
    from app.astronomy import whatsup as wu
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
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch planet data"},
        )


@router.get("/planets")
async def planets(
    lat: str = None, lon: str = None, tz: str = None, dt: str = None,
):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ

        location, _ = _build_location(lat_f, lon_f, tz_name, dt)

        bodies = ["mercury", "venus", "mars", "jupiter",
                   "saturn", "uranus", "neptune", "pluto"]
        query_set = set(bodies) & set(OBJECT_DICT.keys())
        query_list = [OBJECT_DICT[k] for k in query_set]
        result = get_data(query_list, location)
        return _serialize(result, tz_name)
    except Exception as e:
        print(f"Error in /planets: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch planet data"},
        )


@router.get("/sun")
async def sun(
    lat: str = None, lon: str = None, tz: str = None, dt: str = None,
):
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
        return JSONResponse(
            status_code=502, content={"error": "Failed to fetch sun data"},
        )


@router.get("/moon")
async def moon(
    lat: str = None, lon: str = None, tz: str = None, dt: str = None,
):
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
        return JSONResponse(
            status_code=502, content={"error": "Failed to fetch moon data"},
        )


@router.get("/whatsup")
async def whatsup(
    lat: str = None, lon: str = None, tz: str = None,
    start: str = None, end: str = None,
):
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
        return JSONResponse(
            status_code=502, content={"error": "Failed to fetch sky data"},
        )


@router.get("/whatsup-next")
@router.get("/whatsup_next")
async def whatsup_next():
    try:
        lat = DEFAULT_LAT
        lon = DEFAULT_LON
        tz_name = DEFAULT_TZ

        now = datetime.datetime.now()
        # Get upcoming Sunday
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
        return JSONResponse(
            status_code=502, content={"error": "Failed to fetch sky data"},
        )
```

- [ ] **Step 3: Register in app/main.py**

Add:
```python
from app.routes import celestial
app.include_router(celestial.router)
```

- [ ] **Step 4: Verify /planets, /sun, /moon endpoints work manually**

Run the server and curl a few endpoints (these need API keys to fully work):
```bash
uvicorn app.main:app --port 3333 &
curl -s http://localhost:3333/hours
curl -s http://localhost:3333/health
```

- [ ] **Step 5: Commit**

```bash
git add app/services/astropical.py app/routes/celestial.py app/main.py
git commit -m "feat: add celestial routes (planets, sun, moon, whatsup)"
```

---

### Task 8: Satellite and NEO routes

**Files:**
- Create: `app/services/iss.py`
- Create: `app/services/neo_api.py`
- Create: `app/routes/satellites.py`
- Create: `app/routes/neo.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create app/services/iss.py**

```python
import httpx
from datetime import datetime, timezone
import pytz


def get_iss_position(timestamp: datetime, tz_name: str) -> dict:
    epoch = int(timestamp.timestamp())
    url = f"https://api.wheretheiss.at/v1/satellites/25544?timestamp={epoch}"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    dt = datetime.fromtimestamp(data["timestamp"], tz=timezone.utc)
    data["timestamp"] = dt.astimezone(pytz.timezone(tz_name)).isoformat()
    alt_km = data["altitude"]
    data["altitude"] = {"km": alt_km, "mi": alt_km / 1.609344}
    vel_kph = data["velocity"]
    data["velocity"] = {
        "kph": vel_kph,
        "mph": vel_kph / 1.609344,
        "m/s": vel_kph / 3.6,
        "ft/s": vel_kph / 1.09728,
    }
    for key in ("units", "footprint", "daynum", "solar_lat", "solar_lon"):
        data.pop(key, None)
    return data


def get_iss_passes(
    lat: float, lon: float, elev: float, tz_name: str, api_key: str,
) -> dict:
    days = 2
    visibility = 10
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/visualpasses/25544"
        f"/{lat}/{lon}/{elev}/{days}/{visibility}/&apiKey={api_key}"
    )
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    for p in data.get("passes", []):
        for field in ("startUTC", "maxUTC", "endUTC"):
            epoch = p[field]
            dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)
            p[field] = dt_utc
            local_key = field.replace("UTC", "Local")
            p[local_key] = dt_utc.astimezone(
                pytz.timezone(tz_name)
            ).isoformat()
    return data
```

- [ ] **Step 2: Create app/services/neo_api.py**

```python
import httpx
from datetime import datetime, timezone
import pytz


def get_neo_list(
    start_date: str, end_date: str, tz_name: str, api_key: str,
) -> dict:
    url = (
        f"https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    )
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise Exception(data["error"])

    data.pop("links", None)

    for date_key, neos in data.get("near_earth_objects", {}).items():
        for neo in neos:
            neo.pop("links", None)
            neo.pop("is_potentially_hazardous_asteroid", None)
            neo.pop("is_sentry_object", None)
            if neo.get("close_approach_data"):
                ca = neo["close_approach_data"][0]
                epoch = ca.get("epoch_date_close_approach")
                if epoch:
                    dt = datetime.fromtimestamp(
                        epoch / 1000, tz=timezone.utc
                    )
                    ca["close_approach_date_full"] = dt.astimezone(
                        pytz.timezone(tz_name)
                    ).isoformat()
                    ca.pop("epoch_date_close_approach", None)
    return data
```

- [ ] **Step 3: Create app/routes/satellites.py**

```python
from datetime import datetime, timezone
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
        return JSONResponse(
            status_code=502, content={"error": "Failed to fetch ISS data"},
        )


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
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch ISS pass data"},
        )
```

- [ ] **Step 4: Create app/routes/neo.py**

```python
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
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch near-Earth object data"},
        )
```

- [ ] **Step 5: Register both routers in app/main.py**

Add:
```python
from app.routes import satellites, neo
app.include_router(satellites.router)
app.include_router(neo.router)
```

- [ ] **Step 6: Commit**

```bash
git add app/services/iss.py app/services/neo_api.py app/routes/satellites.py app/routes/neo.py app/main.py
git commit -m "feat: add ISS, ISS passes, and NEO routes"
```

---

### Task 9: Error handling middleware and final app/main.py

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: Finalize app/main.py with all routers and error handling**

The complete `app/main.py` should look like:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import observatory, celestial, weather, satellites, neo

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/15minutes"],
)

app = FastAPI(title="Lake Afton API")
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests, please try again later"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(observatory.router)
app.include_router(celestial.router)
app.include_router(weather.router)
app.include_router(satellites.router)
app.include_router(neo.router)
```

- [ ] **Step 2: Start the server and test all no-api-key endpoints**

```bash
. .venv/bin/activate
uvicorn app.main:app --port 3333 &
curl -s http://localhost:3333/
curl -s http://localhost:3333/health
curl -s http://localhost:3333/hours
curl -s http://localhost:3333/schedule
```

Expected: All return valid JSON matching the Node.js output format.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: finalize app with error handling and all route registrations"
```

---

### Task 10: Cleanup and README update

**Files:**
- Modify: `README.md`
- Remove: Node.js files no longer needed

- [ ] **Step 1: Remove Node.js artifacts**

```bash
git rm -r routes/ bin/ app.js package.json package-lock.json lib/helpers.js lib/astropical.js lib/viewingSchedule.js lib/whatsup.py lib/celestial_objects.py
git rm .eslintrc.js 2>/dev/null || true
git rm -r test/ 2>/dev/null || true
git rm -r node_modules/ 2>/dev/null || true
```

Keep: `lib/messier.txt`, `lib/caldwell.txt`, `lib/stars.txt`, `lib/others.txt` if they haven't been moved yet (they should be in `data/` by now).

- [ ] **Step 2: Update README.md**

Update the Getting Started section to reflect Python-only setup:

```markdown
# Lake Afton API

A REST API for [Lake Afton Public Observatory](https://www.lakeafton.com/) (LAPO), providing astronomical data, weather conditions, and observatory information.

## Getting Started

### Prerequisites

- Python 3.11+

### Setup

1. Fork and clone the repo
2. Create a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env_example` to `.env` and fill in your API keys (see [API Keys](#api-keys))
5. Run: `uvicorn app.main:app --reload`
6. Visit `http://localhost:8000` (or `http://localhost:$PORT` if `PORT` is set)
7. Interactive API docs available at `http://localhost:8000/docs`
```

Keep the existing Endpoints and API Keys sections from the current README.

Add to the bottom:
```markdown
### Running Tests

```bash
python -m pytest tests/ -v
```
```

- [ ] **Step 3: Update setup.sh**

```bash
#!/usr/bin/env bash
set -e

echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed. Please install it first."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env_example .env
  echo "Created .env from .env_example — fill in your API keys before running."
else
  echo ".env already exists, skipping."
fi

echo "Installing Python packages..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

echo "Done! Run 'uvicorn app.main:app --reload' to start the server."
```

- [ ] **Step 4: Run full test suite**

Run: `. .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Start server and smoke test**

Run: `. .venv/bin/activate && uvicorn app.main:app --port 3333 &`
Test: `curl -s http://localhost:3333/ && curl -s http://localhost:3333/health && curl -s http://localhost:3333/hours`
Expected: Valid JSON responses matching original API output

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove Node.js code, update README and setup for Python-only stack"
```

---

## Self-Review Notes

- **Spec coverage:** All 14 active endpoints from the Node.js app are covered (/, /health, /hours, /schedule, /visiblePlanets, /planets, /sun, /moon, /whatsup, /whatsup-next, /weather, /forecast, /mars-weather, /iss, /iss-passes, /neo). The deprecated /events endpoint is intentionally excluded.
- **Placeholder scan:** All tasks include complete code. No TBDs.
- **Type consistency:** `get_observatory_hours` returns the same `display`/`h24` dict structure in both `utils.py` and the route handlers that consume it. `validate_lat`/`validate_lon` return `Optional[float]` consistently. The `_serialize` function in celestial.py correctly references `Encoder` from the astronomy module — **note:** the `Encoder` class needs to be kept in `app/astronomy/whatsup.py` (do not delete it during the refactor in Task 6 step 4, despite what that step says about removing it).
- **Response shape compatibility:** The weather reshaping logic in `weather_api.py` preserves the same key names (`temperature`, `groundLevelPressure`, `humidity`, `clouds`, `wind.speed.metersPerSecond`, etc.) as the Node.js version.
