const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const server = supertest(BaseUrl);

describe('Weather', function() {
  this.timeout(0);
  it('should return weather object', function(done) {
    server
        .get('/weather')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.includes.all.keys('coord',
                  'weather',
                  'base',
                  'main',
                  'visibility',
                  'wind',
                  'clouds',
                  'dt',
                  'id',
                  'name');
          done();
        });
  });
});
