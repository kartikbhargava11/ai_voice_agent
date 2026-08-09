from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('appointment', '0004_bookingrequest_unique_appointment_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[
                    ('SCHEDULED', 'Scheduled'),
                    ('ATTENDED', 'Attended'),
                    ('MISSED', 'Missed'),
                ],
                default='SCHEDULED',
                max_length=12,
            ),
        ),
    ]
