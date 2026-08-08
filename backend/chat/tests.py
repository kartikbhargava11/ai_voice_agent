import json
import logging
from unittest.mock import patch

from django.test import TestCase

from appointment.models import Appointment, BookingRequest
from automation.models import AutomationJob
from leads.models import Lead
from mysite.observability import JsonFormatter

from .services import handle_chat_message


COMPLETE_STATE = {
    'customer_name': 'Ada Lovelace',
    'customer_phone': '9999999999',
    'service_needed': 'DENTAL CHECKUP',
    'appointment_date': '2030-01-10',
    'appointment_time': '10:00',
}


def ai_result():
    return {
        'intent': 'book_appointment',
        'extracted_fields': {},
        'reply': 'Let me check that slot.',
    }


class LoggingPrivacyTests(TestCase):
    def test_json_formatter_masks_phone_and_credentials(self):
        record = logging.LogRecord(
            name='app.test',
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg='privacy_check',
            args=(),
            exc_info=None,
        )
        record.event = 'privacy_check'
        record.customer_phone = '+49 1234 567890'
        record.access_token = 'never-log-this'

        result = json.loads(JsonFormatter().format(record))

        self.assertEqual(result['customer_phone'], '******7890')
        self.assertEqual(result['access_token'], '[REDACTED]')


class BookingWorkflowTests(TestCase):
    @patch('chat.services.extract_receptionist_data', return_value=ai_result())
    @patch('chat.services.check_calendar_availability_with_n8n')
    def test_n8n_failure_never_creates_or_confirms_booking(self, n8n, _extract):
        n8n.return_value = {'status': 'failed', 'error_message': 'timeout'}

        result = handle_chat_message('book it', COMPLETE_STATE.copy(), 'request-1')

        self.assertTrue(result['error'])
        self.assertEqual(result['http_status'], 503)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(Appointment.objects.count(), 0)
        self.assertEqual(
            BookingRequest.objects.get(idempotency_key='request-1').status,
            BookingRequest.Status.FAILED,
        )

    @patch('chat.services.extract_receptionist_data', return_value=ai_result())
    @patch('chat.services.check_calendar_availability_with_n8n')
    def test_success_requires_calendar_event_id(self, n8n, _extract):
        n8n.return_value = {'status': 'available'}

        result = handle_chat_message('book it', COMPLETE_STATE.copy(), 'request-2')

        self.assertTrue(result['error'])
        self.assertEqual(Appointment.objects.count(), 0)

    @patch('chat.services.extract_receptionist_data', return_value=ai_result())
    @patch('chat.services.check_calendar_availability_with_n8n')
    def test_completed_request_is_idempotently_replayed(self, n8n, _extract):
        n8n.return_value = {'status': 'available', 'calendar_event_id': 'event-1'}

        first = handle_chat_message('book it', COMPLETE_STATE.copy(), 'request-3')
        second = handle_chat_message('book it again', COMPLETE_STATE.copy(), 'request-3')

        self.assertEqual(first['next_step'], 'booking_completed')
        self.assertTrue(second['idempotent_replay'])
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(AutomationJob.objects.count(), 2)
        self.assertTrue(
            AutomationJob.objects.filter(job_type=AutomationJob.JobType.CRM_SYNC).exists()
        )
        n8n.assert_called_once()

    @patch('chat.services.extract_receptionist_data', return_value=ai_result())
    @patch('chat.services.cancel_calendar_event_with_n8n')
    @patch('chat.services.check_calendar_availability_with_n8n')
    def test_slot_race_rolls_back_and_compensates(self, n8n, cancel, _extract):
        existing_lead = Lead.objects.create(
            customer_name='Existing',
            customer_phone='8888888888',
            service_needed='DENTAL CHECKUP',
        )
        Appointment.objects.create(
            lead=existing_lead,
            appointment_date='2030-01-10',
            appointment_time='10:00',
            calendar_event_id='existing-event',
        )
        n8n.return_value = {'status': 'available', 'calendar_event_id': 'duplicate-event'}
        cancel.return_value = {'status': 'cancelled'}

        result = handle_chat_message('book it', COMPLETE_STATE.copy(), 'request-4')

        self.assertEqual(result['http_status'], 409)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Lead.objects.count(), 1)
        cancel.assert_called_once_with(
            calendar_event_id='duplicate-event',
            idempotency_key='request-4',
        )

    @patch('chat.services.extract_receptionist_data', return_value=ai_result())
    @patch('chat.services.cancel_calendar_event_with_n8n')
    @patch('chat.services.check_calendar_availability_with_n8n')
    def test_failed_compensation_is_queued_for_retry(self, n8n, cancel, _extract):
        existing_lead = Lead.objects.create(
            customer_name='Existing',
            customer_phone='8888888888',
            service_needed='DENTAL CHECKUP',
        )
        Appointment.objects.create(
            lead=existing_lead,
            appointment_date='2030-01-10',
            appointment_time='10:00',
        )
        n8n.return_value = {'status': 'available', 'calendar_event_id': 'duplicate-event'}
        cancel.return_value = {'status': 'failed', 'error_message': 'n8n unavailable'}

        handle_chat_message('book it', COMPLETE_STATE.copy(), 'request-5')

        booking_request = BookingRequest.objects.get(idempotency_key='request-5')
        self.assertEqual(booking_request.status, BookingRequest.Status.COMPENSATION_REQUIRED)
        self.assertTrue(
            AutomationJob.objects.filter(
                job_type=AutomationJob.JobType.CALENDAR_CANCELLATION,
                booking_request=booking_request,
                status=AutomationJob.Status.PENDING,
            ).exists()
        )
