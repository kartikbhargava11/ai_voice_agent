from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from automation.models import AutomationWorkerHeartbeat


class Command(BaseCommand):
    help = 'Exit successfully when the automation worker heartbeat is fresh.'

    def handle(self, *args, **options):
        stale_before = timezone.now() - timedelta(
            seconds=settings.AUTOMATION_WORKER_STALE_SECONDS
        )
        if not AutomationWorkerHeartbeat.objects.filter(
            name='default',
            last_seen_at__gte=stale_before,
        ).exists():
            raise CommandError('Automation worker heartbeat is stale or missing.')
        self.stdout.write('Automation worker is healthy.')
