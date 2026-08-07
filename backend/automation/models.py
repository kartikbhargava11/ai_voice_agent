from django.db import models
from django.utils import timezone


class AutomationJob(models.Model):
    class JobType(models.TextChoices):
        WHATSAPP_CONFIRMATION = 'whatsapp_confirmation', 'WhatsApp confirmation'
        CRM_SYNC = 'crm_sync', 'CRM sync'
        CALENDAR_CANCELLATION = 'calendar_cancellation', 'Calendar cancellation'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    job_type = models.CharField(max_length=32, choices=JobType.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    appointment = models.ForeignKey(
        'appointment.Appointment',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='automation_jobs',
    )
    booking_request = models.ForeignKey(
        'appointment.BookingRequest',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='automation_jobs',
    )
    payload = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    run_after = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['status', 'run_after'],
                name='automation__status_805089_idx',
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['job_type', 'appointment'],
                condition=models.Q(appointment__isnull=False),
                name='unique_appointment_automation_job',
            ),
            models.UniqueConstraint(
                fields=['job_type', 'booking_request'],
                condition=models.Q(booking_request__isnull=False),
                name='unique_booking_request_automation_job',
            ),
        ]
