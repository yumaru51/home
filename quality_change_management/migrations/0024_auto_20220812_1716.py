# Generated by Django 2.1.12 on 2022-08-12 08:16

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality_change_management', '0023_request_application_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='education_management_system_id',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='教育管理システムID'),
        ),
        migrations.AlterField(
            model_name='request',
            name='application_date',
            field=models.DateField(blank=True, default=datetime.datetime(2022, 8, 12, 17, 16, 1, 903758), null=True, verbose_name='申請日'),
        ),
    ]
