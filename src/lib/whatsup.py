"""A series of functions to use PyEphem for lake-afton-api."""

from typing import Optional, Union, Tuple, List
import sys
import json
import datetime
import ephem
import pytz
import dateutil.parser
import celestial_objects

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
DEFAULT_TZ = 'America/Chicago'

OBJECT_DICT = celestial_objects.get_objects([
    ('./lib/messier.txt', None),
    ('./lib/caldwell.txt', None),
    ('./lib/stars.txt', 'star'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Bright/2018/Soft03Bright.txt', 'solar_system'),
    ('https://minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt', 'solar_system'),
    ('http://celestrak.com/NORAD/elements/visual.txt', 'satellite')
])

def read_in() -> dict:
    """Read parameters from node call."""
    lines = sys.stdin.readlines()
    return json.loads(lines[0])

def get_location(lat: float,
                 lon: float,
                 elev: Optional[float] = None,
                 date: Optional[datetime.datetime] = None,
                 horizon: Optional[str] = None,
                 temp: float = 25,
                 pressure: Optional[float] = None) -> ephem.Observer:
    """Create location from provided information."""
    obs = ephem.Observer()
    obs.lat, obs.lon = lat, lon
    if elev:
        obs.elev = elev
    if date:
        obs.date = date
    if horizon:
        obs.horizon = horizon
    obs.temp = temp
    if pressure:
        obs.pressure = pressure
    else:
        obs.compute_pressure()
    return obs

def format_angle(angle: float, dms: bool = False) -> Union[float, Tuple[int, int, float]]:
    """Format angle as degrees or (degrees,minutes,seconds) tuple instead of radians."""
    a = angle.znorm
    a *= 180 / ephem.pi
    if dms:
        d = int(a)
        a -= int(a)
        a *= 60
        m = int(a)
        a -= int(a)
        a *= 60
        s = a
        return d, m, s
    return a

def format_ra(angle: float, hms: bool = False) -> Union[float, Tuple[int, int, float]]:
    """Format right ascension as hour angle or (hours,minutes,seconds) tuple instead of radians."""
    a = angle.norm
    a *= 12/ephem.pi
    if hms:
        h = int(a)
        a -= int(a)
        a *= 60
        m = int(a)
        a -= int(a)
        a *= 60
        s = a
        return h, m, s
    return a

def get_data(object_list: List[Tuple[ephem.Body, str]],
             location: Optional[ephem.Observer] = None) -> list:
    """Create data dictionary for object list."""
    body_data = {}
    if location:
        body_data['query_date'] = location.date.datetime()
    for o, body_type in object_list:
        if location:
            o.compute(location)
        else:
            o.compute()
        data = {
            # Split name if multiple designations are given. The separator is a pipe (|).
            'name': o.name.split('|') if o.name.find('|') >= 0 else o.name,
            'ra': format_ra(o.ra),
            'dec': format_angle(o.dec),
            'size': o.size,
            'mag': o.mag,
            'elong': o.elong,
        }
        if location: # altitude and azimuth only available with a valid location
            data['alt'] = format_angle(o.alt)
            data['az'] = format_angle(o.az)
        if body_type == 'star': # spectral type is (usually) available with a star body type
            data['spectral_type'] = o._spect
        if body_type == 'solar_system': # special properties available for solar system objects
            data['earth_dist'] = {
                'au': o.earth_distance,
                'km': o.earth_distance * 149597870.700,
                'mi': o.earth_distance * 149597870700 / 1604.344
            }
            data['constellation'] = ephem.constellation(o)
            # date for calculations below
            date = location.date if location else ephem.now()
            if o.name != 'Sun': # we don't need "phase" or "sun_dist" for the sun itself
                data['sun_dist'] = {
                    'au': o.sun_distance,
                    'km': o.sun_distance * 149597870.700,
                    'mi': o.sun_distance * 149597870700 / 1604.344
                }
                data['phase'] = o.phase
            if o.name == 'Moon': # special properties available for the moon
                data['illuminated_surface'] = o.moon_phase * 100
                data['phase_name'] = get_phase_name(location)
                data['next_new_moon'] = (ephem.next_new_moon(date)).datetime()
                data['next_first_quarter'] = (ephem.next_first_quarter_moon(date)).datetime()
                data['next_full_moon'] = (ephem.next_full_moon(date)).datetime()
                data['next_last_quarter'] = (ephem.next_last_quarter_moon(date)).datetime()
            if o.name == 'Sun': # special properties available for the sun
                data['next_solstice'] = (ephem.next_solstice(date)).datetime()
                data['next_equinox'] = (ephem.next_equinox(date)).datetime()
        elif body_type == 'satellite': # special properties available for satellites
            data['elev'] = {'m' :o.elevation, 'mi': o.elevation / 1604.344}
            data['eclipsed'] = o.eclipsed
            if location:
                data['range'] = {'m': o.range, 'mi': o.range / 1604.344}
                data['range_velocity'] = o.range_velocity
                rise_time, rise_az, max_alt_time, max_alt, set_time, set_az = location.next_pass(o)
                data['next_pass'] = {
                    'rise_time': rise_time.datetime(),
                    'rise_az': format_angle(rise_az),
                    'max_altitude_time': max_alt_time.datetime(),
                    'max_altitude': format_angle(max_alt),
                    'set_time': set_time.datetime(),
                    'set_az': format_angle(set_az),
                }
        elif body_type == 'planetary_moon': # special properties available for planetary moons
            data['visible'] = o.earth_visible
            data['pos'] = o.x, o.y, o.z
        # computed last, since these calculations change time, body position
        if body_type not in ['satellite', 'planetary_moon'] and location:
            # compute antitransit time of object
            antitransit = location.previous_antitransit(o)
            data['rise_time'] = (location.next_rising(o, start = antitransit)).datetime()
            data['rise_az'] = format_angle(o.az)
            data['transit_time'] = (location.next_transit(o, start = antitransit)).datetime()
            data['transit_alt'] = format_angle(o.alt)
            data['set_time'] = (location.next_setting(o, start = antitransit)).datetime()
            data['set_az'] = format_angle(o.az)
        if o.name == 'Sun':
            # computed last, since these calculations change the horizon
            location.horizon = '-18'
            astro_dawn = location.next_rising(o, start = antitransit)
            astro_dusk = location.next_setting(o, start = antitransit)
            location.horizon = '-12'
            nautical_dawn  = location.next_rising(o, start = antitransit)
            nautical_dusk = location.next_setting(o, start = antitransit)
            location.horizon = '-6'
            civil_dawn = location.next_rising(o, start = antitransit)
            civil_dusk = location.next_setting(o, start = antitransit)
            # The US Naval Observatory uses -34' as a constant for sunrise/sunset,
            # rather than using atmospheric refraction.
            # Setting pressure to 0 has the effect of ignoring effects of refraction.
            # Save pressure for reset after calculations.
            pressure, location.pressure = location.pressure, 0
            location.horizon = '-0:34'
            usno_dawn = location.next_rising(o, start = antitransit)
            usno_dusk = location.next_setting(o, start = antitransit)
            data['astronomical_dawn'] = astro_dawn.datetime()
            data['nautical_dawn'] = nautical_dawn.datetime()
            data['civil_dawn'] = civil_dawn.datetime()
            data['USNO_sunrise'] = usno_dawn.datetime()
            data['USNO_sunset'] = usno_dusk.datetime()
            data['civil_dusk'] = civil_dusk.datetime()
            data['nautical_dusk'] = nautical_dusk.datetime()
            data['astronomical_dusk'] = astro_dusk.datetime()
            #reset pressure and horizon
            location.pressure = pressure
            location.horizon = 0
        body_data[o.name] = data
    return body_data

def whats_up(
        start: datetime.datetime,
        end: datetime.datetime,
        location: ephem.Observer,
        magnitude: float = 6.) -> dict:
    """
    Find all objects that will be "up" between start and end time.

    Takes a location, start and end time, and limiting magnitude.
    """
    body_list = []
    start_e, end_e = ephem.Date(start), ephem.Date(end)
    location.date = start_e
    for o,body_type in filter(lambda x: x[1] != 'planetary_moon', OBJECT_DICT.values()):
        o.compute(location)
        circumpolar = False
        rising, setting = None, None
        if body_type != 'satellite':
            try:
                rising = location.next_rising(o, start = location.previous_antitransit(o))
                setting = location.next_setting(o, start = rising)
            except ephem.AlwaysUpError:
                circumpolar = True
            except ephem.NeverUpError:
                pass
        elif body_type == 'satellite':
            info = list(location.next_pass(o))
            rising, setting = info[0], info[4]
        # the logic here is as follows:
        # 1. Is object bright enough?
        # 2. Is it in the sky now?
        #    a. Is it circumpolar (does it never set)?
        #    b. Does it rise during the given timeframe?
        #    c. Does it set during the given timeframe?
        #    d. Does it rise before the given timeframe and set after the given timeframe?
        if o.mag < -30:
            # something's wrong with the data--skip it.
            continue
        if o.mag < magnitude and (circumpolar or \
                                  (rising and start_e < rising < end_e) or \
                                  (setting and start_e < setting < end_e) or \
                                  (rising and setting and (rising < start_e) and \
                                      (setting > end_e))):
            # If it's in the sky and bright enough, add the entry to the list
            if rising or setting or circumpolar:
                body_list.append({
                    'name': o.name.split('|') if o.name.find('|') >= 0 else o.name,
                    'magnitude': o.mag
                })
            # If it has a rise time, add that to the most recently added item
            if rising:
                body_list[-1]['rise_time'] = rising.datetime()
            # If it has a set time, add that to the most recently added item
            if setting:
                body_list[-1]['set_time'] = setting.datetime()
            if o.name == 'Moon':
                body_list[-1]['phase'] = o.moon_phase * 100
    body_list.sort(key = lambda x: x['magnitude'])
    return {
        'start_time': start, # start of timeframe
        'end_time': end, # end of timeframe
        'objects': body_list # all items visible during timeframe, as computed above
    }

def get_phase_name(location: Optional[ephem.Observer] = None, wiggle_room: float = 1.5) -> str:
    """Return name of the phase of the moon."""
    if location:
        date = location.date
    else:
        date = ephem.now()
    if abs(ephem.next_first_quarter_moon(date) - date) < wiggle_room or \
            abs(ephem.previous_first_quarter_moon(date) - date) < wiggle_room:
        return 'first quarter moon'
    elif abs(ephem.next_full_moon(date) - date) < wiggle_room or \
            abs(ephem.previous_full_moon(date) - date) < wiggle_room:
        return 'full moon'
    elif abs(ephem.next_last_quarter_moon(date) - date) < wiggle_room or \
            abs(ephem.previous_last_quarter_moon(date) - date) < wiggle_room:
        return 'last quarter moon'
    elif abs(ephem.next_new_moon(date) - date) < wiggle_room or \
            abs(ephem.previous_new_moon(date) - date) < wiggle_room:
        return 'new moon'
    elif ephem.next_first_quarter_moon(date) - ephem.previous_new_moon(date) < 29:
        return 'waxing crescent'
    elif ephem.next_full_moon(date) - ephem.previous_first_quarter_moon(date) < 29:
        return 'waxing gibbous'
    elif ephem.next_last_quarter_moon(date) - ephem.previous_full_moon(date) < 29:
        return 'waning gibbous'
    elif ephem.next_new_moon(date) - ephem.previous_last_quarter_moon(date) < 29:
        return 'waning crescent'
    return ''

class Encoder(json.JSONEncoder):
    """JSON Encoder to serialize datetime objects."""

    global tz
    def default(self, obj):
        """JSON Encoder to serialize datetime objects."""
        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is None or obj.tzinfo.utcoffset(obj) is None:
                obj = pytz.utc.localize(obj)
            if tz is not None:
                return obj.astimezone(pytz.timezone(tz)).strftime(TIME_FORMAT)
            return obj.strftime(TIME_FORMAT)
        return json.JSONEncoder.default(self, obj)

def main():
    """Process arguments."""
    global tz
    data = read_in()
    lat = str(data['lat']) if 'lat' in data.keys() else None
    lon = str(data['lon']) if 'lon' in data.keys() else None
    elev = data['elev'] if 'elev' in data.keys() else None
    horizon = data['horizon'] if 'horizon' in data.keys() else None
    date = data['date'] if 'date' in data.keys() else datetime.datetime.now()
    tz = data['tz'] if 'tz' in data.keys() else DEFAULT_TZ
    temp = data['temp'] if 'temp' in data.keys() else 25
    pressure = data['pressure'] if 'pressure' in data.keys() else None
    if isinstance(date, str):
        date = dateutil.parser.parse(date)
    if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
        date = pytz.timezone(tz).localize(date)
    date = date.astimezone(pytz.utc)
    end = data['end'] if 'end' in data.keys() else None
    if isinstance(end, str):
        end = dateutil.parser.parse(end)
    if end and (end.tzinfo is None or end.tzinfo.utcoffset(end) is None):
        end = pytz.timezone(tz).localize(end)
    if end:
        end = end.astimezone(pytz.utc)
    min_magnitude = data['mag'] if 'mag' in data.keys() else 6
    if lat and lon:
        location = get_location(lat, lon, elev, date, horizon, temp, pressure)
    else:
        location=None
    try:
        query_set = set(map(str.lower, data['body']))
        query_set = query_set.intersection(set(OBJECT_DICT.keys()))
        query_list = list(map(lambda x: OBJECT_DICT[x], query_set))
        info = get_data(query_list, location)
    except KeyError:
        if location:
            if not end:
                end = date
            info = whats_up(date, end, location, magnitude = min_magnitude)
        else:
            info='nothing'
    print(json.dumps(info, cls = Encoder))

if __name__ == '__main__':
    main()
