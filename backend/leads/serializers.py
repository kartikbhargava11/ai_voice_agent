from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['id', 'customer_name', 'customer_phone', 'service_needed', 'created_at', 'updated_at']
