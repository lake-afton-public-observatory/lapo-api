"""A database of objects for use with the whatsup api."""

import ephem
import re
import os
import requests
import requests_cache
from typing import List, Tuple

def read_file(filename: str, object_type: str) -> List[Tuple[ephem.Body, str]]:
    """Read the given file into a dictionary."""
    file_objects = {}
    s = requests_cache.core.CachedSession(cache_name='./lib/cache',expire_after = 7 * 24 * 60 * 60, old_data_on_error = True) # 7*24*60*60=604800 seconds is one week
    if re.match('http', filename):
        ask = s.get(filename)
        if ask.status_code == 200:
            file = ask.content.decode('utf-8').split('\n')
        else:
            file = []
    if os.path.isfile(filename):
        try:
            with open(filename) as f:
                file = f.readlines()
        except Exception:
            file = []
    if object_type != 'satellite':
        for line in file:
            if line and line[0] != '#':
                try:
                    file_objects[re.match('[^,|]+', line).group().lower()] = (ephem.readdb(line), object_type)
                except Exception:
                    pass
    else:
        for tle in [file[i:i+3] for i in range(0, len(file), 3)]:
            try:
                file_objects[tle[0].lower()] = (ephem.readtle(tle[0], tle[1], tle[2]), object_type)
            except Exception:
                pass
    return file_objects

def get_objects(additional_catalogs_list: List[str]) -> dict:
    """Return a dictionary of all objects."""
    object_dict = {}
    #Solar System
    object_dict['sun'] = (ephem.Sun(), 'solar_system')

    object_dict['mercury'] = (ephem.Mercury(), 'solar_system')

    object_dict['venus'] = (ephem.Venus(), 'solar_system')

    object_dict['moon'] = (ephem.Moon(), 'solar_system')

    object_dict['mars'] = (ephem.Mars(), 'solar_system')
    object_dict['phobos'] = (ephem.Phobos(), 'planetary_moon')
    object_dict['deimos'] = (ephem.Deimos(), 'planetary_moon')

    object_dict['jupiter'] = (ephem.Jupiter(), 'solar_system')
    object_dict['ganymede'] = (ephem.Ganymede(), 'planetary_moon')
    object_dict['callisto'] = (ephem.Callisto(), 'planetary_moon')
    object_dict['io'] = (ephem.Io(), 'planetary_moon')
    object_dict['europa'] = (ephem.Europa(), 'planetary_moon')

    object_dict['saturn'] = (ephem.Saturn(), 'solar_system')
    object_dict['titan'] = (ephem.Titan(), 'planetary_moon')
    object_dict['iapetus'] = (ephem.Iapetus(), 'planetary_moon')
    object_dict['rhea'] = (ephem.Rhea(), 'planetary_moon')
    object_dict['tethys'] = (ephem.Tethys(), 'planetary_moon')
    object_dict['dione'] = (ephem.Dione(), 'planetary_moon')
    object_dict['enceladus'] = (ephem.Enceladus(), 'planetary_moon')
    object_dict['mimas'] = (ephem.Mimas(), 'planetary_moon')

    object_dict['uranus'] = (ephem.Uranus(), 'solar_system')
    object_dict['titania'] = (ephem.Titania(), 'planetary_moon')
    object_dict['oberon'] = (ephem.Oberon(), 'planetary_moon')
    object_dict['hyperion'] = (ephem.Hyperion(), 'planetary_moon')
    object_dict['ariel'] = (ephem.Ariel(), 'planetary_moon')
    object_dict['umbriel'] = (ephem.Umbriel(), 'planetary_moon')
    object_dict['miranda'] = (ephem.Miranda(), 'planetary_moon')

    object_dict['neptune'] = (ephem.Neptune(), 'solar_system')

    object_dict['pluto'] = (ephem.Pluto(), 'solar_system')

    for file,object_type in additional_catalogs_list:
        object_dict.update(read_file(file, object_type))
    return object_dict
