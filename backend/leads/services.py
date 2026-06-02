from .models import Lead

def handle_leads(customer_name, customer_phone, service_needed):

    lead = Lead.objects.create(
        customer_name=customer_name,
        customer_phone=customer_phone,
        service_needed=service_needed,
    )

    return lead