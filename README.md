[![Build Status](https://travis-ci.org/nessalc/lake-afton-api.svg?branch=master)](https://travis-ci.org/nessalc/lake-afton-api)

# Lake Afton API
An endpoint for getting data about Lake Afton Public Observatory
https://api.lakeafton.com

### Contribute

You're gonna need node.js; this was written on v8.11.3. You'll also need Python 3.5+; this was written with v3.7.2.

1. Make a fork
2. Clone to your machine
3. CD into the folder
4. Fill out the .env file (use .env_example as a guideline)
5. run ```npm install```
6. run ```pip install -r requirements.txt```
7. run ```npm start``` or ```nodemon start``` if you have nodemon installed.
8. Write code
9. Upload to your fork
10. Submit a pull request

If you have other any questions, you can reach out at sduncan@lakeafton.com

### Endpoints

* Current online documentation: [apidocs.lakeafton.com]](http://apidocs.lakeafton.com)

* LAPO Specific -- These take no additional parameters, and are specific to use by Lake Afton Public Observatory
    * GET `/` -- returns a basic welcome message
    * GET `/hours` -- returns current hours of operation
    * GET `/events` -- returns summary, description, start/end time and location of events happening in the next 30 days
    * GET `/schedule` -- returns info on the viewing program for the upcoming/current weekend
    * GET `/whatsup_next` -- returns names of objects brighter than magnitude 6 that will be visible the next time LAPO is open.
* Configurable -- These are configurable and accept parameters for use in specific situations and for special events, e.g. star parties and Messier marathons.
    * ***Parameter Notes:***
        * `lat` is latitude in degrees, positive for north, negative for south. DMS format is not accepted--must be in decimal degrees (e.g. 37.6222 rather than 37°37'19.8688")
        * `lon` is longitude in degrees, positive for east, negative for west. DMS format is not accepted--must be in decimal degrees (e.g. -97.6270 rather than -97°37'37.0484")
        * `dt` (`start` and `end`, also) is a timestamp in a very particular format: YYYY-MM-DDThh:mm:ss±hhmm. YYYY is the year; negative values are acceptable but behavior may not be predictable. MM and DD are the month and day, respectively, and must be entered as two digit values. hh is the hour in a 24-hour format, and must be entered with two digits. mm and ss are minutes and seconds, respectively. Decimals may be added to seconds to increase precision, but output will only be to the whole second. ±hhmm specifies the timezone offset of the timestamp. This must be entered with a sign (+ or -) and four digits: the hours and minutes each as two digits. An alternative is the letter Z, denoting UTC. All parameters are required at this time.
        * `tz` is a timezone in the format of the Olson database for the output of the query. Default is 'America/Chicago'. Currently all formats are allowed, but in the future only canonical names and aliases may be accepted (ability to recognize deprecated names will be removed).
        * Parameters are entered as a standard query string, e.g. `/whatsup/?key1=value1&key2=value2`. Order among different keys is unimportant. If a key is dupicated, only the *last* value associated with a key will be utilized. If a value is inappropriate for the type, it will be ignored and the default will be used. The program does its best to decide what you meant, but typos can still cause unexpected issues.
    * GET `/planets` -- returns planets that are visible right now
        * ***credit to [astropical](https://astropical.space/) for this data***
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
    * GET `/planets2` -- returns the following information about *all* planets:
        * current right ascension/declination
        * current size (diameter in arcseconds)
        * current magnitude
        * current earth distance (au, km, mi)
        * current sun distance (au, km, mi)
        * current phase
        * current constellation
        * rise time/rise azimuth
        * transit time/transit altitude
        * set time/set azimuth,
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
            * `dt` (now)
    * GET `/sun` -- returns sunrise, sunset, twilight, and dusk information
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
    * GET `/sun2` -- returns the following information about the sun (based on the current date and time):
        * right ascension/declination
        * size (diameter in arcseconds)
        * magnitude
        * earth distance (au, km, mi)
        * next solstice
        * next equinox
        * constellation
        * rise time/rise azimuth
        * transit time/transit altitude
        * set time/set azimuth,
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
            * `dt` (now)
    * GET `/moon` -- returns moonrise, moonset, and phase of the moon
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
    * GET `/moon2` -- returns the following information about the moon (based on the current date and time):
        * right ascension/declination
        * size (diameter in arcseconds)
        * magnitude
        * earth distance (au, km, mi)
        * sun distance (au, km, mi)
        * phase
        * illuminated surface
        * phase name
        * next new moon
        * next first quarter
        * next full moon
        * next last quarter
        * constellation
        * rise time/rise azimuth
        * transit time/transit altitude
        * set time/set azimuth
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
            * `dt` (now)
    * GET `/whatsup` -- return names of objects brighter than magnitude 6 (see [here](objects.md) for list of objects)
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
            * `start` (now)
            * `end` (now)
    * GET `/weather` -- return weather data for Earth at the given location
        * ***credit to [OpenWeather](https://openweathermap.org/) for this data***
        * datetime of forecast data
        * temp (°C, °F, "feels like")
            * min (°C, °F)
            * max (°C, °F)
        * ground level pressure (mBar/hPa)
        * humidity (%)
        * weather
            * description
            * long description
            * iconurl
        * wind
            * speed (m/s, mph)
            * direction
        * visibility (km, mi)
        * clouds (%)
        * rain (if applicable)
        * snow (if applicable)
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
    * GET `/forecast` -- return weather forecast data for Earth at the given location in 3 hour intervals for the next 5 days
        * datetime of forecast data
        * temp (°C, °F, "feels like")
            * min (°C, °F)
            * max (°C, °F)
        * sea level adjusted pressure (mBar/hPa)
        * ground level pressure (mBar/hPa)
        * humidity (%)
        * weather
            * description
            * long description
            * iconurl
        * wind
            * speed (m/s, mph)
            * direction
        * clouds (%)
        * rain (if applicable)
        * snow (if applicable)
        * Valid parameters (defaults):
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
    * GET `/mars-weather` -- return weather data from the Curiosity rover
        * ***credit to [Apollorion](https://apollorion.com/) for this data***
    * GET `/iss` -- return current position and velocity of the International Space Station
        * ***credit to [Where the ISS At?](https://wheretheiss.at/) for this data***
        * Valid parameters (defaults):
            * `tz` (America/Chicago)
            * `dt` (now)
    * GET `/iss-passes` -- return details of future visible ISS Passes:
        * ***credit to [N2YO](https://www.n2yo.com/) for this data***
        * start azimuth
        * start azimuth compass point
        * start elevation
        * start timestamp (UTC & local)
        * max azimuth
        * max azimuth compass point
        * max elevation
        * max timestamp (UTC & local)
        * end azimuth
        * end azimuth compass point
        * end elevation
        * end timestamp (UTC & local)
        * magnitude
        * duration (in seconds)
        * Valid parameters (defaults)
            * `lat` (37.62218579135644)
            * `lon` (-97.62695789337158)
            * `tz` (America/Chicago)
    * GET `/neo` -- return information on near-earth objects over the next seven days
        * ***credit to [NASA](https://www.nasa.gov) for this data***
        * ID
        * NEO reference ID
        * name
        * NASA JPL URL
        * absolute magnitude (H)
        * estimated diameter (km, m, mi, ft)
            * min
            * max
        * close approach data
            * date
            * datetime (local)
            * relative velocity (kps, kph, mph)
            * miss distance (au, ld, km, mi)
            * orbiting body
        * Valid parameters (defaults):
            * `tz` (America/Chicago)

***One more note:*** the data provided at these endpoints is probably more than enough to get a hobbyist started, to at least get an object of interest in a finder scope. And while these numbers are at least mostly accurate, don't try to steer Hubble or launch a rocket to Neptune with them.
