import logging
import time

from .observability import new_request_id, reset_context, set_context


logger = logging.getLogger('app.http')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_request_id = new_request_id(request.headers.get('X-Request-ID'))
        idempotency_key = request.headers.get('Idempotency-Key')
        tokens = set_context(current_request_id, idempotency_key)
        started = time.monotonic()
        log_request = request.path != '/health/'
        if log_request:
            logger.info(
                'request_started',
                extra={
                    'event': 'request_started',
                    'method': request.method,
                    'path': request.path,
                },
            )
        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                'request_failed',
                extra={
                    'event': 'request_failed',
                    'method': request.method,
                    'path': request.path,
                    'duration_ms': round((time.monotonic() - started) * 1000),
                },
            )
            raise
        else:
            response['X-Request-ID'] = current_request_id
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            if log_request:
                logger.log(
                    level,
                    'request_completed',
                    extra={
                        'event': 'request_completed',
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                        'duration_ms': round((time.monotonic() - started) * 1000),
                    },
                )
            return response
        finally:
            reset_context(tokens)
