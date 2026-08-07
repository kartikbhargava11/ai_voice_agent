import hashlib
import json
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from appointment.models import BookingRequest
from appointment.services import handle_booking
from automation.jobs import (
    enqueue_calendar_cancellation,
    enqueue_crm_sync,
    enqueue_whatsapp_confirmation,
)
from automation.services import (
    cancel_calendar_event_with_n8n,
    check_calendar_availability_with_n8n,
)
from leads.services import handle_leads

from .formatter import human_date, human_time
from .llm_service import extract_receptionist_data
from .validators import is_within_office_hours, office_hours_message

REQUIRED_FIELDS = [
    'customer_name',
    'customer_phone',
    'service_needed',
    'appointment_date',
    'appointment_time',
]
N8N_SUCCESS_STATUS = 'available'
PROCESSING_LEASE = timedelta(minutes=2)


def default_state():
    return {field: None for field in REQUIRED_FIELDS}


def _payload_hash(state):
    payload = {field: state.get(field) for field in REQUIRED_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def _reserve_booking_request(idempotency_key, state):
    payload_hash = _payload_hash(state)
    with transaction.atomic():
        booking_request, created = BookingRequest.objects.select_for_update().get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                'payload_hash': payload_hash,
                'status': BookingRequest.Status.PROCESSING,
            },
        )

        if not created and booking_request.payload_hash != payload_hash:
            return None, {
                'error': True,
                'error_message': 'This idempotency key was already used for different booking details.',
                'next_step': 'new_booking_request',
                'http_status': 409,
                'reset_idempotency_key': True,
                'state': state,
            }

        if booking_request.status == BookingRequest.Status.COMPLETED:
            response = dict(booking_request.response_data)
            response['idempotent_replay'] = True
            return None, response

        recently_updated = booking_request.updated_at >= timezone.now() - PROCESSING_LEASE
        if not created and booking_request.status == BookingRequest.Status.PROCESSING and recently_updated:
            return None, {
                'error': True,
                'error_message': 'This booking request is already being processed.',
                'next_step': 'booking_processing',
                'http_status': 409,
                'state': state,
            }

        booking_request.status = BookingRequest.Status.PROCESSING
        booking_request.error_message = ''
        booking_request.save(update_fields=['status', 'error_message', 'updated_at'])
        return booking_request, None


def _record_external_failure(booking_request, message):
    BookingRequest.objects.filter(pk=booking_request.pk).update(
        status=BookingRequest.Status.FAILED,
        error_message=message,
        updated_at=timezone.now(),
    )


def _compensate_calendar_event(booking_request, calendar_event_id):
    result = cancel_calendar_event_with_n8n(
        calendar_event_id=calendar_event_id,
        idempotency_key=booking_request.idempotency_key,
    )
    if result.get('status') in {'cancelled', 'success'}:
        BookingRequest.objects.filter(pk=booking_request.pk).update(
            status=BookingRequest.Status.FAILED,
            error_message='Local booking failed; calendar event was cancelled.',
            updated_at=timezone.now(),
        )
        return result

    BookingRequest.objects.filter(pk=booking_request.pk).update(
        status=BookingRequest.Status.COMPENSATION_REQUIRED,
        calendar_event_id=calendar_event_id,
        error_message=result.get('error_message', 'Calendar cancellation failed.'),
        updated_at=timezone.now(),
    )
    booking_request.refresh_from_db()
    enqueue_calendar_cancellation(booking_request, calendar_event_id)
    return result


