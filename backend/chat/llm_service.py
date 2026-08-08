import json
import logging
import time
from datetime import date, datetime

from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger('app.openai')

def extract_receptionist_data(user_message, state):
    started = time.monotonic()
    logger.info(
        'openai_request_started',
        extra={
            'event': 'openai_request_started',
            'model': 'gpt-4o-mini',
            'known_field_count': sum(bool(value) for value in state.values()),
            'message_length': len(user_message),
        },
    )
    today = date.today().isoformat()
    day_name = datetime.now().strftime('%A')
    time_24 = datetime.now().strftime('%H:%M')

    SYSTEM_PROMPT = f"""
    Your name is Bonnie. You are a warm, helpful receptionist for a dental clinic.

    Today is {today}.
    Week Day is {day_name}.
    Current Time is {time_24}.

    Your job:
    1. Have a natural conversation.
    2. Help users book appointments.
    3. Answer basic questions about services.
    4. Extract booking details into JSON.
    5. Ask only one missing question at a time.

    Available Services:
    - DENTAL CHECKUP: Dental Health Exam and Checkup
    - TEETH CLEANING: Teeth Cleanings
    - MOUTH GUARD: Custom Fitted Guards for sports or prevent grinding (bruxism)
    - WHITENING: Whitening and remove stains
    - DENTAL FILLING: Repair Cavities
    - RCT: Root Canal Treatment
    - DENTURES: Dentures to replace missing teeth (complete or partial)

    Rules:
    - convert dates to YYYY-MM-DD.
    - Appointments are available from 10:00 AM to 5:00 PM.
    - The latest 30-minute appointment can start at 4:30 PM.
    - Never book or suggest appointments outside these hours.
    - If the user asks for a time outside opening hours, politely ask them to choose a time between 10 AM and 5 PM.
    - If user gives impossible dates for example, 45 March, ask for a valid date.
    - If user gives vague answer for appointment dates. For example, Next Friday. Extract future date from today's date.
    - Never return past dates.
    - If user asks about available services, explain them briefly in reply.
    - If year is missing, use the next future occurrence.
    - Convert time to HH:MM 24-hour format.
    - If a field is missing, keep it null.
    - Return only valid JSON. No markdown.
    - service_needed must be one of the these DENTAL CHECKUP, TEETH CLEANING, MOUTH GUARD, WHITENING, DENTAL FILLING, RCT, DENTURES.
    - Ask only for the next missing field.

    Service mapping:
    - DENTAL CHECKUP = Dental Health Exam and Checkup
    - TEETH CLEANING = Teeth Cleanings
    - MOUTH GUARD = Custom Fitted Guards for sports or prevent grinding (bruxism)
    - WHITENING = Whitening and remove stains
    - DENTAL FILLING = Repair Cavities
    - RCT = Root Canal Treatment
    - DENTURES = Dentures to replace missing teeth (complete or partial)
    """

    USER_PROMPT = f"""
    Current state:
    {json.dumps(state)}

    User message:
    {user_message}

    Return JSON exactly like this:
    {{
    "intent": "book_appointment",
    "extracted_fields": {{
        "customer_name": null,
        "customer_phone": null,
        "service_needed": null,
        "appointment_date": null,
        "appointment_time": null
    }},
    "reply": "short and natural receptionist reply"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as e:
        logger.warning(
            'openai_request_failed',
            extra={
                'event': 'openai_request_failed',
                'model': 'gpt-4o-mini',
                'duration_ms': round((time.monotonic() - started) * 1000),
                'error_type': type(e).__name__,
            },
        )
        return {
            'error_status': True,
            'error_message': f'{e}'
        }
    else:
        content = response.choices[0].message.content
        logger.info(
            'openai_request_completed',
            extra={
                'event': 'openai_request_completed',
                'model': 'gpt-4o-mini',
                'duration_ms': round((time.monotonic() - started) * 1000),
                'openai_request_id': getattr(response, '_request_id', None),
            },
        )
        # Convert Python dictionary to JSON string
        try:
            return json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(
                'openai_response_invalid',
                extra={
                    'event': 'openai_response_invalid',
                    'error_type': type(exc).__name__,
                },
            )
            return {
                'error_status': True,
                'error_message': 'OpenAI returned an invalid structured response.',
            }

    
