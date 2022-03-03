const supertest = require('supertest');
const BaseUrl = 'http://localhost:3000';
const server = supertest(BaseUrl);

describe('What\'s Up', function() {
  this.timeout(0);
  it('should return whatsup object', function(done) {
    server
        .get('/whatsup')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(function(err, res) {
          if (err) return done(err);
          res.body.should.be.an('object')
              .that.has.all.keys('start_time',
                  'end_time',
                  'objects');
          done();
        });
  });
});
