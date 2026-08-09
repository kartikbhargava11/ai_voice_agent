from django.test import TestCase

from leads.models import Lead

from .services import handle_booking
from .serializers import AppointmentSerializer


class LeadConversionTests(TestCase):
    def test_creating_appointment_marks_lead_converted(self):
        lead = Lead.objects.create(
            customer_name='Test Lead',
            customer_phone='9999999999',
            service_needed=Lead.ServiceList.DENTAL_CHECKUP,
            lead_source=Lead.SourceList.WEB_CHAT,
        )

        handle_booking(lead, '2030-08-24', '14:30', 'calendar-event')

        lead.refresh_from_db()
        self.assertEqual(lead.status, Lead.Status.CONVERTED)


class AppointmentStatusTests(TestCase):
    def setUp(self):
        lead = Lead.objects.create(
            customer_name='Appointment Status Lead',
            customer_phone='7777777777',
            service_needed=Lead.ServiceList.DENTAL_CHECKUP,
        )
        self.appointment = handle_booking(lead, '2030-08-25', '14:30')

    def test_new_appointment_is_scheduled(self):
        self.assertEqual(
            self.appointment.status,
            self.appointment.Status.SCHEDULED,
        )

    def test_appointment_can_be_marked_attended_and_saved(self):
        serializer = AppointmentSerializer(
            self.appointment,
            data={'status': self.appointment.Status.ATTENDED},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.appointment.refresh_from_db()
        self.assertEqual(
            self.appointment.status,
            self.appointment.Status.ATTENDED,
        )

    def test_appointment_can_be_marked_missed_and_saved(self):
        serializer = AppointmentSerializer(
            self.appointment,
            data={'status': self.appointment.Status.MISSED},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.appointment.refresh_from_db()
        self.assertEqual(
            self.appointment.status,
            self.appointment.Status.MISSED,
        )
