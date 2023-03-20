from django.db import models
from .common_master_models import DepartmentMaster, User


# 予算状態マスタ
class BudgetConditionMaster(models.Model):
    condition_id = models.IntegerField('状態id', primary_key=True)
    condition_name = models.CharField('状態名', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.condition_name)


# 進捗マスタ
class StepMaster(models.Model):
    step_id = models.IntegerField('工程id', primary_key=True)
    step_name = models.CharField('工程名', max_length=20, blank=True, null=True)
    next_step = models.IntegerField('次工程id', blank=True, null=True)  # たぶん不要
    previous_step = models.IntegerField('前工程id', blank=True, null=True)  # たぶん不要
    charge_department_class = models.CharField('担当部署区分', max_length=10, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    step_level = models.IntegerField('工程レベル', blank=True, null=True)
    link_str = models.CharField('リンク文字列', max_length=200, blank=True, null=True)  # たぶん不要
    template_class = models.CharField('使用テンプレート', max_length=200, blank=True, null=True)  # viewsを修正すれば不要･･･現在は使用している
    new_entry_flag = models.IntegerField('新規登録FL', blank=True, null=True)
    target = models.CharField('対象', max_length=200, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    hidden_flag = models.IntegerField('非表示FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.step_name)


# 進捗工程関係マスタ
class StepRelation(models.Model):
    step_id = models.IntegerField('工程id',  blank=True, null=True)
    next_step = models.IntegerField('次工程id', blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 工事区分マスタ
class BudgetClassMaster(models.Model):
    budget_class_cd = models.IntegerField('工事区分CD', primary_key=True)
    budget_class_name = models.CharField('工事区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.budget_class_name)


# 工程マスタ
class ProcessMaster(models.Model):
    process_cd2 = models.CharField('工程CD2', max_length=10, primary_key=True)
    process_cd = models.CharField('工程CD', max_length=10, blank=False, null=False)
    process_name = models.CharField('工程名', max_length=20, blank=True, null=True)
    department = models.CharField('部署', max_length=10, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.process_cd)+" : "+(self.process_name)

    # class Meta:
    #     unique_together = ('process_cd', 'department')


# 申請区分マスタ
class ApplicationClassMaster(models.Model):
    application_class_cd = models.IntegerField('申請区分CD', primary_key=True)
    application_class_name = models.CharField('申請区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.application_class_name)


# 作業マスタ
class ActionMaster(models.Model):
    action_cd = models.CharField('作業CD', max_length=20, primary_key=True)
    action_name = models.CharField('作業名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    status_after_action = models.CharField('作業後状態', max_length=20, blank=True, null=True)
    action_authority = models.IntegerField('作業権限', blank=True, null=True)
    action_class = models.CharField('作業属性', max_length=20, blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.action_name)


# 目的区分マスタ
class PurposeClassMaster(models.Model):
    purpose_class_cd = models.CharField('目的区分CD', max_length=20, primary_key=True)
    purpose_class_name = models.CharField('目的区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.purpose_class_cd)+" : "+(self.purpose_class_name)


# 対象マスタ
class TargetMaster(models.Model):
    target_cd = models.CharField('対象CD', max_length=40, primary_key=True)
    target_name = models.CharField('対象名', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.target_name)


# 進捗通知マスタ
class StepNoticeMaster(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='工程id', null=True, on_delete=models.PROTECT)
    target = models.ForeignKey(TargetMaster, verbose_name='対象CD', null=True, on_delete=models.PROTECT)
    to_address = models.CharField('通知先アドレス', max_length=150, blank=True, null=True)
    check_function = models.CharField('通知判定用関数', max_length=150,  blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 物質状態マスタ
class MaterialStateMaster(models.Model):
    state_id = models.IntegerField('状態id', primary_key=True)
    state_name = models.CharField('状態名', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.state_name)


# 単位マスタ
class UnitMaster(models.Model):
    unit_id = models.IntegerField('単位id', primary_key=True)
    unit = models.CharField('単位', max_length=20, blank=True, null=True)
    unit_class = models.CharField('単位分類', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.unit)


# 圧力単位マスタ
class PressureUnitMaster(models.Model):
    unit_id = models.IntegerField('単位id', primary_key=True)
    unit = models.CharField('単位', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.unit)


# 濃度単位マスタ
class ConcentrationUnitMaster(models.Model):
    unit_id = models.IntegerField('単位id', primary_key=True)
    unit = models.CharField('単位', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.unit)


# 物質情報マスタ
class MaterialMaster(models.Model):
    material_cd = models.CharField('物質記号', max_length=20, blank=True, null=True)
    material_name = models.CharField('物質名', max_length=40, blank=True, null=True)
    chemical_formula = models.CharField('化学式', max_length=20, blank=True, null=True)
    sub_no = models.IntegerField('サブNo', blank=True, null=True)
    state = models.ForeignKey(MaterialStateMaster, verbose_name='状態', null=True, on_delete=models.PROTECT)
    normal_pressure = models.FloatField('通常圧力', blank=True, null=True)
    str_normal_pressure = models.CharField('通常圧力', max_length=30, blank=True, null=True)
    maximum_pressure = models.FloatField('最高圧力', blank=True, null=True)
    minimum_pressure = models.FloatField('最低圧力', blank=True, null=True)
    pressure_unit = models.ForeignKey(PressureUnitMaster, verbose_name='圧力単位', null=True, on_delete=models.PROTECT)
    normal_temperature = models.FloatField('通常温度', blank=True, null=True)
    str_normal_temperature = models.CharField('通常温度', max_length=30, blank=True, null=True)
    maximum_temperature = models.FloatField('最高温度', blank=True, null=True)
    minimum_temperature = models.FloatField('最低温度', blank=True, null=True)
    concentration_unit = models.ForeignKey(ConcentrationUnitMaster, verbose_name='濃度単位', null=True, on_delete=models.PROTECT)
    concentration = models.FloatField('濃度', blank=True, null=True)
    ph = models.FloatField('pH', blank=True, null=True)
    str_ph = models.CharField('pH', max_length=30, blank=True, null=True)
    viscosity = models.FloatField('粘度', blank=True, null=True)
    angle_of_repose = models.CharField('安息角', max_length=30, blank=True, null=True)
    bulk_specific_gravity = models.FloatField('嵩密度', blank=True, null=True)
    str_bulk_specific_gravity = models.CharField('嵩密度', max_length=30, blank=True, null=True)
    true_specific_gravity = models.FloatField('真比重', blank=True, null=True)
    str_true_specific_gravity = models.CharField('真比重', max_length=30, blank=True, null=True)
    apparent_specific_gravity = models.FloatField('見掛比重', blank=True, null=True)
    str_apparent_specific_gravity = models.CharField('見掛比重', max_length=30, blank=True, null=True)
    particle_size = models.FloatField('粒径', blank=True, null=True)
    str_particle_size = models.CharField('粒径', max_length=30, blank=True, null=True)
    moisture = models.FloatField('水分', blank=True, null=True)
    str_moisture = models.CharField('水分', max_length=30, blank=True, null=True)
    others = models.TextField('その他', max_length=1000, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.material_name)


# 量単位マスタ
class AmountUnitMaster(models.Model):
    unit_id = models.IntegerField('単位id', primary_key=True)
    unit = models.CharField('単位', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.unit)


# 機能マスタ
class FunctionMaster(models.Model):
    function_cd = models.CharField('機能cd', max_length=10, primary_key=True)
    function_name = models.CharField('機能名', max_length=20, blank=True, null=True)
    function_class = models.CharField('機能分類', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.function_name)


# 工程アクション
class StepAction(models.Model):
    step_id = models.IntegerField('工程id', blank=True, null=True)
    action_cd = models.CharField('作業CD', max_length=20, blank=True, null=True)
    next_step = models.IntegerField('次工程id', blank=True, null=True)  # たぶん不要
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    target = models.CharField('対象', max_length=40, blank=True, null=True)


# 法令マスタ
class RegulationMaster(models.Model):
    regulation_cd = models.CharField('法令CD', max_length=5, primary_key=True)
    regulation_name = models.CharField('法令名', max_length=20, blank=True, null=True)
    rem = models.CharField('備考', max_length=200, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.regulation_name)


# 物品/工事マスタ
class WorkClassMaster(models.Model):
    work_class_cd = models.IntegerField('物品/工事区分CD', primary_key=True)
    work_class_name = models.CharField('物品/工事区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.work_class_name)


# データ登録工程マスタ
class DataEntryStepMaster(models.Model):
    step_id = models.IntegerField('工程id', blank=True, null=True)
    target_table = models.CharField('対象テーブル', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 管理区分マスタ
class ManagementClassMaster(models.Model):
    management_class_cd = models.CharField('管理区分CD', max_length=1, blank=True, null=True)
    management_class_name = models.CharField('管理区分名', max_length=2, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 機器ファミリマスタ
class EquipmentFamilyMaster(models.Model):
    management_class = models.CharField('管理区分', max_length=1, blank=True, null=True)
    equipment_family_cd = models.CharField('機器ファミリCD', max_length=2, blank=True, null=True)
    equipment_family_name = models.CharField('機器ファミリ名', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 機器カテゴリマスタ
class EquipmentCategoryMaster(models.Model):
    management_class = models.CharField('管理区分', max_length=1, blank=True, null=True)
    equipment_category_cd = models.CharField('機器カテゴリCD', max_length=2, blank=True, null=True)
    equipment_category_name = models.CharField('機器カテゴリ名', max_length=40, blank=True, null=True)
    equipment_family = models.CharField('機器ファミリ', max_length=2, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 熱交換器型式マスタ
class ExchangeTypeMaster(models.Model):
    mex_type_cd = models.CharField('熱交換器型式CD', max_length=10, primary_key=True)
    mex_type_name = models.CharField('熱交換器型式名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.mex_type_name)


# PLANTIAの機器型別フィールド表示マスタ
class SpecmanAttrs(models.Model):
    section = models.CharField('管理区分', max_length=5, blank=True, null=True)
    eqp_family = models.CharField('機器ファミリー', max_length=5, blank=True, null=True)
    column_name = models.CharField('カラム名', max_length=40, blank=True, null=True)
    seq_no = models.IntegerField('SEQ_NO', blank=True, null=True)
    hdr_text = models.CharField('カラム表記名', max_length=40, blank=True, null=True)
    unit_name = models.CharField('単位名', max_length=20, blank=True, null=True)
    list_name = models.CharField('リスト名', max_length=20, blank=True, null=True)
    init_value = models.CharField('初期値', max_length=20, blank=True, null=True)
    using_type = models.CharField('使用機器型', max_length=200, blank=True, null=True)


# PLANTIAの機器型マスタ
class Eqpt_Category(models.Model):
    mgt_cls = models.CharField('管理区分', max_length=5, blank=True, null=True)
    eqpt_family = models.CharField('機器ファミリー', max_length=5, blank=True, null=True)
    eqpt_tp = models.CharField('機器タイプ', max_length=20, blank=True, null=True)
    eqpt_cat_nm = models.CharField('機器タイプ名', max_length=40, blank=True, null=True)
    eqpt_cat_abbr = models.CharField('機器タイプ??', max_length=40, blank=True, null=True)
    disp_order = models.IntegerField('表示順', blank=True, null=True)
    rem = models.CharField('備考', max_length=200, blank=True, null=True)


# 提出書類マスタ
class SubmissionDocumentMaster(models.Model):
    document_name = models.CharField('書類名', max_length=50, blank=True, null=True)
    default_submission_deadline = models.CharField('初期提出期限', max_length=50, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    default_number_of_copies = models.IntegerField('初期部数', blank=True, null=True)


# 支給品マスタ
class SuppliesMaster(models.Model):
    supplies_name = models.CharField('支給品名', max_length=50, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# PLANTIA設備工程マスタ
class FCLTYCDMaster(models.Model):
    FCLTY_CD = models.CharField('工程CD', max_length=50, primary_key=True)
    FCLTY_NM = models.CharField('工程名', max_length=50, blank=True, null=True)
    DISP_ORDER = models.IntegerField('表示順', blank=True, null=True)
    FCLTY_CLS_CD = models.CharField('部署CD', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# PLANTIA機器リスト
class EQPTBASICMST(models.Model):
    MGT_CLS = models.CharField('区分', max_length=10, blank=True, null=True)
    FCLTY_CD = models.CharField('工程名', max_length=50, blank=True, null=True)
    EQPT_ID = models.CharField('機器NO', max_length=50, blank=True, null=True)
    EQPT_NM = models.CharField('機器名', max_length=50, blank=True, null=True)
    EQPT_FMLY = models.CharField('機器ファミリー', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 総務管轄工場立地法マスタ
class FactoryLocationActMotiveMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % self.motive


# 安全衛生管理管轄消防法危険物承認申請場所マスタ
class FireServiceAppPlaceMaster(models.Model):
    place = models.CharField('場所', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 安全衛生管理管轄消防法危険物承認申請扱いマスタ
class FireServiceAppActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 安全衛生管理管轄消防法危険物届場所マスタ
class FireServiceNtfcPlaceMaster(models.Model):
    place = models.CharField('場所', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 安全衛生管理管轄消防法危険物届改廃マスタ
class FireServiceNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 安全衛生管理管轄消防法危険物品名数量倍数変更届場所マスタ
class FireServiceQuantityNtfcPlaceMaster(models.Model):
    place = models.CharField('場所', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 消防法圧縮アセチレンガス等貯蔵取扱届出改廃マスタ
class FireServiceAcetyleneGasNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 消防法危険物仮承認申請扱いマスタ
class FireServiceTentativeAppActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 市火災予防条例危険物貯蔵取扱届種類マスタ
class FirePreventStorageNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 市火災予防条例危険物貯蔵取扱届改廃マスタ
class FirePreventStorageNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 市火災予防条例設備設置届種類マスタ
class FirePreventEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 劇毒物取締法劇毒物変更届取扱マスタ
class DeleteriousSubstancesNtfcPurposeMaster(models.Model):
    purpose = models.CharField('取扱', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法特定高圧ガス設備申請製造/変更マスタ
class PressGasAppMotiveMaster(models.Model):
    motive = models.CharField('製造/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法液化石油高圧ガス設備申請製造/変更マスタ
class PressGasLpgAppMotiveMaster(models.Model):
    motive = models.CharField('製造/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法冷凍高圧ガス設備申請製造/変更マスタ
class PressGasFrozenGasAppMotiveMaster(models.Model):
    motive = models.CharField('製造/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法特定高圧ガス設備届改廃マスタ
class PressGasNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法液化石油高圧ガス設備届改廃マスタ
class PressGasLpgNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法冷凍高圧ガス設備届改廃マスタ
class PressGasFrozenGasNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 高圧ガス保安法特定高圧ガス消費設備届改廃マスタ
class PressGasConsumptionNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法設置物届種類マスタ
class SafetyHealthEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法設置物届設置/変更マスタ
class SafetyHealthEquipNtfcMotiveMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法有害物質届種類マスタ
class SafetyHealthDeleteriousNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法有害物質届設置/変更マスタ
class SafetyHealthDeleteriousMotiveNtfcMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法設備届種類マスタ
class SafetyHealthSpecifiedEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法設備届設置/変更マスタ
class SafetyHealthSpecifiedEquipNtfcMotiveMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 労働安全衛生法設備設置報告種類マスタ
class SafetyHealthInstallationReportCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 放射線障害防止法放射性同位元素申請使用/変更マスタ
class RadiationHazardsAppMotiveMaster(models.Model):
    motive = models.CharField('使用/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 大気汚染防止法大気汚染物質発生施設届種類マスタ
class AirPollutionEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 大気汚染防止法大気汚染物質発生施設届設置/変更マスタ
class AirPollutionEquipNtfcMotiveMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 大気汚染防止法大気汚染物質発生施設廃止届種類マスタ
class AirPollutionRepealEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 大気汚染防止法揮発性有機化合物発生施設届扱いマスタ
class AirPollutionVocNtfcActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 水質汚濁防止法特定施設届扱いマスタ
class WaterPollutionNtfcActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 廃棄物処理法産業廃棄物処理施設申請設置/変更マスタ
class WasteEquipAppMotiveMaster(models.Model):
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 県生活環境保全条例指定施設届種類マスタ
class LivingEnvEquipNtfcCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 県生活環境保全条例指定施設届扱いマスタ
class LivingEnvEquipNtfcActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 浄化槽法浄化槽届出改廃マスタ
class WaterPurificationTanksNtfcAmendmentMaster(models.Model):
    amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 建築基準法確認申請種類マスタ
class BuildingStandardsActCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 省エネ法特定建築物届出種類マスタ
class EnergyRationalizationActCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 省エネ法特定建築物届出扱いマスタ
class EnergyRationalizationActActionMaster(models.Model):
    action = models.CharField('扱い', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 建設リサイクル法種類マスタ
class ConstructionRecyclingCategoryMaster(models.Model):
    category = models.CharField('種類', max_length=20, blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)


# 工事管理区分マスタ
class WorkManagementClassMaster(models.Model):
    management_class_cd = models.CharField('工事管理区分CD', max_length=2, blank=True, null=True)
    management_class_name = models.CharField('工事管理区分名', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 工事中止原因マスタ
class StopWorkCauseMaster(models.Model):
    stop_work_cause_name = models.CharField('中止原因名', max_length=20, blank=True, null=True)
    target = models.CharField('中止対象', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# チェック項目マスタ
class CheckItemMaster(models.Model):
    check_cd = models.CharField('チェック項目CD', max_length=40, primary_key=True)
    function_cd = models.CharField('機能コード', max_length=40, blank=True, null=True)
    check_name = models.CharField('名称', max_length=40, blank=True, null=True)
    text_input_flag = models.BooleanField('テキスト入力FL', blank=True, null=True)
    assign_departments = models.ManyToManyField(DepartmentMaster, blank=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 機能担当者マスタ
class StepFunctionUserMaster(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='該当ステップ', null=True, on_delete=models.PROTECT)
    department = models.ForeignKey(DepartmentMaster, verbose_name='部署', null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, verbose_name='ユーザー名', null=True, on_delete=models.PROTECT)
    user_order = models.IntegerField('部署内優先順位', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 計画区分マスタ
class PlanClassMaster(models.Model):
    class_cd = models.CharField('計画区分CD', max_length=20, primary_key=True)
    name = models.CharField('名称', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % self.name


# 中期申請希望額根拠マスタ
class MPlanBasisMaster(models.Model):
    basis_cd = models.CharField('申請希望額根拠CD', max_length=40, primary_key=True)
    name = models.CharField('名称', max_length=100, blank=True, null=True)
    detail = models.CharField('詳細', max_length=100, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 予算状態関連マスタ
class BudgetConditionRelation(models.Model):
    this_step = models.ForeignKey(StepMaster, verbose_name='元工程', null=True, on_delete=models.PROTECT, related_name='budgetconditionrelation_this_step')
    next_step = models.ForeignKey(StepMaster, verbose_name='次工程', null=True, on_delete=models.PROTECT, related_name='budgetconditionrelation_next_step')
    budget_condition = models.ForeignKey(BudgetConditionMaster, verbose_name='予算状態', null=True, on_delete=models.PROTECT)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
