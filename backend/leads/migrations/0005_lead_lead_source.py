from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('leads', '0004_remove_lead_lead_score_remove_lead_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='lead_source',
            field=models.CharField(
                choices=[
                    ('WEB_VOICE', 'Web voice assistant'),
                    ('WEB_CHAT', 'Web chat'),
                    ('PHONE', 'Phone call'),
                    ('MANUAL', 'Manual entry'),
                ],
                default='WEB_VOICE',
                max_length=20,
            ),
        ),
    ]
