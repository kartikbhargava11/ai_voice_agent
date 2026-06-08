import requests
from requests.exceptions import HTTPError, ProxyError, ConnectionError, ConnectTimeout
from django.conf import settings


def send_whatsapp_confirmation(lead, booking):
    error = None
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
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Throws an exception if the status code is 4xx or 5xx
        response.raise_for_status()
    except HTTPError as e:
        error = str(e)
    except (ProxyError, ConnectionError, ConnectTimeout):
        error = str(e)
    except Exception as e:
        error = str(e)
    else:
        return response.json()

    return {
        "error": True,
        "error_message": error
    }