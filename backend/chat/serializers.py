# this file shapes the input/output JSON

from rest_framework import serializers # core utility from DRF to auto validate data and convert it between JSON and Python objects format
from .models import Chat


class ChatSerializer(serializers.ModelSerializer):
    class Meta: # provides the instructions for the serializer
        model = Chat # ties the serializer directly to Chat database model
        fields = '__all__' # specifies the exact db columns that will be exposed through the API

        