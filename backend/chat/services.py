from appointment.services import handle_booking
from leads.services import handle_leads

from automation.services import check_calendar_availability_with_n8n
from automation.whatsapp import send_whatsapp_confirmation

from .llm_service import extract_receptionist_data
from .validators import is_within_office_hours, office_hours_message
from .formatter import human_date, human_time

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
    print(missing_fields)
    if missing_fields: # if there are still some missing info left, sending response to frontend
        print('MISSING FIELDS PRESENT.....')
        return {
            "reply": ai_result.get("reply", "Please share the missing details."),
            "intent": ai_result.get("intent", "book_appointment"),
            "next_step": f"collect_{missing_fields[0]}",
            "missing_fields": missing_fields,
            "state": state,
        }
    
    # office opening hours check
    if state.get('appointment_time') and not is_within_office_hours(state['appointment_time']):
        state['appointment_time'] = None

        return {
            "reply": office_hours_message(),
            "intent": 'book_appointment',
            'next_step': 'collect_appointment_time',
            'missing_fields': ['appointment_time'],
            'state': state,
        }
    
    # triggering n8n webhook workflow to automate the CRM updates
    n8n_result = check_calendar_availability_with_n8n(state)


    if n8n_result.get('status') ==  'unavailable':
        state['appointment_time'] = None
        suggested_slots = n8n_result.get('suggested_slots', [])

        if suggested_slots:
            slots_text = ', '.join(suggested_slots[:3])
            reply = (
                f"Sorry, that slot is booked. "
                f"I have {slots_text} available. "
                f"which one works best for you"
            )
        else:
            reply = 'Sorry, the slot is unavailable. Please choose another time'
        return {
            'reply': reply,
            'intent': 'book_appointment',
            'next_step': 'collect_booking_time',
            'missing_fields': ['appointment_time'],
            'state': state,
            'n8n_result': n8n_result
        }
    
    calendar_event_id = n8n_result.get('calendar_event_id')

    # following code will run, if all the required fields have been captured and are valid
    # saving caller's demographic info into the "Lead" Table
    lead = handle_leads(
        customer_name=state['customer_name'],
        customer_phone=state['customer_phone'],
        service_needed=state['service_needed'],
    )

    # saving caller's appointment booking info into the "Appointment" Table
    booking = handle_booking(
        lead=lead,
        appointment_date=state['appointment_date'],
        appointment_time=state['appointment_time']
    )

    if calendar_event_id:
        booking.calendar_event_id = calendar_event_id
        booking.save()
    
   
    
    # triggering whatsapp cloud API to send booking confirmations
    whatsapp_result = send_whatsapp_confirmation(
        lead=lead,
        booking=booking
    )

    friendly_date = human_date(state['appointment_date'])
    friendly_time = human_time(state['appointment_time'])

    # returning the unified result 
    return {
        "reply": f"Perfect {state['customer_name']}. Your appointment has been booked for {friendly_date} at {friendly_time}.",
        "intent": "book_appointment",
        "next_step": "booking_completed",
        "state": state,
        "lead_id": lead.id,
        "booking_id": booking.id,
        "n8n_result": n8n_result,
        "whatsapp_notification_result": whatsapp_result
    }

