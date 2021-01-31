require('dotenv').config();
const express = require('express');
const router = express.Router(); // eslint-disable-line new-cap
const suncalc = require('suncalc');
const moment = require('moment-timezone');
const viewingSchedule = require('../lib/viewingSchedule');
const astropical = require('../lib/astropical');
const getEvents = require('../lib/events');
const helpers = require('../lib/helpers');

/* home page. */
router.get('/', function(req, res, next) {
  const response = {
    message:
      'Welcome to the Lake Afton Public Observatory API! To contribute, visit https://github.com/lake-afton-public-observatory/lapo-api',
  };
  res.json(response);
});

/* LAPO hours

Returns hours in a "pretty-print" format, as well as an open and close time
*/
router.get('/hours', function(req, res, next) {
  // need upcoming Saturday if current date is not Saturday
  const dayAnchor=6;
  const currentTime = new Date();
  if (currentTime.getDay()<dayAnchor) {
    currentTime.setDate(currentTime.getDate()+(dayAnchor-currentTime.getDay()));
  }
  const month = currentTime.getMonth() + 1;
  const response = {
    hours: {
      prettyHours: '',
      open: '',
      close: '',
    },
  };
  switch (month) {
    case 3:
    case 4:
      response.hours.open = '8:30pm';
      response.hours.close = '10:30pm';
      break;
    case 5:
    case 6:
    case 7:
    case 8:
      response.hours.open = '9:00pm';
      response.hours.close = '11:30pm';
      break;
    case 9:
    case 10:
      response.hours.open = '8:30pm';
      response.hours.close = '10:30pm';
      break;
    case 11:
    case 12:
    case 1:
    case 2:
      response.hours.open = '7:30pm';
      response.hours.close = '9:30pm';
      break;
  }
  response.hours.prettyHours =
    `${response.hours.open} – ${response.hours.close}`;
  res.json(response);
});

/* planets

Returns a list of all planets visible, their altitude (above the horizon),
distance from Earth in AU and in miles, visual magnitude, a description of the
magnitude, and the constellation in which the planet can be found.
*/
router.get('/planets', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = qs.lat || 37.62218579135644;
  const lon = qs.lon || -97.62695789337158;
  const data = await astropical.getPlanetEphem(lat, lon);
  // now we have the data
  const planets = data.response;
  if (planets !== undefined) {
    const visiblePlanets = [];

    planets.forEach(function(planet) {
      if (planet.alt > 0) {
        let brightness = '';
        if (planet.mag > 6.5) {
          brightness = 'not visible to naked eye';
        } else if (planet.mag >= 2) {
          brightness = 'dim';
        } else if (planet.mag >= 1) {
          brightness = 'average';
        } else if (planet.mag >= 0) {
          brightness = 'bright';
        } else if (planet.mag >= -3) {
          brightness = 'very bright';
        } else {
          brightness = 'extremely bright';
        }

        const prettyPlanetStruct = {
          name: planet.name,
          altitudeDegrees: planet.alt,
          distanceFromEarthAU: planet.au_earth,
          distanceFromEarthMiles: (planet.au_earth * 149597870700) / 1609.344,
          magnitude: planet.mag,
          brightness: brightness,
          constellation: planet.const,
        };

        visiblePlanets.push(prettyPlanetStruct);
      }
    });
    res.json(visiblePlanets);
  } else {
    res.json(data);
  }
});

/* planets 2

Returns a structure containing the following data on *all* the planets:
- right ascension
- declination
- size (in arcseconds)
- magnitude
- elongation
- altitude
- azimuth
- earth distance
  - au
  - km
  - mi
- constellation
- sun distance
  - au
  - km
  - mi
- phase
- rise time
- rise azimuth
- transit time
- transit altitude
- set time
- set azimuth
*/
router.get('/planets2', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = qs.lat || 37.62218579135644;
  const lon = qs.lon || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago'; // eslint-disable-line max-len
  const date = qs.dt;
  const key = process.env.OpenWeatherMapAPIKey;
  const elev = await helpers.getElevation(
      lat,
      lon,
      process.env.GooglePlacesAPIKey
  );
  const weatherData = await helpers.getWeather(lat, lon, key);
  const pressure = weatherData.groundLevelPressure;
  const temp = weatherData.temperature.celsius;
  const data = {
    lat: lat,
    lon: lon,
    elev: elev,
    tz: tz,
    body: [
      'mercury',
      'venus',
      'mars',
      'jupiter',
      'saturn',
      'uranus',
      'neptune',
      'pluto',
    ],
    pressure: pressure,
    temp: temp,
  };
  if (qs.dt) {
    data.date = date;
  }
  const result = await helpers.pythonCall(data);
  res.json(result);
});

