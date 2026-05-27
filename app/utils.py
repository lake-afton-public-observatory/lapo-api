"""Utility functions for the Lake Afton Public Observatory API."""

from datetime import datetime
from typing import Optional

import pytz


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9


def mps_to_mph(meters_per_second: float) -> float:
    return meters_per_second / 0.44704


def meters_to_miles(meters: float) -> float:
    return meters / 1609.344


def round_off(number: float, digits: int = 0) -> float:
    return round(number * 10**digits) / 10**digits


def feels_like_temp(
    temp_celsius: float,
    wind_mps: float,
    relative_humidity: float,
) -> float:
    """Return feels-like temperature in Celsius using NOAA wind chill and heat index.

    Wind chill applies when T <= 50°F and wind speed >= 3 mph.
    Heat index applies when T > 80°F and RH < (245 - T*5/3).
    Otherwise returns the actual temperature.
    """
    T_f = celsius_to_fahrenheit(temp_celsius)
    W_mph = mps_to_mph(wind_mps)
    RH = relative_humidity

    # Wind chill
    if T_f <= 50 and W_mph >= 3:
        wind_chill_f = (
            35.74
            + 0.6215 * T_f
            - 35.75 * W_mph**0.16
            + 0.4275 * T_f * W_mph**0.16
        )
        return fahrenheit_to_celsius(wind_chill_f)

    # Heat index: applies when T > 80°F and RH <= (245 - T*5/3)
    # (if RH exceeds that threshold, the formula gives absurd results)
    if T_f > 80 and (245 - T_f * 5 / 3) >= RH:
        # Start with simplified formula
        HI = 0.5 * (T_f + 61 + (T_f - 68) * 1.2 + RH * 0.094)
        # Only use Rothfusz when the average of HI and T exceeds 80°F
        if (HI + T_f) / 2 >= 80:
            HI = (
                -42.379
                + 2.04901523 * T_f
                + 10.14333127 * RH
                - 0.22475541 * T_f * RH
                - 0.00683783 * T_f**2
                - 0.05481717 * RH**2
                + 0.00122874 * T_f**2 * RH
                + 0.00085282 * T_f * RH**2
                - 0.00000199 * T_f**2 * RH**2
            )
            ADJ = 0
            # Low humidity adjustment: RH < 13% and 80 <= T <= 112
            if RH < 13 and 80 <= T_f <= 112:
                ADJ = -((13 - RH) / 4) * ((17 - abs(T_f - 95)) / 17) ** 0.5
            # High humidity adjustment: RH > 85% and 80 <= T <= 87
            elif RH > 85 and 80 <= T_f <= 87:
                ADJ = ((RH - 85) / 10) * ((87 - T_f) / 5)
            HI += ADJ
            return fahrenheit_to_celsius(HI)

    return temp_celsius


# Observatory hours by month group
# Months 3,4,9,10: 8:30pm-10:30pm
# Months 5-8:      9:00pm-11:30pm
# Months 11,12,1,2: 7:30pm-9:30pm
_OBSERVATORY_HOURS = {
    "spring_fall": {
        "months": {3, 4, 9, 10},
        "open_h24": "20:30",
        "close_h24": "22:30",
        "open_display": "8:30pm",
        "close_display": "10:30pm",
    },
    "summer": {
        "months": {5, 6, 7, 8},
        "open_h24": "21:00",
        "close_h24": "23:30",
        "open_display": "9:00pm",
        "close_display": "11:30pm",
    },
    "winter": {
        "months": {11, 12, 1, 2},
        "open_h24": "19:30",
        "close_h24": "21:30",
        "open_display": "7:30pm",
        "close_display": "9:30pm",
    },
}


def get_observatory_hours(month: int) -> dict:
    """Return observatory hours for a given month number (1-12).

    Returns a dict with 'display' and 'h24' sub-dicts each containing
    'open' and 'close' times.
    """
    for group in _OBSERVATORY_HOURS.values():
        if month in group["months"]:
            return {
                "display": {
                    "open": group["open_display"],
                    "close": group["close_display"],
                },
                "h24": {
                    "open": group["open_h24"],
                    "close": group["close_h24"],
                },
            }
    raise ValueError(f"Invalid month: {month}")


def validate_lat(value) -> Optional[float]:
    """Parse string to float latitude; return None if outside -90..90 or if None."""
    if value is None:
        return None
    try:
        lat = float(value)
    except (TypeError, ValueError):
        return None
    if lat < -90 or lat > 90:
        return None
    return lat


def validate_lon(value) -> Optional[float]:
    """Parse string to float longitude; return None if outside -180..180 or if None."""
    if value is None:
        return None
    try:
        lon = float(value)
    except (TypeError, ValueError):
        return None
    if lon < -180 or lon > 180:
        return None
    return lon


def parse_date(value: str, tz_name: str) -> Optional[datetime]:
    """Parse an ISO date string, localize if naive, return None on failure."""
    if value is None:
        return None
    try:
        tz = pytz.timezone(tz_name)
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        return dt
    except Exception:
        return None
