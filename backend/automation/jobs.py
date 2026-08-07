from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import AutomationJob
from .services import cancel_calendar_event_with_n8n, sync_lead_to_crm_with_n8n
from .whatsapp import send_whatsapp_confirmation


def enqueue_whatsapp_confirmation(appointment):
    return AutomationJob.objects.get_or_create(
        job_type=AutomationJob.JobType.WHATSAPP_CONFIRMATION,
        appointment=appointment,
        defaults={'run_after': timezone.now()},
    )[0]


def enqueue_crm_sync(appointment):
    return AutomationJob.objects.get_or_create(
        job_type=AutomationJob.JobType.CRM_SYNC,
        appointment=appointment,
        defaults={'run_after': timezone.now()},
    )[0]


def enqueue_calendar_cancellation(booking_request, calendar_event_id):
    return AutomationJob.objects.get_or_create(
        job_type=AutomationJob.JobType.CALENDAR_CANCELLATION,
        booking_request=booking_request,
        defaults={
            'payload': {'calendar_event_id': calendar_event_id},
            'run_after': timezone.now(),
        },
    )[0]


def _execute(job):
    if job.job_type == AutomationJob.JobType.WHATSAPP_CONFIRMATION:
        appointment = job.appointment
        result = send_whatsapp_confirmation(appointment.lead, appointment)
    elif job.job_type == AutomationJob.JobType.CRM_SYNC:
        appointment = job.appointment
        result = sync_lead_to_crm_with_n8n(appointment.lead, appointment)
    elif job.job_type == AutomationJob.JobType.CALENDAR_CANCELLATION:
        result = cancel_calendar_event_with_n8n(
            job.payload['calendar_event_id'],
            job.booking_request.idempotency_key,
        )
    else:
        result = {'status': 'failed', 'error_message': 'Unsupported automation job'}

    if result.get('status') == 'failed' or result.get('error_message'):
        raise RuntimeError(result.get('error_message', 'Automation job failed'))
    return result


def process_next_job():
    now = timezone.now()
    stale_before = now - timedelta(minutes=5)
    with transaction.atomic():
        job = (
            AutomationJob.objects.select_for_update(skip_locked=True)
            .filter(
                Q(status=AutomationJob.Status.PENDING, run_after__lte=now)
                | Q(status=AutomationJob.Status.PROCESSING, updated_at__lte=stale_before)
            )
            .order_by('run_after', 'id')
            .first()
        )
        if not job:
            return False
        job.status = AutomationJob.Status.PROCESSING
        job.attempts += 1
        job.save(update_fields=['status', 'attempts', 'updated_at'])

    try:
        _execute(job)
    except Exception as exc:
        job.last_error = str(exc)
        if job.attempts >= job.max_attempts:
            job.status = AutomationJob.Status.FAILED
        else:
            job.status = AutomationJob.Status.PENDING
            delay_seconds = min(60 * (2 ** (job.attempts - 1)), 3600)
            job.run_after = timezone.now() + timedelta(seconds=delay_seconds)
        job.save(update_fields=['status', 'last_error', 'run_after', 'updated_at'])
    else:
        job.status = AutomationJob.Status.COMPLETED
        job.last_error = ''
        job.save(update_fields=['status', 'last_error', 'updated_at'])
    return True
