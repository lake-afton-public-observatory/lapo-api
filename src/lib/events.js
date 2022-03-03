const fetch = require('node-fetch');

const getEvents = async function(calendarId, key, ttl) {
  const now = new Date();
  const thirtyDaysLater = new Date().setDate(now.getDate() + 30);
  // convert dates to ISO strings for Google API
  const timeMin = now.toISOString();
  const timeMax = new Date(thirtyDaysLater).toISOString();
  const orderBy = 'startTime';
  const url = 'https://www.googleapis.com/calendar/v3/calendars/' + calendarId + '/events?key=' + key + '&timeMin=' + timeMin + '&timeMax=' + timeMax + '&singleEvents=true&orderBy=' + orderBy;
  fetch(url).then(function(response) {
    if (response.ok) {
      reply=response.json();
      if (reply.hasOwnProperty('error')) {
        if (reply.error.hasOwnProperty('errors')) {
          reply.error.errors.forEach(function(error) {
            console.error(error.domain,
                error.reason,
                error.message,
                error.extendedHelp);
          });
        }
        throw reply;
      }
      return response.json();
    }
    const error =
      {
        'code': response.status,
        'message': response.statusText,
      };
    throw error;
  }).catch(function(error) {
    console.error(error.code, error.message);
  });
};

module.exports = getEvents;
