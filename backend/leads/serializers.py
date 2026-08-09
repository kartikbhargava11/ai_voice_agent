from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    lead_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'

    def validate_status(self, value):
        has_appointment = bool(
            self.instance and self.instance.appointment_set.exists()
        )
        if has_appointment and value != Lead.Status.CONVERTED:
            raise serializers.ValidationError(
                'A lead with an appointment must remain converted.'
            )
        if not has_appointment and value == Lead.Status.CONVERTED:
            raise serializers.ValidationError(
                'A lead becomes converted automatically when an appointment is created.'
            )
        return value
