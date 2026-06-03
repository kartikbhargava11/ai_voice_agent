import requests
from django.conf import settings

def trigger_booking_automation(lead, booking):
    payload = {
        'lead_id': lead.id,
        'customer_name': lead.customer_name,
        'customer_phone': lead.customer_phone,
        'service_needed': lead.service_needed,
        'lead_score': lead.lead_score,
        'appointment_id': booking.id,
        'appointment_date': str(booking.appointment_date),
        'appointment_time': str(booking.appointment_time)
    }

    response = requests.post(
        settings.N8N_BOOKING_WEBHOOK_URL,
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