from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('automation', '0002_alter_automationjob_job_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationWorkerHeartbeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default', max_length=64, unique=True)),
                ('last_seen_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
