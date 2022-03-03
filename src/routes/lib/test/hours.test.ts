import 'dotenv/config';
import { getHours, Hours } from '../hours';

describe('hours', () => {
    beforeAll(() => {
        // set the date to Jan 1, 2022 for testing
        jest.useFakeTimers('modern');
        jest.setSystemTime(new Date(2022, 0, 1));
    });

    it('returns a properly typed hours object', () => {
        const hoursResponse: Hours = getHours();
        console.log(
            '-------------- WOOKIEE -------------- hoursResponse -->',
            hoursResponse
        );
        expect(hoursResponse).toBeDefined();
    });

    it('returns the expected hours for January', () => {
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('7:30pm');
        expect(hoursResponse.hours.close).toBe('9:30pm');
    });

    it('returns the expected hours for February', () => {
        jest.setSystemTime(new Date(2022, 1, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('7:30pm');
        expect(hoursResponse.hours.close).toBe('9:30pm');
    });

    it('returns the expected hours for March', () => {
        jest.setSystemTime(new Date(2022, 2, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('8:30pm');
        expect(hoursResponse.hours.close).toBe('10:30pm');
    });

    it('returns the expected hours for April', () => {
        jest.setSystemTime(new Date(2022, 3, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('8:30pm');
        expect(hoursResponse.hours.close).toBe('10:30pm');
    });

    it('returns the expected hours for May', () => {
        jest.setSystemTime(new Date(2022, 4, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('9:00pm');
        expect(hoursResponse.hours.close).toBe('11:30pm');
    });

    it('returns the expected hours for June', () => {
        jest.setSystemTime(new Date(2022, 5, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('9:00pm');
        expect(hoursResponse.hours.close).toBe('11:30pm');
    });

    it('returns the expected hours for July', () => {
        jest.setSystemTime(new Date(2022, 6, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('9:00pm');
        expect(hoursResponse.hours.close).toBe('11:30pm');
    });

    it('returns the expected hours for August', () => {
        jest.setSystemTime(new Date(2022, 7, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('9:00pm');
        expect(hoursResponse.hours.close).toBe('11:30pm');
    });

    it('returns the expected hours for September', () => {
        jest.setSystemTime(new Date(2022, 8, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('8:30pm');
        expect(hoursResponse.hours.close).toBe('10:30pm');
    });

    it('returns the expected hours for October', () => {
        jest.setSystemTime(new Date(2022, 9, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('8:30pm');
        expect(hoursResponse.hours.close).toBe('10:30pm');
    });

    it('returns the expected hours for November', () => {
        jest.setSystemTime(new Date(2022, 10, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('7:30pm');
        expect(hoursResponse.hours.close).toBe('9:30pm');
    });

    it('returns the expected hours for December', () => {
        jest.setSystemTime(new Date(2022, 11, 1));
        const hoursResponse: Hours = getHours();
        expect(hoursResponse.hours.open).toBe('7:30pm');
        expect(hoursResponse.hours.close).toBe('9:30pm');
    });
});
