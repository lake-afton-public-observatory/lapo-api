import 'dotenv/config';
import express, { Request, Response } from 'express';
import { verifyEnvironment } from './lib/tools';
import { getHours } from './lib/hours';
const app = express();
const port = process.env.PORT;

verifyEnvironment();

app.listen(port, () => {
    console.log(`API started on port ${port}...`);
});

app.get('/', (req: Request, res: Response) => {
    const responseJson = {
        message:
            'Welcome to the Lake Afton Public Observatory API! To contribute, visit https://github.com/lake-afton-public-observatory/lapo-api',
    };
    res.json(responseJson);
});

app.get('/hours', (req: Request, res: Response) => {
    res.json(getHours());
});
