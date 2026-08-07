from .models import Lead

def handle_leads(
    customer_name,
    customer_phone,
    service_needed,
    lead_source=Lead.SourceList.WEB_VOICE,
):

    lead = Lead.objects.create(
        customer_name=customer_name,
        customer_phone=customer_phone,
        service_needed=service_needed,
        lead_source=lead_source,
    )

    return lead
