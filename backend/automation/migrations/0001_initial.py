import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('appointment', '0004_bookingrequest_unique_appointment_slot'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_type', models.CharField(choices=[('whatsapp_confirmation', 'WhatsApp confirmation'), ('calendar_cancellation', 'Calendar cancellation')], max_length=32)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('max_attempts', models.PositiveSmallIntegerField(default=5)),
                ('run_after', models.DateTimeField(default=timezone.now)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='automation_jobs', to='appointment.appointment')),
                ('booking_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='automation_jobs', to='appointment.bookingrequest')),
            ],
            options={
                'indexes': [models.Index(fields=['status', 'run_after'], name='automation__status_805089_idx')],
                'constraints': [
                    models.UniqueConstraint(condition=models.Q(('appointment__isnull', False)), fields=('job_type', 'appointment'), name='unique_appointment_automation_job'),
                    models.UniqueConstraint(condition=models.Q(('booking_request__isnull', False)), fields=('job_type', 'booking_request'), name='unique_booking_request_automation_job'),
                ],
            },
        ),
    ]
