"""Celestial object catalog using Skyfield."""

import os
import re
import requests
import requests_cache
from typing import Optional
from skyfield.api import Star, EarthSatellite, Loader

_load = Loader(os.path.join(os.path.dirname(__file__), '../../data'))


def _get_ts():
    return _load.timescale()


def _parse_ra(s: str) -> float:
    """XEphem RA string (H:MM:SS.s or H:MM.m, optional |pm suffix) → decimal hours."""
    s = s.split('|')[0].strip()
    parts = re.split(r'[: ]+', s)
    h = float(parts[0])
    m = float(parts[1]) if len(parts) > 1 else 0.0
    sec = float(parts[2]) if len(parts) > 2 else 0.0
    return h + m / 60 + sec / 3600


def _parse_dec(s: str) -> float:
    """XEphem Dec string (±D:MM:SS.s, optional |pm suffix) → decimal degrees."""
    s = s.split('|')[0].strip()
    neg = s.startswith('-')
    s = s.lstrip('+-')
    parts = re.split(r'[: ]+', s)
    d = float(parts[0])
    m = float(parts[1]) if len(parts) > 1 else 0.0
    sec = float(parts[2]) if len(parts) > 2 else 0.0
    val = d + m / 60 + sec / 3600
    return -val if neg else val


def _parse_pm(s: str) -> float:
    """Extract proper motion from 'coord|pm_mas_yr' string."""
    parts = s.split('|')
    if len(parts) > 1:
        try:
            return float(parts[1])
        except ValueError:
            pass
    return 0.0


