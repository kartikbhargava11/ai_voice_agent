from datetime import datetime

from .models import Appointment

def handle_booking(lead, appointment_date, appointment_time):
    booking = Appointment.objects.create(
        lead=lead,
        appointment_date=datetime.strptime(appointment_date, '%Y-%m-%d').date(),
        appointment_time=datetime.strptime(appointment_time, '%H:%M').time(),
        calendar_event_id=''
    )

    return booking