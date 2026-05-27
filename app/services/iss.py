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


def get_iss_passes(lat: float, lon: float, elev: float, tz_name: str, api_key: str) -> dict:
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
            p[local_key] = dt_utc.astimezone(pytz.timezone(tz_name)).isoformat()
    return data
