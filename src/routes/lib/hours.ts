export interface Hours {
    hours: {
        prettyHours: string;
        open: string;
        close: string;
    };
}

export const getHours = (): Hours => {
    // need upcoming Saturday if current date is not Saturday
    const dayAnchor = 6;
    const currentTime = new Date();
    if (currentTime.getDay() < dayAnchor) {
        currentTime.setDate(
            currentTime.getDate() + (dayAnchor - currentTime.getDay())
        );
    }
    const month = currentTime.getMonth() + 1;
    const response = {
        hours: {
            prettyHours: '',
            open: '',
            close: '',
        },
    };
    switch (month) {
        case 3:
        case 4:
            response.hours.open = '8:30pm';
            response.hours.close = '10:30pm';
            break;
        case 5:
        case 6:
        case 7:
        case 8:
            response.hours.open = '9:00pm';
            response.hours.close = '11:30pm';
            break;
        case 9:
        case 10:
            response.hours.open = '8:30pm';
            response.hours.close = '10:30pm';
            break;
        case 11:
        case 12:
        case 1:
        case 2:
            response.hours.open = '7:30pm';
            response.hours.close = '9:30pm';
            break;
    }
    response.hours.prettyHours = `${response.hours.open} – ${response.hours.close}`;
    return response;
};
