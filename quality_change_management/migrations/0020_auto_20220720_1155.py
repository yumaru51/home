# Generated by Django 2.1.12 on 2022-07-20 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality_change_management', '0019_auto_20220719_1401'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntryMaster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target', models.CharField(blank=True, max_length=20, null=True, verbose_name='対象')),
                ('item', models.CharField(blank=True, max_length=40, null=True, verbose_name='項目')),
                ('item_type', models.CharField(blank=True, max_length=40, null=True, verbose_name='項目種類')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
            ],
            options={
                'db_table': 'm_entry',
            },
        ),
        migrations.RenameModel(
            old_name='StepDisplayItem',
            new_name='StepDisplayPage',
        ),
        migrations.RemoveField(
            model_name='steppageentrymaster',
            name='item_type',
        ),
        migrations.AddField(
            model_name='steppageentrymaster',
            name='entry',
            field=models.IntegerField(blank=True, null=True, verbose_name='入力FL'),
        ),
        migrations.AlterModelTable(
            name='stepdisplaypage',
            table='m_step_display_page',
        ),
    ]