from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import LeadSerializer
from .models import Lead
from .services import handle_leads

class LeadViewSet(viewsets.ModelViewSet): # ModelViewSet parent class provides automatic CRUD actions for the Lead model
    queryset = Lead.objects.all().order_by('-created_at') # fetches all the "leads" from the db, sorted by newest first
    serializer_class = LeadSerializer # links the view to serializer to auto handle validation and conversion to/from JSON for CRUD operations

    parser_classes = [FormParser, MultiPartParser, JSONParser] # limits the backend to only accept data send as JSON or url-encoded form or multi-part form

    # action decorator creates a custom routing path inside the viewset, acts on the whole collection, accepts only post requests, and changes url slug to "save-leads"
    @action(detail=False, methods=['post'], url_path='save-leads')
    def lead(self, request):
        # extracting data from the incoming request payload 
        customer_name = request.data.get('customer_name')
        customer_phone = request.data.get('customer_phone')
        service_needed = request.data.get('service_needed')

        # simple data validation checks
        error = None
        if not customer_name:
            error = "customer name is required"
        elif not customer_phone:
            error = "customer phone number is required"
        elif not service_needed:
            error = "service needed is required"
        
        if error is not None:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # execute the business logic, after data sanity checks
        result = handle_leads(customer_name=customer_name, customer_phone=customer_phone, service_needed=service_needed)

        # return the response back to the client with http status code 201 confirming "Lead" has been saved successfully
        return Response(
            result,
            status=status.HTTP_201_CREATED
        )







