// Tools related to the infrastructure of this API

export const verifyEnvironment = (): void => {
    if (!process.env.PORT) {
        throw new Error('Missing PORT in .env');
    }
};
