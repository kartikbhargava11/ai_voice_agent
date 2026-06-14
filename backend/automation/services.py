import requests
from requests.exceptions import HTTPError
from django.conf import settings

def normalize_indian_phone(phone):
    phone = str(phone).replace(" ", "").replace("+", "")
    
    if len(phone) == 10:
        return "91" + phone

    return phone

def check_calendar_availability_with_n8n(state):

    payload = {
        # 'lead_id': lead.id,
        'customer_name': state['customer_name'],
        'customer_phone': state['customer_phone'],
        'service_needed': state['service_needed'],
        # 'lead_score': lead.lead_score,
        # 'appointment_id': booking.id,
        'appointment_date': state['appointment_date'],
        'appointment_time': state['appointment_time'],
        # 'phoned_at': str(lead.created_at)
    }

    try:
        response = requests.post(
            settings.WEBHOOK_TRIGGER_URL,
            json=payload,
            timeout=20,
            headers={
                'Content-Type':'application/json'
            }
        )
        response.raise_for_status()

    except Exception as e:
        error = f'{e}'
    else:
        # no exception raised
        # return the response from the webhook
        return response.json()

    return {
        'status': 'failed',
        'error_message': error,
    }
    