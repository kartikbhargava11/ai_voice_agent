from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from .serializers import LeadSerializer
from .models import Lead

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer

    parser_classes = [FormParser, MultiPartParser, JSONParser]
