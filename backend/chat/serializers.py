# this file shapes the input/output JSON

from rest_framework import serializers # core utility from DRF to auto validate data and convert it between JSON and Python objects format
from .models import Chat


class ChatSerializer(serializers.ModelSerializer):
    class Meta: # provides the instructions for the serializer
        model = Chat # ties the serializer directly to Chat database model
        fields = '__all__' # specifies the exact db columns that will be exposed through the API


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(
        help_text='The latest message spoken or typed by the customer.'
    )
    state = serializers.DictField(
        required=False,
        default=dict,
        help_text='Information already collected during the conversation.',
    )
    idempotency_key = serializers.CharField(
        required=False,
        help_text='Optional duplicate-protection key. Prefer the Idempotency-Key header.',
    )


class ChatResponseSerializer(serializers.Serializer):
    error = serializers.BooleanField(required=False)
    error_message = serializers.CharField(required=False)
    response = serializers.CharField(required=False)
    next_step = serializers.CharField(required=False)
    state = serializers.DictField(required=False)
    n8n_result = serializers.DictField(required=False)
