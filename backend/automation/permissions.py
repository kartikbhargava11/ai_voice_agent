import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasN8NWebhookSecret(BasePermission):
    message = 'A valid n8n webhook secret is required.'

    def has_permission(self, request, view):
        expected = settings.N8N_WEBHOOK_SECRET
        supplied = request.headers.get('X-Webhook-Secret', '')
        return bool(expected and supplied and hmac.compare_digest(expected, supplied))
