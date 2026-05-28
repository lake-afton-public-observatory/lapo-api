import srtm
from cachetools import TTLCache, cached

_elevation_data = None
_elevation_cache = TTLCache(maxsize=256, ttl=3600)


def _get_srtm():
    global _elevation_data
    if _elevation_data is None:
        _elevation_data = srtm.get_data()
    return _elevation_data


@cached(cache=_elevation_cache)
def get_elevation(lat: float, lon: float, api_key: str = None) -> float:
    """Return elevation in metres for the given coordinates using SRTM data.

    SRTM tiles are downloaded on first use (~4 MB per 1°×1° tile) and cached
    locally. No API key required.
    """
    try:
        elev = _get_srtm().get_elevation(lat, lon)
        return float(elev) if elev is not None else 0.0
    except Exception as e:
        print(f"Error fetching SRTM elevation: {e}")
        return 0.0
