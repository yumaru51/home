from django.db import models


# 届出CS管理テーブル
class CsManage(models.Model):
    budget_id = models.IntegerField('予算ID', blank=True, null=True)
    work_id = models.IntegerField('工事ID', blank=True, null=True)
    cs_no = models.IntegerField('届出CS管理NO', blank=True, null=True)
    cs_rev_no = models.IntegerField('RevNo', blank=True, null=True)
    related_cs_no = models.IntegerField('関連届出CS管理NO', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    comment = models.TextField('コメント', max_length=400, blank=True, null=True)
    budget_charge_id = models.IntegerField('担当者ID', blank=True, null=True)
    budget_charge_comment = models.TextField('担当者コメント', max_length=400, blank=True, null=True)
    remand_comment = models.TextField('差戻コメント', max_length=400, blank=True, null=True)
    confirmer_id = models.IntegerField('確認者ID', blank=True, null=True)
    confirmer_comment = models.TextField('確認者コメント', max_length=400, blank=True, null=True)
    confirmer_remand_comment = models.TextField('確認者差戻コメント', max_length=400, blank=True, null=True)
    authorizer_id = models.IntegerField('承認者ID', blank=True, null=True)
    authorizer_comment = models.TextField('原課コメント', max_length=400, blank=True, null=True)
    authorizer_remand_comment = models.TextField('承認者差戻コメント', max_length=400, blank=True, null=True)
    wod_charge_id = models.IntegerField('原課ID', blank=True, null=True)
    wod_charge_comment = models.TextField('原課コメント', max_length=400, blank=True, null=True)
    env_g_confirmer_id_1 = models.IntegerField('確認者ID1', blank=True, null=True)
    env_g_confirmer_comment_1 = models.TextField('確認者コメント1', max_length=400, blank=True, null=True)
    env_g_confirmer_id_2 = models.IntegerField('確認者ID2', blank=True, null=True)
    env_g_confirmer_comment_2 = models.TextField('確認者コメント2', max_length=400, blank=True, null=True)
    env_g_authorizer_id = models.IntegerField('承認者ID', blank=True, null=True)
    env_g_authorizer_comment = models.TextField('承認者コメント', max_length=400, blank=True, null=True)
    hse_director_id = models.IntegerField('環境安全衛生部長ID', blank=True, null=True)
    hse_director_comment = models.TextField('環境安全衛生部長コメント', max_length=400, blank=True, null=True)
    hse_director_remand_comment = models.TextField('環境安全衛生部長差戻コメント', max_length=400, blank=True, null=True)
    ed_director_id = models.IntegerField('環境部長ID', blank=True, null=True)
    ed_director_comment = models.TextField('環境部長コメント', max_length=400, blank=True, null=True)
    hs_director_id = models.IntegerField('安全衛生部長ID', blank=True, null=True)
    hs_director_comment = models.TextField('安全衛生部長コメント', max_length=400, blank=True, null=True)
    wod_director_id = models.IntegerField('原課部長ID', blank=True, null=True)
    wod_director_comment = models.TextField('原課部長コメント', max_length=400, blank=True, null=True)
    gad_director_id = models.IntegerField('総務部長ID', blank=True, null=True)
    gad_director_comment = models.TextField('総務部長コメント', max_length=400, blank=True, null=True)
    cd_director_id = models.IntegerField('工務部長ID', blank=True, null=True)
    cd_director_comment = models.TextField('工務部長コメント', max_length=400, blank=True, null=True)
    env_department_id = models.IntegerField('環境部ID', blank=True, null=True)
    env_department_comment = models.TextField('環境部コメント', max_length=400, blank=True, null=True)
    hs_department_id = models.IntegerField('安全衛生部ID', blank=True, null=True)
    hs_department_comment = models.TextField('安全衛生部コメント', max_length=400, blank=True, null=True)
    wo_department_id = models.IntegerField('原課部ID', blank=True, null=True)
    wo_department_comment = models.TextField('原課部コメント', max_length=400, blank=True, null=True)
    ga_department_id = models.IntegerField('総務部ID', blank=True, null=True)
    ga_department_comment = models.TextField('総務部コメント', max_length=400, blank=True, null=True)
    constr_department_id = models.IntegerField('工務部ID', blank=True, null=True)
    constr_department_comment = models.TextField('工務部コメント', max_length=400, blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 総務届出CSテーブル
class CsGeneralAffairs(models.Model):
    cs_no = models.IntegerField('届出CS管理NO', blank=True, null=True)
    cs_rev_no = models.IntegerField('RevNo', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    factory_location_act = models.BooleanField('工場立地法', blank=True, null=True)
    motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    port_harbour_act = models.BooleanField('港湾法', blank=True, null=True)
    port_regulations = models.BooleanField('港則法', blank=True, null=True)
    buildings_regulations = models.BooleanField('市中高層建築物等条例', blank=True, null=True)
    cityscape_regulations = models.BooleanField('市都市景観条例', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    note = models.TextField('備考', max_length=400, blank=True, null=True)


# 安全衛生管理CSテーブル
class CsSafetyHealth(models.Model):
    cs_no = models.IntegerField('届出CS管理NO', blank=True, null=True)
    cs_rev_no = models.IntegerField('RevNo', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    fire_service_app = models.BooleanField('消防法_危険物承認申請', blank=True, null=True)
    fire_service_app_place = models.CharField('場所', max_length=20, blank=True, null=True)
    fire_service_app_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    fire_service_ntfc = models.BooleanField('消防法_危険物届', blank=True, null=True)
    fire_service_ntfc_place = models.CharField('場所', max_length=20, blank=True, null=True)
    fire_service_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    fire_service_quantity_ntfc = models.BooleanField('消防法_危険物品名数量倍数変更届', blank=True, null=True)
    fire_service_quantity_ntfc_place = models.CharField('場所', max_length=20, blank=True, null=True)
    fire_service_acetylene_gas_ntfc = models.BooleanField('消防法_圧縮アセチレンガス等貯蔵取扱届出', blank=True, null=True)
    fire_service_acetylene_gas_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    fire_service_tentative_app = models.BooleanField('消防法_危険物仮承認申請', blank=True, null=True)
    fire_service_tentative_app_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    fire_prevent_storage_ntfc = models.BooleanField('市火災予防条例_危険物貯蔵取扱届', blank=True, null=True)
    fire_prevent_storage_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    fire_prevent_storage_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    fire_prevent_equip_ntfc = models.BooleanField('市火災予防条例_設備設置届', blank=True, null=True)
    fire_prevent_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    fire_prevent_commencement_ntfc = models.BooleanField('市火災予防条例_防火対象物使用開始届', blank=True, null=True)
    fire_prevent_construction_plan = models.BooleanField('市火災予防条例_消防用設備等　工事計画書', blank=True, null=True)
    fire_prevent_installation_ntfc = models.BooleanField('市火災予防条例_消防用設備等　設置届', blank=True, null=True)
    fire_prevent_hazardous_work_ntfc = models.BooleanField('市火災予防条例_危険作業　開始届', blank=True, null=True)
    fire_prevent_fires_smoke_ntfc = models.BooleanField('市火災予防条例_発煙・発火行為届出書', blank=True, null=True)
    deleterious_substances_list_app = models.BooleanField('劇毒物取締法_劇毒物製造業品目登録 申請', blank=True, null=True)
    deleterious_substances_ntfc = models.BooleanField('劇毒物取締法_劇毒物変更届', blank=True, null=True)
    deleterious_substances_ntfc_purpose = models.CharField('取扱', max_length=20, blank=True, null=True)
    press_gas_app = models.BooleanField('高圧ガス保安法_特定高圧ガス設備申請', blank=True, null=True)
    press_gas_app_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    press_gas_lpg_app = models.BooleanField('高圧ガス保安法_液化石油高圧ガス設備申請', blank=True, null=True)
    press_gas_lpg_app_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    press_gas_frozen_gas_app = models.BooleanField('高圧ガス保安法_冷凍高圧ガス設備申請', blank=True, null=True)
    press_gas_frozen_gas_app_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    press_gas_ntfc = models.BooleanField('高圧ガス保安法_特定高圧ガス設備届', blank=True, null=True)
    press_gas_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    press_gas_lpg_ntfc = models.BooleanField('高圧ガス保安法_液化石油高圧ガス設備届', blank=True, null=True)
    press_gas_lpg_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    press_gas_frozen_gas_ntfc = models.BooleanField('高圧ガス保安法_冷凍高圧ガス設備届', blank=True, null=True)
    press_gas_frozen_gas_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    press_gas_consumption_ntfc = models.BooleanField('高圧ガス保安法_特定高圧ガス消費設備届', blank=True, null=True)
    press_gas_consumption_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    safety_health_equip_ntfc = models.BooleanField('労働安全衛生法_設置物届', blank=True, null=True)
    safety_health_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    safety_health_equip_ntfc_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    safety_health_deleterious_ntfc = models.BooleanField('労働安全衛生法_有害物質届', blank=True, null=True)
    safety_health_deleterious_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    safety_health_deleterious_ntfc_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    safety_health_asbestos = models.BooleanField('労働安全衛生法_石綿障害予防規則', blank=True, null=True)
    safety_health_specified_equip_ntfc = models.BooleanField('労働安全衛生法_設備届', blank=True, null=True)
    safety_health_specified_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    safety_health_specified_equip_ntfc_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    safety_health_installation_report = models.BooleanField('労働安全衛生法_設備設置報告', blank=True, null=True)
    safety_health_installation_report_category = models.CharField('種類', max_length=20, blank=True, null=True)
    safety_health_installation_report_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    radiation_hazards_app = models.BooleanField('放射線障害防止法_放射性同位元素申請', blank=True, null=True)
    radiation_hazards_app_motive = models.CharField('使用/変更', max_length=20, blank=True, null=True)
    petroleum_complexes_act = models.BooleanField('石災法', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    note = models.TextField('備考', max_length=400, blank=True, null=True)


# 環境管轄CSテーブル
class CsEnvironment(models.Model):
    cs_no = models.IntegerField('届出CS管理NO', blank=True, null=True)
    cs_rev_no = models.IntegerField('RevNo', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    air_pollution_equip_ntfc = models.BooleanField('大気汚染防止法_大気汚染物質発生施設届', blank=True, null=True)
    air_pollution_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    air_pollution_equip_ntfc_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    air_pollution_repeal_equip_ntfc = models.BooleanField('大気汚染防止法_大気汚染物質発生施設廃止届', blank=True, null=True)
    air_pollution_repeal_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    air_pollution_voc_ntfc = models.BooleanField('大気汚染防止法_揮発性有機化合物発生施設届', blank=True, null=True)
    air_pollution_voc_ntfc_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    air_pollution_particulates_ntfc = models.BooleanField('大気汚染防止法_特定粉じん排出等作業実施届出', blank=True, null=True)
    water_pollution_ntfc = models.BooleanField('水質汚濁防止法_特定施設届', blank=True, null=True)
    water_pollution_ntfc_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    soil_contamination_ntfc = models.BooleanField('土壌汚染対策法_土地形質変更届', blank=True, null=True)
    waste_equip_app = models.BooleanField('廃棄物処理法_産業廃棄物処理施設申請', blank=True, null=True)
    waste_equip_app_motive = models.CharField('設置/変更', max_length=20, blank=True, null=True)
    waste_repeal_equip_ntfc = models.BooleanField('廃棄物処理法_産業廃棄物処理施設廃止届', blank=True, null=True)
    management_freon_plan = models.BooleanField('フロン排出抑制法_工程管理票', blank=True, null=True)
    living_env_equip_ntfc = models.BooleanField('県生活環境保全条例_指定施設届', blank=True, null=True)
    living_env_equip_ntfc_category = models.CharField('種類', max_length=20, blank=True, null=True)
    living_env_equip_ntfc_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    living_env_nox_emission_plan_ntfc = models.BooleanField('県生活環境保全条例_窒素酸化物排出計画届', blank=True, null=True)
    living_env_soil_survey = models.BooleanField('県生活環境保全条例_土壌調査', blank=True, null=True)
    living_env_water_pumping_app = models.BooleanField('県生活環境保全条例_揚水設備届出/申請', blank=True, null=True)
    pollution_agree_consultation = models.BooleanField('市公害防止協定_公害防止協定事前協議', blank=True, null=True)
    titanium_compatible_report = models.BooleanField('チタン鉱石問題対応方針_報告書', blank=True, null=True)
    water_purification_tanks_ntfc = models.BooleanField('浄化槽法_浄化槽届出', blank=True, null=True)
    water_purification_tanks_ntfc_amendment = models.CharField('改廃', max_length=20, blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    note = models.TextField('備考', max_length=400, blank=True, null=True)


# 工務管轄CSテーブル
class CsEngineering(models.Model):
    cs_no = models.IntegerField('届出CS管理NO', blank=True, null=True)
    cs_rev_no = models.IntegerField('RevNo', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    building_standards_act = models.BooleanField('建築基準法_確認申請', blank=True, null=True)
    building_standards_act_category = models.CharField('種類', max_length=20, blank=True, null=True)
    energy_rationalization_act = models.BooleanField('省エネ法_特定建築物届出', blank=True, null=True)
    energy_rationalization_act_category = models.CharField('種類', max_length=20, blank=True, null=True)
    energy_rationalization_act_action = models.CharField('扱い', max_length=20, blank=True, null=True)
    construction_recycling = models.BooleanField('建設リサイクル法', blank=True, null=True)
    construction_recycling_category = models.CharField('種類', max_length=20, blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    note = models.TextField('備考', max_length=400, blank=True, null=True)


# 届出進捗テーブル
class CsNotificationProgress(models.Model):
    cs_no = models.IntegerField('CS_NO', blank=True, null=True)
    sub_no = models.IntegerField('届出ID', blank=True, null=True)
    laws_name = models.CharField('法令名', max_length=20, blank=True, null=True)
    law_code = models.CharField('コード', max_length=20, blank=True, null=True)
    laws_detail_name = models.CharField('法令詳細分類名称', max_length=60, blank=True, null=True)
    department_name = models.CharField('所管部署', max_length=20, blank=True, null=True)
    limit_date = models.CharField('提出期限', max_length=20, blank=True, null=True)
    witness_inspection = models.IntegerField('立会検査', blank=True, null=True)
    submission_date = models.DateField('提出日', blank=True, null=True)
    notification_date = models.DateField('届出日', blank=True, null=True)
    permit_date = models.DateField('許可日', blank=True, null=True)
    permit_no = models.CharField('許可番号', max_length=100, blank=True, null=True)

