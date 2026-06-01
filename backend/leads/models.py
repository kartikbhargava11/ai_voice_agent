from django.db import models

_service_needed_choices = [
    ("DC", "Dental Checkup"),
    ("TC", "Teeth Cleaning"),
    ("TP", "Tooth Pain"),
    ("WH", "Whitening"),
    ("BC", "Braces Consultation"),
    ("RC", "Root Canal"),
    ("TF", "Tooth Filling")
]

_urgency_choices = [
    ("S", "Severe"),
    ("H", "High"),
    ("M", "Medium"),
    ("L", "Low")
]

_status_choices = [
    ("C", "Completed"),
    ("P", "Pending"),
    ("F", "Failed")
]


class Lead(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=12)
    service_needed = models.CharField(choices=_service_needed_choices)
    urgency = models.CharField(choices=_urgency_choices)
    lead_score = models.IntegerField()
    status = models.CharField(choices=_status_choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    