from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import AppointmentSerializer
from .models import Appointment
from .services import handle_booking

# handles appointment data and provides a custom endpoint to process booking details
class AppointmentViewSet(viewsets.ModelViewSet): # viewsets.ModelViewSet provides auto CRUD actions for the Appointment model
    queryset = Appointment.objects.all().order_by('-created_at') # fetch all the bookings from the db, sorted by the newest first
    serializer_class = AppointmentSerializer # links the view to serializer to auto handle validation and coversion to/from JSON for CRUD operations
    permission_classes = [IsAuthenticated]

    parser_classes = [FormParser, JSONParser] # limits the backend to only accept data send as JSON or url-encoded forms

    # action decorator creates a custom routing path inside the viewset, acts on the whole collection, accepts only post request and changes the URL slug to new-booking
    @action(detail=False, methods=['post'], url_path='new-booking')
    def appointment(self, request):
        # extract data from the incoming request payload
        appointment_date = request.data.get('appointment_date')
        appointment_time = request.data.get('appointment_time')

        # simple data sanity check before moving to the business logic
        if not appointment_date or not appointment_time:
            return Response(
                {"error": "Appointment Date and Time are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # data sanity checks passed, execute the business logic
        result = handle_booking(appointment_date=appointment_date, appointment_time=appointment_time)

        # send the result back to the client with http status code 201 confirming booking has been successfully created
        return Response(
            result,
            status=status.HTTP_201_CREATED
        )
