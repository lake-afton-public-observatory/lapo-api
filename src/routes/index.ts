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
    res.json({ abc: '123' });
});
