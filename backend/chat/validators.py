from datetime import datetime, timedelta

from .constants import OFFICE_CLOSE, OFFICE_OPEN, APPOINTMENT_DURATION_MINUTES

def is_within_office_hours(appointment_time: str) -> bool:
    try:
        start_time = datetime.strptime(appointment_time, '%H:%M').time()
    except:
        return False
    
    start_datetime = datetime.combine(datetime.today(), start_time)
    end_datetime = start_datetime + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

    end_time = end_datetime.time()

    return start_time >= OFFICE_OPEN and end_time <= OFFICE_CLOSE

def office_hours_message():
    return (
        "We are open from 10 AM to 5 PM. "
        "Please choose a time within those hours"
    )