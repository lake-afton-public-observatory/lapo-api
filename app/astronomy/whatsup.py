"""Astronomy calculations using Skyfield (replaces PyEphem)."""

import json
import math
import datetime
from typing import Optional
import pytz
import numpy as np

from skyfield.api import load, wgs84, Star, Loader
from skyfield import almanac
from skyfield.magnitudelib import planetary_magnitude
from skyfield.constellationlib import load_constellation_map
from skyfield.api import position_of_radec
import os

from app.astronomy import celestial_objects

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
DEFAULT_TZ = 'America/Chicago'
tz = DEFAULT_TZ

_load = Loader(os.path.join(os.path.dirname(__file__), '../../data'))
_ts = None
_eph = None
_constellation_map = None


def _get_ephemeris():
    global _ts, _eph, _constellation_map
    if _ts is None:
        _ts = _load.timescale()
    if _eph is None:
        _eph = _load('de421.bsp')
    if _constellation_map is None:
        _constellation_map = load_constellation_map()
    return _ts, _eph


OBJECT_DICT = celestial_objects.get_objects([
    ('./data/messier.txt', None),
    ('./data/caldwell.txt', None),
    ('./data/stars.txt', 'star'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Bright/2018/Soft03Bright.txt', 'solar_system'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt', 'solar_system'),
    ('http://celestrak.com/NORAD/elements/visual.txt', 'satellite'),
])


class SFObserver:
    """Wraps a Skyfield observer location and observation time."""

    def __init__(self, lat: str, lon: str, elev: float, dt_utc: datetime.datetime,
                 temp: float = 25, pressure: Optional[float] = None):
        ts, eph = _get_ephemeris()
        self.ts = ts
        self.eph = eph
        self.lat = float(lat)
        self.lon = float(lon)
        self.elev = elev or 0
        self.temp = temp
        self.pressure = pressure
        self.wgs84_loc = wgs84.latlon(self.lat, self.lon, elevation_m=self.elev)
        self.sf_observer = eph['earth'] + self.wgs84_loc
        if dt_utc.tzinfo is None:
            dt_utc = pytz.utc.localize(dt_utc)
        self.t = ts.from_datetime(dt_utc)
        self.dt_utc = dt_utc


def get_location(lat: str, lon: str,
                 elev: Optional[float] = None,
                 date: Optional[datetime.datetime] = None,
                 horizon: Optional[str] = None,
                 temp: float = 25,
                 pressure: Optional[float] = None) -> 'SFObserver':
    """Create an observer from location and optional date."""
    if date is None:
        date = datetime.datetime.now(tz=pytz.utc)
    return SFObserver(lat, lon, elev, date, temp, pressure)


def _get_planet_body(obj: dict):
    """Return the Skyfield planet body for a solar_system entry."""
    _, eph = _get_ephemeris()
    return eph[obj['skyfield']]


def _safe_first(arr) -> Optional[datetime.datetime]:
    """Return first UTC datetime from a Skyfield Time array, or None."""
    try:
        if arr is None:
            return None
        if hasattr(arr, '__len__') and len(arr) == 0:
            return None
        t = arr[0] if hasattr(arr, '__len__') else arr
        dt = t.utc_datetime()
        return dt[0] if isinstance(dt, (list, np.ndarray)) else dt
    except Exception:
        return None


def _find_rise_set(observer: SFObserver, obj: dict, t_start, t_end):
    """Return (rise_dt, set_dt) for an object within the given time window."""
    ts, eph = _get_ephemeris()
    try:
        obj_type = obj['type']
        skyfield_body = obj['skyfield']

        if obj_type == 'solar_system':
            planet = eph[skyfield_body]
            f = almanac.risings_and_settings(eph, planet, observer.wgs84_loc)
            times, events = almanac.find_discrete(t_start, t_end, f)
            rise_dt = set_dt = None
            for t, is_rise in zip(times, events):
                dt = t.utc_datetime()
                if isinstance(dt, (list, np.ndarray)):
                    dt = dt[0]
                if is_rise and rise_dt is None:
                    rise_dt = dt
                elif not is_rise and set_dt is None:
                    set_dt = dt
            return rise_dt, set_dt

        elif obj_type in ('star', 'fixed', None, 'nebula') or isinstance(skyfield_body, Star):
            star = skyfield_body
            rise_times = almanac.find_risings(observer.sf_observer, star, t_start, t_end)
            set_times = almanac.find_settings(observer.sf_observer, star, t_start, t_end)
            rise_dt = _safe_first(rise_times)
            set_dt = _safe_first(set_times)
            return rise_dt, set_dt

        elif obj_type == 'satellite':
            sat = skyfield_body
            diff = sat - observer.sf_observer
            top = diff.at(t_start)
            alt, az, dist = top.altaz()
            # Approximate: sample satellite at start/end
            return None, None

    except Exception:
        pass
    return None, None


