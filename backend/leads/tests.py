from django.test import TestCase

from .models import Lead
from .serializers import LeadSerializer


class LeadStatusTests(TestCase):
    def setUp(self):
        self.lead = Lead.objects.create(
            customer_name='Unconverted Lead',
            customer_phone='8888888888',
            service_needed=Lead.ServiceList.TEETH_CLEANING,
            lead_source=Lead.SourceList.MANUAL,
        )

    def test_unconverted_lead_can_be_marked_lost(self):
        serializer = LeadSerializer(
            self.lead,
            data={'status': Lead.Status.LOST},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.LOST)

    def test_lead_cannot_be_manually_marked_converted(self):
        serializer = LeadSerializer(
            self.lead,
            data={'status': Lead.Status.CONVERTED},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
