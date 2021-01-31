const fetch = require('node-fetch');
const pMemoize = require('p-memoize');
const moment = require('moment-timezone');
const {
  PythonShell,
} = require('python-shell');
const myPythonScriptPath = './lib/whatsup.py';

const fetchElevation = function(lat, lon, key) {
  const GoogleUrl = 'https://maps.googleapis.com/maps/api/elevation/json?locations=' + lat + ',' + lon + '&key=' + key;
  return fetch(GoogleUrl).then(function(response) {
    return response.json();
  }).catch((err)=>{
    console.error('Error in Elevation API: ' + err.message);
  }).then(function(json) {
    const elev = json.results[0].elevation;
    return elev;
  }).catch((err)=>{
    console.error('Error processing return from Elevation API: ' + err.message);
    return 0;
  });
};

const weather = function(lat, lon, key, tz) {
  const url = 'http://api.openweathermap.org/data/2.5/weather?lat=' + lat + '&lon=' + lon + '&units=metric&APPID=' + key;
  return fetch(url).then(function(response) {
    return response.json();
  }).catch((err)=>{
    console.error('Error in Weather API: '+err.message);
  }).then(function(data) {
    // The wind chill and heat index formulae (from NOAA/NWS) are based on
    // temperature in degrees Fahrenheit and wind speed in miles per hour.
    const temp = data.main.temp;
    const windSpeed = data.wind.speed;
    const feelsLike = getFeelsLikeTemp(temp,
        windSpeed,
        data.main.humidity);
    data.main.temp = {
      celsius: temp,
      fahrenheit: roundOff(celsiusToFahrenheit(temp), 2),
    };
    if (feelsLike !== temp) {
      data.main.temp.feels_like = {
        celsius: roundOff(feelsLike, 2),
        fahrenheit: roundOff(celsiusToFahrenheit(feelsLike), 2),
      };
    }
    // if these are the same, it's not worth displaying them
    if (data.main.temp_min === data.main.temp_max) {
      delete data.main.temp_min;
      delete data.main.temp_max;
    } else { // otherwise move them to where it makes more sense
      data.main.temp.min = {
        celsius: data.main.temp_min,
        fahrenheit: roundOff(celsiusToFahrenheit(data.main.temp_min), 2),
      };
      data.main.temp.max = {
        celsius: data.main.temp_max,
        fahrenheit: roundOff(celsiusToFahrenheit(data.main.temp_max), 2),
      };
      delete data.main.temp_min;
      delete data.main.temp_max;
    }
    // move temperature object
    data.temperature = data.main.temp;
    data.wind.speed = {
      metersPerSecond: windSpeed,
      milesPerHour: roundOff(mpsToMPH(windSpeed), 2),
    };
    // move other info:
    data.groundLevelPressure=data.main.pressure;
    data.humidity=data.main.humidity;
    data.clouds=data.clouds.all;
    // delete rest of "main" object
    delete data.main;
    // rename wind direction parameter
    data.wind.direction = data.wind.deg;
    delete data.wind.deg;
    const weathers = data.weather;
    // yes, apparently there can be more than one "weather"
    weathers.forEach(function(weather) {
      const iconurl = 'http://openweathermap.org/img/w/' + weather.icon + '.png';
      weather.iconurl = iconurl;
      // this swaps two variables, except I renamed one here
      weather.longDescription = [weather.description,
        weather.description = weather.main][0];
      delete weather.main;
      delete weather.id;
      delete weather.icon;
    });
    if (data.hasOwnProperty('visibility')) {
      const vis = data.visibility;
      data.visibility = {
        km: roundOff(vis / 1000, 2),
        mi: roundOff(metersToMiles(vis), 2),
      };
    }
    // reformat date
    try {
      data.dt = moment(data.dt * 1000).tz(tz).format();
    } catch (e) {
      data.dt = moment(data.dt * 1000, tz).format();
    }
    // remove internal parameters
    delete data.sys;
    delete data.cod;
    delete data.timezone;
    delete data.id;
    delete data.name;
    delete data.base;
    delete data.coord;
    return data;
  }).catch((err)=>{
    console.error('Error processing data from Weather API: '+err.message);
  });
};

