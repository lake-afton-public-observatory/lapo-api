const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const server = supertest(BaseUrl);

// Set additional test location as Chongquing, China
const lat = 29.55834;
const lon = 106.56667;
// Set additional test info
const tz = 'Asia/Chongqing';

describe('Moon', function() {
  this.timeout(0);
  it('should return times of specific altitudes of the moon', function(done) {
    server
        .get('/moon')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys('moonrise',
                  'phase',
                  'moonset',
                  'illumination');
          done();
        });
  });
  it('should return times of specific altitudes of the moon'
    + ' from a specified location', function(done) {
    server
        .get(`/moon/?lat=${lat}&lon=${lon}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys('moonrise',
                  'phase',
                  'moonset',
                  'illumination');
          done();
        });
  });
  it('should return times of specific altitudes of the moon'
    + ' from a specified location with a given timezone', function(done) {
    server
        .get(`/moon?lat=${lat}&lon=${lon}&tz=${tz}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys(
                  'moonrise',
                  'phase',
                  'moonset',
                  'illumination');
          done();
        });
  });
});
