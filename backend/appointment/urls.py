from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet

router = DefaultRouter()
router.register(r'', AppointmentViewSet)


urlpatterns = [
    path('book-appointment/', include(router.urls)),
]