const forecast = function(lat, lon, key, tz) {
  const url = 'http://api.openweathermap.org/data/2.5/forecast?lat=' + lat + '&lon=' + lon + '&units=metric&APPID=' + key;
  return fetch(url).then(function(response) {
    return response.json();
  }).then(function(data) {
    if (data.hasOwnProperty('list')) {
      const forecasts = data.list;
      forecasts.forEach(function(forecast) {
        // The wind chill and heat index formulae (from NOAA/NWS) are based on
        // temperature in degrees Fahrenheit and wind speed in miles per hour.
        const temp = forecast.main.temp;
        const windSpeed = forecast.wind.speed;
        const feelsLike = getFeelsLikeTemp(temp,
            windSpeed,
            forecast.main.humidity);
        forecast.main.temp = {
          celsius: temp,
          fahrenheit: roundOff(celsiusToFahrenheit(temp), 2),
        };
        if (feelsLike !== temp) {
          forecast.main.temp.feelsLike = {
            celsius: roundOff(feelsLike, 2),
            fahrenheit: roundOff(celsiusToFahrenheit(feelsLike), 2),
          };
        }
        // if these are the same, it's not worth displaying them
        if (forecast.main.temp_min === forecast.main.temp_max) {
          delete forecast.main.temp_min;
          delete forecast.main.temp_max;
        } else { // otherwise move them to where it makes more sense
          forecast.main.temp.min = {
            celsius: forecast.main.temp_min,
            fahrenheit: roundOff(
                celsiusToFahrenheit(forecast.main.temp_min), 2),
          };
          forecast.main.temp.max = {
            celsius: forecast.main.temp_max,
            fahrenheit: roundOff(
                celsiusToFahrenheit(forecast.main.temp_max), 2),
          };
          delete forecast.main.temp_min;
          delete forecast.main.temp_max;
        }
        // move temperature object
        forecast.temperature = forecast.main.temp;
        forecast.wind.speed = {
          metersPerSecond: windSpeed,
          milesPerHour: roundOff(mpsToMPH(windSpeed), 2),
        };
        // move other info:
        forecast.seaLevelPressure=forecast.main.sea_level;
        forecast.groundLevelPressure=forecast.main.grnd_level;
        forecast.humidity=forecast.main.humidity;
        forecast.clouds=forecast.clouds.all;
        // delete rest of "main" object
        delete forecast.main;
        // rename wind direction parameter
        forecast.wind.direction = forecast.wind.deg;
        delete forecast.wind.deg;
        try {
          forecast.dt = moment(forecast.dt * 1000).tz(tz).format();
        } catch (e) {
          forecast.dt = moment(forecast.dt * 1000, tz).format();
        }
        const weathers = forecast.weather;
        // yes, apparently there can be more than one "weather"
        weathers.forEach(function(weather) {
          const iconurl = 'http://openweathermap.org/img/w/' + weather.icon + '.png';
          weather.iconurl = iconurl;
          // this swaps two variables, except I renamed one here
          weather.longDescription = [weather.description,
            weather.description = weather.main][0];
          delete weather.main;
          delete weather.id;
          delete weather.icon;
        });
        // remove internal parameters
        delete forecast.sys;
        delete forecast.dt_txt;
      });
    }
    delete data.cod;
    delete data.message;
    return data;
  });
};

const getMarsWeather = function() {
  const url = 'https://api.maas2.apollorion.com/';
  return fetch(url).then(function(response) {
    return response.json().then(function(jsonResponse) {
      return jsonResponse;
    });
  });
};

const whatsup = function(data) {
  return new Promise(function(resolve, reject) {
    const pyshell = new PythonShell(myPythonScriptPath);
    let result;
    pyshell.send(JSON.stringify(data));
    pyshell.on('message', function(message) {
      result = JSON.parse(message);
      return result;
    });
    pyshell.end(function(err, code, signal) {
      if (err) reject(err);
      resolve(result);
    });
  });
};

