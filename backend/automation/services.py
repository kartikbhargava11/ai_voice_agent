import requests
from django.conf import settings

def normalize_indian_phone(phone):
    phone = str(phone).replace(" ", "").replace("+", "")

    if len(phone) == 10:
        return "91" + phone

    return phone

def check_calendar_availability_with_n8n(state, idempotency_key):

    payload = {
        # 'lead_id': lead.id,
        'customer_name': state['customer_name'],
        'customer_phone': state['customer_phone'],
        'service_needed': state['service_needed'],
        # 'lead_score': lead.lead_score,
        # 'appointment_id': booking.id,
        'appointment_date': state['appointment_date'],
        'appointment_time': state['appointment_time'],
        'idempotency_key': idempotency_key,
        'action': 'create_booking',
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
        if not response.content or not response.text.strip():
            return {
                'status': 'failed',
                'error_message': 'n8n returned an empty response body',
            }
        try:
            result = response.json()
        except ValueError:
            content_type = response.headers.get('Content-Type', 'unknown')
            return {
                'status': 'failed',
                'error_message': (
                    f'n8n returned non-JSON content ({content_type}): '
                    f'{response.text[:200]}'
                ),
            }
        if not isinstance(result, dict):
            return {
                'status': 'failed',
                'error_message': 'n8n returned JSON, but the response was not an object',
            }
        return result
    except Exception as exc:
        return {
            'status': 'failed',
            'error_message': str(exc),
        }


def cancel_calendar_event_with_n8n(calendar_event_id, idempotency_key):
    """Compensate for a calendar event whose local booking could not be saved."""
    url = getattr(settings, 'N8N_CANCEL_WEBHOOK_URL', None) or settings.WEBHOOK_TRIGGER_URL
    try:
        response = requests.post(
            url,
            json={
                'action': 'cancel_booking',
                'calendar_event_id': calendar_event_id,
                'idempotency_key': idempotency_key,
            },
            timeout=20,
            headers={'Content-Type': 'application/json'},
        )
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return {'status': 'failed', 'error_message': str(exc)}

    if result.get('status') not in {'cancelled', 'success'}:
        return {
            'status': 'failed',
            'error_message': result.get('error_message', 'n8n did not confirm cancellation'),
        }
    return result


def sync_lead_to_crm_with_n8n(lead, appointment):
    """Send committed database identifiers and timestamps to the CRM workflow."""
    url = getattr(settings, 'N8N_CRM_WEBHOOK_URL', None) or settings.WEBHOOK_TRIGGER_URL
    payload = {
        'action': 'sync_crm',
        'lead_id': lead.id,
        'lead_source': lead.lead_source,
        'created_at': lead.created_at.isoformat(),
        'customer_name': lead.customer_name,
        # Phone numbers intentionally remain strings to preserve + and leading zeroes.
        'customer_phone': normalize_indian_phone(lead.customer_phone),
        'service_needed': lead.service_needed,
        'appointment_id': appointment.id,
        'appointment_date': appointment.appointment_date.isoformat(),
        'appointment_time': appointment.appointment_time.strftime('%H:%M'),
        'calendar_event_id': appointment.calendar_event_id,
    }
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=20,
            headers={'Content-Type': 'application/json'},
        )
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        return {'status': 'failed', 'error_message': str(exc)}

    if result.get('status') not in {'synced', 'success'}:
        return {
            'status': 'failed',
            'error_message': result.get('error_message', 'n8n did not confirm CRM sync'),
        }
    return result
