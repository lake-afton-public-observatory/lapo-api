const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const server = supertest(BaseUrl);

// Set additional test location as Chongquing, China
const lat = 29.55834;
const lon = 106.56667;

const planetsRegEx = /Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto/;

describe('Planets', function() {
  it('should return planets array at a default location', function(done) {
    server
        .get('/planets')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          if (res.body) {
            res.body.should.be.an('array');
            res.body.forEach((element) => {
              element.name.should.match(planetsRegEx);
            });
          }
          done();
        });
  });
  it('should return planets array at a specified location', function(done) {
    server
        .get(`/planets?lat=${lat}&lon=${lon}`)
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          if (res.body) {
            res.body.should.be.an('array');
            res.body.forEach((element) => {
              element.name.should.match(planetsRegEx);
            });
          }
          done();
        });
  });
});
