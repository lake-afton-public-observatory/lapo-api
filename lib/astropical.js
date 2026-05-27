const fetch = require('node-fetch');
const pMemoize = require('p-memoize');

const BaseUrl = 'http://astropical.space/';

const fetchPlanetEphem = async function(lat, lon) {
  const url = BaseUrl + 'api-ephem.php?lat=' + lat + '&lon=' + lon;
  return fetch(url).then(function(response) {
    return response.json();
  });
};

const getPlanetEphem = pMemoize(fetchPlanetEphem);

module.exports = {
  getPlanetEphem,
};
