export const verifyEnvironment = (): void => {
    if (!process.env.PORT) {
        throw new Error('omg noooo');
    }
};
