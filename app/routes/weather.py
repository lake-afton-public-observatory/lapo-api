from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ, OPENWEATHERMAP_API_KEY
from app.services.weather_api import get_weather, get_forecast
from app.utils import validate_lat, validate_lon

router = APIRouter()

_LAT_Q = Query(None, description="Observer latitude in decimal degrees (default: LAPO 37.622°N)")
_LON_Q = Query(None, description="Observer longitude in decimal degrees (default: LAPO -97.627°W)")
_TZ_Q  = Query(None, description="IANA timezone name, e.g. `America/Chicago` (default: LAPO timezone)")


@router.get(
    "/current",
    summary="Current weather conditions",
    description=(
        "Returns current weather at the given location via OpenWeatherMap: "
        "temperature (°C and °F with feels-like), wind speed and direction, "
        "humidity, cloud cover percentage, visibility, and weather description."
    ),
)
async def weather(
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
        return get_weather(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)
    except Exception as e:
        print(f"Error in /weather/current: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch weather data"})


@router.get(
    "/forecast",
    summary="5-day weather forecast",
    description=(
        "Returns a 5-day, 3-hour interval forecast via OpenWeatherMap. "
        "Each interval includes temperature, wind, humidity, cloud cover, "
        "and weather description. Response includes city metadata."
    ),
)
async def forecast(
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
        return get_forecast(lat_f, lon_f, OPENWEATHERMAP_API_KEY, tz_name)
    except Exception as e:
        print(f"Error in /weather/forecast: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to fetch forecast data"})
