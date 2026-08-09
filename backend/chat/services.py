import hashlib
import json
import logging
import re
from datetime import timedelta

from django.core import signing
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
logger = logging.getLogger('app.booking')
CONFIRMATION_SALT = 'chat.booking-confirmation'
CONFIRMATION_MAX_AGE_SECONDS = 15 * 60
YES_ANSWERS = {
    'yes',
    'yes please',
    'yeah',
    'yep',
    'confirm',
    'confirmed',
    'book it',
    'go ahead',
    'correct',
    'okay',
    'ok',
    'please do',
}
NO_ANSWERS = {'no', 'nope', 'cancel', 'change it', 'incorrect', 'not correct'}


def default_state():
    return {field: None for field in REQUIRED_FIELDS}


def _payload_hash(state):
    payload = {field: state.get(field) for field in REQUIRED_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def _confirmation_answer(message):
    normalized = re.sub(r'[^a-z ]', '', str(message).lower()).strip()
    if normalized in YES_ANSWERS or normalized.startswith('yes '):
        return True
    if normalized in NO_ANSWERS or normalized.startswith('no '):
        return False
    return None


def _confirmation_summary(state):
    service = str(state['service_needed']).replace('_', ' ').lower()
    phone_digits = re.sub(r'\D', '', str(state['customer_phone']))
    phone_ending = phone_digits[-3:] if phone_digits else 'unknown'
    return (
        f"Book a {service} for {state['customer_name']} on "
        f"{human_date(state['appointment_date'])} at {human_time(state['appointment_time'])} "
        f"using the phone number ending in {phone_ending}? Please say yes or no."
    )


def _confirmation_token(state):
    payload = {field: state.get(field) for field in REQUIRED_FIELDS}
    return signing.dumps(payload, salt=CONFIRMATION_SALT, compress=True)


def _confirmation_is_valid(state):
    token = state.get('_booking_confirmation_token')
    if not token:
        return False
    try:
        confirmed_payload = signing.loads(
            token,
            salt=CONFIRMATION_SALT,
            max_age=CONFIRMATION_MAX_AGE_SECONDS,
        )
    except signing.BadSignature:
        return False
    current_payload = {field: state.get(field) for field in REQUIRED_FIELDS}
    return confirmed_payload == current_payload


def _request_booking_confirmation(state):
    state['awaiting_booking_confirmation'] = True
    state['_booking_confirmation_token'] = _confirmation_token(state)
    return {
        'reply': _confirmation_summary(state),
        'intent': 'book_appointment',
        'next_step': 'confirm_booking',
        'state': state,
    }


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
            logger.info(
                'booking_idempotent_replay',
                extra={'event': 'booking_idempotent_replay', 'booking_request_id': booking_request.id},
            )
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
        logger.info(
            'booking_request_reserved',
            extra={
                'event': 'booking_request_reserved',
                'booking_request_id': booking_request.id,
                'new_request': created,
            },
        )
        return booking_request, None


def _record_external_failure(booking_request, message):
    BookingRequest.objects.filter(pk=booking_request.pk).update(
        status=BookingRequest.Status.FAILED,
        error_message=message,
        updated_at=timezone.now(),
    )


def _compensate_calendar_event(booking_request, calendar_event_id):
    logger.warning(
        'calendar_compensation_started',
        extra={
            'event': 'calendar_compensation_started',
            'booking_request_id': booking_request.id,
            'calendar_event_id': calendar_event_id,
        },
    )
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
        logger.info(
            'calendar_compensation_completed',
            extra={
                'event': 'calendar_compensation_completed',
                'booking_request_id': booking_request.id,
                'result_status': result.get('status'),
            },
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
    logger.warning(
        'calendar_compensation_queued',
        extra={
            'event': 'calendar_compensation_queued',
            'booking_request_id': booking_request.id,
        },
    )
    return result


def _complete_booking(state, booking_request, calendar_event_id, n8n_result):
    logger.info(
        'database_transaction_started',
        extra={'event': 'database_transaction_started', 'booking_request_id': booking_request.id},
    )
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
            logger.info(
                'database_transaction_completed',
                extra={
                    'event': 'database_transaction_completed',
                    'booking_request_id': locked_request.id,
                    'lead_id': lead.id,
                    'appointment_id': booking.id,
                    'calendar_event_id': calendar_event_id,
                },
            )
            return response
    except IntegrityError:
        logger.warning(
            'database_slot_conflict',
            extra={'event': 'database_slot_conflict', 'booking_request_id': booking_request.id},
        )
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
    except Exception as exc:
        logger.exception(
            'database_transaction_failed',
            extra={
                'event': 'database_transaction_failed',
                'booking_request_id': booking_request.id,
                'error_type': type(exc).__name__,
            },
        )
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
    confirmation_accepted = False

    if state.get('awaiting_booking_confirmation'):
        answer = _confirmation_answer(user_message)
        if answer is False:
            state['awaiting_booking_confirmation'] = False
            state.pop('_booking_confirmation_token', None)
            return {
                'reply': 'No problem. What booking detail would you like to change?',
                'intent': 'book_appointment',
                'next_step': 'change_booking_details',
                'state': state,
            }
        if answer is not True:
            return {
                'reply': 'Please say yes to confirm this booking or no to change it.',
                'intent': 'book_appointment',
                'next_step': 'confirm_booking',
                'state': state,
            }
        if not _confirmation_is_valid(state):
            return _request_booking_confirmation(state)
        state['awaiting_booking_confirmation'] = False
        state.pop('_booking_confirmation_token', None)
        confirmation_accepted = True
        ai_result = {'intent': 'book_appointment', 'extracted_fields': {}, 'reply': ''}
    else:
        ai_result = extract_receptionist_data(user_message=user_message, state=state)

    if ai_result.get('error_status', False):
        return {**ai_result, 'error': True, 'http_status': 503}

    for key, value in ai_result.get('extracted_fields', {}).items():
        if key in REQUIRED_FIELDS and value:
            state[key] = value

    missing_fields = [field for field in REQUIRED_FIELDS if not state.get(field)]
    logger.info(
        'booking_details_processed',
        extra={
            'event': 'booking_details_processed',
            'known_fields': [field for field in REQUIRED_FIELDS if state.get(field)],
            'missing_fields': missing_fields,
        },
    )
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

    if not confirmation_accepted:
        return _request_booking_confirmation(state)

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
        logger.info(
            'booking_slot_unavailable',
            extra={
                'event': 'booking_slot_unavailable',
                'booking_request_id': booking_request.id,
                'suggested_slot_count': len(n8n_result.get('suggested_slots', [])),
            },
        )
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
        logger.warning(
            'booking_calendar_not_confirmed',
            extra={
                'event': 'booking_calendar_not_confirmed',
                'booking_request_id': booking_request.id,
                'result_status': n8n_status,
            },
        )
        return {
            'error': True,
            'error_message': 'The calendar could not confirm this booking. No local appointment was created.',
            'next_step': 'retry_booking',
            'state': state,
            'n8n_result': n8n_result,
            'http_status': 503,
        }

    return _complete_booking(state, booking_request, calendar_event_id, n8n_result)