const getNEOList = function(startDate, endDate, tz, key) {
  const url =
    'https://api.nasa.gov/neo/rest/v1/feed?start_date=' +
    startDate +
    '&end_date=' +
    endDate +
    '&api_key=' +
    key;
  return fetch(url).then(function(response) {
    if (response.ok) {
      return response.json();
    }
    const error =
      {
        'code': response.status,
        'message': response.statusText,
      };
    throw error;
  }).then(function(data) {
    if (data.hasOwnProperty('error')) {
      throw data.error;
    }
    delete data.links;
    for (const [, value] of Object.entries(data.near_earth_objects)) {
      value.forEach(function(neo) {
        delete neo.links;
        delete neo.is_potentially_hazardous_asteroid;
        delete neo.is_sentry_object;
        neo.close_approach_data[0].close_approach_date_full =
        moment(neo.close_approach_data[0].epoch_date_close_approach)
            .tz(tz).format();
        delete neo.close_approach_data[0].epoch_date_close_approach;
      });
    }
    return data;
  }).catch(function(error) {
    console.error(error.code, error.message);
  });
};

const getObjectPosition = function(objectId, timestamp, tz) {
  const url = 'https://api.wheretheiss.at/v1/satellites/'
  + objectId
  + '?timestamp='
  + timestamp.format('X');
  return fetch(url).then(function(response) {
    if (response.ok) {
      return response.json();
    }
    error = {
      'code': response.status,
      'message': response.statusText,
    };
    throw error;
  }).then(function(data) {
    data.timestamp=moment(data.timestamp*1000).tz(tz).format();
    data.altitude = {
      'km': data.altitude,
      'mi': data.altitude / 1.609344,
    };
    data.velocity = {
      'kph': data.velocity,
      'mph': data.velocity / 1.609344,
      'm/s': data.velocity / 3.6,
      'ft/s': data.velocity / 1.09728,
    };
    delete data.units;
    delete data.footprint;
    delete data.daynum;
    delete data.solar_lat;
    delete data.solar_lon;
    return data;
  }).catch(function(error) {
    console.error(error.code, error.message);
  });
};

const getObjectNextPass = function(objectID, lat, lon, elev, tz, key) {
  objectID = objectID || 25544; // default to ISS
  const days = 2; // days of visibility for prediciton, 10 is max
  const visibility = 10; // minimum number of seconds satellite should be
  // considered optically visibile during the pass
  // to be returned as a result.
  const url =
    'https://api.n2yo.com/rest/v1/satellite/visualpasses/' +
    objectID +
    '/' +
    lat +
    '/' +
    lon +
    '/' +
    elev +
    '/' +
    days +
    '/' +
    visibility +
    '/&apiKey=' +
    key;
  return fetch(url)
      .then(function(response) {
        if (response.ok) {
          return response.json();
        }
        error = {
          'code': response.status,
          'message': response.statusText,
        };
        throw error;
      })
      .then(function(data) {
        console.log('data', data)
        const passes = data.passes;
        passes.forEach(function(pass) {
          pass.startUTC = moment(pass.startUTC * 1000).utc();
          pass.startLocal = pass.startUTC.tz(tz).format();
          pass.maxUTC = moment(pass.maxUTC * 1000).utc();
          pass.maxLocal = pass.maxUTC.tz(tz).format();
          pass.endUTC = moment(pass.endUTC * 1000).utc();
          pass.endLocal = pass.endUTC.tz(tz).format();
        });
        return data;
      }).catch(function(error) {
        console.error(error.code, error.message);
      });
};

