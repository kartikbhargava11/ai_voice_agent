import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('appointment', '0003_remove_appointment_status'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='appointment',
            constraint=models.UniqueConstraint(
                fields=('appointment_date', 'appointment_time'),
                name='unique_appointment_slot',
            ),
        ),
        migrations.CreateModel(
            name='BookingRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idempotency_key', models.CharField(max_length=128, unique=True)),
                ('payload_hash', models.CharField(max_length=64)),
                ('status', models.CharField(choices=[('processing', 'Processing'), ('unavailable', 'Unavailable'), ('failed', 'Failed'), ('completed', 'Completed'), ('compensation_required', 'Compensation required')], default='processing', max_length=32)),
                ('calendar_event_id', models.CharField(blank=True, max_length=255, null=True)),
                ('response_data', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='booking_request', to='appointment.appointment')),
            ],
        ),
    ]
