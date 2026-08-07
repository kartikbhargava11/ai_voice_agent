from django.contrib import admin

# Register your models here.
from .models import Appointment, BookingRequest

admin.site.register(Appointment)
admin.site.register(BookingRequest)
