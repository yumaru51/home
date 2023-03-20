from django.db import models


# 管理区分マスタ   移行テーブル作成済み
class MGTClassMaster(models.Model):
    MGT_CLS = models.CharField(primary_key=True, max_length=1)
    MGT_CLS_DESC = models.CharField(max_length=10, blank=True, null=True)
    EQPT_ALIAS = models.CharField(max_length=10, blank=True, null=True)
    EQPT_NM_ALIAS = models.CharField(max_length=10, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'MGT_CLS_MST'


# 工場マスタ   移行テーブル作成済み
class FacilityCodeMaster(models.Model):
    FCLTY_CD = models.CharField(max_length=10, primary_key=True)
    FCLTY_NM = models.CharField(max_length=40, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)
    FCLTY_CLS_CD = models.CharField(max_length=10, blank=True, null=True)
    FCLTY_IN_CHRGE = models.CharField(max_length=10, blank=True, null=True)
    FCLTY_ABBR = models.CharField(max_length=8, blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FCLTY_CD'


# 状況マスタ   移行テーブル作成済み
class ConditionCode(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    CONDITION_CD = models.CharField(max_length=4)
    CONDITION_DESC = models.CharField(max_length=20, blank=True, null=True)
    STAT_ABBR = models.CharField(max_length=8, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CONDITION_CD'
        unique_together = (('MGT_CLS', 'CONDITION_CD'),)


# # 機器情報   移行テーブル作成済み
class EquipmentBasicMaster(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    FCLTY_CD = models.CharField(max_length=10)
    EQPT_ID = models.CharField(max_length=20)
    EQPT_DSTNCT_ID = models.CharField(max_length=7, blank=True, null=True)
    EQPT_STATUS = models.CharField(max_length=1, blank=True, null=True)
    EQPT_NM = models.CharField(max_length=40, blank=True, null=True)
    EQPT_FMLY = models.CharField(max_length=2, blank=True, null=True)
    EQPT_TP = models.CharField(max_length=3, blank=True, null=True)
    PRIORITY = models.CharField(max_length=4, blank=True, null=True)
    LOOP_NO = models.CharField(max_length=20, blank=True, null=True)
    RELTD_EQPT_NO = models.CharField(max_length=20, blank=True, null=True)
    PROC_CD = models.CharField(max_length=10, blank=True, null=True)
    MNTCE_METHD_CBM = models.CharField(max_length=1, blank=True, null=True)
    MNTCE_METHD_TBM = models.CharField(max_length=1, blank=True, null=True)
    MNTCE_METHD_BM = models.CharField(max_length=1, blank=True, null=True)
    TARGET_QLTY = models.CharField(max_length=1, blank=True, null=True)
    TARGET_ENVIRONMENT = models.CharField(max_length=1, blank=True, null=True)
    MAKER_1 = models.CharField(max_length=10, blank=True, null=True)
    MAKER_2 = models.CharField(max_length=10, blank=True, null=True)
    MODEL_TP_1 = models.CharField(max_length=30, blank=True, null=True)
    MODEL_TP_2 = models.CharField(max_length=30, blank=True, null=True)
    DISP_METHD = models.CharField(max_length=20, blank=True, null=True)
    REGULATION_CD_1 = models.CharField(max_length=5, blank=True, null=True)
    REGULATION_CD_2 = models.CharField(max_length=5, blank=True, null=True)
    REGULATION_CD_3 = models.CharField(max_length=5, blank=True, null=True)
    APPLD_STD_CD_1 = models.CharField(max_length=5, blank=True, null=True)
    APPLD_STD_CD_2 = models.CharField(max_length=5, blank=True, null=True)
    APPLD_STD_CD_3 = models.CharField(max_length=5, blank=True, null=True)
    ASSET_NO = models.CharField(max_length=20, blank=True, null=True)
    OPRTN_STRT_DTE = models.DateTimeField(blank=True, null=True)
    MFG_NO = models.CharField(max_length=20, blank=True, null=True)
    MFG_DTE = models.DateTimeField(blank=True, null=True)
    INSTLN_PLACE = models.CharField(max_length=30, blank=True, null=True)
    INSTLN_DTE = models.DateTimeField(blank=True, null=True)
    PURCH_SUB_CO_CD = models.CharField(max_length=10, blank=True, null=True)
    PURCH_DTE = models.DateTimeField(blank=True, null=True)
    ACQTN_PRICE = models.IntegerField(blank=True, null=True)
    ATTCH_DOC_1 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_1 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_2 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_2 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_3 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_3 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_4 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_4 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_5 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_5 = models.CharField(max_length=1000, blank=True, null=True)
    SUPPLEMENT_DATA_1 = models.CharField(max_length=100, blank=True, null=True)
    SUPPLEMENT_DATA_2 = models.CharField(max_length=100, blank=True, null=True)
    EQPT_IN_CHRG = models.CharField(max_length=10, blank=True, null=True)
    MFG_END_DTE = models.DateTimeField(blank=True, null=True)
    USER_DEFINED_1 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_2 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_3 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_4 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_5 = models.CharField(max_length=50, blank=True, null=True)
    UPDATE_DTE = models.DateTimeField(blank=True, null=True)
    U_REGULATION_CD_5 = models.CharField(max_length=5, blank=True, null=True)
    U_REGULATION_CD_4 = models.CharField(max_length=5, blank=True, null=True)
    U_COST_CENTER = models.CharField(max_length=10, blank=True, null=True)
    AP_EXCLUSION_FLG = models.CharField(max_length=1, blank=True, null=True)
    U_REG_EQPT_NM = models.CharField(max_length=30, blank=True, null=True)
    U_REG_AREA = models.CharField(max_length=20, blank=True, null=True)
    U_E_IMPORTANCE = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'EQPT_BASIC_MST'
        unique_together = (('MGT_CLS', 'FCLTY_CD', 'EQPT_ID'),)


# 原因コードマスタ   移行テーブル作成済み
class CauseCode(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    CAUSE_CD = models.CharField(max_length=4)
    CAUSE_DESC = models.CharField(max_length=20, blank=True, null=True)
    CAUSE_ABBR = models.CharField(max_length=8, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CAUSE_CD'
        unique_together = (('MGT_CLS', 'CAUSE_CD'),)


# 結果コードマスタ   移行テーブル作成済み
class ResultCode(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    RESULT_CD = models.CharField(max_length=4)
    RESULT_DESC = models.CharField(max_length=20, blank=True, null=True)
    RESULT_ABBR = models.CharField(max_length=8, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'RESULT_CD'
        unique_together = (('MGT_CLS', 'RESULT_CD'),)


# 症状コードマスタ   移行テーブル作成済み
class PhenomenonCode(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    PHENOMENON_CD = models.CharField(max_length=4)
    PHENOMENON_DESC = models.CharField(max_length=20, blank=True, null=True)
    PHENOMENON_ABBR = models.CharField(max_length=8, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'PHENOMENON_CD'
        unique_together = (('MGT_CLS', 'PHENOMENON_CD'),)


# 機器履歴情報   移行テーブル作成済み
class MaintenanceLoger(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    FCLTY_CD = models.CharField(max_length=10)
    EQPT_ID = models.CharField(max_length=20)
    HIST_NO = models.IntegerField(blank=True, null=True)
    EQPT_DSTNCT_ID = models.CharField(max_length=7, blank=True, null=True)
    EQPT_NM = models.CharField(max_length=40, blank=True, null=True)
    EQPT_FMLY = models.CharField(max_length=2, blank=True, null=True)
    EQPT_TP = models.CharField(max_length=3, blank=True, null=True)
    PROC_CD = models.CharField(max_length=10, blank=True, null=True)
    ASSET_NO = models.CharField(max_length=20, blank=True, null=True)
    MFG_NO = models.CharField(max_length=20, blank=True, null=True)
    LOOP_NO = models.CharField(max_length=20, blank=True, null=True)
    RELTD_EQPT_NO = models.CharField(max_length=20, blank=True, null=True)
    MNTCE_MGT_NO = models.CharField(max_length=10, blank=True, null=True)
    EXE_CLS = models.CharField(max_length=4, blank=True, null=True)
    CYCLE_ID = models.IntegerField(blank=True, null=True)
    CYCLE_STD_DTE = models.DateTimeField(blank=True, null=True)
    MNTCE_NM = models.CharField(max_length=100, blank=True, null=True)
    STRT_DTE = models.DateTimeField(blank=True, null=True)
    COMPLTN_DTE = models.DateTimeField(blank=True, null=True)
    PERSON_IN_CHRG = models.CharField(max_length=10, blank=True, null=True)
    ITEM_NO = models.CharField(max_length=12, blank=True, null=True)
    REM = models.CharField(max_length=200, blank=True, null=True)
    ATTCH_DOC_1 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_1 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_2 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_2 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_3 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_3 = models.CharField(max_length=1000, blank=True, null=True)
    SHELVED = models.CharField(max_length=1, blank=True, null=True)
    NOTES = models.CharField(max_length=1000, blank=True, null=True)
    NXT_MNTCE_REM = models.CharField(max_length=1000, blank=True, null=True)
    CONDITION_CD = models.CharField(max_length=4, blank=True, null=True)
    CONDITION_POS_CD = models.CharField(max_length=10, blank=True, null=True)
    PHENOMENON_CD = models.CharField(max_length=4, blank=True, null=True)
    PHENOMENON_POS_CD = models.CharField(max_length=10, blank=True, null=True)
    CAUSE_CD = models.CharField(max_length=4, blank=True, null=True)
    CAUSE_POS_CD = models.CharField(max_length=10, blank=True, null=True)
    TREATMENT_CD = models.CharField(max_length=4, blank=True, null=True)
    TREATMENT_POS_CD = models.CharField(max_length=10, blank=True, null=True)
    RESULT_CD = models.CharField(max_length=4, blank=True, null=True)
    OCRNCE_DTE = models.DateTimeField(blank=True, null=True)
    OPRTN_TIME = models.IntegerField(blank=True, null=True)
    DOWN_TIME = models.IntegerField(blank=True, null=True)
    REPAIR_TIME = models.IntegerField(blank=True, null=True)
    MH_IN_HOUSE = models.IntegerField(blank=True, null=True)
    MH_SUB_CON = models.IntegerField(blank=True, null=True)
    LABOR_CST = models.IntegerField(blank=True, null=True)
    MATL_CST = models.IntegerField(blank=True, null=True)
    USER_DEFINED_1 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_2 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_3 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_4 = models.CharField(max_length=50, blank=True, null=True)
    USER_DEFINED_5 = models.CharField(max_length=50, blank=True, null=True)
    REG_COMPLTN = models.CharField(max_length=1, blank=True, null=True)
    ORDER_DESC1 = models.CharField(max_length=1000, blank=True, null=True)
    ORDER_DESC2 = models.CharField(max_length=1000, blank=True, null=True)
    ORDER_DESC3 = models.CharField(max_length=1000, blank=True, null=True)
    TEST_DESC = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_4 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_4 = models.CharField(max_length=1000, blank=True, null=True)
    ATTCH_DOC_5 = models.CharField(max_length=100, blank=True, null=True)
    ATTCH_FILE_5 = models.CharField(max_length=1000, blank=True, null=True)
    PRIORITY = models.CharField(max_length=4, blank=True, null=True)
    U_MNTCE_CODE = models.CharField(max_length=10, blank=True, null=True)
    U_REG_CODE = models.CharField(max_length=10, blank=True, null=True)
    U_MAINTE_PERSON1 = models.CharField(max_length=10, blank=True, null=True)
    U_MAINTE_PERSON2 = models.CharField(max_length=10, blank=True, null=True)
    U_CAUS_OPT = models.CharField(max_length=200, blank=True, null=True)
    U_CAUS_MNT = models.CharField(max_length=200, blank=True, null=True)
    U_CTMS_OPT = models.CharField(max_length=200, blank=True, null=True)
    U_CTMS_MNT = models.CharField(max_length=200, blank=True, null=True)
    U_PHENOM = models.CharField(max_length=200, blank=True, null=True)
    U_ADMISSION_DECISION = models.CharField(max_length=10, blank=True, null=True)
    U_CONSTRUCTION_NUM = models.CharField(max_length=10, blank=True, null=True)
    U_REGISTRANT = models.CharField(max_length=30, blank=True, null=True)
    U_NXT_MNTCE_REM_OPT = models.CharField(max_length=200, blank=True, null=True)
    U_NXT_MNTCE_REM_MNT = models.CharField(max_length=200, blank=True, null=True)
    U_NOTES_OPT = models.CharField(max_length=200, blank=True, null=True)
    U_NOTES_MNT = models.CharField(max_length=200, blank=True, null=True)
    U_PRIORITY = models.CharField(max_length=10, blank=True, null=True)
    PROGRESS_CD = models.CharField(max_length=4, blank=True, null=True)
    CHILD_ITEM_NO = models.CharField(max_length=1000, blank=True, null=True)
    U_WORK_CODE = models.CharField(max_length=10, blank=True, null=True)
    CYCLE_STD_DTE_C = models.DateTimeField(blank=True, null=True)
    CYCLE_STD_DTE_P = models.DateTimeField(blank=True, null=True)
    STRT_SCHED_DTE_P = models.DateTimeField(blank=True, null=True)
    END_SCHED_DTE_P = models.DateTimeField(blank=True, null=True)
    OPRTN_TIME_P = models.IntegerField(blank=True, null=True)
    DOWN_TIME_P = models.IntegerField(blank=True, null=True)
    REPAIR_TIME_P = models.IntegerField(blank=True, null=True)
    MH_IN_HOUSE_P = models.IntegerField(blank=True, null=True)
    MH_SUB_CON_P = models.IntegerField(blank=True, null=True)
    LABOR_CST_C = models.IntegerField(blank=True, null=True)
    LABOR_CST_P = models.IntegerField(blank=True, null=True)
    MATL_CST_C = models.IntegerField(blank=True, null=True)
    MATL_CST_P = models.IntegerField(blank=True, null=True)
    UPDATE_DTE = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'MNTCE_LDGR'
        unique_together = (('MGT_CLS', 'FCLTY_CD', 'EQPT_ID', 'HIST_NO'),)


# 機器ファミリマスタ   移行テーブル作成済み
class EqptFmlyMst(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    EQPT_FMLY = models.CharField(max_length=2)
    EQPT_FMLY_NM = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'EQPT_FMLY_MST'
        unique_together = (('MGT_CLS', 'EQPT_FMLY'),)


# PLANTIAの機器型マスタ   移行テーブル作成済み(機器ファミリマスタEqptFmlyMstと統合)
class EqptCategory(models.Model):
    MGT_CLS = models.CharField(max_length=1, primary_key=True)
    EQPT_FMLY = models.CharField(max_length=2)
    EQPT_TP = models.CharField(max_length=3)
    EQPT_CAT_NM = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'EQPT_CATEGORY'
        unique_together = (('MGT_CLS', 'EQPT_FMLY'),)


# PLANTIA設備工程マスタ   移行テーブル作成済み(FacilityCodeMaster)
class FcltyCd(models.Model):
    FCLTY_CD = models.CharField(max_length=10, primary_key=True)
    FCLTY_NM = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'FCLTY_CD'
        unique_together = ('FCLTY_CD',)


# PLANTIA機器リスト   移行テーブル作成済み(EquipmentBasicMaster)
class EqptBasicMst(models.Model):
    MGT_CLS = models.CharField(max_length=10, primary_key=True)
    FCLTY_CD = models.CharField(max_length=10)
    EQPT_ID = models.CharField(max_length=10)
    EQPT_DSTNCT_ID = models.CharField(max_length=10)
    EQPT_STATUS = models.CharField(max_length=10)
    EQPT_NM = models.CharField(max_length=10)
    EQPT_FMLY = models.CharField(max_length=10)
    EQPT_TP = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'EQPT_BASIC_MST'
        unique_together = (('MGT_CLS', 'FCLTY_CD', 'EQPT_ID'),)


