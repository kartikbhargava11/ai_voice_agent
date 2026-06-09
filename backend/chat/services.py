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

    ai_result = extract_receptionist_data(user_message=user_message, state=state)

    if ai_result.get('error_status', False):
        # OpenAI client failed
        return ai_result

    # OpenAI client passed
    # returns extracted data from the inbound call as a dict as a whole or in parts
    # "extracted_fields": {
    #     "customer_name": null,
    #     "customer_phone": null,
    #     "service_needed": null,
    #     "appointment_date": null,
    #     "appointment_time": null
    # },
    extracted_fields = ai_result.get('extracted_fields', {})

    for key, value in extracted_fields.items():
        if value:
            # making a copy or mapping the extracted data with a pre-developed schema
            state[key] = value

    missing_fields = [
        field for field in REQUIRED_FIELDS if not state.get(field)
    ]

    if missing_fields: # if there are still some missing info left, sending response to frontend
        return {
            "reply": ai_result.get("reply", "Please share the missing details."),
            "intent": ai_result.get("intent", "book_appointment"),
            "next_step": f"collect_{missing_fields[0]}",
            "missing_fields": missing_fields,
            "state": state,
        }

    # following code will run, if all the required fields have been captured or filled
    # saving caller's demographic info into the "Lead" Table
    lead = handle_leads(
        customer_name=state['customer_name'],
        customer_phone=state['customer_phone'],
        service_needed=state['service_needed']
    )

    # saving caller's appointment booking info into the "Appointment" Table
    booking = handle_booking(
        lead=lead,
        appointment_date=state['appointment_date'],
        appointment_time=state['appointment_time']
    )
    
    # triggering n8n webhook workflow to automate the CRM updates
    n8n_result = trigger_booking_automation(
        lead=lead,
        booking=booking
    )

    if n8n_result.get('status') ==  'not-available':
        return {
            'reply': f'Sorry that slot is unavailable. Please choose another time',
            'intent': 'book_appointment',
            'next_step': 'collect_booking_time',
            'state': state
        }
    
    # triggering whatsapp cloud API to send booking confirmations
    whatsapp_result = send_whatsapp_confirmation(
        lead=lead,
        booking=booking
    )

    # returning the unified result 
    return {
        "reply": f"Perfect {state['customer_name']}. Your appointment has been booked for {state['appointment_date']} at {state['appointment_time']}.",
        "intent": "book_appointment",
        "next_step": "booking_completed",
        "state": state,
        "lead_id": lead.id,
        "booking_id": booking.id,
        "n8n_result": n8n_result,
        "whatsapp_notification_result": whatsapp_result
    }

