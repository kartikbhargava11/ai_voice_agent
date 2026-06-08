import requests
from django.conf import settings

def normalize_indian_phone(phone):
    phone = str(phone).replace(" ", "").replace("+", "")
    
    if len(phone) == 10:
        return "91" + phone

    return phone

def trigger_booking_automation(lead, booking):
    payload = {
        'lead_id': lead.id,
        'customer_name': lead.customer_name,
        'customer_phone': lead.customer_phone,
        'service_needed': lead.service_needed,
        'lead_score': lead.lead_score,
        'appointment_id': booking.id,
        'appointment_date': str(booking.appointment_date),
        'appointment_time': str(booking.appointment_time),
        'appointment_datetime': f"{booking.appointment_date}T{booking.appointment_time}:00",
    }

    response = requests.post(
        settings.WEBHOOK_TRIGGER_URL,
        json=payload,
        timeout=10,
        headers={
            'Content-Type':'application/json'
        }
    )

    response.raise_for_status()

    return {
        'status':'success',
        'n8n_response': response.text
    }