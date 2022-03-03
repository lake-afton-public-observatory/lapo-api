const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const server = supertest(BaseUrl);

// Set additional test location as Chongquing, China
const lat = 29.55834;
const lon = 106.56667;
// Set additional test info
const tz = 'Asia/Chongqing';
// let endtime = '2019-01-01T14:00:00-0600';

describe('Sun', function() {
  this.timeout(0);
  it('should return times of specific altitudes of the sun', function(done) {
    server
        .get('/sun')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.times.should.be.an('object')
              .that.has.all.keys('nadir',
                  'night_end',
                  'astro_twilight_end',
                  'sunrise',
                  'solar_noon',
                  'sunset',
                  'astro_twilight_start',
                  'night_start');
          done();
        });
  });
  it('should return times of specific altitudes of the sun'
    + ' from a specified location', function(done) {
    server
        .get(`/sun/?lat=${lat}&lon=${lon}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.times.should.be.an('object')
              .that.has.all.keys('nadir',
                  'night_end',
                  'astro_twilight_end',
                  'sunrise',
                  'solar_noon',
                  'sunset',
                  'astro_twilight_start',
                  'night_start');
          done();
        });
  });
  it('should return times of specific altitudes of the sun'
    + ' from a specified location with a given timezone', function(done) {
    server
        .get(`/sun?lat=${lat}&lon=${lon}&tz=${tz}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.times.should.be.an('object')
              .that.has.all.keys('nadir',
                  'night_end',
                  'astro_twilight_end',
                  'sunrise',
                  'solar_noon',
                  'sunset',
                  'astro_twilight_start',
                  'night_start');
          done();
        });
  });
});