/* sun

Returns a structure containing the following data on the sun:
- right ascension
- declination
- size (in arcseconds)
- magnitude (really bright--don't look directly at it)
- elongation
- altitude
- azimuth
- earth distance
  - au
  - km
  - mi
- constellation
- next solstice (date of next solstice)
- next equinox (date of next equinox)
- rise time (center of sun crosses horizon)
- rise azimuth
- transit time
- transit altitude
- set time (center of sun crosses horizon)
- set azimuth
- astronomical dawn (sun crosses 18° below horizion)
- nautical dawn (sun crosses 12° below horizion)
- civil dawn (sun crosses 6° below horizion)
- USNO sunrise (sunrise using US Naval Observatory method,
      sun crosses 0.34° below horizon, no atmospheric refraction included)
- USNO sunset (sunset using US Naval Observatory method,
      sun crosses 0.34° below horizon, no atmospheric refraction included)
- civil dusk (sun crosses 6° below horizion)
- nautical dusk (sun crosses 12° below horizion)
- astronomical dusk (sun crosses 18° below horizion)
*/
router.get('/sun', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = qs.lat || 37.62218579135644;
  const lon = qs.lon || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago';
  const date = moment(qs.dt).format();
  const key = process.env.OpenWeatherMapAPIKey;
  const elev = await helpers.getElevation(
      lat,
      lon,
      process.env.GooglePlacesAPIKey
  );
  const weatherData = await helpers.getWeather(lat, lon, key);
  const pressure = weatherData.groundLevelPressure;
  const temp = weatherData.temperature.celsius;
  const data = {
    lat: lat,
    lon: lon,
    elev: elev,
    tz: tz,
    body: ['sun'],
    pressure: pressure,
    temp: temp,
  };
  if (qs.dt) {
    data.date = date;
  }
  const result = await helpers.pythonCall(data);
  res.json(result);
});

/* moon

Returns a structure containing the following data on the moon:
- right ascension
- declination
- size (in arcseconds)
- magnitude
- elongation
- altitude
- azimuth
- earth distance
  - au
  - km
  - mi
- constellation
- sun distance
  - au
  - km
  - mi
- phase
- illuminated surface
- phase name
- next new moon (date and time)
- next first quarter (date and time)
- next full moon (date and time)
- next last quarter (date and time)
- rise time (center of moon crosses horizon)
- rise azimuth
- transit time
- transit altitude
- set time (center of moon crosses horizon)
- set azimuth
*/
router.get('/moon', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = qs.lat || 37.62218579135644;
  const lon = qs.lon || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago';
  const date = moment(qs.dt).format();
  const key = process.env.OpenWeatherMapAPIKey;
  const elev = await helpers.getElevation(
      lat,
      lon,
      process.env.GooglePlacesAPIKey
  );
  const weatherData = await helpers.getWeather(lat, lon, key);
  const pressure = weatherData.groundLevelPressure;
  const temp = weatherData.temperature.celsius;
  const data = {
    lat: lat,
    lon: lon,
    elev: elev,
    tz: tz,
    body: ['moon'],
    pressure: pressure,
    temp: temp,
  };
  if (qs.dt) {
    data.date = date;
  }
  const result = await helpers.pythonCall(data);
  res.json(result);
});