def _parse_xephem_line(line: str, object_type: str) -> Optional[dict]:
    """Parse one XEphem .edb line into a catalog entry dict."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    fields = line.split(',')
    if len(fields) < 3:
        return None

    names = [n.strip() for n in fields[0].split('|') if n.strip()]
    if not names:
        return None
    key = names[0].lower()

    try:
        ra_hours = _parse_ra(fields[2])
        dec_degrees = _parse_dec(fields[3])
    except (IndexError, ValueError):
        return None

    magnitude = None
    if len(fields) > 4 and fields[4].strip():
        try:
            magnitude = float(fields[4].strip())
        except ValueError:
            pass

    ra_mas = _parse_pm(fields[2]) if object_type == 'star' else 0.0
    dec_mas = _parse_pm(fields[3]) if object_type == 'star' else 0.0

    try:
        star = Star(
            ra_hours=ra_hours,
            dec_degrees=dec_degrees,
            ra_mas_per_year=ra_mas,
            dec_mas_per_year=dec_mas,
        )
    except Exception:
        return None

    return {
        'key': key,
        'names': names,
        'type': object_type or 'fixed',
        'skyfield': star,
        'magnitude': magnitude,
    }


def _parse_tle_lines(lines: list) -> list:
    """Parse list of lines into TLE triplets → list of satellite entries."""
    entries = []
    ts = _get_ts()
    triplets = [lines[i:i+3] for i in range(0, len(lines) - 2, 3)]
    for triplet in triplets:
        if len(triplet) < 3:
            continue
        name = triplet[0].strip()
        line1 = triplet[1].strip()
        line2 = triplet[2].strip()
        if not name or not line1.startswith('1 ') or not line2.startswith('2 '):
            continue
        try:
            sat = EarthSatellite(line1, line2, name, ts)
            key = name.lower()
            entries.append({
                'key': key,
                'names': [name],
                'type': 'satellite',
                'skyfield': sat,
                'magnitude': 2.0,  # default assumed visible magnitude
            })
        except Exception:
            pass
    return entries


def _read_catalog(filename: str, object_type: str) -> dict:
    """Load a catalog file (local path or HTTP URL) → dict of entries."""
    cache = requests_cache.CachedSession(
        cache_name=os.path.join(os.path.dirname(__file__), '../../data/catalog_cache'),
        expire_after=7 * 24 * 3600,
    )

    lines = []
    if re.match(r'https?://', filename):
        try:
            resp = cache.get(filename, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.split('\n')
        except Exception:
            pass
    elif os.path.isfile(filename):
        try:
            with open(filename) as f:
                lines = f.readlines()
        except Exception:
            pass

    result = {}
    if object_type == 'satellite':
        for entry in _parse_tle_lines(lines):
            result[entry['key']] = entry
    else:
        for line in lines:
            entry = _parse_xephem_line(line, object_type)
            if entry:
                result[entry['key']] = entry
    return result


# Planet name → JPL ephemeris body key
PLANET_KEYS = {
    'sun':     'sun',
    'mercury': 'mercury',
    'venus':   'venus barycenter',
    'moon':    'moon',
    'mars':    'mars barycenter',
    'jupiter': 'jupiter barycenter',
    'saturn':  'saturn barycenter',
    'uranus':  'uranus barycenter',
    'neptune': 'neptune barycenter',
    'pluto':   'pluto barycenter',
}

# Approximate mean magnitudes for filtering (updated dynamically in whatsup.py)
_PLANET_MAGNITUDES = {
    'sun': -26.7, 'moon': -12.6, 'mercury': 0.0, 'venus': -4.0,
    'mars': 0.7, 'jupiter': -2.0, 'saturn': 0.7, 'uranus': 5.7,
    'neptune': 7.8, 'pluto': 14.0,
}

_PLANET_SIZES = {
    'sun': 1919.0, 'moon': 1800.0, 'mercury': 6.0, 'venus': 25.0,
    'mars': 8.0, 'jupiter': 40.0, 'saturn': 17.0, 'uranus': 4.0,
    'neptune': 2.3, 'pluto': 0.1,
}

# Planetary moon entries (kept for API compatibility; not computed by Skyfield here)
_PLANETARY_MOONS = [
    ('phobos', 'Phobos', 'mars'), ('deimos', 'Deimos', 'mars'),
    ('ganymede', 'Ganymede', 'jupiter'), ('callisto', 'Callisto', 'jupiter'),
    ('io', 'Io', 'jupiter'), ('europa', 'Europa', 'jupiter'),
    ('titan', 'Titan', 'saturn'), ('iapetus', 'Iapetus', 'saturn'),
    ('rhea', 'Rhea', 'saturn'), ('tethys', 'Tethys', 'saturn'),
    ('dione', 'Dione', 'saturn'), ('enceladus', 'Enceladus', 'saturn'),
    ('mimas', 'Mimas', 'saturn'),
    ('titania', 'Titania', 'uranus'), ('oberon', 'Oberon', 'uranus'),
    ('hyperion', 'Hyperion', 'saturn'), ('ariel', 'Ariel', 'uranus'),
    ('umbriel', 'Umbriel', 'uranus'), ('miranda', 'Miranda', 'uranus'),
]


def get_objects(additional_catalogs_list: list) -> dict:
    """Return the full OBJECT_DICT."""
    objects = {}

    # Solar system planets
    for key, jpl_key in PLANET_KEYS.items():
        objects[key] = {
            'key': key,
            'names': [key.capitalize() if key != 'moon' else 'Moon'],
            'type': 'solar_system',
            'skyfield': jpl_key,  # string key into eph
            'magnitude': _PLANET_MAGNITUDES.get(key),
            'size': _PLANET_SIZES.get(key),
        }
    objects['sun']['names'] = ['Sun']
    objects['moon']['names'] = ['Moon']

    # Planetary moons (type only, no Skyfield body — computed elsewhere)
    for key, name, parent in _PLANETARY_MOONS:
        objects[key] = {
            'key': key,
            'names': [name],
            'type': 'planetary_moon',
            'skyfield': None,
            'magnitude': None,
        }

    # Additional catalogs (Messier, Caldwell, stars, satellites)
    for filename, object_type in additional_catalogs_list:
        catalog = _read_catalog(filename, object_type)
        objects.update(catalog)

    return objects
