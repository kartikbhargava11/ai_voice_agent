from rest_framework import serializers
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'lead', 'appointment_date', 'appointment_time', 'status', 'calendar_event_id']
        