def _get_az_at(observer: SFObserver, obj: dict, t) -> Optional[float]:
    """Get azimuth of an object at time t."""
    try:
        skyfield_body = obj['skyfield']
        obj_type = obj['type']
        _, eph = _get_ephemeris()

        if obj_type == 'solar_system':
            planet = eph[skyfield_body]
            astr = observer.sf_observer.at(t).observe(planet).apparent()
        elif isinstance(skyfield_body, Star):
            astr = observer.sf_observer.at(t).observe(skyfield_body).apparent()
        else:
            return None
        alt, az, dist = astr.altaz()
        return float(az.degrees)
    except Exception:
        return None


def _get_constellation(ra_hours: float, dec_degrees: float) -> str:
    """Return IAU constellation abbreviation for RA/Dec."""
    try:
        _, _ = _get_ephemeris()
        pos = position_of_radec(ra_hours, dec_degrees)
        return _constellation_map(pos)
    except Exception:
        return ''


def get_data(object_list: list, location: Optional[SFObserver] = None) -> dict:
    """Compute ephemeris data for a list of (obj_dict, type) or obj_dict items.

    Returns a dict keyed by object name with position and rise/set data.
    """
    ts, eph = _get_ephemeris()
    body_data = {}

    if location:
        body_data['query_date'] = location.dt_utc

    for item in object_list:
        if isinstance(item, tuple):
            obj, _ = item
        else:
            obj = item

        if obj is None or obj.get('type') == 'planetary_moon':
            continue

        obj_type = obj['type']
        names = obj['names']
        name_key = names[0] if names else 'unknown'
        skyfield_body = obj['skyfield']

        try:
            t = location.t if location else ts.now()

            # Compute position
            if obj_type == 'solar_system':
                planet = eph[skyfield_body]
                astr = location.sf_observer.at(t).observe(planet).apparent()
            elif isinstance(skyfield_body, Star):
                astr = location.sf_observer.at(t).observe(skyfield_body).apparent()
            elif obj_type == 'satellite':
                sat = skyfield_body
                diff = sat - location.wgs84_loc
                top = diff.at(t)
                alt, az, dist = top.altaz()
                data = {
                    'name': names[0] if len(names) == 1 else names,
                    'alt': float(alt.degrees),
                    'az': float(az.degrees),
                    'mag': obj.get('magnitude', 0),
                    'size': obj.get('size'),
                    'elev': {'m': float(dist.m), 'mi': float(dist.m) / 1609.344},
                    'eclipsed': False,
                }
                body_data[name_key] = data
                continue
            else:
                continue

            ra, dec, dist = astr.radec()
            alt, az, _ = astr.altaz()
            ra_hours = float(ra.hours)
            dec_degrees = float(dec.degrees)
            alt_degrees = float(alt.degrees)
            az_degrees = float(az.degrees)

            # Magnitude
            try:
                if obj_type == 'solar_system':
                    mag = float(planetary_magnitude(location.sf_observer.at(t).observe(eph[skyfield_body])))
                else:
                    mag = obj.get('magnitude', 0) or 0
            except Exception:
                mag = obj.get('magnitude', 0) or 0

            data = {
                'name': names[0] if len(names) == 1 else names,
                'ra': ra_hours,
                'dec': dec_degrees,
                'alt': alt_degrees,
                'az': az_degrees,
                'mag': mag,
                'size': obj.get('size'),
                'elong': 0,  # elongation computed below for planets
            }

            if obj_type == 'solar_system' and name_key.lower() != 'sun':
                # Earth distance
                earth_dist_au = float(dist.au)
                data['earth_dist'] = {
                    'au': earth_dist_au,
                    'km': earth_dist_au * 149597870.700,
                    'mi': earth_dist_au * 149597870700 / 1609.344,
                }
                # Sun distance
                sun_pos = eph['sun'].at(t).position.au
                planet_pos = eph[skyfield_body].at(t).position.au
                sun_dist_au = float(np.linalg.norm(planet_pos - sun_pos))
                data['sun_dist'] = {
                    'au': sun_dist_au,
                    'km': sun_dist_au * 149597870.700,
                    'mi': sun_dist_au * 149597870700 / 1609.344,
                }
                # Elongation (angle from sun)
                sun_astr = location.sf_observer.at(t).observe(eph['sun']).apparent()
                sun_ra, sun_dec, _ = sun_astr.radec()
                dra = ra_hours - float(sun_ra.hours)
                data['elong'] = dra * 15  # rough elongation in degrees

                # Phase (0-100)
                if name_key.lower() == 'moon':
                    phase_ang = almanac.moon_phase(eph, t)
                    illum = (1 - math.cos(math.radians(float(phase_ang.degrees)))) / 2 * 100
                    data['phase'] = illum
                else:
                    # Simple phase angle approximation
                    data['phase'] = 50.0

                # Constellation
                data['constellation'] = _get_constellation(ra_hours, dec_degrees)

            if obj_type == 'solar_system' and name_key.lower() == 'sun':
                data['constellation'] = _get_constellation(ra_hours, dec_degrees)

            # Rise / transit / set
            if location and obj_type != 'satellite':
                t_start = ts.from_datetime(location.dt_utc - datetime.timedelta(hours=12))
                t_end = ts.from_datetime(location.dt_utc + datetime.timedelta(hours=24))
                rise_dt, set_dt = _find_rise_set(location, obj, t_start, t_end)
                if rise_dt:
                    data['rise_time'] = rise_dt
                    data['rise_az'] = _get_az_at(location, obj, ts.from_datetime(pytz.utc.localize(rise_dt) if rise_dt.tzinfo is None else rise_dt)) or 0
                if set_dt:
                    data['set_time'] = set_dt
                    data['set_az'] = _get_az_at(location, obj, ts.from_datetime(pytz.utc.localize(set_dt) if set_dt.tzinfo is None else set_dt)) or 0
                data['transit_time'] = None
                data['transit_alt'] = alt_degrees

            # Moon-specific
            if name_key.lower() == 'moon':
                phase_ang = almanac.moon_phase(eph, t)
                illum = (1 - math.cos(math.radians(float(phase_ang.degrees)))) / 2 * 100
                data['illuminated_surface'] = illum
                data['phase'] = illum
                data['phase_name'] = get_phase_name(t)
                data['next_new_moon'] = _safe_first(almanac.find_discrete(t, ts.from_datetime(location.dt_utc + datetime.timedelta(days=30)), almanac.moon_phases(eph))[0])
                data['next_full_moon'] = None
                data['next_first_quarter'] = None
                data['next_last_quarter'] = None
                # Find next moon phase events
                t_far = ts.from_datetime(location.dt_utc + datetime.timedelta(days=35))
                phase_times, phase_events = almanac.find_discrete(t, t_far, almanac.moon_phases(eph))
                for pt, pe in zip(phase_times, phase_events):
                    dt = pt.utc_datetime()
                    if isinstance(dt, (list, np.ndarray)):
                        dt = dt[0]
                    if pe == 0 and data['next_new_moon'] is None:
                        data['next_new_moon'] = dt
                    elif pe == 1 and data['next_first_quarter'] is None:
                        data['next_first_quarter'] = dt
                    elif pe == 2 and data['next_full_moon'] is None:
                        data['next_full_moon'] = dt
                    elif pe == 3 and data['next_last_quarter'] is None:
                        data['next_last_quarter'] = dt

            # Sun-specific twilight times
            if name_key.lower() == 'sun':
                t_start = ts.from_datetime(location.dt_utc - datetime.timedelta(hours=12))
                t_end = ts.from_datetime(location.dt_utc + datetime.timedelta(hours=24))
                sun_body = eph['sun']
                twilight_fn = almanac.dark_twilight_day(eph, location.wgs84_loc)
                times, events = almanac.find_discrete(t_start, t_end, twilight_fn)

                def _first_event(target_level, rising=True):
                    for ti, ev in zip(times, events):
                        if rising and ev == target_level:
                            dt = ti.utc_datetime()
                            return dt[0] if isinstance(dt, (list, np.ndarray)) else dt
                        elif not rising and ev == target_level:
                            dt = ti.utc_datetime()
                            return dt[0] if isinstance(dt, (list, np.ndarray)) else dt
                    return None

                # dark_twilight_day levels: 0=night, 1=astronomical, 2=nautical, 3=civil, 4=day
                data['astronomical_dawn'] = _first_event(1)
                data['nautical_dawn'] = _first_event(2)
                data['civil_dawn'] = _first_event(3)
                data['USNO_sunrise'] = _first_event(4)

                # Dusk events: falling transitions
                for ti, ev in zip(reversed(list(times)), reversed(list(events))):
                    dt = ti.utc_datetime()
                    if isinstance(dt, (list, np.ndarray)):
                        dt = dt[0]
                    if 'USNO_sunset' not in data and ev == 3:
                        data['USNO_sunset'] = dt
                    if 'civil_dusk' not in data and ev == 2:
                        data['civil_dusk'] = dt
                    if 'nautical_dusk' not in data and ev == 1:
                        data['nautical_dusk'] = dt
                    if 'astronomical_dusk' not in data and ev == 0:
                        data['astronomical_dusk'] = dt

                # Equinox / solstice
                eq_sol_fn = almanac.seasons(eph)
                t_far = ts.from_datetime(location.dt_utc + datetime.timedelta(days=366))
                sol_times, sol_events = almanac.find_discrete(t, t_far, eq_sol_fn)
                data['next_solstice'] = None
                data['next_equinox'] = None
                for st, se in zip(sol_times, sol_events):
                    dt = st.utc_datetime()
                    if isinstance(dt, (list, np.ndarray)):
                        dt = dt[0]
                    # 0=March equinox, 1=June solstice, 2=Sep equinox, 3=Dec solstice
                    if se in (1, 3) and data['next_solstice'] is None:
                        data['next_solstice'] = dt
                    if se in (0, 2) and data['next_equinox'] is None:
                        data['next_equinox'] = dt

            body_data[name_key] = data

        except Exception as e:
            # Skip objects that fail to compute
            pass

    return body_data


