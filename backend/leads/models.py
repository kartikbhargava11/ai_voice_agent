# this file defines the structure of all the incoming or generated Leads
from django.db import models # core django module used to define database fields, relationships and constraints
from django.utils.translation import gettext_lazy as _


class Lead(models.Model):
    class SourceList(models.TextChoices):
        WEB_VOICE = 'WEB_VOICE', _('Web voice assistant')
        WEB_CHAT = 'WEB_CHAT', _('Web chat')
        PHONE = 'PHONE', _('Phone call')
        MANUAL = 'MANUAL', _('Manual entry')

    class ServiceList(models.TextChoices):
        DENTAL_CHECKUP = 'DENTAL CHECKUP', _('Dental Health Exam and Checkup')
        TEETH_CLEANING = 'TEETH CLEANING', _('Teeth Cleanings')
        MOUTH_GUARD = 'MOUTH GUARD', _('Custom Fitted Guards for sports or prevent grinding (bruxism)')
        WHITENING = 'WHITENING', _('Whitening and remove stains')
        DENTAL_FILLINGS = 'DENTAL FILLING', _('Repair Cavities')
        ROOT_CANAL_TREATMENT = 'RCT', _('Root Canal Treatment')
        DENTURES = 'DENTURES', _('Dentures to replace missing teeth (complete or partial)')

    class UrgencyList(models.TextChoices):
        EMERGENCY = 'E', _('Emergency')
        HIGH = 'H', _('High')
        MEDIUM = 'M', _('Medium')
        LOW = 'L', _('LOW')

    customer_name = models.CharField(max_length=100) # creates a standard text column in the db
    customer_phone = models.CharField(max_length=12) # creates a standard text column in the db
    lead_source = models.CharField(
        choices=SourceList,
        default=SourceList.WEB_VOICE,
        max_length=20,
    )
    service_needed = models.CharField( # creates a text column if a mapping is given
        choices=ServiceList,
        max_length=25
    )
    # urgency = models.CharField(
    #     choices=UrgencyList,
    #     default='M',
    #     max_length=1
    # )
    created_at = models.DateTimeField(auto_now_add=True) # this will store the data and time when a 'Lead' is created
    updated_at = models.DateTimeField(auto_now=True) # this will store the data and time when a 'Lead' is updated

    @property
    def lead_score(self):
        if self.service_needed == self.ServiceList.ROOT_CANAL_TREATMENT:
            return 9
        if self.service_needed == self.ServiceList.MOUTH_GUARD:
            return 8
        return 5
