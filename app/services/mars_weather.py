import httpx


def get_mars_weather() -> dict:
    resp = httpx.get("https://api.maas2.apollorion.com/", timeout=10)
    resp.raise_for_status()
    return resp.json()
