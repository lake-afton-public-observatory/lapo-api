const fetch = require('node-fetch');
const pMemoize = require('p-memoize');

const BaseUrl = 'http://astropical.space/';

const fetchPlanetEphem = async function(lat, lon) {
  const url = BaseUrl + 'api-ephem.php?lat=' + lat + '&lon=' + lon;
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const fetchEquatorialChart = async function(width, height, ra, dec, fov) {
  const url = BaseUrl + 'starchart.php?width=' + width + '&height=' + height
    + '&rc=' + ra + '&dc=' + dec + '&fov=' + fov;
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const fetchPlanisphere = async function(lat, lon, diameter, deepsky) {
  let url = BaseUrl + 'starchart.php?planis=1&lat=' + lat + '&lon=' + lon
    + '&width=' + diameter;
  if (deepsky) {
    url = url + 'mes=1&cld=1&ngc=1';
  }
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const fetchStarByConstellation = async function(constellation) {
  const url = BaseUrl + 'api.php?table=stars&which=constellation&limit='
    + constellation + '&format=json';
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const fetchStarByCommonName = async function(commonName) {
  const url = BaseUrl + 'api.php?table=stars&which=name' + '&limit='
    + commonName + '&format=json';
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const fetchStarByCatalog = async function(catalog, number) {
  const url = BaseUrl + 'api.php?table=stars&which=' + catalog
    + '&limit=' + number + '&format=json';
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const getPlanetEphem = pMemoize(fetchPlanetEphem);
const getEquatorialChart = pMemoize(fetchEquatorialChart);
const getPlanisphere = pMemoize(fetchPlanisphere);
const getStarByCatalog = pMemoize(fetchStarByCatalog);
const getStarByCommonName = pMemoize(fetchStarByCommonName);
const getStarByConstellation = pMemoize(fetchStarByConstellation);

module.exports = {
  getPlanetEphem,
  getEquatorialChart,
  getPlanisphere,
  getStarByConstellation,
  getStarByCommonName,
  getStarByCatalog,
};
