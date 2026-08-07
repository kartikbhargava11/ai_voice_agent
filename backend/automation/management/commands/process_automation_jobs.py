import time

from django.core.management.base import BaseCommand

from automation.jobs import process_next_job


class Command(BaseCommand):
    help = 'Process durable retryable automation jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true')
        parser.add_argument('--poll-seconds', type=float, default=5.0)

    def handle(self, *args, **options):
        while True:
            processed = process_next_job()
            if not options['loop']:
                break
            if not processed:
                time.sleep(options['poll_seconds'])
