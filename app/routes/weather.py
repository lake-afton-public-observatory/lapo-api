from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ, OPENWEATHERMAP_API_KEY
from app.services.weather_api import get_weather, get_forecast
from app.utils import validate_lat, validate_lon

router = APIRouter()


@router.get("/current")
async def weather(lat: str = None, lon: str = None, tz: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ
        return get_weather(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)
    except Exception as e:
        print(f"Error in /weather: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch weather data"})


@router.get("/forecast")
async def forecast(lat: str = None, lon: str = None, tz: str = None):
    try:
        lat_f = validate_lat(lat) if lat else DEFAULT_LAT
        lon_f = validate_lon(lon) if lon else DEFAULT_LON
        if lat_f is None:
            lat_f = DEFAULT_LAT
        if lon_f is None:
            lon_f = DEFAULT_LON
        tz_name = tz or DEFAULT_TZ
        return get_forecast(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)
    except Exception as e:
        print(f"Error in /forecast: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch forecast data"})


