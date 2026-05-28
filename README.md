# Lake Afton API

A REST API for [Lake Afton Public Observatory](https://www.lakeafton.com/) (LAPO), providing astronomical data, weather conditions, and observatory information.

## Getting Started

### Prerequisites

- Python 3.11+

### Setup

1. Fork and clone the repo
2. Run `./setup.sh` — this creates a virtual environment and installs dependencies
3. Fill out `.env` with your API keys (see [API Keys](#api-keys) below)
4. Activate the virtual environment: `source .venv/bin/activate`
5. Run `make run` (or `uvicorn app.main:app --reload --port 3333`)
6. Visit `http://localhost:3333`
7. Interactive API docs available at `http://localhost:3333/docs`
8. Stop the server with `Ctrl+C`

### API Keys

| Key | Source | Required for |
|-----|--------|--------------|
| `OpenWeatherMapAPIKey` | [OpenWeatherMap](https://openweathermap.org/api) | Weather, forecast, seeing conditions |
| `NASAAPIKey` | [NASA API](https://api.nasa.gov/) | Near-Earth objects |

Elevation data is sourced from SRTM via `srtm.py` (no key needed — tiles are downloaded automatically on first use).
ISS pass predictions use Skyfield + Celestrak TLE data (no key needed).

### Available Commands

| Command | Description |
|---------|-------------|
| `make run` | Start the dev server on port 3333 with auto-reload |
| `make test` | Run the test suite |
| `make install` | Install Python dependencies |

### Running Tests

```
make test
```

## Endpoints

All endpoints default to the observatory's location (37.62N, 97.63W) and the `America/Chicago` timezone.

### Common Query Parameters

Most endpoints accept the following optional parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `lat` | Latitude (-90 to 90) | `37.62` |
| `lon` | Longitude (-180 to 180) | `-97.63` |
| `tz` | Timezone (IANA format) | `America/Chicago` |
| `dt` | Date/time (ISO 8601) | `2026-06-15T21:00:00` |

### Observatory

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /hours` | Seasonal open/close times for the upcoming Saturday | none |
| `GET /schedule` | Viewing schedule for the upcoming Friday/Saturday | none |

### Celestial Bodies

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /planets` | Detailed ephemeris for all planets (RA, dec, rise/set, distance, phase) | `lat`, `lon`, `tz`, `dt` |
| `GET /visiblePlanets` | Currently visible planets with brightness descriptions | `lat`, `lon` |
| `GET /sun` | Sun position, rise/set, dawn/dusk times, next solstice/equinox | `lat`, `lon`, `tz`, `dt` |
| `GET /moon` | Moon position, phase, illumination, rise/set, next phase dates | `lat`, `lon`, `tz`, `dt` |

### Sky Visibility

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /whatsup` | Objects in the sky above a limiting magnitude during a time window | `lat`, `lon`, `tz`, `start`, `end` |
| `GET /whatsup-next` | Objects visible during the next LAPO open hours | none |

### Weather

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /weather` | Current conditions (temperature, wind, humidity, visibility, clouds) | `lat`, `lon`, `tz` |
| `GET /forecast` | 3-hour interval forecast | `lat`, `lon`, `tz` |
| `GET /mars-weather` | Current weather on Mars | none |

### Satellites & Space

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /iss` | Current ISS position, altitude, and velocity | `tz`, `dt` |
| `GET /iss-passes` | Upcoming visible ISS passes | `lat`, `lon`, `tz` |
| `GET /neo` | Near-Earth objects for the next 7 days | `tz` |

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run `python -m pytest tests/ -v`
5. Submit a pull request

Questions? Reach out at sduncan@lakeafton.com

## License

[ISC](LICENSE)
