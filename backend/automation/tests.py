from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from appointment.models import Appointment
from leads.models import Lead

from .jobs import process_next_job
from .models import AutomationJob
from .services import check_calendar_availability_with_n8n


class N8nResponseTests(TestCase):
    @patch('automation.services.requests.post')
    def test_empty_n8n_response_is_a_controlled_failure(self, post):
        response = post.return_value
        response.content = b''
        response.text = ''
        response.raise_for_status.return_value = None

        result = check_calendar_availability_with_n8n(
            {
                'customer_name': 'Test',
                'customer_phone': '1234567890',
                'service_needed': 'DENTAL CHECKUP',
                'appointment_date': '2030-01-01',
                'appointment_time': '10:00',
            },
            'request-key',
        )

        self.assertEqual(result['status'], 'failed')
        self.assertIn('empty response', result['error_message'])

    @patch('automation.services.requests.post')
    def test_non_json_n8n_response_is_a_controlled_failure(self, post):
        response = post.return_value
        response.content = b'Webhook received'
        response.text = 'Webhook received'
        response.headers = {'Content-Type': 'text/plain'}
        response.raise_for_status.return_value = None
        response.json.side_effect = ValueError('not JSON')

        result = check_calendar_availability_with_n8n(
            {
                'customer_name': 'Test',
                'customer_phone': '1234567890',
                'service_needed': 'DENTAL CHECKUP',
                'appointment_date': '2030-01-01',
                'appointment_time': '10:00',
            },
            'request-key',
        )

        self.assertEqual(result['status'], 'failed')
        self.assertIn('non-JSON', result['error_message'])


class AutomationJobTests(TestCase):
    def setUp(self):
        lead = Lead.objects.create(
            customer_name='Grace Hopper',
            customer_phone='7777777777',
            service_needed='DENTAL CHECKUP',
        )
        self.appointment = Appointment.objects.create(
            lead=lead,
            appointment_date='2030-02-10',
            appointment_time='11:00',
        )

    @patch('automation.jobs.send_whatsapp_confirmation')
    def test_failed_job_is_retried_with_backoff(self, send):
        send.return_value = {'status': 'failed', 'error_message': 'temporary error'}
        job = AutomationJob.objects.create(
            job_type=AutomationJob.JobType.WHATSAPP_CONFIRMATION,
            appointment=self.appointment,
            run_after=timezone.now(),
        )

        self.assertTrue(process_next_job())

        job.refresh_from_db()
        self.assertEqual(job.status, AutomationJob.Status.PENDING)
        self.assertEqual(job.attempts, 1)
        self.assertGreater(job.run_after, timezone.now())

    @patch('automation.jobs.send_whatsapp_confirmation')
    def test_successful_job_is_completed(self, send):
        send.return_value = {'messages': [{'id': 'message-1'}]}
        job = AutomationJob.objects.create(
            job_type=AutomationJob.JobType.WHATSAPP_CONFIRMATION,
            appointment=self.appointment,
            run_after=timezone.now(),
        )

        self.assertTrue(process_next_job())

        job.refresh_from_db()
        self.assertEqual(job.status, AutomationJob.Status.COMPLETED)
        self.assertEqual(job.attempts, 1)

    @patch('automation.jobs.send_whatsapp_confirmation')
    def test_stale_processing_job_is_recovered(self, send):
        send.return_value = {'messages': [{'id': 'message-1'}]}
        job = AutomationJob.objects.create(
            job_type=AutomationJob.JobType.WHATSAPP_CONFIRMATION,
            appointment=self.appointment,
            status=AutomationJob.Status.PROCESSING,
            run_after=timezone.now() - timedelta(minutes=10),
        )
        AutomationJob.objects.filter(pk=job.pk).update(
            updated_at=timezone.now() - timedelta(minutes=10)
        )

        self.assertTrue(process_next_job())

        job.refresh_from_db()
        self.assertEqual(job.status, AutomationJob.Status.COMPLETED)
        self.assertEqual(job.attempts, 1)
