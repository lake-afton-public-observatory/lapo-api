import httpx
from cachetools import TTLCache, cached

_cache = TTLCache(maxsize=64, ttl=300)


@cached(cache=_cache)
def get_planet_ephem(lat: float, lon: float) -> dict:
    url = f"https://astropical.space/api-ephem.php?lat={lat}&lon={lon}"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
