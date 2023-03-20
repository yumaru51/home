from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


# 管理区分マスタ
class MGTClassMaster(models.Model):
    MGT_CLS = models.CharField(primary_key=True, max_length=1)
    MGT_CLS_DESC = models.CharField(max_length=10, blank=True, null=True)
    EQPT_ALIAS = models.CharField(max_length=10, blank=True, null=True)
    EQPT_NM_ALIAS = models.CharField(max_length=10, blank=True, null=True)
    DISP_ORDER = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'MGT_CLS_MST'


# 工場マスタ
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


# 状況マスタ
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


# # 機器情報
# class EquipmentBasicMaster(models.Model):
#     MGT_CLS = models.CharField(max_length=1, primary_key=True)
#     FCLTY_CD = models.CharField(max_length=10)
#     EQPT_ID = models.CharField(max_length=20)
#     EQPT_DSTNCT_ID = models.CharField(max_length=7, blank=True, null=True)
#     EQPT_STATUS = models.CharField(max_length=1, blank=True, null=True)
#     EQPT_NM = models.CharField(max_length=40, blank=True, null=True)
#     EQPT_FMLY = models.CharField(max_length=2, blank=True, null=True)
#     EQPT_TP = models.CharField(max_length=3, blank=True, null=True)
#     PRIORITY = models.CharField(max_length=4, blank=True, null=True)
#     LOOP_NO = models.CharField(max_length=20, blank=True, null=True)
#     RELTD_EQPT_NO = models.CharField(max_length=20, blank=True, null=True)
#     PROC_CD = models.CharField(max_length=10, blank=True, null=True)
#     MNTCE_METHD_CBM = models.CharField(max_length=1, blank=True, null=True)
#     MNTCE_METHD_TBM = models.CharField(max_length=1, blank=True, null=True)
#     MNTCE_METHD_BM = models.CharField(max_length=1, blank=True, null=True)
#     TARGET_QLTY = models.CharField(max_length=1, blank=True, null=True)
#     TARGET_ENVIRONMENT = models.CharField(max_length=1, blank=True, null=True)
#     MAKER_1 = models.CharField(max_length=10, blank=True, null=True)
#     MAKER_2 = models.CharField(max_length=10, blank=True, null=True)
#     MODEL_TP_1 = models.CharField(max_length=30, blank=True, null=True)
#     MODEL_TP_2 = models.CharField(max_length=30, blank=True, null=True)
#     DISP_METHD = models.CharField(max_length=20, blank=True, null=True)
#     REGULATION_CD_1 = models.CharField(max_length=5, blank=True, null=True)
#     REGULATION_CD_2 = models.CharField(max_length=5, blank=True, null=True)
#     REGULATION_CD_3 = models.CharField(max_length=5, blank=True, null=True)
#     APPLD_STD_CD_1 = models.CharField(max_length=5, blank=True, null=True)
#     APPLD_STD_CD_2 = models.CharField(max_length=5, blank=True, null=True)
#     APPLD_STD_CD_3 = models.CharField(max_length=5, blank=True, null=True)
#     ASSET_NO = models.CharField(max_length=20, blank=True, null=True)
#     OPRTN_STRT_DTE = models.DateTimeField(blank=True, null=True)
#     MFG_NO = models.CharField(max_length=20, blank=True, null=True)
#     MFG_DTE = models.DateTimeField(blank=True, null=True)
#     INSTLN_PLACE = models.CharField(max_length=30, blank=True, null=True)
#     INSTLN_DTE = models.DateTimeField(blank=True, null=True)
#     PURCH_SUB_CO_CD = models.CharField(max_length=10, blank=True, null=True)
#     PURCH_DTE = models.DateTimeField(blank=True, null=True)
#     ACQTN_PRICE = models.IntegerField(blank=True, null=True)
#     ATTCH_DOC_1 = models.CharField(max_length=100, blank=True, null=True)
#     ATTCH_FILE_1 = models.CharField(max_length=1000, blank=True, null=True)
#     ATTCH_DOC_2 = models.CharField(max_length=100, blank=True, null=True)
#     ATTCH_FILE_2 = models.CharField(max_length=1000, blank=True, null=True)
#     ATTCH_DOC_3 = models.CharField(max_length=100, blank=True, null=True)
#     ATTCH_FILE_3 = models.CharField(max_length=1000, blank=True, null=True)
#     ATTCH_DOC_4 = models.CharField(max_length=100, blank=True, null=True)
#     ATTCH_FILE_4 = models.CharField(max_length=1000, blank=True, null=True)
#     ATTCH_DOC_5 = models.CharField(max_length=100, blank=True, null=True)
#     ATTCH_FILE_5 = models.CharField(max_length=1000, blank=True, null=True)
#     SUPPLEMENT_DATA_1 = models.CharField(max_length=100, blank=True, null=True)
#     SUPPLEMENT_DATA_2 = models.CharField(max_length=100, blank=True, null=True)
#     EQPT_IN_CHRG = models.CharField(max_length=10, blank=True, null=True)
#     MFG_END_DTE = models.DateTimeField(blank=True, null=True)
#     USER_DEFINED_1 = models.CharField(max_length=50, blank=True, null=True)
#     USER_DEFINED_2 = models.CharField(max_length=50, blank=True, null=True)
#     USER_DEFINED_3 = models.CharField(max_length=50, blank=True, null=True)
#     USER_DEFINED_4 = models.CharField(max_length=50, blank=True, null=True)
#     USER_DEFINED_5 = models.CharField(max_length=50, blank=True, null=True)
#     UPDATE_DTE = models.DateTimeField(blank=True, null=True)
#     U_REGULATION_CD_5 = models.CharField(max_length=5, blank=True, null=True)
#     U_REGULATION_CD_4 = models.CharField(max_length=5, blank=True, null=True)
#     U_COST_CENTER = models.CharField(max_length=10, blank=True, null=True)
#     AP_EXCLUSION_FLG = models.CharField(max_length=1, blank=True, null=True)
#     U_REG_EQPT_NM = models.CharField(max_length=30, blank=True, null=True)
#     U_REG_AREA = models.CharField(max_length=20, blank=True, null=True)
#     U_E_IMPORTANCE = models.CharField(max_length=30, blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'EQPT_BASIC_MST'
#         unique_together = (('MGT_CLS', 'FCLTY_CD', 'EQPT_ID'),)


