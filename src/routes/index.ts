import 'dotenv/config';
import express from 'express';
import { verifyEnvironment } from './lib/tools';
import path from 'path';
const app = express();
const port = process.env.PORT;

verifyEnvironment();

app.listen(port, () => {
    console.log(`API started on port ${port}...`);
});

app.get('/', (req, res) => {
    const response = {
        message:
            'Welcome to the Lake Afton Public Observatory API! To contribute, visit https://github.com/lake-afton-public-observatory/lapo-api',
    };
    res.json(response);
});
