# Generated by Django 2.1.12 on 2021-08-26 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CauseCode',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('CAUSE_CD', models.CharField(max_length=4)),
                ('CAUSE_DESC', models.CharField(blank=True, max_length=20, null=True)),
                ('CAUSE_ABBR', models.CharField(blank=True, max_length=8, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'CAUSE_CD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ConditionCode',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('CONDITION_CD', models.CharField(max_length=4)),
                ('CONDITION_DESC', models.CharField(blank=True, max_length=20, null=True)),
                ('STAT_ABBR', models.CharField(blank=True, max_length=8, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'CONDITION_CD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EqptBasicMst',
            fields=[
                ('MGT_CLS', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('FCLTY_CD', models.CharField(max_length=10)),
                ('EQPT_ID', models.CharField(max_length=10)),
                ('EQPT_DSTNCT_ID', models.CharField(max_length=10)),
                ('EQPT_STATUS', models.CharField(max_length=10)),
                ('EQPT_NM', models.CharField(max_length=10)),
                ('EQPT_FMLY', models.CharField(max_length=10)),
                ('EQPT_TP', models.CharField(max_length=10)),
            ],
            options={
                'db_table': 'EQPT_BASIC_MST',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EqptCategory',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('EQPT_FMLY', models.CharField(max_length=2)),
                ('EQPT_TP', models.CharField(max_length=3)),
                ('EQPT_CAT_NM', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'EQPT_CATEGORY',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EqptFmlyMst',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('EQPT_FMLY', models.CharField(max_length=2)),
                ('EQPT_FMLY_NM', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'EQPT_FMLY_MST',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EquipmentBasicMaster',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('FCLTY_CD', models.CharField(max_length=10)),
                ('EQPT_ID', models.CharField(max_length=20)),
                ('EQPT_DSTNCT_ID', models.CharField(blank=True, max_length=7, null=True)),
                ('EQPT_STATUS', models.CharField(blank=True, max_length=1, null=True)),
                ('EQPT_NM', models.CharField(blank=True, max_length=40, null=True)),
                ('EQPT_FMLY', models.CharField(blank=True, max_length=2, null=True)),
                ('EQPT_TP', models.CharField(blank=True, max_length=3, null=True)),
                ('PRIORITY', models.CharField(blank=True, max_length=4, null=True)),
                ('LOOP_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('RELTD_EQPT_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('PROC_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('MNTCE_METHD_CBM', models.CharField(blank=True, max_length=1, null=True)),
                ('MNTCE_METHD_TBM', models.CharField(blank=True, max_length=1, null=True)),
                ('MNTCE_METHD_BM', models.CharField(blank=True, max_length=1, null=True)),
                ('TARGET_QLTY', models.CharField(blank=True, max_length=1, null=True)),
                ('TARGET_ENVIRONMENT', models.CharField(blank=True, max_length=1, null=True)),
                ('MAKER_1', models.CharField(blank=True, max_length=10, null=True)),
                ('MAKER_2', models.CharField(blank=True, max_length=10, null=True)),
                ('MODEL_TP_1', models.CharField(blank=True, max_length=30, null=True)),
                ('MODEL_TP_2', models.CharField(blank=True, max_length=30, null=True)),
                ('DISP_METHD', models.CharField(blank=True, max_length=20, null=True)),
                ('REGULATION_CD_1', models.CharField(blank=True, max_length=5, null=True)),
                ('REGULATION_CD_2', models.CharField(blank=True, max_length=5, null=True)),
                ('REGULATION_CD_3', models.CharField(blank=True, max_length=5, null=True)),
                ('APPLD_STD_CD_1', models.CharField(blank=True, max_length=5, null=True)),
                ('APPLD_STD_CD_2', models.CharField(blank=True, max_length=5, null=True)),
                ('APPLD_STD_CD_3', models.CharField(blank=True, max_length=5, null=True)),
                ('ASSET_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('OPRTN_STRT_DTE', models.DateTimeField(blank=True, null=True)),
                ('MFG_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('MFG_DTE', models.DateTimeField(blank=True, null=True)),
                ('INSTLN_PLACE', models.CharField(blank=True, max_length=30, null=True)),
                ('INSTLN_DTE', models.DateTimeField(blank=True, null=True)),
                ('PURCH_SUB_CO_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('PURCH_DTE', models.DateTimeField(blank=True, null=True)),
                ('ACQTN_PRICE', models.IntegerField(blank=True, null=True)),
                ('ATTCH_DOC_1', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_1', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_2', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_2', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_3', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_3', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_4', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_4', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_5', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_5', models.CharField(blank=True, max_length=1000, null=True)),
                ('SUPPLEMENT_DATA_1', models.CharField(blank=True, max_length=100, null=True)),
                ('SUPPLEMENT_DATA_2', models.CharField(blank=True, max_length=100, null=True)),
                ('EQPT_IN_CHRG', models.CharField(blank=True, max_length=10, null=True)),
                ('MFG_END_DTE', models.DateTimeField(blank=True, null=True)),
                ('USER_DEFINED_1', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_2', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_3', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_4', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_5', models.CharField(blank=True, max_length=50, null=True)),
                ('UPDATE_DTE', models.DateTimeField(blank=True, null=True)),
                ('U_REGULATION_CD_5', models.CharField(blank=True, max_length=5, null=True)),
                ('U_REGULATION_CD_4', models.CharField(blank=True, max_length=5, null=True)),
                ('U_COST_CENTER', models.CharField(blank=True, max_length=10, null=True)),
                ('AP_EXCLUSION_FLG', models.CharField(blank=True, max_length=1, null=True)),
                ('U_REG_EQPT_NM', models.CharField(blank=True, max_length=30, null=True)),
                ('U_REG_AREA', models.CharField(blank=True, max_length=20, null=True)),
                ('U_E_IMPORTANCE', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'db_table': 'EQPT_BASIC_MST',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FacilityCodeMaster',
            fields=[
                ('FCLTY_CD', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('FCLTY_NM', models.CharField(blank=True, max_length=40, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
                ('FCLTY_CLS_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('FCLTY_IN_CHRGE', models.CharField(blank=True, max_length=10, null=True)),
                ('FCLTY_ABBR', models.CharField(blank=True, max_length=8, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'FCLTY_CD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FcltyCd',
            fields=[
                ('FCLTY_CD', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('FCLTY_NM', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'FCLTY_CD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MaintenanceLoger',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('FCLTY_CD', models.CharField(max_length=10)),
                ('EQPT_ID', models.CharField(max_length=20)),
                ('HIST_NO', models.IntegerField(blank=True, null=True)),
                ('EQPT_DSTNCT_ID', models.CharField(blank=True, max_length=7, null=True)),
                ('EQPT_NM', models.CharField(blank=True, max_length=40, null=True)),
                ('EQPT_FMLY', models.CharField(blank=True, max_length=2, null=True)),
                ('EQPT_TP', models.CharField(blank=True, max_length=3, null=True)),
                ('PROC_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('ASSET_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('MFG_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('LOOP_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('RELTD_EQPT_NO', models.CharField(blank=True, max_length=20, null=True)),
                ('MNTCE_MGT_NO', models.CharField(blank=True, max_length=10, null=True)),
                ('EXE_CLS', models.CharField(blank=True, max_length=4, null=True)),
                ('CYCLE_ID', models.IntegerField(blank=True, null=True)),
                ('CYCLE_STD_DTE', models.DateTimeField(blank=True, null=True)),
                ('MNTCE_NM', models.CharField(blank=True, max_length=100, null=True)),
                ('STRT_DTE', models.DateTimeField(blank=True, null=True)),
                ('COMPLTN_DTE', models.DateTimeField(blank=True, null=True)),
                ('PERSON_IN_CHRG', models.CharField(blank=True, max_length=10, null=True)),
                ('ITEM_NO', models.CharField(blank=True, max_length=12, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
                ('ATTCH_DOC_1', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_1', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_2', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_2', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_3', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_3', models.CharField(blank=True, max_length=1000, null=True)),
                ('SHELVED', models.CharField(blank=True, max_length=1, null=True)),
                ('NOTES', models.CharField(blank=True, max_length=1000, null=True)),
                ('NXT_MNTCE_REM', models.CharField(blank=True, max_length=1000, null=True)),
                ('CONDITION_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('CONDITION_POS_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('PHENOMENON_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('PHENOMENON_POS_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('CAUSE_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('CAUSE_POS_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('TREATMENT_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('TREATMENT_POS_CD', models.CharField(blank=True, max_length=10, null=True)),
                ('RESULT_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('OCRNCE_DTE', models.DateTimeField(blank=True, null=True)),
                ('OPRTN_TIME', models.IntegerField(blank=True, null=True)),
                ('DOWN_TIME', models.IntegerField(blank=True, null=True)),
                ('REPAIR_TIME', models.IntegerField(blank=True, null=True)),
                ('MH_IN_HOUSE', models.IntegerField(blank=True, null=True)),
                ('MH_SUB_CON', models.IntegerField(blank=True, null=True)),
                ('LABOR_CST', models.IntegerField(blank=True, null=True)),
                ('MATL_CST', models.IntegerField(blank=True, null=True)),
                ('USER_DEFINED_1', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_2', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_3', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_4', models.CharField(blank=True, max_length=50, null=True)),
                ('USER_DEFINED_5', models.CharField(blank=True, max_length=50, null=True)),
                ('REG_COMPLTN', models.CharField(blank=True, max_length=1, null=True)),
                ('ORDER_DESC1', models.CharField(blank=True, max_length=1000, null=True)),
                ('ORDER_DESC2', models.CharField(blank=True, max_length=1000, null=True)),
                ('ORDER_DESC3', models.CharField(blank=True, max_length=1000, null=True)),
                ('TEST_DESC', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_4', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_4', models.CharField(blank=True, max_length=1000, null=True)),
                ('ATTCH_DOC_5', models.CharField(blank=True, max_length=100, null=True)),
                ('ATTCH_FILE_5', models.CharField(blank=True, max_length=1000, null=True)),
                ('PRIORITY', models.CharField(blank=True, max_length=4, null=True)),
                ('U_MNTCE_CODE', models.CharField(blank=True, max_length=10, null=True)),
                ('U_REG_CODE', models.CharField(blank=True, max_length=10, null=True)),
                ('U_MAINTE_PERSON1', models.CharField(blank=True, max_length=10, null=True)),
                ('U_MAINTE_PERSON2', models.CharField(blank=True, max_length=10, null=True)),
                ('U_CAUS_OPT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_CAUS_MNT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_CTMS_OPT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_CTMS_MNT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_PHENOM', models.CharField(blank=True, max_length=200, null=True)),
                ('U_ADMISSION_DECISION', models.CharField(blank=True, max_length=10, null=True)),
                ('U_CONSTRUCTION_NUM', models.CharField(blank=True, max_length=10, null=True)),
                ('U_REGISTRANT', models.CharField(blank=True, max_length=30, null=True)),
                ('U_NXT_MNTCE_REM_OPT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_NXT_MNTCE_REM_MNT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_NOTES_OPT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_NOTES_MNT', models.CharField(blank=True, max_length=200, null=True)),
                ('U_PRIORITY', models.CharField(blank=True, max_length=10, null=True)),
                ('PROGRESS_CD', models.CharField(blank=True, max_length=4, null=True)),
                ('CHILD_ITEM_NO', models.CharField(blank=True, max_length=1000, null=True)),
                ('U_WORK_CODE', models.CharField(blank=True, max_length=10, null=True)),
                ('CYCLE_STD_DTE_C', models.DateTimeField(blank=True, null=True)),
                ('CYCLE_STD_DTE_P', models.DateTimeField(blank=True, null=True)),
                ('STRT_SCHED_DTE_P', models.DateTimeField(blank=True, null=True)),
                ('END_SCHED_DTE_P', models.DateTimeField(blank=True, null=True)),
                ('OPRTN_TIME_P', models.IntegerField(blank=True, null=True)),
                ('DOWN_TIME_P', models.IntegerField(blank=True, null=True)),
                ('REPAIR_TIME_P', models.IntegerField(blank=True, null=True)),
                ('MH_IN_HOUSE_P', models.IntegerField(blank=True, null=True)),
                ('MH_SUB_CON_P', models.IntegerField(blank=True, null=True)),
                ('LABOR_CST_C', models.IntegerField(blank=True, null=True)),
                ('LABOR_CST_P', models.IntegerField(blank=True, null=True)),
                ('MATL_CST_C', models.IntegerField(blank=True, null=True)),
                ('MATL_CST_P', models.IntegerField(blank=True, null=True)),
                ('UPDATE_DTE', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'MNTCE_LDGR',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MGTClassMaster',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('MGT_CLS_DESC', models.CharField(blank=True, max_length=10, null=True)),
                ('EQPT_ALIAS', models.CharField(blank=True, max_length=10, null=True)),
                ('EQPT_NM_ALIAS', models.CharField(blank=True, max_length=10, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'MGT_CLS_MST',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PhenomenonCode',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('PHENOMENON_CD', models.CharField(max_length=4)),
                ('PHENOMENON_DESC', models.CharField(blank=True, max_length=20, null=True)),
                ('PHENOMENON_ABBR', models.CharField(blank=True, max_length=8, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'PHENOMENON_CD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ResultCode',
            fields=[
                ('MGT_CLS', models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('RESULT_CD', models.CharField(max_length=4)),
                ('RESULT_DESC', models.CharField(blank=True, max_length=20, null=True)),
                ('RESULT_ABBR', models.CharField(blank=True, max_length=8, null=True)),
                ('DISP_ORDER', models.IntegerField(blank=True, null=True)),
                ('REM', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'RESULT_CD',
                'managed': False,
            },
        ),
    ]