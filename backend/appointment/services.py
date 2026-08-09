from datetime import datetime

from .models import Appointment

def handle_booking(lead, appointment_date, appointment_time, calendar_event_id=''):
    booking = Appointment.objects.create(
        lead=lead,
        appointment_date=datetime.strptime(appointment_date, '%Y-%m-%d').date(),
        appointment_time=datetime.strptime(appointment_time, '%H:%M').time(),
        calendar_event_id=calendar_event_id,
    )
    if lead.status != lead.Status.CONVERTED:
        lead.status = lead.Status.CONVERTED
        lead.save(update_fields=['status', 'updated_at'])

    return booking
