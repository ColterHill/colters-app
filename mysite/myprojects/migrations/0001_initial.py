# Generated by Django 5.0.6 on 2024-06-12 18:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MarketingTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('salesforce_account_id', models.CharField(blank=True, max_length=18, null=True)),
                ('campaign_code', models.CharField(blank=True, max_length=64, null=True)),
            ],
        ),
    ]
