const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const moment = require('moment-timezone');
const server = supertest(BaseUrl);

// Set additional test location as Chongquing, China
const lat = 29.55834;
const lon = 106.56667;
// Set additional test info
const tz = 'Asia/Chongqing';
const datetime = '2019-01-01T12:00:00-0600';

describe('Sun 2', function() {
  this.timeout(0);
  it('should return specific attributes of the sun', function(done) {
    server
        .get('/sun2')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys('query_date', 'Sun');
          res.body.Sun.should.be.an('object')
              .that.has.all.keys('name',
                  'alt',
                  'az',
                  'ra',
                  'dec',
                  'size',
                  'mag',
                  'elong',
                  'earth_dist',
                  'constellation',
                  'next_solstice',
                  'next_equinox',
                  'rise_time',
                  'rise_az',
                  'transit_time',
                  'transit_alt',
                  'set_time',
                  'set_az',
                  'astronomical_dawn',
                  'nautical_dawn',
                  'civil_dawn',
                  'USNO_sunrise',
                  'USNO_sunset',
                  'civil_dusk',
                  'nautical_dusk',
                  'astronomical_dusk');
          done();
        });
  });
  it('should return specific attributes of the sun'
    + ' from a specified location', function(done) {
    server
        .get(`/sun2/?lat=${lat}&lon=${lon}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys('query_date', 'Sun');
          res.body.Sun.should.be.an('object')
              .that.has.all.keys('name',
                  'alt',
                  'az',
                  'ra',
                  'dec',
                  'size',
                  'mag',
                  'elong',
                  'earth_dist',
                  'constellation',
                  'next_solstice',
                  'next_equinox',
                  'rise_time',
                  'rise_az',
                  'transit_time',
                  'transit_alt',
                  'set_time',
                  'set_az',
                  'astronomical_dawn',
                  'nautical_dawn',
                  'civil_dawn',
                  'USNO_sunrise',
                  'USNO_sunset',
                  'civil_dusk',
                  'nautical_dusk',
                  'astronomical_dusk');
          done();
        });
  });
  it('should return specific attributes of the sun'
    + ' from a specified location with a given timezone', function(done) {
    server
        .get(`/sun2?lat=${lat}&lon=${lon}&tz=${tz}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          let pytzformat = moment().tz(tz).format();
          pytzformat = pytzformat.slice(-6, -3) + pytzformat.slice(-2);
          // skip equinox and solstice--DST may interfere
          res.body.query_date.slice(-5).should.equal(pytzformat);
          res.body.Sun.rise_time.slice(-5).should.equal(pytzformat);
          res.body.Sun.transit_time.slice(-5).should.equal(pytzformat);
          res.body.Sun.set_time.slice(-5).should.equal(pytzformat);
          res.body.Sun.astronomical_dawn.slice(-5).should.equal(pytzformat);
          res.body.Sun.nautical_dawn.slice(-5).should.equal(pytzformat);
          res.body.Sun.civil_dawn.slice(-5).should.equal(pytzformat);
          res.body.Sun.USNO_sunrise.slice(-5).should.equal(pytzformat);
          res.body.Sun.USNO_sunset.slice(-5).should.equal(pytzformat);
          res.body.Sun.civil_dusk.slice(-5).should.equal(pytzformat);
          res.body.Sun.nautical_dusk.slice(-5).should.equal(pytzformat);
          res.body.Sun.astronomical_dusk.slice(-5).should.equal(pytzformat);
          done();
        });
  });
  it('should return specific attributes of the sun'
    + ' from a specified location from a particular timestamp', function(done) {
    server
        .get(`/sun2/?lat=${lat}&lon=${lon}&dt=${datetime}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          // TODO: figure out an appropriate range of values to verify accuracy
          done();
        });
  });
  it('should return specific attributes of the sun'
    + ' from a specified location from a particular timestamp'
    + ' with a given timezone', function(done) {
    this.timeout(10000);
    server
        .get(`/sun2?lat=${lat}&lon=${lon}&dt=${datetime}&tz=${tz}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.Sun.next_solstice.should.equal('2019-06-21T23:54:21+0800');
          res.body.Sun.next_equinox.should.equal('2019-03-21T05:58:31+0800');
          done();
        });
  });
});
