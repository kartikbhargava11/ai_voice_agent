from appointment.services import handle_booking
from leads.services import handle_leads

from automation.services import trigger_booking_automation
from automation.whatsapp import send_whatsapp_confirmation

from .llm_service import extract_receptionist_data

REQUIRED_FIELDS = [
    'customer_name',
    'customer_phone',
    'service_needed',
    'appointment_date',
    'appointment_time'
]

def default_state():
    return {
        'customer_name': None,
        'customer_phone': None,
        'service_needed': None,
        'appointment_date': None,
        'appointment_time': None
    }

def handle_chat_message(user_message, state=None):

    if not state:
        state = default_state()

    ai_result, error = extract_receptionist_data(user_message=user_message, state=state)

    if error:
        return ai_result, error

    extracted_fields = ai_result.get('extracted_fields', {})

    for key, value in extracted_fields.items():
        if value:
            state[key] = value

    missing_fields = [
        field for field in REQUIRED_FIELDS if not state.get(field)
    ]

    if missing_fields:
        return {
            "reply": ai_result.get("reply", "Please share the missing details."),
            "intent": ai_result.get("intent", "book_appointment"),
            "next_step": f"collect_{missing_fields[0]}",
            "missing_fields": missing_fields,
            "state": state,
        }, error

    lead = handle_leads(
        customer_name=state['customer_name'],
        customer_phone=state['customer_phone'],
        service_needed=state['service_needed']
    )

    booking = handle_booking(
        lead=lead,
        appointment_date=state['appointment_date'],
        appointment_time=state['appointment_time']
    )
    
    try:
        automation_result = trigger_booking_automation(
            lead=lead,
            booking=booking
        )
    except Exception as e:
        automation_result = {
            'status':'failed',
            'error': str(e)
        }
    
    whatsapp_result = send_whatsapp_confirmation(lead, booking)

    return {
        "reply": f"Perfect {state['customer_name']}. Your appointment has been booked for {state['appointment_date']} at {state['appointment_time']}.",
        "intent": "book_appointment",
        "next_step": "booking_completed",
        "state": state,
        "lead_id": lead.id,
        "booking_id": booking.id,
        "automation": automation_result,
        "whatsapp_result": whatsapp_result
    }, error

