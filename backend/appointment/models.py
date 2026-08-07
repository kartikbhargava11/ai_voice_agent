from django.db import models

from leads.models import Lead

class Appointment(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['appointment_date', 'appointment_time'],
                name='unique_appointment_slot',
            )
        ]


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        UNAVAILABLE = 'unavailable', 'Unavailable'
        FAILED = 'failed', 'Failed'
        COMPLETED = 'completed', 'Completed'
        COMPENSATION_REQUIRED = 'compensation_required', 'Compensation required'

    idempotency_key = models.CharField(max_length=128, unique=True)
    payload_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    appointment = models.OneToOneField(
        Appointment,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='booking_request',
    )
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