def whats_up(start: datetime.datetime, end: datetime.datetime,
             location: SFObserver, magnitude: float = 6.0) -> dict:
    """Find all objects visible between start and end from location."""
    ts, eph = _get_ephemeris()

    if start.tzinfo is None:
        start = pytz.utc.localize(start)
    if end.tzinfo is None:
        end = pytz.utc.localize(end)

    # Sample 6 points across the window to check visibility
    total_secs = max((end - start).total_seconds(), 1)
    n_samples = min(6, max(2, int(total_secs / 1800)))
    sample_dts = [
        start + datetime.timedelta(seconds=i * total_secs / (n_samples - 1))
        for i in range(n_samples)
    ]
    t_samples = ts.from_datetimes(sample_dts)
    t_start_sf = ts.from_datetime(start)
    t_end_sf = ts.from_datetime(end)

    body_list = []

    for key, obj in OBJECT_DICT.items():
        obj_type = obj.get('type')
        if obj_type == 'planetary_moon':
            continue

        mag = obj.get('magnitude')
        if mag is None or mag >= magnitude or mag < -30:
            continue

        skyfield_body = obj.get('skyfield')
        if skyfield_body is None:
            continue

        try:
            if obj_type == 'solar_system':
                planet = eph[skyfield_body]
                astr = location.sf_observer.at(t_samples).observe(planet).apparent()
                alt, az, _ = astr.altaz()
            elif isinstance(skyfield_body, Star):
                astr = location.sf_observer.at(t_samples).observe(skyfield_body).apparent()
                alt, az, _ = astr.altaz()
            elif obj_type == 'satellite':
                sat = skyfield_body
                diff = sat - location.wgs84_loc
                top = diff.at(t_samples)
                alt, az, _ = top.altaz()
            else:
                continue

            alt_arr = np.array(alt.degrees)
            if np.max(alt_arr) <= 0:
                continue

            # Object is (or will be) above the horizon — find rise/set within window
            rise_dt, set_dt = _find_rise_set(location, obj, t_start_sf, t_end_sf)

            # Only include if it actually rises/sets within window or is already up
            names = obj['names']
            entry = {
                'name': names[0] if len(names) == 1 else names,
                'magnitude': mag,
            }
            if rise_dt:
                entry['rise_time'] = rise_dt
            if set_dt:
                entry['set_time'] = set_dt
            if obj_type == 'solar_system' and key == 'moon':
                phase_ang = almanac.moon_phase(eph, t_start_sf)
                illum = (1 - math.cos(math.radians(float(phase_ang.degrees)))) / 2 * 100
                entry['phase'] = illum

            body_list.append(entry)

        except Exception:
            continue

    body_list.sort(key=lambda x: x['magnitude'])
    return {
        'start_time': start,
        'end_time': end,
        'objects': body_list,
    }


def get_phase_name(t, wiggle_days: float = 1.5) -> str:
    """Return the name of the moon's current phase."""
    ts, eph = _get_ephemeris()
    phase_ang = float(almanac.moon_phase(eph, t).degrees)

    if phase_ang < 10 or phase_ang > 350:
        return 'new moon'
    elif 80 < phase_ang < 100:
        return 'first quarter moon'
    elif 170 < phase_ang < 190:
        return 'full moon'
    elif 260 < phase_ang < 280:
        return 'last quarter moon'
    elif phase_ang < 80:
        return 'waxing crescent'
    elif phase_ang < 170:
        return 'waxing gibbous'
    elif phase_ang < 260:
        return 'waning gibbous'
    else:
        return 'waning crescent'


class Encoder(json.JSONEncoder):
    """JSON Encoder to serialize datetime objects."""

    global tz

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is None or obj.tzinfo.utcoffset(obj) is None:
                obj = pytz.utc.localize(obj)
            if tz is not None:
                return obj.astimezone(pytz.timezone(tz)).strftime(TIME_FORMAT)
            return obj.strftime(TIME_FORMAT)
        return json.JSONEncoder.default(self, obj)
