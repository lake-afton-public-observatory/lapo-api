import httpx
from cachetools import TTLCache
from datetime import datetime, timezone, timedelta
import pytz
from skyfield.api import wgs84, EarthSatellite
from app.astronomy.whatsup import _get_ephemeris

_ISS_NORAD_ID = 25544
_TLE_URL = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={_ISS_NORAD_ID}&FORMAT=TLE"
_tle_cache: TTLCache = TTLCache(maxsize=4, ttl=2 * 3600)

_COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']


def _az_compass(az: float) -> str:
    return _COMPASS[round(az / 45) % 8]


def _fetch_tle() -> tuple[str, str, str]:
    cached = _tle_cache.get('iss')
    if cached:
        return cached
    resp = httpx.get(_TLE_URL, timeout=10)
    resp.raise_for_status()
    lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        raise ValueError("Invalid TLE response from Celestrak")
    name = lines[0] if len(lines) >= 3 else 'ISS (ZARYA)'
    line1 = lines[1] if len(lines) >= 3 else lines[0]
    line2 = lines[2] if len(lines) >= 3 else lines[1]
    result = (name, line1, line2)
    _tle_cache['iss'] = result
    return result


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


def get_iss_passes(lat: float, lon: float, elev: float, tz_name: str,
                   api_key: str = None, days: int = 2, min_alt: float = 10.0) -> dict:
    """Return upcoming visible ISS passes using Skyfield + Celestrak TLE.

    No API key required. Passes are filtered to those where the ISS is sunlit
    and the observer is in at least civil twilight darkness (sun < -6°).
    """
    ts, eph = _get_ephemeris()
    name, line1, line2 = _fetch_tle()
    sat = EarthSatellite(line1, line2, name, ts)

    loc = wgs84.latlon(lat, lon, elevation_m=elev or 0)
    obs = eph['earth'] + loc
    tz = pytz.timezone(tz_name)

    now = datetime.now(timezone.utc)
    t0 = ts.from_datetime(now)
    t1 = ts.from_datetime(now + timedelta(days=days))

    times, events = sat.find_events(loc, t0, t1, altitude_degrees=min_alt)

    # Group into passes: each pass is (rise, culminate, set)
    passes = []
    current = {}
    for t, ev in zip(times, events):
        if ev == 0:
            current = {'rise': t}
        elif ev == 1 and 'rise' in current:
            current['culminate'] = t
        elif ev == 2 and 'rise' in current:
            current['set'] = t
            if 'culminate' in current:
                passes.append(current)
            current = {}

    sun = eph['sun']
    visible = []

    for p in passes:
        t_rise = p['rise']
        t_max = p['culminate']
        t_set = p['set']

        # ISS must be sunlit at culmination
        if not sat.at(t_max).is_sunlit(eph):
            continue

        # Observer must be in darkness (sun below civil twilight at -6°)
        sun_astr = obs.at(t_max).observe(sun).apparent()
        sun_alt, _, _ = sun_astr.altaz()
        if sun_alt.degrees > -6:
            continue

        def _pos(t):
            top = (sat - loc).at(t)
            alt, az, dist = top.altaz()
            dt = t.utc_datetime()
            local = dt.astimezone(tz).isoformat()
            return {
                'utc': dt.isoformat(),
                'local': local,
                'alt': round(float(alt.degrees), 1),
                'az': round(float(az.degrees), 1),
                'azCompass': _az_compass(float(az.degrees)),
            }

        rise_data = _pos(t_rise)
        max_data = _pos(t_max)
        set_data = _pos(t_set)
        duration = int((t_set - t_rise) * 86400)  # Skyfield time diff is in days

        visible.append({
            'startUTC': rise_data['utc'],
            'startLocal': rise_data['local'],
            'startAz': rise_data['az'],
            'startAzCompass': rise_data['azCompass'],
            'maxUTC': max_data['utc'],
            'maxLocal': max_data['local'],
            'maxAz': max_data['az'],
            'maxAzCompass': max_data['azCompass'],
            'maxEl': max_data['alt'],
            'endUTC': set_data['utc'],
            'endLocal': set_data['local'],
            'endAz': set_data['az'],
            'endAzCompass': set_data['azCompass'],
            'duration': duration,
        })

    return {
        'info': {
            'satname': name,
            'satid': _ISS_NORAD_ID,
            'passescount': len(visible),
        },
        'passes': visible,
    }
