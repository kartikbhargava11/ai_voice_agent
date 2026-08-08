from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    lead_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'