/* events

Returns a list of upcoming events from the LAPO Google Calendar.
*/
router.get('/events', async function(req, res, next) {
  const key = process.env.GoogleCalendarAPIKey;
  const calendarId = process.env.GoogleCalendarId;
  const data = await getEvents(calendarId, key);
  try {
    const events = data.items;
    const eventsForDisplay = [];

    events.forEach(function(event) {
      const startDate = new Date(event.start.dateTime).toString();
      const endDate = new Date(event.end.dateTime).toString();
      const eventStruct = {
        summary: event.summary,
        description: event.description,
        startTime: startDate,
        endTime: endDate,
        location: event.location,
      };
      eventsForDisplay.push(eventStruct);
    });

    res.json(eventsForDisplay);
  } catch (e) {
    console.error(e.name, e.message);
  }
});

/* schedule

Get the date of the upcoming Sunday, then subtract two days to get the
relevant Friday. The schedules are made for "Fridays" but they apply for
both Friday and Saturday, so if someone requests the schedule on
Saturday, we need to get the schedule that's made for "yesterday" but
if they request on a Thursday, we need to get it for "tomorrow"--so
we use the next Sunday, minus two days to get that. Math'd.

The schedule lives in /lib/viewingSchedule and is manually generated by
minions
*/
router.get('/schedule', function(req, res, next) {
  const upcomingSunday = new Date();
  upcomingSunday.setDate(upcomingSunday.getDate() +
    (0 + 7 - upcomingSunday.getDay()) % 7);
  // let upcomingSundayFormatted = moment(upcomingSunday).format('MM-DD-YYYY');
  const relevantFriday = moment(upcomingSunday).subtract(2, 'days');
  const relevantFridayFormatted = moment(relevantFriday).format('MM-DD-YYYY');

  const response = {
    schedule: viewingSchedule[relevantFridayFormatted],
  };

  res.json(response);
});

/* what's up

Returns a list of objects in the sky above a limiting magnitude. Each item
also includes the magnitude, rise time and set time (if applicable), sorted
by magnitude from brightest to dimmest.
*/
router.get('/whatsup', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = qs.lat || 37.62218579135644;
  const lon = qs.lon || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago';
  const start = moment(qs.start).format();
  let end = moment(qs.end).format();
  const key = process.env.OpenWeatherMapAPIKey;
  const elev = await helpers.getElevation(
      lat,
      lon,
      process.env.GooglePlacesAPIKey
  );
  if (moment(start) > moment(end)) {
    end = start;
  }
  const weatherData = await helpers.getWeather(lat, lon, key);
  const pressure = weatherData.groundLevelPressure;
  const temp = weatherData.temperature.celsius;
  const data = {
    lat: lat,
    lon: lon,
    elev: elev,
    tz: tz,
    mag: 6,
    pressure: pressure,
    temp: temp,
  };
  if (qs.start) {
    data.date = start;
  }
  if (qs.end) {
    data.end = end;
  }
  const result = await helpers.pythonCall(data);
  res.json(result);
});

/* whatsup-next

Returns a list of objects that will be in the sky during the upcoming open
hours of LAPO, above a limiting magnitude. Each item also includes the
magnitude, rise time and set time (if applicable), sorted by magnitude from
brightest to dimmest.
*/
router.get(/whatsup[_-]next\/?/, async function(req, res, next) {
  const lat = 37.62218579135644;
  const lon = -97.62695789337158;
  const elev = await helpers.getElevation(
      lat,
      lon,
      process.env.GooglePlacesAPIKey
  );
  const tz = 'America/Chicago';
  const currentDate = new Date();
  const upcomingSunday = new Date();
  upcomingSunday.setDate(
      upcomingSunday.getDate() + ((0 + 7 - upcomingSunday.getDay()) % 7)
  );
  const Friday = moment(upcomingSunday)
      .subtract(2, 'days')
      .format('YYYY-MM-DD');
  const Saturday = moment(upcomingSunday)
      .subtract(1, 'days')
      .format('YYYY-MM-DD');
  const monthF = moment(Friday).month() + 1;
  let open;
  let close;
  switch (monthF) {
    case 11:
    case 12:
    case 1:
    case 2:
      open = '19:30';
      close = '21:30';
      break;
    case 5:
    case 6:
    case 7:
    case 8:
      open = '21:00';
      close = '23:30';
      break;
    case 3:
    case 4:
    case 9:
    case 10:
      open = '20:30';
      close = '22:30';
      break;
  }
  if (moment(Friday + 'T' + close).isAfter(currentDate)) {
    open = Friday + 'T' + open;
    close = Friday + 'T' + close;
  } else {
    open = Saturday + 'T' + open;
    close = Saturday + 'T' + close;
  }
  const data = {
    lat: lat,
    lon: lon,
    elev: elev,
    tz: tz,
    mag: 6,
    date: open,
    end: close,
  };
  const result = await helpers.pythonCall(data);
  res.json(result);
});

