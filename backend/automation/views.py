import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import HasN8NWebhookSecret


logger = logging.getLogger('app.integrations.n8n')


class N8NCallbackSerializer(serializers.Serializer):
    action = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    request_id = serializers.CharField(required=False)


class N8NCallbackResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class N8NCallbackView(APIView):
    authentication_classes = []
    permission_classes = [HasN8NWebhookSecret]

    @extend_schema(
        summary='Receive an authenticated n8n callback',
        request=N8NCallbackSerializer,
        responses={200: N8NCallbackResponseSerializer},
    )
    def post(self, request):
        logger.info(
            'n8n_callback_received',
            extra={
                'event': 'n8n_callback_received',
                'action': request.data.get('action'),
                'result_status': request.data.get('status'),
            },
        )
        return Response({'status': 'accepted'})
