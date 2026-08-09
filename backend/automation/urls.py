from django.urls import path

from .views import N8NCallbackView


urlpatterns = [
    path('webhook/callback/', N8NCallbackView.as_view(), name='n8n-callback'),
]