/* weather

Returns current weather conditions, including a description of current
conditions (e.g. light snow), temperature (in degrees Celsius and degrees
Fahrenheit), feels like temperature (wind chill/heat index, if applicable),
min and max temperatures for the area, barometric pressure in millibars,
relative humidity, visibility (in kilometers and miles), wind speed (in meters
per second and miles per hour) and direction, cloud cover in percentage
*/
router.get('/weather', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = parseFloat(qs.lat) || 37.62218579135644;
  const lon = parseFloat(qs.lon) || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago';
  const key = process.env.OpenWeatherMapAPIKey;
  const reply = await helpers.getWeather(lat, lon, key, tz);
  res.json(reply);
});

/* forecast

Returns weather forecast at 3 hour intervals, including a description of
current conditions (e.g. light snow), temperature (in degrees Celsius and
degrees Fahrenheit), feels like temperature (wind chill/heat index, if
applicable), min and max temperatures for the area, barometric pressure in
millibars, relative humidity, visibility (in kilometers and miles), wind speed
(in meters per second and miles per hour) and direction, cloud cover in
percentage. May include amount of anticipated precipitation in mm (snow water
equivalent for snow).
*/
router.get('/forecast', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const lat = parseFloat(qs.lat) || 37.62218579135644;
  const lon = parseFloat(qs.lon) || -97.62695789337158;
  const tz = qs.tz || 'America/Chicago';
  const key = process.env.OpenWeatherMapAPIKey;
  const reply = await helpers.getForecast(lat, lon, key, tz);
  res.json(reply);
});

router.get('/mars-weather', async function(req, res, next) {
  const reply = await helpers.getMarsWeather();
  res.json(reply);
});

/* iss

Returns current ISS position, altitude, velocity, and visibility.

Accepts the following parameter(s) (see README for details):
- dt
- tz
*/
router.get('/iss', async function(req, res, next) {
  const qs=helpers.parseQueryString(req.query);
  const tz = qs.tz || 'America/Chicago';
  const timestamp = moment(qs.dt);
  const reply = await helpers.getObjectPosition(25544, timestamp, tz);
  res.json(reply);
});

/* iss-passes

Returns details of future visible ISS Passes:
- start azimuth
- start azimuth compass point
- start elevation
- start timestamp (UTC & local)
- max azimuth
- max azimuth compass point
- max elevation
- max timestamp (UTC & local)
- end azimuth
- end azimuth compass point
- end elevation
- end timestamp (UTC & local)
- magnitude
- duration (in seconds)

Accepts the following parameter(s) (see README for details):
- lat
- lon
- tz
*/
router.get('/iss-passes', async function(req, res, next) {
  const qs=helpers.parseQueryString(req.query);
  const lat = parseFloat(qs.lat) || 37.62218579135644;
  const lon = parseFloat(qs.lon) || -97.62695789337158;
  const elev = await helpers.getElevation(lat,
      lon,
      process.env.GooglePlacesAPIKey);
  const tz = qs.tz || 'America/Chicago';
  const key = process.env.N2YOAPIKey;
  const reply = await helpers.getObjectNextPass(25544, lat, lon, elev, tz, key);
  res.json(reply);
});

/* neo

Returns a JSON object of near earth objects for the next seven days, sorted
by the distance from Earth of each object on each of those days.
*/
router.get('/neo', async function(req, res, next) {
  const qs = helpers.parseQueryString(req.query);
  const tz = qs.tz || 'America/Chicago';
  const key = process.env.NASAAPIKey;
  startDate = moment();
  endDate = startDate.clone().add(6, 'days').format('YYYY-MM-DD');
  startDate = startDate.format('YYYY-MM-DD');
  const reply = await helpers.getNEOList(startDate, endDate, tz, key);
  res.json(reply);
});

module.exports = router;
