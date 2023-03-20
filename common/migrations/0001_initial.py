# Generated by Django 2.1.12 on 2022-02-28 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessYearMaster',
            fields=[
                ('business_year', models.IntegerField(primary_key=True, serialize=False, verbose_name='年度')),
                ('display_flag', models.IntegerField(blank=True, null=True, verbose_name='表示FL')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
            ],
        ),
        migrations.CreateModel(
            name='DepartmentMaster',
            fields=[
                ('department_cd', models.CharField(max_length=10, primary_key=True, serialize=False, verbose_name='部署CD')),
                ('department_name', models.CharField(blank=True, max_length=20, null=True, verbose_name='部署名')),
                ('division_cd', models.CharField(blank=True, max_length=10, null=True, verbose_name='部門CD')),
                ('display_order', models.IntegerField(blank=True, null=True, verbose_name='表示順')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
            ],
        ),
        migrations.CreateModel(
            name='DivisionMaster',
            fields=[
                ('division_cd', models.CharField(max_length=10, primary_key=True, serialize=False, verbose_name='部門CD')),
                ('division_name', models.CharField(blank=True, max_length=20, null=True, verbose_name='部門名')),
                ('display_order', models.IntegerField(blank=True, null=True, verbose_name='表示順')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
            ],
        ),
        migrations.CreateModel(
            name='PeriodClassMaster',
            fields=[
                ('period_class_cd', models.IntegerField(primary_key=True, serialize=False, verbose_name='期CD')),
                ('period_class_name', models.CharField(blank=True, max_length=20, null=True, verbose_name='期区分名')),
                ('display_order', models.IntegerField(blank=True, null=True, verbose_name='表示順')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
            ],
        ),
        migrations.CreateModel(
            name='UserAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=150, null=True, verbose_name='ユーザー名')),
                ('department', models.CharField(blank=True, max_length=10, null=True, verbose_name='部署')),
                ('division', models.CharField(blank=True, max_length=10, null=True, verbose_name='部門')),
                ('authority', models.CharField(blank=True, max_length=10, null=True, verbose_name='権限')),
                ('confirm_username', models.CharField(blank=True, max_length=150, null=True, verbose_name='確認者')),
                ('permit_username', models.CharField(blank=True, max_length=150, null=True, verbose_name='承認者')),
                ('lost_flag', models.IntegerField(blank=True, null=True, verbose_name='無効FL')),
                ('display_order', models.IntegerField(blank=True, null=True, verbose_name='表示順')),
            ],
        ),
    ]