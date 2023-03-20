from django.db import models
from .common_master_models import DepartmentMaster, User


# 異常報告
class Phenomenon(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    project_title = models.CharField('案件名', max_length=40, blank=True, null=True)
    discovery_date = models.DateField('発見日', blank=True, null=True)
    department = models.ForeignKey(DepartmentMaster, verbose_name=' 部署', null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, verbose_name=' 発見者', null=True, on_delete=models.PROTECT)
    m_condition_cd_skey = models.IntegerField('skey_状況', blank=True, null=True)
    condition_detail = models.CharField('状況詳細', max_length=400, blank=True, null=True)
    improvement_proposal = models.CharField('改善提案', max_length=400, blank=True, null=True)
    m_mgt_cls_skey = models.IntegerField('skey_管理区分', blank=True, null=True)
    m_location_skey = models.IntegerField('skey_工場区分', blank=True, null=True)
    equipment_no = models.CharField('機器番号', max_length=200, blank=True, null=True)
    jurisdiction_area = models.CharField('保全担当', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)
    # 不要
    discovery_datetime = models.DateTimeField('発見日時', blank=True, null=True)
    discoverer = models.CharField('発見者', max_length=20, blank=True, null=True)
    condition = models.CharField('状況', max_length=20, blank=True, null=True)
    management_class = models.CharField('管理区分', max_length=5, blank=True, null=True)
    factory_name = models.CharField('工場名', max_length=20, blank=True, null=True)


# 故障対応機器
class MaintenanceEquipment(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    t_fclty_ldgr_skey = models.IntegerField('skey_機器', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 対応方針
class Measure(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    measure_order_detail = models.CharField('工事内容', max_length=1000, blank=True, null=True)
    m_exe_cls_skey = models.IntegerField('skey_実施区分', blank=True, null=True)
    malfunction_class = models.CharField('故障/作業種別', max_length=30, blank=True, null=True)
    desired_delivery_date_start = models.DateField('希望納期日FROM', blank=True, null=True)
    desired_delivery_date_end = models.DateField('希望納期日TO', blank=True, null=True)
    work_order_charge_department = models.ForeignKey(DepartmentMaster, verbose_name='原課担当部署', null=True, on_delete=models.PROTECT)
    work_order_department_charge_person = models.ForeignKey(User, related_name='work_order_department_charge_users2', verbose_name='原課担当者', on_delete=models.PROTECT, null=True)
    instruction_no = models.CharField('指図書NO', max_length=20, blank=True, null=True)
    cost_center = models.CharField('原価センタ', max_length=10, blank=True, null=True)
    account_cd = models.CharField('勘定コード', max_length=20, blank=True, null=True)
    diagnosis_class = models.IntegerField('診断', blank=True, null=True)
    desired_vendor = models.CharField('希望業者', max_length=30, blank=True, null=True)
    maintenance_status = models.IntegerField('メンテナンス対応状況', blank=True, null=True)
    response_request_date = models.DateField('対応依頼日', blank=True, null=True)
    orders_received_person = models.CharField('依頼受付者', max_length=50, blank=True, null=True)
    notification_required_flag = models.IntegerField('届出必要', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)
    # 不要
    item_class = models.IntegerField('案件区分', blank=True, null=True)
    desired_delivery_date_f = models.DateTimeField('希望納期日FROM', blank=True, null=True)
    desired_delivery_date_t = models.DateTimeField('希望納期日TO', blank=True, null=True)


# 診断
class Inspection(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    inspection_detail = models.CharField('検査診断内容', max_length=200, blank=True, null=True)
    inspection_result = models.CharField('検査診断結果', max_length=10, blank=True, null=True)
    charge_team = models.IntegerField('保全G対応', blank=True, null=True)
    measure = models.IntegerField('対応方針', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# 依頼
class Order(models.Model):
    phenomenon_id = models.IntegerField('案件ID', blank=True, null=True)
    order_id = models.IntegerField('依頼ID', blank=True, null=True)
    contact_request = models.IntegerField('依頼先', blank=True, null=True)
    order_name = models.CharField('依頼名', max_length=50, blank=True, null=True)
    order_name_extension_name = models.CharField('依頼名(拡張)', max_length=10, blank=True, null=True)
    expected_price = models.IntegerField('予想金額', blank=True, null=True)
    desired_start_date = models.DateField('着工希望開始日', blank=True, null=True)
    desired_end_date = models.DateField('着工希望完工日', blank=True, null=True)
    department = models.ForeignKey(DepartmentMaster, verbose_name='原課担当部署', null=True, on_delete=models.PROTECT)
    order_permit_person = models.CharField('原課担当者', max_length=25, blank=True, null=True)
    plant_name = models.CharField('部署工場名', max_length=50, blank=True, null=True)
    m_location_skey = models.IntegerField('skey_工場区分', blank=True, null=True)
    order_detail = models.CharField('依頼内容', max_length=1000, blank=True, null=True)
    rem = models.CharField('備考', max_length=400, blank=True, null=True)
    is_need_input_plantia = models.CharField('PLANTIA入力要否', max_length=5, blank=True, null=True)
    order_detail_for_vendor = models.CharField('業者依頼内容', max_length=1000, blank=True, null=True)
    rem_for_plantia_data = models.CharField('PLANTIA関係備考', max_length=400, blank=True, null=True)
    order_vendor = models.CharField('依頼者希望業者', max_length=100, blank=True, null=True)
    transfer_complete_flag = models.IntegerField('転送完了FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# IEP依頼
class OrderForIEP(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    order_id = models.IntegerField('依頼ID', blank=True, null=True)
    department = models.CharField('部門', max_length=50, blank=True, null=True)
    cost_center = models.CharField('原価センタ', max_length=10, blank=True, null=True)
    order_name = models.CharField('依頼名', max_length=50, blank=True, null=True)
    order_person = models.CharField('依頼者', max_length=25, blank=True, null=True)
    desired_start_date = models.DateTimeField('希望開始日', blank=True, null=True)
    desired_construction_end_date = models.DateTimeField('希望完工日', blank=True, null=True)
    order_date = models.DateTimeField('依頼日', max_length=8, blank=True, null=True)
    order_permit_person = models.CharField('依頼承認者', max_length=25, blank=True, null=True)
    account_code = models.CharField('勘定CD', max_length=10, blank=True, null=True)
    instruction_code = models.CharField('指図書CD', max_length=10, blank=True, null=True)
    construction_details = models.CharField('工事内容', max_length=1000, blank=True, null=True)
    order_rem = models.CharField('依頼備考', max_length=500, blank=True, null=True)
    order_rem_2 = models.CharField('注文備考', max_length=500, blank=True, null=True)
    orders_received_person = models.CharField('依頼受付者', max_length=50, blank=True, null=True)
    status = models.IntegerField('ステータス', blank=True, null=True)
    item_class = models.IntegerField('案件区分', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)
# IEPへのデータ転送時にplantia入力要否、区分_工場_機器番号をrem_for_plantia_dataに保存する


# 届出チェック
class NotificationCheck(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    notification = models.IntegerField('届出要否FL', blank=True, null=True)
    law_facility = models.IntegerField('法令該当施設FL', blank=True, null=True)
    comment = models.TextField('原課部署コメント', max_length=1000, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    cancel_comment = models.TextField('中止理由', max_length=1000, blank=True, null=True)
    cancel_flag = models.IntegerField('中止FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# 保全G報告
class EquipmentHistoryReport(models.Model):
    phenomenon_id2 = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    history_no = models.IntegerField('履歴NO', blank=True, null=True)
    m_site_skey = models.IntegerField('skey_拠点', blank=True, null=True)
    m_mgt_cls_skey = models.IntegerField('skey_管理区分', blank=True, null=True)
    m_location_skey = models.IntegerField('skey_工場区分', blank=True, null=True)
    t_fclty_ldgr_skey = models.IntegerField('skey_機器', blank=True, null=True)
    time_of_occurrence = models.DateField('発生日時', blank=True, null=True)
    m_exe_cls_skey = models.IntegerField('skey_実施区分', blank=True, null=True)
    failure_work_type = models.CharField('故障/作業種別', max_length=20, blank=True, null=True)
    serious_breakdown_case = models.IntegerField('重故障案件', blank=True, null=True)
    s_specman_list_value_skey = models.CharField('skey_保全区分', max_length=20, blank=True, null=True)
    completion_date = models.DateField('完工日', blank=True, null=True)
    cycle_reference_date = models.DateField('周期基準日', blank=True, null=True)
    start_date = models.DateField('着工日', blank=True, null=True)
    maintenance_name = models.CharField('保全名称', max_length=150, blank=True, null=True)
    maintenance_personnel = models.IntegerField('保全担当者', blank=True, null=True)
    person_in_charge_of_the_original_section = models.CharField('原課担当者', max_length=60, blank=True, null=True)
    construction_representative = models.CharField('工事担当者', max_length=20, blank=True, null=True)
    s_user_skey = models.IntegerField('skey_工事担当者', blank=True, null=True)
    m_condition_cd_skey = models.IntegerField('skey_状況', blank=True, null=True)
    m_position_cd_skey_condition = models.IntegerField('skey_状況部位コード', blank=True, null=True)
    m_phenomenon_cd_skey = models.IntegerField('skey_現象', blank=True, null=True)
    m_position_cd_skey_phenomenon = models.IntegerField('skey_現象部位コード', blank=True, null=True)
    m_cause_cd_skey = models.IntegerField('skey_原因', blank=True, null=True)
    m_position_cd_skey_cause = models.IntegerField('skey_原因部位コード', blank=True, null=True)
    m_treatment_cd_skey = models.IntegerField('skey_処置', blank=True, null=True)
    m_position_cd_skey_treatment = models.IntegerField('skey_処置部位コード', blank=True, null=True)
    m_result_cd_skey = models.IntegerField('skey_結果', blank=True, null=True)
    stop_time = models.IntegerField('停止時間', blank=True, null=True)
    repair_time = models.IntegerField('修理時間', blank=True, null=True)
    report_detail = models.CharField('報告詳細', max_length=400, blank=True, null=True)
    cause_detail = models.CharField('原因詳細', max_length=200, blank=True, null=True)
    countermeasure = models.CharField('対策', max_length=200, blank=True, null=True)
    phenomenon_details = models.CharField('現象詳細', max_length=200, blank=True, null=True)
    special_note_construction_work = models.CharField('特記（工務）', max_length=200, blank=True, null=True)
    special_note_production = models.CharField('特記（生産）', max_length=200, blank=True, null=True)
    message = models.CharField('申送事項', max_length=200, blank=True, null=True)
    items_to_be_sent_production = models.CharField('申送り事項（生産）', max_length=200, blank=True, null=True)
    attachment = models.CharField('添付ファイル', max_length=5, blank=True, null=True)
    is_need_input_plantia = models.CharField('PLANTIA入力要否', max_length=5, blank=True, null=True)
    export_complete_flag = models.IntegerField('データエクスポート完了FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)
    # 不要
    phenomenon = models.ForeignKey(Phenomenon, verbose_name=' 案件NO', null=True, on_delete=models.PROTECT)
    mgt_class = models.CharField('管理区分', max_length=5, blank=True, null=True)
    facility = models.CharField('工場', max_length=10, blank=True, null=True)
    equipment_no = models.CharField('機器NO', max_length=20, blank=True, null=True)
    phenomenon_class = models.CharField('現象区分', max_length=5, blank=True, null=True)
    cause_class = models.CharField('原因区分', max_length=5, blank=True, null=True)
    result = models.CharField('結果', max_length=5, blank=True, null=True)
    oprtn_time = models.IntegerField('運転時間', blank=True, null=True)
    special_mention = models.CharField('特記', max_length=200, blank=True, null=True)


# 資料データ
class MaintenanceAttachmentFile(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    sub_no = models.IntegerField('サブNO', blank=True, null=True)
    equipment_no = models.CharField('機器NO', max_length=20, blank=True, null=True)
    history_no = models.IntegerField('履歴NO', blank=True, null=True)
    mgt_class = models.CharField('管理区分', max_length=5, blank=True, null=True)
    facility = models.CharField('工場', max_length=10, blank=True, null=True)
    attachment_point = models.CharField('添付ポイント', max_length=5, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# 小口工事フィルタ保全G担当者マスタ
class MaintenanceChargePersonMastar(models.Model):
    mng_charge_person = models.ForeignKey(User, verbose_name='保全G担当者', null=True, on_delete=models.PROTECT)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 指図書マスタ
class MaintenanceInstructionNoMaster(models.Model):
    instruction_code = models.CharField('指図書コード', primary_key=True, max_length=17)
    instruction_code_textcontent = models.CharField('テキスト短', max_length=40, blank=True, null=True)
    instruction_type = models.CharField('指図書タイプ', max_length=4, blank=True, null=True)
    instruction_type_name = models.CharField('指図書タイプ名称', max_length=30, blank=True, null=True)
    cost_center = models.CharField('利益センター', max_length=10, blank=True, null=True)
    instruction_status = models.DecimalField('指図ステータス', max_digits=2, decimal_places=0, blank=True, null=True)


# 勘定コードマスタ
class MaintenanceAccountCodeMaster(models.Model):
    account_code = models.CharField('勘定コード', primary_key=True, max_length=16)
    account_code_name = models.CharField('テキスト短', max_length=20, blank=True, null=True)


# 勘定コード定義マスタ
class MaintenanceAccountCodeDefinitionMaster(models.Model):
    item_group_code = models.CharField('品目グループコード', primary_key=True, max_length=2)
    cost_center_class_code = models.CharField('原価属性コード', max_length=2)
    account_code = models.CharField('勘定コード', max_length=16, blank=True, null=True)


# 小口工事原価センタマスタ
class MaintenanceCostCenterMaster(models.Model):
    department = models.ForeignKey(DepartmentMaster, verbose_name='部署', null=True, on_delete=models.PROTECT)
    cost_center = models.CharField('原価センター', max_length=10, blank=True, null=True)
    instruction_no = models.CharField('指図書NO', max_length=17, blank=True, null=True)
    account_code = models.CharField('勘定コード', max_length=16, blank=True, null=True)
    year = models.IntegerField('年度', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 故障対応見積進捗状態マスタ
class MaintenanceEstimateStatusMaster(models.Model):
    status_cd = models.CharField('進捗状態CD',  max_length=10, primary_key=True)
    status_text = models.CharField('進捗状態表記', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順序', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 故障対応見積情報
class MaintenanceEstimate(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    estimate_deadline = models.DateField('決定見積提出期日', blank=True, null=True)
    construction_from = models.DateField('決定工期_FROM', blank=True, null=True)
    construction_to = models.DateField('決定工期_TO', blank=True, null=True)
    delivery_date = models.DateField('決定納期', blank=True, null=True)
    delivery_location = models.CharField('決定納入場所', max_length=100, blank=True, null=True)
    confirmed_vendor_no = models.IntegerField('決定業者NO', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# 故障対応見積業者情報
class MaintenanceEstimateVendor(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    status = models.ForeignKey(MaintenanceEstimateStatusMaster, verbose_name='進捗状態', null=True, on_delete=models.PROTECT)
    vendor_no = models.IntegerField('業者NO', blank=True, null=True)
    vendor_name = models.CharField('業者名', max_length=100, blank=True, null=True)
    req_date = models.DateField('見積依頼日', blank=True, null=True)
    reply_date = models.DateField('見積回答期日', blank=True, null=True)
    estimate_price = models.BigIntegerField('本見積額', blank=True, null=True)
    price_after_discount = models.BigIntegerField('交渉後見積額', blank=True, null=True)
    eva_delivery = models.CharField('評価_工期/納期', max_length=100, blank=True, null=True)
    eva_price = models.BigIntegerField('評価_見積査定額', blank=True, null=True)
    eva_estimate = models.CharField('評価_見積査定', max_length=400, blank=True, null=True)
    eva_last_price = models.CharField('評価_最終金額評価', max_length=100, blank=True, null=True)
    eva_other = models.CharField('評価_その他', max_length=100, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)


# 故障対応検収情報
class MaintenanceInspectionAcceptance(models.Model):
    phenomenon_id = models.IntegerField('案件NO', blank=True, null=True)
    documents_receipt_date = models.DateField('提出資料受領日', blank=True, null=True)
    documents_rem = models.CharField('提出資料備考', max_length=400, blank=True, null=True)
    documents_check_result = models.CharField('提出資料確認結果', max_length=20, blank=True, null=True)
    receipt_send_date = models.DateField('検収書送付日', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)

