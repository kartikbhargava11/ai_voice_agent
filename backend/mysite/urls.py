"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import IsAdminUser

from .auth import ThrottledObtainAuthToken
from .health import health, readiness

urlpatterns = [
    path('api/v1/', include('leads.urls')),
    path('api/v1/', include('chat.urls')),
    path('api/v1/', include('appointment.urls')),
    path('api/v1/automation/', include('automation.urls')),
    path('api/v1/auth/token/', ThrottledObtainAuthToken.as_view(), name='api-v1-token'),
    path('api/token/', ThrottledObtainAuthToken.as_view(), name='api-token'),
    path('health/', health, name='health'),
    path('health/ready/', readiness, name='readiness'),
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=[IsAdminUser]),
        name='api-schema',
    ),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='api-schema',
            permission_classes=[IsAdminUser],
        ),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(
            url_name='api-schema',
            permission_classes=[IsAdminUser],
        ),
        name='redoc',
    ),
    path(settings.ADMIN_URL, admin.site.urls),
]
