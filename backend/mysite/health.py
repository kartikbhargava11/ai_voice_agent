from datetime import timedelta

import requests
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from automation.models import AutomationWorkerHeartbeat


@require_GET
def health(request):
    return JsonResponse({'status': 'ok', 'django': 'up'})


def _database_is_ready():
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            return cursor.fetchone() == (1,)
    except Exception:
        return False


def _worker_is_ready():
    try:
        stale_before = timezone.now() - timedelta(
            seconds=settings.AUTOMATION_WORKER_STALE_SECONDS
        )
        return AutomationWorkerHeartbeat.objects.filter(
            name='default',
            last_seen_at__gte=stale_before,
        ).exists()
    except Exception:
        return False


def _n8n_is_ready():
    try:
        response = requests.get(
            settings.N8N_HEALTH_URL,
            timeout=settings.N8N_HEALTH_TIMEOUT_SECONDS,
        )
        return response.ok
    except requests.RequestException:
        return False


@require_GET
def readiness(request):
    checks = {
        'django': True,
        'database': _database_is_ready(),
        'automation_worker': _worker_is_ready(),
        'n8n': _n8n_is_ready(),
    }
    ready = all(checks.values())
    return JsonResponse(
        {'status': 'ready' if ready else 'not_ready', 'checks': checks},
        status=200 if ready else 503,
    )
