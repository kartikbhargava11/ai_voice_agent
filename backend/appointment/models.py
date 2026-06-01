from django.db import models

from leads.models import Lead

_status_choices = [
    ("C", "Completed"),
    ("P", "Pending"),
    ("F", "Failed")
]


class Appointment(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(choices=_status_choices)
    calendar_event_id = models.CharField()

    