import os
from dotenv import load_dotenv

load_dotenv()

# LAPO default coordinates
DEFAULT_LAT = 37.62218579135644
DEFAULT_LON = -97.62695789337158
DEFAULT_TZ = "America/Chicago"

# API keys
GOOGLE_PLACES_API_KEY = os.getenv("GooglePlacesAPIKey", "")
OPENWEATHERMAP_API_KEY = os.getenv("OpenWeatherMapAPIKey", "")
NASA_API_KEY = os.getenv("NASAAPIKey", "")
N2YO_API_KEY = os.getenv("N2YOAPIKey", "")

# Server
PORT = int(os.getenv("PORT", "3000"))
