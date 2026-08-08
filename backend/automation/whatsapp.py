import logging
import time

import requests
from requests.exceptions import HTTPError, ProxyError, ConnectionError, ConnectTimeout
from django.conf import settings

from mysite.observability import request_id


logger = logging.getLogger('app.integrations.whatsapp')


def send_whatsapp_confirmation(lead, booking):
    started = time.monotonic()
    logger.info(
        'whatsapp_request_started',
        extra={
            'event': 'whatsapp_request_started',
            'lead_id': lead.id,
            'appointment_id': booking.id,
        },
    )
    error = None
    error_type = None
    try:
        url = f"{settings.WHATSAPP_BASE_ENDPOINT}{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": "919910477944",
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {
                    "code": "en_US"
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Request-ID": request_id(),
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Throws an exception if the status code is 4xx or 5xx
        response.raise_for_status()
    except HTTPError as e:
        error = str(e)
        error_type = type(e).__name__
    except (ProxyError, ConnectionError, ConnectTimeout) as e:
        error = str(e)
        error_type = type(e).__name__
    except Exception as e:
        error = str(e)
        error_type = type(e).__name__
    else:
        result = response.json()
        logger.info(
            'whatsapp_request_completed',
            extra={
                'event': 'whatsapp_request_completed',
                'lead_id': lead.id,
                'appointment_id': booking.id,
                'status_code': response.status_code,
                'duration_ms': round((time.monotonic() - started) * 1000),
                'response_keys': sorted(result.keys()),
            },
        )
        return result

    logger.warning(
        'whatsapp_request_failed',
        extra={
            'event': 'whatsapp_request_failed',
            'lead_id': lead.id,
            'appointment_id': booking.id,
            'duration_ms': round((time.monotonic() - started) * 1000),
            'error_type': error_type,
        },
    )
    return {
        "status": 'failed',
        "error_message": error
    }
