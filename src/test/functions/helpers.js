require('dotenv').config();
const helpers = require('../../lib/helpers');
const chai = require('chai');
const chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);
chai.should();

describe('Helper Functions', function() {
  describe('api calls', function() {
    this.timeout(0);
    describe('Google Places Elevation', function() {
      const key = process.env.GooglePlacesAPIKey;
      it('Test 1', function(done) {
        helpers.getElevation(37.62218579135644, -97.62695789337158, key)
            .should.eventually.equal(421.9319458007812).notify(done);
      });
      it('Test 2', function(done) {
        helpers.getElevation(29.55834, 106.56667, key)
            .should.eventually.equal(287.4886169433594).notify(done);
      });
    });
    describe('OpenWeatherMap API', function() {
      it('should return current weather conditions from OpenWeather API',
          function(done) {
            const key = process.env.OpenWeatherMapAPIKey;
            helpers.getWeather(37.62218579135644, -97.62695789337158, key)
                .should.eventually.be.an('object')
                .that.includes.all.keys('coord',
                    'weather',
                    'base',
                    'main',
                    'visibility',
                    'wind',
                    'clouds',
                    'dt',
                    'id',
                    'name').notify(done);
          });
      it('should return forecast from OpenWeather API', function(done) {
        const key = process.env.OpenWeatherMapAPIKey;
        helpers.getForecast(37.62218579135644, -97.62695789337158, key)
            .should.eventually.be.an('object')
            .that.includes.all.keys('city', 'cnt', 'list').notify(done);
      });
    });
  });
  describe('unit conversion', function() {
    it('should convert degrees Celsius to degrees Fahrenheit', function(done) {
      helpers.celsiusToFahrenheit(-40).should.equal(-40);
      helpers.celsiusToFahrenheit(0).should.equal(32);
      helpers.celsiusToFahrenheit(100).should.equal(212);
      done();
    });
    it('should convert degrees Fahrenheit to degrees Celsius', function(done) {
      helpers.fahrenheitToCelsius(-40).should.equal(-40);
      helpers.fahrenheitToCelsius(32).should.equal(0);
      helpers.fahrenheitToCelsius(212).should.equal(100);
      done();
    });
    it('should convert meters per second to miles per hour', function(done) {
      helpers.mpsToMPH(0).should.equal(0);
      helpers.mpsToMPH(13.4112).should.equal(30);
      helpers.mpsToMPH(33.528).should.equal(75);
      done();
    });
    it('should convert meters to miles', function(done) {
      helpers.metersToMiles(16093.44).should.equal(10);
      helpers.metersToMiles(10000).should.be.within(6.21, 6.22);
      helpers.metersToMiles(42195).should.be.within(26.21, 26.22);
      done();
    });
  });
  describe('other methods', function() {
    it('should round a number to a specified number of decimal places',
        function(done) {
          helpers.roundOff(3.14159, 2).should.equal(3.14);
          helpers.roundOff(123.456789, 3).should.equal(123.457);
          done();
        });
    it('should calculate wind chill properly', function(done) {
      // using within in case of mathematical weirdness and/or rounding issues
      helpers.getFeelsLikeTemp(5, 3, 0).should.be.within(2.50, 2.51);
      helpers.getFeelsLikeTemp(0, 10, 0).should.be.within(-7.04, -7.03);
      helpers.getFeelsLikeTemp(10, 10, 0).should.be.within(6.21, 6.22);
      // temperature too high, should return input
      helpers.getFeelsLikeTemp(11, 10, 0).should.be.within(10.99, 11.01);
      done();
    });
    it('should calculate heat index properly', function(done) {
      // using within in case of mathematical weirdness and/or rounding issues
      helpers.getFeelsLikeTemp(27, 0, 15).should.be.within(26.98, 27.99);
      helpers.getFeelsLikeTemp(30, 0, 50).should.be.within(31.04, 31.05);
      helpers.getFeelsLikeTemp(40, 0, 40).should.be.within(48.26, 48.27);
      // absurd relative humidity, should return original value
      helpers.getFeelsLikeTemp(50, 0, 75).should.be.within(49.99, 50.01);
      // temperature too low, should return original value
      helpers.getFeelsLikeTemp(25, 0, 90).should.be.within(24.99, 25.01);
      done();
    });
  });
});
