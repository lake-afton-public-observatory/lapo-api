import os
from dotenv import load_dotenv

load_dotenv()

# LAPO default coordinates
DEFAULT_LAT = 37.62218579135644
DEFAULT_LON = -97.62695789337158
DEFAULT_TZ = "America/Chicago"

# API keys (external services)
OPENWEATHERMAP_API_KEY = os.getenv("OpenWeatherMapAPIKey", "")
NASA_API_KEY = os.getenv("NASAAPIKey", "")

# Optional consumer API key auth.
# Set LAPO_API_KEYS to a comma-separated list of valid keys to enable enforcement.
# When unset or empty, all requests are allowed (open mode).
_raw = os.getenv("LAPO_API_KEYS", "")
LAPO_API_KEYS: set[str] = {k.strip() for k in _raw.split(",") if k.strip()}
API_AUTH_ENABLED = bool(LAPO_API_KEYS)

# Sentry error monitoring (optional — leave unset to disable)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Server
PORT = int(os.getenv("PORT", "3000"))