# 設備台帳基本仕様テーブル(機器情報)
class FcltyLdgr(models.Model):
    t_fclty_ldgr_skey = models.DecimalField(max_digits=38, blank=False, null=False, primary_key=True)
    m_site_skey = models.DecimalField(max_digits=38, blank=False, null=False)
    m_mgt_cls_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_location_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    eqpt_id = models.CharField(max_length=20, blank=True, null=True)
    fclty_dstnct_id = models.CharField(max_length=9, blank=False, null=False)
    parent_t_fclty_ldgr_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_fclty_ctg_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_fnc_ctg_1_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_fnc_ctg_2_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_fnc_ctg_3_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_priority_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    m_proc_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    fclty_status = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    m_repair_status_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    spare_fclty_flg = models.DecimalField(max_digits=1, blank=True, null=True)
    mntce_methd_cbm = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    mntce_methd_tbm = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    mntce_methd_bm = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    target_qlty = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    target_environment = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    fclty_nm = models.CharField(max_length=40, blank=True, null=True)
    loop_no = models.CharField(max_length=20, blank=True, null=True)
    reltd_fclty_no = models.CharField(max_length=20, blank=True, null=True)
    display_specs = models.CharField(max_length=20, blank=True, null=True)
    maker_1_m_cmpny_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    maker_2_m_cmpny_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    model_1 = models.CharField(max_length=30, blank=True, null=True)
    model_2 = models.CharField(max_length=30, blank=True, null=True)
    regulation_cd_1_m_regulation_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    regulation_cd_2_m_regulation_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    regulation_cd_3_m_regulation_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    applied_std_cd_1_m_applied_std_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    applied_std_cd_2_m_applied_std_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    applied_std_cd_3_m_applied_std_cd_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    asset_no = models.CharField(max_length=20, blank=True, null=True)
    oprtn_start_date = models.DateTimeField(blank=True, null=True)
    mfg_no = models.CharField(max_length=20, blank=True, null=True)
    mfg_date = models.DateTimeField(blank=True, null=True)
    instln_place = models.CharField(max_length=30, blank=True, null=True)
    instln_date = models.DateTimeField(blank=True, null=True)
    purch_sub_co_m_cmpny_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    purch_date = models.DateTimeField(blank=True, null=True)
    acqtn_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    attch_doc_1 = models.CharField(max_length=100, blank=True, null=True)
    attch_file_1 = models.CharField(max_length=512, blank=True, null=True)
    attch_doc_2 = models.CharField(max_length=100, blank=True, null=True)
    attch_file_2 = models.CharField(max_length=512, blank=True, null=True)
    attch_doc_3 = models.CharField(max_length=100, blank=True, null=True)
    attch_file_3 = models.CharField(max_length=512, blank=True, null=True)
    attch_doc_4 = models.CharField(max_length=100, blank=True, null=True)
    attch_file_4 = models.CharField(max_length=512, blank=True, null=True)
    attch_doc_5 = models.CharField(max_length=100, blank=True, null=True)
    attch_file_5 = models.CharField(max_length=512, blank=True, null=True)
    supplement_data_1 = models.CharField(max_length=100, blank=True, null=True)
    supplement_data_2 = models.CharField(max_length=100, blank=True, null=True)
    fclty_in_chrg_s_user_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    mfg_end_date = models.DateTimeField(blank=True, null=True)
    user_defined_1 = models.CharField(max_length=50, blank=True, null=True)
    user_defined_2 = models.CharField(max_length=50, blank=True, null=True)
    user_defined_3 = models.CharField(max_length=50, blank=True, null=True)
    user_defined_4 = models.CharField(max_length=50, blank=True, null=True)
    user_defined_5 = models.CharField(max_length=50, blank=True, null=True)
    ap_exclusion_flg = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    u_cost_center = models.CharField(max_length=10, blank=True, null=True)
    u_reg_eqpt_nm = models.CharField(max_length=30, blank=True, null=True)
    u_reg_area = models.CharField(max_length=20, blank=True, null=True)
    u_e_importance = models.CharField(max_length=30, blank=True, null=True)
    latest_rev_chg_reason = models.CharField(max_length=2000, blank=True, null=True)
    latest_rev = models.DecimalField(max_digits=10, default=1, blank=False, null=False)
    latest_rev_m_chg_reason_cls_skey = models.DecimalField(max_digits=38, blank=True, null=True)
    deleted_flg = models.DecimalField(max_digits=1, blank=False, null=False, default=0)
    created_dt = models.DateTimeField(blank=False, null=False)
    created_id = models.CharField(max_length=50, blank=False, null=False)
    created_app = models.CharField(max_length=50, blank=False, null=False)
    update_dt = models.DateTimeField(blank=False, null=False)
    update_id = models.CharField(max_length=50, blank=False, null=False)
    update_app = models.CharField(max_length=50, blank=False, null=False)
    eqpt_id_mgt_flg = models.DecimalField(max_digits=1, blank=True, null=True, default=0)
    thumbnail_image_doc_1 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_1 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_2 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_2 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_3 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_3 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_4 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_4 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_5 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_5 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_6 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_6 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_7 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_7 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_8 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_8 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_9 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_9 = models.CharField(max_length=512, blank=True, null=True)
    thumbnail_image_doc_10 = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_image_file_10 = models.CharField(max_length=512, blank=True, null=True)
    u_regulation_cd_4 = models.DecimalField(max_digits=38, blank=True, null=True)
    u_regulation_cd_5 = models.DecimalField(max_digits=38, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 't_fclty_ldgr'

