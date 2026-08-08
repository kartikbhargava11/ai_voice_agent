import contextvars
import json
import logging
import re
import uuid
from datetime import UTC, datetime


_request_id = contextvars.ContextVar('request_id', default='-')
_booking_key = contextvars.ContextVar('booking_key', default='-')
_SENSITIVE_KEY_PARTS = ('password', 'token', 'secret', 'authorization', 'api_key')
_PHONE_KEY_PARTS = ('phone', 'mobile')
_RESERVED_LOG_FIELDS = set(logging.makeLogRecord({}).__dict__) | {'message', 'asctime'}


def request_id():
    return _request_id.get()


def booking_key():
    return _booking_key.get()


def new_request_id(candidate=None):
    if candidate and re.fullmatch(r'[A-Za-z0-9._-]{1,128}', candidate):
        return candidate
    return str(uuid.uuid4())


def set_context(current_request_id=None, current_booking_key=None):
    return (
        _request_id.set(current_request_id or new_request_id()),
        _booking_key.set(_short_key(current_booking_key)),
    )


def reset_context(tokens):
    _request_id.reset(tokens[0])
    _booking_key.reset(tokens[1])


def _short_key(value):
    if not value:
        return '-'
    value = str(value)
    return value if len(value) <= 12 else f'{value[:8]}…{value[-4:]}'


def _mask_phone(value):
    digits = re.sub(r'\D', '', str(value))
    return f'******{digits[-4:]}' if digits else '******'


def _safe(value, key=''):
    lowered = key.lower()
    if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
        return '[REDACTED]'
    if any(part in lowered for part in _PHONE_KEY_PARTS):
        return _mask_phone(value)
    if isinstance(value, dict):
        return {str(k): _safe(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            'timestamp': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'event': getattr(record, 'event', record.getMessage()),
            'request_id': getattr(record, 'request_id', request_id()),
            'booking_key': getattr(record, 'booking_key', booking_key()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_FIELDS and key not in data and not key.startswith('_'):
                data[key] = _safe(value, key)
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False, default=str)
