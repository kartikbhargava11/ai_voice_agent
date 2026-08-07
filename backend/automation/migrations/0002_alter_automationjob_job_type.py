from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('automation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automationjob',
            name='job_type',
            field=models.CharField(
                choices=[
                    ('whatsapp_confirmation', 'WhatsApp confirmation'),
                    ('crm_sync', 'CRM sync'),
                    ('calendar_cancellation', 'Calendar cancellation'),
                ],
                max_length=32,
            ),
        ),
    ]
