from django.db import migrations, models


def mark_existing_bookings_converted(apps, schema_editor):
    Lead = apps.get_model('leads', 'Lead')
    Lead.objects.filter(appointment__isnull=False).update(status='CONVERTED')


class Migration(migrations.Migration):
    dependencies = [
        ('appointment', '0004_bookingrequest_unique_appointment_slot'),
        ('leads', '0005_lead_lead_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='status',
            field=models.CharField(
                choices=[
                    ('NEW', 'New'),
                    ('CONVERTED', 'Converted'),
                    ('LOST', 'Lost'),
                ],
                default='NEW',
                max_length=12,
            ),
        ),
        migrations.RunPython(mark_existing_bookings_converted, migrations.RunPython.noop),
    ]
