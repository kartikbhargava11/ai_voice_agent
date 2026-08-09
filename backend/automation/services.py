import logging
import time

import requests
from django.conf import settings

from mysite.observability import request_id


logger = logging.getLogger('app.integrations.n8n')


def _headers():
    secret = settings.N8N_WEBHOOK_SECRET
    if not secret:
        raise RuntimeError('N8N_WEBHOOK_SECRET is not configured')
    return {
        'Content-Type': 'application/json',
        'X-Request-ID': request_id(),
        'X-Webhook-Secret': secret,
    }


def _log_result(action, response, started, result):
    logger.info(
        'n8n_request_completed',
        extra={
            'event': 'n8n_request_completed',
            'action': action,
            'status_code': response.status_code,
            'duration_ms': round((time.monotonic() - started) * 1000),
            'result_status': result.get('status'),
            'calendar_event_id': result.get('calendar_event_id'),
            'response_keys': sorted(result.keys()),
        },
    )

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
        'request_id': request_id(),
        'action': 'create_booking',
        # 'phoned_at': str(lead.created_at)
    }

    started = time.monotonic()
    logger.info(
        'n8n_request_started',
        extra={'event': 'n8n_request_started', 'action': 'create_booking'},
    )
    try:
        response = requests.post(
            settings.WEBHOOK_TRIGGER_URL,
            json=payload,
            timeout=20,
            headers=_headers(),
        )
        response.raise_for_status()
        if not response.content or not response.text.strip():
            result = {
                'status': 'failed',
                'error_message': 'n8n returned an empty response body',
            }
            _log_result('create_booking', response, started, result)
            return result
        try:
            result = response.json()
        except ValueError:
            content_type = response.headers.get('Content-Type', 'unknown')
            result = {
                'status': 'failed',
                'error_message': (
                    f'n8n returned non-JSON content ({content_type})'
                ),
            }
            _log_result('create_booking', response, started, result)
            return result
        if not isinstance(result, dict):
            result = {
                'status': 'failed',
                'error_message': 'n8n returned JSON, but the response was not an object',
            }
            _log_result('create_booking', response, started, result)
            return result
        _log_result('create_booking', response, started, result)
        return result
    except Exception as exc:
        logger.warning(
            'n8n_request_failed',
            extra={
                'event': 'n8n_request_failed',
                'action': 'create_booking',
                'duration_ms': round((time.monotonic() - started) * 1000),
                'error_type': type(exc).__name__,
            },
        )
        return {
            'status': 'failed',
            'error_message': str(exc),
        }


def cancel_calendar_event_with_n8n(calendar_event_id, idempotency_key):
    """Compensate for a calendar event whose local booking could not be saved."""
    url = getattr(settings, 'N8N_CANCEL_WEBHOOK_URL', None) or settings.WEBHOOK_TRIGGER_URL
    started = time.monotonic()
    logger.info(
        'n8n_request_started',
        extra={'event': 'n8n_request_started', 'action': 'cancel_booking'},
    )
    try:
        response = requests.post(
            url,
            json={
                'action': 'cancel_booking',
                'calendar_event_id': calendar_event_id,
                'idempotency_key': idempotency_key,
                'request_id': request_id(),
            },
            timeout=20,
            headers=_headers(),
        )
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        logger.warning(
            'n8n_request_failed',
            extra={
                'event': 'n8n_request_failed',
                'action': 'cancel_booking',
                'duration_ms': round((time.monotonic() - started) * 1000),
                'error_type': type(exc).__name__,
            },
        )
        return {'status': 'failed', 'error_message': str(exc)}

    if result.get('status') not in {'cancelled', 'success'}:
        failure = {
            'status': 'failed',
            'error_message': result.get('error_message', 'n8n did not confirm cancellation'),
        }
        _log_result('cancel_booking', response, started, failure)
        return failure
    _log_result('cancel_booking', response, started, result)
    return result


def sync_lead_to_crm_with_n8n(lead, appointment):
    """Send committed database identifiers and timestamps to the CRM workflow."""
    url = getattr(settings, 'N8N_CRM_WEBHOOK_URL', None) or settings.WEBHOOK_TRIGGER_URL
    payload = {
        'action': 'sync_crm',
        'lead_id': lead.id,
        'lead_source': lead.lead_source,
        'lead_status': lead.status,
        'created_at': lead.created_at.isoformat(),
        'customer_name': lead.customer_name,
        # Phone numbers intentionally remain strings to preserve + and leading zeroes.
        'customer_phone': normalize_indian_phone(lead.customer_phone),
        'service_needed': lead.service_needed,
        'appointment_id': appointment.id,
        'appointment_date': appointment.appointment_date.isoformat(),
        'appointment_time': appointment.appointment_time.strftime('%H:%M'),
        'appointment_status': appointment.status,
        'calendar_event_id': appointment.calendar_event_id,
        'request_id': request_id(),
    }
    started = time.monotonic()
    logger.info(
        'n8n_request_started',
        extra={
            'event': 'n8n_request_started',
            'action': 'sync_crm',
            'lead_id': lead.id,
            'appointment_id': appointment.id,
        },
    )
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=20,
            headers=_headers(),
        )
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        logger.warning(
            'n8n_request_failed',
            extra={
                'event': 'n8n_request_failed',
                'action': 'sync_crm',
                'lead_id': lead.id,
                'appointment_id': appointment.id,
                'duration_ms': round((time.monotonic() - started) * 1000),
                'error_type': type(exc).__name__,
            },
        )
        return {'status': 'failed', 'error_message': str(exc)}

    if result.get('status') not in {'synced', 'success'}:
        failure = {
            'status': 'failed',
            'error_message': result.get('error_message', 'n8n did not confirm CRM sync'),
        }
        _log_result('sync_crm', response, started, failure)
        return failure
    _log_result('sync_crm', response, started, result)
    return result
