from django.db import models
from .master_models import ProcessMaster, ApplicationClassMaster, RegulationMaster, FunctionMaster
from .master_models import BudgetClassMaster, BudgetConditionMaster, PurposeClassMaster, MaterialStateMaster
from .master_models import PressureUnitMaster, ConcentrationUnitMaster, AmountUnitMaster
from .master_models import PlanClassMaster, MPlanBasisMaster
from .common_master_models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, User


# 定量評価基準マスタ
class EvaluationCriteriaMaster(models.Model):
    target = models.CharField('対象', max_length=20, blank=True, null=True)
    criteria_cd = models.CharField('評価基準コード', max_length=40, blank=True, null=True)
    criteria_detail = models.CharField('評価基準詳細', max_length=100, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 定量評価点数マスタ
class EvaluationPointMaster(models.Model):
    criteria = models.ForeignKey(
        EvaluationCriteriaMaster, verbose_name='評価基準id', null=True, on_delete=models.PROTECT,
        related_name='point_set')
    point = models.IntegerField('点数', blank=True, null=True)
    point_detail = models.CharField('点数詳細', max_length=100, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 予算
class Budget(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    budget_no = models.CharField('予算NO', max_length=20, blank=True, null=True)
    request_name = models.CharField('依頼名', max_length=70, blank=True, null=True)
    budget_name = models.CharField('予算名', max_length=70, blank=True, null=True)
    relation_budget_id = models.IntegerField('関連予算id', blank=True, null=True)
    decision_no = models.CharField('決裁番号', max_length=20, blank=True, null=True)
    business_year = models.ForeignKey(BusinessYearMaster, verbose_name='年度', null=True, on_delete=models.PROTECT)
    carry_over_flag = models.IntegerField('見送りフラグ', blank=True, null=True)
    application_class = models.ForeignKey(ApplicationClassMaster, verbose_name='申請区分', null=True, on_delete=models.PROTECT)
    budget_class = models.ForeignKey(BudgetClassMaster, verbose_name='工事区分', null=True, on_delete=models.PROTECT)
    period_class = models.ForeignKey(PeriodClassMaster, verbose_name='期区分', null=True, on_delete=models.PROTECT)
    application_price = models.BigIntegerField('申請金額', blank=True, null=True)
    budget_price = models.BigIntegerField('予算金額', blank=True, null=True)
    budget_main_department = models.ForeignKey(DepartmentMaster, verbose_name=' 主部署', null=True, on_delete=models.PROTECT)
    budget_department_charge_person = models.ForeignKey(User, verbose_name='原課担当者', null=True, on_delete=models.PROTECT)
    budget_person = models.ForeignKey(User, verbose_name='予算担当者', null=True, on_delete=models.PROTECT, related_name="budget_budget_person")
    jurisdiction_area = models.CharField('所管エリア', max_length=20, blank=True, null=True)
    area_manager = models.ForeignKey(User, verbose_name='エリア管理者', null=True, on_delete=models.PROTECT, related_name="budget_area_manager")
    facility_process = models.ForeignKey(ProcessMaster, verbose_name='設備工程', null=True, on_delete=models.PROTECT)
    start_date = models.DateField('着工日', blank=True, null=True)
    end_date = models.DateField('完工日', blank=True, null=True)
    order_date = models.DateField('発注日', blank=True, null=True)
    delivery_date = models.DateField('納期日', blank=True, null=True)
    pre_order_flag = models.CharField('事前発注', max_length=10, blank=True, null=True)
    asdm_flag = models.CharField('定修区分', max_length=20, blank=True, null=True)
    purpose_class = models.ForeignKey(PurposeClassMaster, verbose_name='目的区分', null=True, on_delete=models.PROTECT)
    management_class_cd = models.CharField('管理区分CD', max_length=2, blank=True, null=True)
    purpose = models.TextField('目的', max_length=400, blank=True, null=True)
    request_detail = models.TextField('依頼内容', max_length=400, blank=True, null=True)
    detail = models.TextField('内容', max_length=400, blank=True, null=True)
    effect = models.TextField('効果', max_length=400, blank=True, null=True)
    influence_for_operation = models.TextField('操業影響', max_length=400, blank=True, null=True)
    influence_for_quality = models.TextField('品質影響', max_length=400, blank=True, null=True)
    remove_assets = models.TextField('除却資産', max_length=400, blank=True, null=True)
    budget_rem = models.TextField('備考', max_length=400, blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    cancel_flag = models.IntegerField('中止FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    importance_criteria = models.ForeignKey(
        EvaluationCriteriaMaster, verbose_name='重要度評価基準id', null=True, on_delete=models.PROTECT,
        related_name='budget_importance_criteria')
    importance_point = models.ForeignKey(
        EvaluationPointMaster, verbose_name='重要度評価点数id', null=True, on_delete=models.PROTECT,
        related_name='budget_importance_point')
    urgency_criteria = models.ForeignKey(
        EvaluationCriteriaMaster, verbose_name='緊急度評価基準id', null=True, on_delete=models.PROTECT,
        related_name='budget_urgency_criteria')
    urgency_point = models.ForeignKey(
        EvaluationPointMaster, verbose_name='緊急度評価点数id', null=True, on_delete=models.PROTECT,
        related_name='budget_urgency_point')
    decision_rank_detail = models.CharField('判定ランク詳細', max_length=20, blank=True, null=True)
    no_make_cs_flag = models.IntegerField('届出CS作成不要FL', blank=True, null=True, default=0)
    check_material_flag = models.CharField('物質情報入力該当FL', max_length=10, blank=True, null=True)

    plan_class = models.ForeignKey(PlanClassMaster, verbose_name='計画区分', null=True, on_delete=models.PROTECT)
    last_plan_id = models.IntegerField('前計画区分予算ID', blank=True, null=True)
    mplan_desired_amount = models.BigIntegerField('中計申請希望額', blank=True, null=True)
    mplan_adjustment_amount = models.BigIntegerField('中計申請後調整額', blank=True, null=True)
    mplan_basis = models.ForeignKey(MPlanBasisMaster, verbose_name='中計申請希望額根拠', null=True, on_delete=models.PROTECT)
    mplan_basis_comment = models.CharField('中計申請額根拠コメント', max_length=200, blank=True, null=True)
    mplan_concerns = models.TextField('中計懸念事項', max_length=400, blank=True, null=True)
    mpaln_evaluation = models.ForeignKey(
        EvaluationCriteriaMaster, verbose_name='中計評価id', null=True, on_delete=models.PROTECT,
        related_name='budget_mpaln_evaluation')


# 予算関連部署
class BudgetRelationDepartment(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    budget_relation_department = models.ForeignKey(DepartmentMaster, verbose_name='関連部署', null=True, on_delete=models.PROTECT)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 予算状態
class BudgetCondition(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    budget_condition = models.ForeignKey(BudgetConditionMaster, verbose_name='予算状態', null=True, on_delete=models.PROTECT)


# 予算関係法令
class BudgetRegulation(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    budget_regulation = models.ForeignKey(RegulationMaster, verbose_name='関係法令', null=True, on_delete=models.PROTECT)


# 取扱物質
class BudgetMaterial(models.Model):
    budget_id = models.IntegerField('予算id')
    work_id = models.IntegerField('工事id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
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
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 要求仕様
class BudgetRequiredFunction(models.Model):
    budget_id = models.IntegerField('予算id')
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    required_function = models.ForeignKey(FunctionMaster, verbose_name='要求機能', null=True, on_delete=models.PROTECT)
    sub_no = models.IntegerField('サブNo', blank=True, null=True)
    material = models.CharField('取扱物質', max_length=40, blank=True, null=True)
    required_material_capacity = models.FloatField('要求量', blank=True, null=True)
    material_capacity_unit = models.ForeignKey(AmountUnitMaster, verbose_name='量単位', null=True, on_delete=models.PROTECT)
    required_cooling_temperature = models.FloatField('要求冷却温度', blank=True, null=True)
    required_heating_temperature = models.FloatField('要求加熱温度', blank=True, null=True)
    temperature = models.FloatField('温度', blank=True, null=True)
    required_compress_pressure = models.FloatField('要求圧縮圧', blank=True, null=True)
    required_vacuum_pressure = models.FloatField('要求減圧', blank=True, null=True)
    pressure = models.FloatField('圧力', blank=True, null=True)
    pressure_unit = models.ForeignKey(PressureUnitMaster, verbose_name='圧力単位', null=True, on_delete=models.PROTECT)
    required_moisture = models.FloatField('要求水分', blank=True, null=True)
    required_concentration = models.FloatField('要求濃度', blank=True, null=True)
    concentration_unit = models.ForeignKey(ConcentrationUnitMaster, verbose_name='濃度単位', null=True, on_delete=models.PROTECT)
    required_particle_size = models.FloatField('要求粒径', blank=True, null=True)
    required_transfer_length = models.FloatField('要求輸送距離', blank=True, null=True)
    required_others = models.TextField('その他要求', max_length=400, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 取扱物質個人マスタ
class MyBudgetMaterialData(models.Model):
    material_cd = models.CharField('物質記号', max_length=20, blank=True, null=True)
    material_name = models.CharField('物質名', max_length=40, blank=True, null=True)
    chemical_formula = models.CharField('化学式', max_length=20, blank=True, null=True)
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
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)


# 対機能要求仕様表示項目
class DisplayRequiredItemForFunction(models.Model):
    required_function = models.ForeignKey(FunctionMaster, verbose_name='要求機能', null=True, on_delete=models.PROTECT)
    display_material_flag = models.IntegerField('取扱物質表示FL', blank=True, null=True)
    display_required_material_capacity_flag = models.IntegerField('要求量表示FL', blank=True, null=True)
    display_material_capacity_unit_flag = models.IntegerField('量単位表示FL', blank=True, null=True)
    display_required_cooling_temperature_flag = models.IntegerField('要求冷却温度表示FL', blank=True, null=True)
    display_required_heating_temperature_flag = models.IntegerField('要求加熱温度表示FL', blank=True, null=True)
    display_temperature_flag = models.IntegerField('温度表示FL', blank=True, null=True)
    display_required_compress_pressure_flag = models.IntegerField('要求圧縮圧表示FL', blank=True, null=True)
    display_required_vacuum_pressure_flag = models.IntegerField('要求減圧表示FL', blank=True, null=True)
    display_pressure_flag = models.IntegerField('圧力表示FL', blank=True, null=True)
    display_pressure_unit_flag = models.IntegerField('圧力単位表示FL', blank=True, null=True)
    display_required_moisture_flag = models.IntegerField('要求水分表示FL', blank=True, null=True)
    display_required_concentration_flag = models.IntegerField('要求濃度表示FL', blank=True, null=True)
    display_concentration_unit_flag = models.IntegerField('濃度単位表示FL', blank=True, null=True)
    display_required_particle_size_flag = models.IntegerField('要求粒径表示FL', blank=True, null=True)
    display_required_transfer_length_flag = models.IntegerField('要求輸送距離表示FL', blank=True, null=True)
    display_required_others_flag = models.IntegerField('そのた要求表示FL', blank=True, null=True)


# 予算計画担当者
class PlanningChargePerson(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    charge_person = models.CharField('計画担当者', max_length=150, blank=True, null=True)
    main_charge_flag = models.IntegerField('主担当FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    complete_flag = models.IntegerField('完了FL', blank=True, null=True)


# 予算関係法令
class BudgetLaw(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    law_name = models.CharField('法令', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 予算関係機器
class BudgetEquipment(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    equip_no = models.CharField('機器NO', max_length=50, blank=True, null=True)
    equip_name = models.CharField('機器名', max_length=100, blank=True, null=True)
    management_class = models.CharField('区分', max_length=50, blank=True, null=True)
    facility = models.CharField('設備工程', max_length=50, blank=True, null=True)
    equip_family = models.CharField('機器ファミリー', max_length=50, blank=True, null=True)
    equip_type = models.CharField('機器タイプ', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 要求仕様
class RequiredSpecification(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    budget_rev_no = models.IntegerField('予算RevNo', blank=True, null=True)
    no = models.IntegerField('No', blank=True, null=True)
    required_spec = models.TextField('要求仕様', max_length=2000, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 工事方針･概要
class ConstructionPolicyOverview(models.Model):
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    budget_rev_no = models.IntegerField('予算RevNo', blank=True, null=True)
    required_spec_no = models.CharField('要求仕様No', max_length=20, blank=True, null=True)
    no = models.IntegerField('No', blank=True, null=True)
    policy = models.TextField('工事方針', max_length=2000, blank=True, null=True)
    overview = models.TextField('工事概要', max_length=2000, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 定量評価判定マスタ
class EvaluationDecisionMaster(models.Model):
    target = models.CharField('対象', max_length=20, blank=True, null=True)
    evaluation_cd = models.CharField('評価コード', max_length=40, blank=True, null=True)
    evaluation_point = models.IntegerField('評価点数', blank=True, null=True)
    decision_rank = models.CharField('判定ランク', max_length=20, blank=True, null=True)
    decision_rank_detail = models.CharField('判定ランク詳細', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 予算繰越情報
class BudgetCarryForward(models.Model):
    carry_forward_id = models.IntegerField('繰越情報id', blank=True, null=True)
    budget_id = models.IntegerField('予算id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    carry_forward_price = models.BigIntegerField('繰越金額', blank=True, null=True)
    end_date = models.DateField('完了予定工期', blank=True, null=True)
    order_complete_flag = models.IntegerField('発注完了状態', blank=True, null=True)
    carry_forward_reason = models.TextField('予算繰越理由', max_length=400, blank=True, null=True)
    carry_forward_year_from = models.ForeignKey(
        BusinessYearMaster, verbose_name='繰越元年度', null=True, on_delete=models.PROTECT, related_name='budget_carry_forward_year_from')
    carry_forward_year_to = models.ForeignKey(
        BusinessYearMaster, verbose_name='繰越先年度', null=True, on_delete=models.PROTECT, related_name='budget_carry_forward_year_to')
    settlement_no = models.CharField('繰越決済No', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
