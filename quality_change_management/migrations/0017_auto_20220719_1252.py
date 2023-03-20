# Generated by Django 2.1.12 on 2022-07-19 03:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quality_change_management', '0016_auto_20220719_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='steppageentrymaster',
            name='item',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='項目'),
        ),
        migrations.AddField(
            model_name='steppageentrymaster',
            name='target',
            field=models.ForeignKey(default='request', max_length=20, on_delete=django.db.models.deletion.PROTECT, to='quality_change_management.TargetMaster', verbose_name='対象'),
            preserve_default=False,
        ),
    ]
