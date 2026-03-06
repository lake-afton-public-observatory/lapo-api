[![Build Status](https://travis-ci.org/nessalc/lake-afton-api.svg?branch=master)](https://travis-ci.org/nessalc/lake-afton-api)

# Lake Afton API
An endpoint for getting data about Lake Afton Public Observatory
https://api.lakeafton.com

## Contribute

You'll need node.js and Python 3.

1. Make a fork
2. Clone to your machine
3. CD into the folder
4. Run ```./setup.sh``` — this will copy `.env_example` to `.env`, run `npm install`, and install Python dependencies into a `.venv` virtual environment
5. Fill out the `.env` file with your API keys
6. Run ```npm start``` or ```nodemon start``` if you have nodemon installed
7. Visit ```http://localhost:3000``` (or whatever `PORT` is set to in your `.env`)
8. Write code
9. Upload to your fork
10. Submit a pull request

If you have other any questions, you can reach out at sduncan@lakeafton.com

## Endpoints

* Current online documentation: [apidocs.lakeafton.com](http://apidocs.lakeafton.com)

***Note:*** the data provided at these endpoints is probably more than enough to get a hobbyist started, to at least get an object of interest in a finder scope. And while these numbers are at least mostly accurate, don't try to steer Hubble or launch a rocket to Neptune with them.
