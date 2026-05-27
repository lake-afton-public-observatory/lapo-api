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