def _complete_booking(state, booking_request, calendar_event_id, n8n_result):
    try:
        with transaction.atomic():
            locked_request = BookingRequest.objects.select_for_update().get(pk=booking_request.pk)
            lead = handle_leads(
                customer_name=state['customer_name'],
                customer_phone=state['customer_phone'],
                service_needed=state['service_needed'],
            )
            booking = handle_booking(
                lead=lead,
                appointment_date=state['appointment_date'],
                appointment_time=state['appointment_time'],
                calendar_event_id=calendar_event_id,
            )
            enqueue_crm_sync(booking)
            enqueue_whatsapp_confirmation(booking)

            response = {
                'reply': (
                    f"Perfect {state['customer_name']}. Your appointment has been booked "
                    f"for {human_date(state['appointment_date'])} "
                    f"at {human_time(state['appointment_time'])}."
                ),
                'intent': 'book_appointment',
                'next_step': 'booking_completed',
                'state': state,
                'lead_id': lead.id,
                'booking_id': booking.id,
                'n8n_result': n8n_result,
                'whatsapp_notification_result': {'status': 'queued'},
            }
            locked_request.status = BookingRequest.Status.COMPLETED
            locked_request.appointment = booking
            locked_request.calendar_event_id = calendar_event_id
            locked_request.response_data = response
            locked_request.error_message = ''
            locked_request.save()
            return response
    except IntegrityError:
        compensation = _compensate_calendar_event(booking_request, calendar_event_id)
        return {
            'reply': 'Sorry, that appointment slot was just booked. Please choose another time.',
            'intent': 'book_appointment',
            'next_step': 'collect_appointment_time',
            'missing_fields': ['appointment_time'],
            'state': {**state, 'appointment_time': None},
            'reset_idempotency_key': True,
            'compensation_result': compensation,
            'http_status': 409,
        }
    except Exception:
        compensation = _compensate_calendar_event(booking_request, calendar_event_id)
        return {
            'error': True,
            'error_message': 'The calendar reservation was reversed because the booking could not be saved.',
            'next_step': 'retry_booking',
            'state': state,
            'compensation_result': compensation,
            'http_status': 503,
        }


def handle_chat_message(user_message, state=None, idempotency_key=None):
    state = state or default_state()
    ai_result = extract_receptionist_data(user_message=user_message, state=state)

    if ai_result.get('error_status', False):
        return {**ai_result, 'error': True, 'http_status': 503}

    for key, value in ai_result.get('extracted_fields', {}).items():
        if key in REQUIRED_FIELDS and value:
            state[key] = value

    missing_fields = [field for field in REQUIRED_FIELDS if not state.get(field)]
    if missing_fields:
        return {
            'reply': ai_result.get('reply', 'Please share the missing details.'),
            'intent': ai_result.get('intent', 'book_appointment'),
            'next_step': f'collect_{missing_fields[0]}',
            'missing_fields': missing_fields,
            'state': state,
        }

    if not is_within_office_hours(state['appointment_time']):
        state['appointment_time'] = None
        return {
            'reply': office_hours_message(),
            'intent': 'book_appointment',
            'next_step': 'collect_appointment_time',
            'missing_fields': ['appointment_time'],
            'state': state,
        }

    if not idempotency_key or len(idempotency_key) > 128:
        return {
            'error': True,
            'error_message': 'A valid idempotency key is required to book an appointment.',
            'next_step': 'retry_booking',
            'state': state,
            'http_status': 400,
        }

    booking_request, prior_response = _reserve_booking_request(idempotency_key, state)
    if prior_response is not None:
        return prior_response

    n8n_result = check_calendar_availability_with_n8n(state, idempotency_key)
    n8n_status = n8n_result.get('status')

    if n8n_status == 'unavailable':
        state['appointment_time'] = None
        suggested_slots = n8n_result.get('suggested_slots', [])
        slots_text = ', '.join(suggested_slots[:3])
        reply = (
            f'Sorry, that slot is booked. I have {slots_text} available. Which one works best for you?'
            if slots_text
            else 'Sorry, that slot is unavailable. Please choose another time.'
        )
        BookingRequest.objects.filter(pk=booking_request.pk).update(
            status=BookingRequest.Status.UNAVAILABLE,
            response_data=n8n_result,
            updated_at=timezone.now(),
        )
        return {
            'reply': reply,
            'intent': 'book_appointment',
            'next_step': 'collect_appointment_time',
            'missing_fields': ['appointment_time'],
            'state': state,
            'n8n_result': n8n_result,
            'reset_idempotency_key': True,
        }

    calendar_event_id = n8n_result.get('calendar_event_id')
    if n8n_status != N8N_SUCCESS_STATUS or not calendar_event_id:
        message = n8n_result.get(
            'error_message',
            'n8n did not explicitly confirm the calendar booking.',
        )
        _record_external_failure(booking_request, message)
        return {
            'error': True,
            'error_message': 'The calendar could not confirm this booking. No local appointment was created.',
            'next_step': 'retry_booking',
            'state': state,
            'n8n_result': n8n_result,
            'http_status': 503,
        }

    return _complete_booking(state, booking_request, calendar_event_id, n8n_result)