const parseQueryString = function(querystring) {
  for (const key in querystring) {
    if (querystring.hasOwnProperty(key)) {
      qval = querystring[key];
      if (Array.isArray(qval)) {
        qval = qval[qval.length - 1];
      } else {
        qval = qval;
      }
      switch (key) {
        case 'lat':
          qval = parseFloat(qval);
          if (qval > 90 || qval < -90) {
            qval = null;
          }
          break;
        case 'lon':
          qval = parseFloat(qval);
          if (qval > 180 || qval < -180) {
            qval = null;
          }
          break;
        case 'dt':
        case 'start':
        case 'end':
          qval = moment(qval);
          if (qval.isValid()) {
            qval = qval.format();
          } else {
            qval = null;
          }
          break;
        case 'tz':
          try {
            qval = qval.toString();
          } catch (e) {
            qval = null;
          }
          qval = moment.tz.zone(qval);
          if (qval) {
            qval = qval.name;
          }
          break;
        default:
      }
      if (qval) {
        querystring[key] = qval;
      } else {
        delete querystring[key];
      }
    }
  }
  return querystring;
};

const celsiusToFahrenheit = function(celsius) {
  return celsius * 9 / 5 + 32;
};
const fahrenheitToCelsius = function(fahrenheit) {
  return (fahrenheit - 32) * 5 / 9;
};
const mpsToMPH = function(metersPerSecond) {
  return metersPerSecond / 0.44704;
};
const getFeelsLikeTemp = function(tempCelsius,
    windMetersPerSecond,
    relativeHumidity) {
  // these calculations are based on a temperature in degrees Fahrenheit
  const T = celsiusToFahrenheit(tempCelsius);
  // these calculations are based on a wind speed in miles per hour
  const W = mpsToMPH(windMetersPerSecond);
  const RH = relativeHumidity;
  if (T <= 50 && W >= 3) { // calculate wind chill
    const windChillF = 35.74 + (0.6215 * T) - (35.75 * W ** 0.16)
      + (0.4275 * T * W ** 0.16);
    return fahrenheitToCelsius(windChillF);
  } else if (T > 80 && ((245 - (T * 5 / 3)) >= RH)) {
    // calculate heat index--this one's complicated
    // if relative humidity is more than 245-T*5/3, results of the formula
    // will be absurd, so I don't calculate, but it's best to stay indoors, too!
    let HI = 0.5 * (T + 61 + ((T - 68) * 1.2) + RH * 0.094);
    if ((HI + T) / 2 >= 80) {
      HI = -42.379 + 2.04901523 * T + 10.14333127 * RH
        - 0.22475541 * T * RH - 0.00683783 * T * T
        - 0.05481717 * RH * RH + 0.00122874 * T * T * RH
        + 0.00085282 * T * RH * RH - 0.00000199 * T * T * RH * RH;
      let ADJ = 0;
      if (RH < 13 && T >= 80 && T <= 112) {
        ADJ = -(((13 - RH) / 4) * Math.sqrt((17 - Math.abs(T - 95)) / 17));
      } else if (RH > 85 && T >= 80 && T <= 87) {
        ADJ = ((RH - 85) / 10) * ((87 - T) / 5);
      }
      HI = HI + ADJ;
      return fahrenheitToCelsius(HI);
    }
  }
  return fahrenheitToCelsius(T);
};
const roundOff = function(number, digits) {
  if (typeof(digits) === 'undefined') digits = 0;
  return Math.round(number * 10 ** digits) / 10 ** digits;
};
const metersToMiles = function(kilometers) {
  return kilometers / 1609.344;
};

const getElevation = pMemoize(fetchElevation);
const pythonCall = pMemoize(whatsup, {
  maxAge: 300000,
});
const getWeather = pMemoize(weather, {
  maxAge: 60000,
});
const getForecast = pMemoize(forecast, {
  maxAge: 300000,
});

module.exports = {
  getElevation,
  getWeather,
  getForecast,
  getFeelsLikeTemp,
  celsiusToFahrenheit,
  fahrenheitToCelsius,
  roundOff,
  mpsToMPH,
  metersToMiles,
  pythonCall,
  parseQueryString,
  getMarsWeather,
  getObjectPosition,
  getObjectNextPass,
  getNEOList,
};
