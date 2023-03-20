# Generated by Django 2.1.12 on 2022-07-19 03:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quality_change_management', '0015_actionmaster_progress_transition'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quality_aspect', models.CharField(blank=True, max_length=40, null=True, verbose_name='所管評価レベル')),
                ('judgement', models.CharField(blank=True, max_length=40, null=True, verbose_name='判定')),
                ('results', models.CharField(blank=True, max_length=200, null=True, verbose_name='対策検討結果')),
                ('evaluation', models.CharField(blank=True, max_length=200, null=True, verbose_name='変更結果評価')),
            ],
            options={
                'db_table': 't_quality',
            },
        ),
        migrations.CreateModel(
            name='Safety',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('safety_aspect', models.CharField(blank=True, max_length=40, null=True, verbose_name='所管評価レベル')),
                ('judgement', models.CharField(blank=True, max_length=40, null=True, verbose_name='判定')),
                ('results', models.CharField(blank=True, max_length=200, null=True, verbose_name='対策検討結果')),
                ('evaluation', models.CharField(blank=True, max_length=200, null=True, verbose_name='変更結果評価')),
            ],
            options={
                'db_table': 't_safety',
            },
        ),
        migrations.AddField(
            model_name='request',
            name='delivery_date_end',
            field=models.DateField(blank=True, max_length=40, null=True, verbose_name='変更日終了'),
        ),
        migrations.AddField(
            model_name='request',
            name='delivery_date_start',
            field=models.DateField(blank=True, max_length=40, null=True, verbose_name='変更日開始'),
        ),
        migrations.AddField(
            model_name='request',
            name='level2',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='継続/一過性'),
        ),
        migrations.AddField(
            model_name='request',
            name='others2',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='その他'),
        ),
        migrations.AddField(
            model_name='safety',
            name='request',
            field=models.ForeignKey(max_length=20, on_delete=django.db.models.deletion.PROTECT, to='quality_change_management.Request', verbose_name='依頼ID'),
        ),
        migrations.AddField(
            model_name='quality',
            name='request',
            field=models.ForeignKey(max_length=20, on_delete=django.db.models.deletion.PROTECT, to='quality_change_management.Request', verbose_name='依頼ID'),
        ),
    ]
