import httpx
from datetime import datetime, timezone
import pytz


def get_neo_list(start_date: str, end_date: str, tz_name: str, api_key: str) -> dict:
    url = (
        f"https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    )
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise Exception(data["error"])

    data.pop("links", None)

    for date_key, neos in data.get("near_earth_objects", {}).items():
        for neo in neos:
            neo.pop("links", None)
            neo.pop("is_sentry_object", None)
            if neo.get("close_approach_data"):
                ca = neo["close_approach_data"][0]
                epoch = ca.get("epoch_date_close_approach")
                if epoch:
                    dt = datetime.fromtimestamp(epoch / 1000, tz=timezone.utc)
                    ca["close_approach_date_full"] = dt.astimezone(
                        pytz.timezone(tz_name)
                    ).isoformat()
                    ca.pop("epoch_date_close_approach", None)
    return data
