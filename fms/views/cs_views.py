# datetimeをインポート
import datetime
import time
# ログインユーザーを使用するmoduleをインポート
import math
import traceback

from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.db import connections
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# formsをインポート
from fms.forms import BudgetEditFormLeft, BudgetEditFormCenter, BudgetEditFormRight
# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import StepDisplayItem, StepRelation
from fms.models import BudgetLaw, BudgetEquipment
from fms.models import CsManage, CsGeneralAffairs, CsSafetyHealth, CsEnvironment, CsEngineering
from fms.models import FactoryLocationActMotiveMaster
from fms.models import FireServiceAppPlaceMaster, FireServiceAppActionMaster, FireServiceNtfcPlaceMaster, FireServiceNtfcAmendmentMaster, FireServiceQuantityNtfcPlaceMaster, FireServiceAcetyleneGasNtfcAmendmentMaster, FireServiceTentativeAppActionMaster
from fms.models import FirePreventStorageNtfcCategoryMaster, FirePreventStorageNtfcAmendmentMaster, FirePreventEquipNtfcCategoryMaster
from fms.models import DeleteriousSubstancesNtfcPurposeMaster
from fms.models import PressGasAppMotiveMaster, PressGasLpgAppMotiveMaster, PressGasFrozenGasAppMotiveMaster, PressGasNtfcAmendmentMaster, PressGasLpgNtfcAmendmentMaster, PressGasFrozenGasNtfcAmendmentMaster, PressGasConsumptionNtfcAmendmentMaster
from fms.models import SafetyHealthEquipNtfcCategoryMaster, SafetyHealthEquipNtfcMotiveMaster, SafetyHealthDeleteriousNtfcCategoryMaster, SafetyHealthDeleteriousMotiveNtfcMaster, SafetyHealthSpecifiedEquipNtfcCategoryMaster, SafetyHealthSpecifiedEquipNtfcMotiveMaster, SafetyHealthInstallationReportCategoryMaster
from fms.models import RadiationHazardsAppMotiveMaster
from fms.models import AirPollutionEquipNtfcCategoryMaster, AirPollutionEquipNtfcMotiveMaster, AirPollutionRepealEquipNtfcCategoryMaster, AirPollutionVocNtfcActionMaster
from fms.models import WaterPollutionNtfcActionMaster
from fms.models import WasteEquipAppMotiveMaster
from fms.models import LivingEnvEquipNtfcCategoryMaster, LivingEnvEquipNtfcActionMaster
from fms.models import WaterPurificationTanksNtfcAmendmentMaster
from fms.models import BuildingStandardsActCategoryMaster
from fms.models import EnergyRationalizationActCategoryMaster, EnergyRationalizationActActionMaster
from fms.models import ConstructionRecyclingCategoryMaster
from fms.models import CsNotificationProgress
from fms.views.common_def_views import convert_charge_department, get_next_operator_cs
from fms.views.common_def_views import get_ng_character_list
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from django.utils.timezone import make_aware
from fms.views.notice_mail_views import step_notice


# 総務管轄の法令一覧画面を表示
@login_required
@require_POST
def cs_data_info(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_id = int(request.POST['target_unique_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        first_open_flag = 0

        # 新規登録(target_id=0)を判定
        # 新規ではないときの処理
        if target_unique_id > 0:
            # 対象データの現在の工程IDを取得
            cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)

            if CsGeneralAffairs.objects.filter(cs_no=cs_manage_data.cs_no, lost_flag=0).count() == 0:
                first_open_flag = 1
            else:
                cs_general_affairs_data = CsGeneralAffairs.objects.get(cs_no=cs_manage_data.cs_no, lost_flag=0)
                # 工場立地法
                if cs_general_affairs_data.factory_location_act is not None:
                    factory_location_act = cs_general_affairs_data.factory_location_act
                else:
                    factory_location_act = False

                # 工場立地法_設置/変更
                if cs_general_affairs_data.motive is not None:
                    factory_location_act_motive = cs_general_affairs_data.motive
                else:
                    factory_location_act_motive = "設置/変更"

                # 港湾法
                if cs_general_affairs_data.port_harbour_act is not None:
                    port_harbour_act = cs_general_affairs_data.port_harbour_act
                else:
                    port_harbour_act = False

                # 港則法
                if cs_general_affairs_data.port_regulations is not None:
                    port_regulations = cs_general_affairs_data.port_regulations
                else:
                    port_regulations = False

                # 市中高層建築物等条例
                if cs_general_affairs_data.buildings_regulations is not None:
                    buildings_regulations = cs_general_affairs_data.buildings_regulations
                else:
                    buildings_regulations = False

                # 市都市景観条例
                if cs_general_affairs_data.cityscape_regulations is not None:
                    cityscape_regulations = cs_general_affairs_data.cityscape_regulations
                else:
                    cityscape_regulations = False

                # 備考
                if cs_general_affairs_data.note is not None:
                    note = cs_general_affairs_data.note
                else:
                    note = ""

                # rev_no
                # チェックシートデータののRevNO取得
                cs_rev_no = cs_general_affairs_data.cs_rev_no

                # 継承する値を取得
                cs_no = cs_general_affairs_data.cs_no
                str_cs_no = str(cs_no)
                target_budget_id = cs_manage_data.budget_id
                str_target_budget_id = str(target_budget_id)
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                # present_step_data = Progress.objects.get(target_id=cs_no, target='cs')
                # present_step = present_step_data.present_step
                present_step = int(request.POST['this_step'])
                step_data = StepMaster.objects.get(step_id=present_step, lost_flag=0)
                step_name = step_data.step_name
                previous_step = step_data.previous_step
                # 次のstepを取得
                next_step_data = StepRelation.objects.filter(step_id=present_step, lost_flag=0).order_by('display_order')[0]
                next_step = next_step_data.next_step
                # 次のstepの情報取得
                step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)

                charge_department_class = convert_charge_department(step_data.charge_department_class)

                charge_name = cs_manage_data.budget_charge_id
                if charge_name is not None:
                    charge_data = User.objects.get(username=charge_name, lost_flag=0)
                else:
                    charge_data = budget_data.budget_department_charge_person_id
                cs_department = cs_manage_data.wo_department_id
                if cs_department is None:
                    cs_department = budget_data.budget_main_department_id
                department_data = DepartmentMaster.objects.get(department_cd=cs_department)
                department_name = department_data.department_name
                if charge_department_class == 'BD':
                    next_division = department_data.division_cd
                    next_department = department_data.department_cd
                else:
                    next_division = ""
                    next_department = charge_department_class

                # rev_noの古い同じ予算IDのデータの有無を確認
                old_cs_data_num = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).count()

        if target_unique_id == 0 or first_open_flag == 1:
            # 新規登録時処理
            cs_general_affairs_data = ""

            # 工場立地法
            factory_location_act = False

            # 工場立地法_設置/変更
            factory_location_act_motive = "設置/変更"

            # 港湾法
            port_harbour_act = False

            # 港則法
            port_regulations = False

            # 市中高層建築物等条例
            buildings_regulations = False

            # 市都市景観条例
            cityscape_regulations = False

            # 備考
            note = ""

            if first_open_flag == 1:
                cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)
                cs_no = cs_manage_data.cs_no
                str_cs_no = str(cs_no)
                str_target_budget_id = str(cs_manage_data.budget_id)
            else:
                str_cs_no = ""
                str_target_budget_id = ""
                cs_no = 0
            cs_rev_no = 0
            department_name = ""
            step_name = ""
            previous_step = 0
            present_step = new_step
            next_division = user_division_cd
            next_department = user_department_cd
            charge_department_class = "BD"
            charge_data = ""
            charge_name = ""
            old_cs_data_num = 0

            # フラグOFF
            first_open_flag = 0

        # マスタソースとなるリスト抽出
        # 工場立地法_設置/変更リスト
        factory_location_act_motive_list = FactoryLocationActMotiveMaster.objects.filter(lost_flag=0).all()
        # factory_location_act_motive_list = FactoryLocationActMotiveMaster.objects.all()

        # rev_no比較
        if old_cs_data_num > 0:
            old_cs_data = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).all().order_by('-id')[0]
        else:
            old_cs_data = ""

        # データ編集機能要否判定
        cs_edit_action_num = 0

        cs_edit_action_num = cs_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                     target_table='cs_general_affairs').count()

        edit_flag = 0

        if cs_edit_action_num > 0:
            edit_flag = 1

        # データ保存
        data = {
            'cs_general_affairs_data': cs_general_affairs_data,
            'old_cs_data_num': old_cs_data_num,
            'old_cs_data': old_cs_data,
            't_username': t_username,
            't_user_last_name': t_user_last_name,
            't_user_first_name': t_user_first_name,
            'department_name': department_name,
            'charge_name': charge_name,
            'charge_data': charge_data,
            'step_name': step_name,
            'previous_step': previous_step,
            'charge_department_class': charge_department_class,
            'next_division': next_division,
            'next_department': next_department,
            'factory_location_act': factory_location_act,
            'factory_location_act_motive': factory_location_act_motive,
            'factory_location_act_motive_list': factory_location_act_motive_list,
            'port_harbour_act': port_harbour_act,
            'port_regulations': port_regulations,
            'buildings_regulations': buildings_regulations,
            'cityscape_regulations': cityscape_regulations,
            'cs_no': str_cs_no,
            'target_budget_id': str_target_budget_id,
            # 'relation_budget_id': str_relation_budget_id,
            'target_id': cs_no,
            # 'user_authority': user_authority,
            # 'confirm_user': confirm_user,
            # 'permit_user': permit_user,
            # 'level5_step_id': level5_step_id,
            'note': note,
            'cs_rev_no': cs_rev_no,
            'ga_edit_flag': edit_flag
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/check_sheet/cs_general_affairs_edit.html', data)

        else:
            return render(request, 'fms/parts/check_sheet/cs_general_affairs_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 安全衛生管轄の法令一覧画面を表示
@login_required
@require_POST
def cs_safety_health_data_info(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_id = int(request.POST['target_unique_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        first_open_flag = 0

        # 新規登録(target_id=0)を判定
        # 新規ではないときの処理
        if target_unique_id > 0:
            # 対象データの現在の工程IDを取得
            cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)

            if CsSafetyHealth.objects.filter(cs_no=cs_manage_data.cs_no, lost_flag=0).count() == 0:
                first_open_flag = 1
            else:
                cs_safety_health_data = CsSafetyHealth.objects.get(cs_no=cs_manage_data.cs_no, lost_flag=0)

                # 消防法_危険物承認申請
                if cs_safety_health_data.fire_service_app is not None:
                    fire_service_app = cs_safety_health_data.fire_service_app
                else:
                    fire_service_app = False

                # 消防法_危険物承認申請_場所
                if cs_safety_health_data.fire_service_app_place is not None:
                    fire_service_app_place = cs_safety_health_data.fire_service_app_place
                else:
                    fire_service_app_place = "場所"

                # 消防法_危険物承認申請_扱い
                if cs_safety_health_data.fire_service_app_action is not None:
                    fire_service_app_action = cs_safety_health_data.fire_service_app_action
                else:
                    fire_service_app_action = "扱い"

                # 消防法_危険物届
                if cs_safety_health_data.fire_service_ntfc is not None:
                    fire_service_ntfc = cs_safety_health_data.fire_service_ntfc
                else:
                    fire_service_ntfc = False

                # 消防法_危険物届_場所
                if cs_safety_health_data.fire_service_ntfc_place is not None:
                    fire_service_ntfc_place = cs_safety_health_data.fire_service_ntfc_place
                else:
                    fire_service_ntfc_place = "場所"

                # 消防法_危険物届_改廃
                if cs_safety_health_data.fire_service_ntfc_amendment is not None:
                    fire_service_ntfc_amendment = cs_safety_health_data.fire_service_ntfc_amendment
                else:
                    fire_service_ntfc_amendment = "改廃"

                # 消防法_危険物品名数量倍数変更届
                if cs_safety_health_data.fire_service_quantity_ntfc is not None:
                    fire_service_quantity_ntfc = cs_safety_health_data.fire_service_quantity_ntfc
                else:
                    fire_service_quantity_ntfc = False

                # 消防法_危険物品名数量倍数変更届_場所
                if cs_safety_health_data.fire_service_quantity_ntfc_place is not None:
                    fire_service_quantity_ntfc_place = cs_safety_health_data.fire_service_quantity_ntfc_place
                else:
                    fire_service_quantity_ntfc_place = "場所"

                # 消防法_圧縮アセチレンガス等貯蔵取扱届出
                if cs_safety_health_data.fire_service_acetylene_gas_ntfc is not None:
                    fire_service_acetylene_gas_ntfc = cs_safety_health_data.fire_service_acetylene_gas_ntfc
                else:
                    fire_service_acetylene_gas_ntfc = False

                # 消防法_圧縮アセチレンガス等貯蔵取扱届出_改廃
                if cs_safety_health_data.fire_service_acetylene_gas_ntfc_amendment is not None:
                    fire_service_acetylene_gas_ntfc_amendment = cs_safety_health_data.fire_service_acetylene_gas_ntfc_amendment
                else:
                    fire_service_acetylene_gas_ntfc_amendment = "改廃"

                # 消防法_危険物仮承認申請
                if cs_safety_health_data.fire_service_tentative_app is not None:
                    fire_service_tentative_app = cs_safety_health_data.fire_service_tentative_app
                else:
                    fire_service_tentative_app = False

                # 消防法_危険物仮承認申請_扱い
                if cs_safety_health_data.fire_service_tentative_app_action is not None:
                    fire_service_tentative_app_action = cs_safety_health_data.fire_service_tentative_app_action
                else:
                    fire_service_tentative_app_action = "扱い"

                # 市火災予防条例_危険物貯蔵取扱届
                if cs_safety_health_data.fire_prevent_storage_ntfc is not None:
                    fire_prevent_storage_ntfc = cs_safety_health_data.fire_prevent_storage_ntfc
                else:
                    fire_prevent_storage_ntfc = False

                # 市火災予防条例_危険物貯蔵取扱届_種類
                if cs_safety_health_data.fire_prevent_storage_ntfc_category is not None:
                    fire_prevent_storage_ntfc_category = cs_safety_health_data.fire_prevent_storage_ntfc_category
                else:
                    fire_prevent_storage_ntfc_category = "種類"

                # 市火災予防条例_危険物貯蔵取扱届_改廃
                if cs_safety_health_data.fire_prevent_storage_ntfc_amendment is not None:
                    fire_prevent_storage_ntfc_amendment = cs_safety_health_data.fire_prevent_storage_ntfc_amendment
                else:
                    fire_prevent_storage_ntfc_amendment = "改廃"

                # 市火災予防条例_設備設置届
                if cs_safety_health_data.fire_prevent_equip_ntfc is not None:
                    fire_prevent_equip_ntfc = cs_safety_health_data.fire_prevent_equip_ntfc
                else:
                    fire_prevent_equip_ntfc = False

                # 市火災予防条例_設備設置届_種類
                if cs_safety_health_data.fire_prevent_equip_ntfc_category is not None:
                    fire_prevent_equip_ntfc_category = cs_safety_health_data.fire_prevent_equip_ntfc_category
                else:
                    fire_prevent_equip_ntfc_category = "種類"

                # 市火災予防条例_防火対象物使用開始届
                if cs_safety_health_data.fire_prevent_commencement_ntfc is not None:
                    fire_prevent_commencement_ntfc = cs_safety_health_data.fire_prevent_commencement_ntfc
                else:
                    fire_prevent_commencement_ntfc = False

                # 市火災予防条例_消防用設備等　工事計画書
                if cs_safety_health_data.fire_prevent_construction_plan is not None:
                    fire_prevent_construction_plan = cs_safety_health_data.fire_prevent_construction_plan
                else:
                    fire_prevent_construction_plan = False

                # 市火災予防条例_消防用設備等　設置届
                if cs_safety_health_data.fire_prevent_installation_ntfc is not None:
                    fire_prevent_installation_ntfc = cs_safety_health_data.fire_prevent_installation_ntfc
                else:
                    fire_prevent_installation_ntfc = False

                # 市火災予防条例_危険作業　開始届
                if cs_safety_health_data.fire_prevent_hazardous_work_ntfc is not None:
                    fire_prevent_hazardous_work_ntfc = cs_safety_health_data.fire_prevent_hazardous_work_ntfc
                else:
                    fire_prevent_hazardous_work_ntfc = False

                # 市火災予防条例_発煙・発火行為届出書
                if cs_safety_health_data.fire_prevent_fires_smoke_ntfc is not None:
                    fire_prevent_fires_smoke_ntfc = cs_safety_health_data.fire_prevent_fires_smoke_ntfc
                else:
                    fire_prevent_fires_smoke_ntfc = False

                # 劇毒物取締法_劇毒物製造業品目登録 申請
                if cs_safety_health_data.deleterious_substances_list_app is not None:
                    deleterious_substances_list_app = cs_safety_health_data.deleterious_substances_list_app
                else:
                    deleterious_substances_list_app = False

                # 劇毒物取締法_劇毒物変更届
                if cs_safety_health_data.deleterious_substances_ntfc is not None:
                    deleterious_substances_ntfc = cs_safety_health_data.deleterious_substances_ntfc
                else:
                    deleterious_substances_ntfc = False

                # 劇毒物取締法_劇毒物変更届_取扱
                if cs_safety_health_data.deleterious_substances_ntfc_purpose is not None:
                    deleterious_substances_ntfc_purpose = cs_safety_health_data.deleterious_substances_ntfc_purpose
                else:
                    deleterious_substances_ntfc_purpose = "取扱"

                # 高圧ガス保安法_特定高圧ガス設備申請
                if cs_safety_health_data.press_gas_app is not None:
                    press_gas_app = cs_safety_health_data.press_gas_app
                else:
                    press_gas_app = False

                # 高圧ガス保安法_特定高圧ガス設備申請_設置/変更
                if cs_safety_health_data.press_gas_app_motive is not None:
                    press_gas_app_motive = cs_safety_health_data.press_gas_app_motive
                else:
                    press_gas_app_motive = "設置/変更"

                # 高圧ガス保安法_液化石油高圧ガス設備申請
                if cs_safety_health_data.press_gas_lpg_app is not None:
                    press_gas_lpg_app = cs_safety_health_data.press_gas_lpg_app
                else:
                    press_gas_lpg_app = False

                # 高圧ガス保安法_液化石油高圧ガス設備申請_設置/変更
                if cs_safety_health_data.press_gas_lpg_app_motive is not None:
                    press_gas_lpg_app_motive = cs_safety_health_data.press_gas_lpg_app_motive
                else:
                    press_gas_lpg_app_motive = "設置/変更"

                # 高圧ガス保安法_冷凍高圧ガス設備申請
                if cs_safety_health_data.press_gas_frozen_gas_app is not None:
                    press_gas_frozen_gas_app = cs_safety_health_data.press_gas_frozen_gas_app
                else:
                    press_gas_frozen_gas_app = False

                # 高圧ガス保安法_冷凍高圧ガス設備申請_設置/変更
                if cs_safety_health_data.press_gas_frozen_gas_app_motive is not None:
                    press_gas_frozen_gas_app_motive = cs_safety_health_data.press_gas_frozen_gas_app_motive
                else:
                    press_gas_frozen_gas_app_motive = "設置/変更"

                # 高圧ガス保安法_特定高圧ガス設備届
                if cs_safety_health_data.press_gas_ntfc is not None:
                    press_gas_ntfc = cs_safety_health_data.press_gas_ntfc
                else:
                    press_gas_ntfc = False

                # 高圧ガス保安法_特定高圧ガス設備届_改廃
                if cs_safety_health_data.press_gas_ntfc_amendment is not None:
                    press_gas_ntfc_amendment = cs_safety_health_data.press_gas_ntfc_amendment
                else:
                    press_gas_ntfc_amendment = "改廃"

                # 高圧ガス保安法_液化石油高圧ガス設備届
                if cs_safety_health_data.press_gas_lpg_ntfc is not None:
                    press_gas_lpg_ntfc = cs_safety_health_data.press_gas_lpg_ntfc
                else:
                    press_gas_lpg_ntfc = False

                # 高圧ガス保安法_液化石油高圧ガス設備届_改廃
                if cs_safety_health_data.press_gas_lpg_ntfc_amendment is not None:
                    press_gas_lpg_ntfc_amendment = cs_safety_health_data.press_gas_lpg_ntfc_amendment
                else:
                    press_gas_lpg_ntfc_amendment = "改廃"

                # 高圧ガス保安法_冷凍高圧ガス設備届
                if cs_safety_health_data.press_gas_frozen_gas_ntfc is not None:
                    press_gas_frozen_gas_ntfc = cs_safety_health_data.press_gas_frozen_gas_ntfc
                else:
                    press_gas_frozen_gas_ntfc = False

                # 高圧ガス保安法_冷凍高圧ガス設備届_改廃
                if cs_safety_health_data.press_gas_frozen_gas_ntfc_amendment is not None:
                    press_gas_frozen_gas_ntfc_amendment = cs_safety_health_data.press_gas_frozen_gas_ntfc_amendment
                else:
                    press_gas_frozen_gas_ntfc_amendment = "改廃"

                # 高圧ガス保安法_特定高圧ガス消費設備届
                if cs_safety_health_data.press_gas_consumption_ntfc is not None:
                    press_gas_consumption_ntfc = cs_safety_health_data.press_gas_consumption_ntfc
                else:
                    press_gas_consumption_ntfc = False

                # 高圧ガス保安法_特定高圧ガス消費設備届_改廃
                if cs_safety_health_data.press_gas_consumption_ntfc_amendment is not None:
                    press_gas_consumption_ntfc_amendment = cs_safety_health_data.press_gas_consumption_ntfc_amendment
                else:
                    press_gas_consumption_ntfc_amendment = "改廃"

                # 労働安全衛生法_設置物届
                if cs_safety_health_data.safety_health_equip_ntfc is not None:
                    safety_health_equip_ntfc = cs_safety_health_data.safety_health_equip_ntfc
                else:
                    safety_health_equip_ntfc = False

                # 労働安全衛生法_設置物届_種類
                if cs_safety_health_data.safety_health_equip_ntfc_category is not None:
                    safety_health_equip_ntfc_category = cs_safety_health_data.safety_health_equip_ntfc_category
                else:
                    safety_health_equip_ntfc_category = "種類"

                # 労働安全衛生法_設置物届_設置/変更
                if cs_safety_health_data.safety_health_equip_ntfc_motive is not None:
                    safety_health_equip_ntfc_motive = cs_safety_health_data.safety_health_equip_ntfc_motive
                else:
                    safety_health_equip_ntfc_motive = "設置/変更"

                # 労働安全衛生法_有害物質届
                if cs_safety_health_data.safety_health_deleterious_ntfc is not None:
                    safety_health_deleterious_ntfc = cs_safety_health_data.safety_health_deleterious_ntfc
                else:
                    safety_health_deleterious_ntfc = False

                # 労働安全衛生法_有害物質届_種類
                if cs_safety_health_data.safety_health_deleterious_ntfc_category is not None:
                    safety_health_deleterious_ntfc_category = cs_safety_health_data.safety_health_deleterious_ntfc_category
                else:
                    safety_health_deleterious_ntfc_category = "種類"

                # 労働安全衛生法_有害物質届_設置/変更
                if cs_safety_health_data.safety_health_deleterious_ntfc_motive is not None:
                    safety_health_deleterious_ntfc_motive = cs_safety_health_data.safety_health_deleterious_ntfc_motive
                else:
                    safety_health_deleterious_ntfc_motive = "設置/変更"

                # 労働安全衛生法_石綿障害予防規則
                if cs_safety_health_data.safety_health_asbestos is not None:
                    safety_health_asbestos = cs_safety_health_data.safety_health_asbestos
                else:
                    safety_health_asbestos = False

                # 労働安全衛生法_設備届
                if cs_safety_health_data.safety_health_specified_equip_ntfc is not None:
                    safety_health_specified_equip_ntfc = cs_safety_health_data.safety_health_specified_equip_ntfc
                else:
                    safety_health_specified_equip_ntfc = False

                # 労働安全衛生法_設備届_種類
                if cs_safety_health_data.safety_health_specified_equip_ntfc_category is not None:
                    safety_health_specified_equip_ntfc_category = cs_safety_health_data.safety_health_specified_equip_ntfc_category
                else:
                    safety_health_specified_equip_ntfc_category = "種類"

                # 労働安全衛生法_設備届_設置/変更
                if cs_safety_health_data.safety_health_specified_equip_ntfc_motive is not None:
                    safety_health_specified_equip_ntfc_motive = cs_safety_health_data.safety_health_specified_equip_ntfc_motive
                else:
                    safety_health_specified_equip_ntfc_motive = "設置/変更"

                # 労働安全衛生法_設備設置報告
                if cs_safety_health_data.safety_health_installation_report is not None:
                    safety_health_installation_report = cs_safety_health_data.safety_health_installation_report
                else:
                    safety_health_installation_report = False

                # 労働安全衛生法_設備設置報告_種類
                if cs_safety_health_data.safety_health_installation_report_category is not None:
                    safety_health_installation_report_category = cs_safety_health_data.safety_health_installation_report_category
                else:
                    safety_health_installation_report_category = "種類"

                # # 労働安全衛生法_設備設置報告_設置/変更
                # if cs_safety_health_data.safety_health_installation_report_motive is not None:
                #     safety_health_installation_report_motive = cs_safety_health_data.safety_health_installation_report_motive
                # else:
                #     safety_health_installation_report_motive = "設置/変更"

                # 放射線障害防止法_放射性同位元素申請
                if cs_safety_health_data.radiation_hazards_app is not None:
                    radiation_hazards_app = cs_safety_health_data.radiation_hazards_app
                else:
                    radiation_hazards_app = False

                # 放射線障害防止法_放射性同位元素申請_使用/変更
                if cs_safety_health_data.radiation_hazards_app_motive is not None:
                    radiation_hazards_app_motive = cs_safety_health_data.radiation_hazards_app_motive
                else:
                    radiation_hazards_app_motive = "使用/変更"

                # 石災法
                if cs_safety_health_data.petroleum_complexes_act is not None:
                    petroleum_complexes_act = cs_safety_health_data.petroleum_complexes_act
                else:
                    petroleum_complexes_act = False

                # 備考
                if cs_safety_health_data.note is not None:
                    note = cs_safety_health_data.note
                else:
                    note = ""

                # rev_no
                # チェックシートデータののRevNO取得
                cs_rev_no = cs_safety_health_data.cs_rev_no

                # 継承する値を取得
                cs_no = cs_safety_health_data.cs_no
                str_cs_no = str(cs_no)
                target_budget_id = cs_manage_data.budget_id
                str_target_budget_id = str(target_budget_id)
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                # present_step_data = Progress.objects.get(target_id=cs_no, target='cs')
                # present_step = present_step_data.present_step
                present_step = int(request.POST['this_step'])
                step_data = StepMaster.objects.get(step_id=present_step, lost_flag=0)
                step_name = step_data.step_name
                previous_step = step_data.previous_step
                # 次のstepを取得
                next_step_data = StepRelation.objects.filter(step_id=present_step, lost_flag=0).order_by('display_order')[0]
                next_step = next_step_data.next_step
                # 次のstepの情報取得
                step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)

                charge_department_class = convert_charge_department(step_data.charge_department_class)

                charge_name = cs_manage_data.budget_charge_id
                if charge_name is not None:
                    charge_data = User.objects.get(username=charge_name, lost_flag=0)
                else:
                    charge_data = budget_data.budget_department_charge_person_id
                cs_department = cs_manage_data.wo_department_id
                if cs_department is None:
                    cs_department = budget_data.budget_main_department_id
                department_data = DepartmentMaster.objects.get(department_cd=cs_department)
                department_name = department_data.department_name
                if charge_department_class == 'BD':
                    next_division = department_data.division_cd
                    next_department = department_data.department_cd
                else:
                    next_division = ""
                    next_department = charge_department_class

                # rev_noの古い同じ予算IDのデータの有無を確認
                old_cs_data_num = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).count()

        if target_unique_id == 0 or first_open_flag == 1:
            # 新規登録時処理
            cs_safety_health_data = ""

            # 消防法_危険物承認申請
            fire_service_app = False

            # 消防法_危険物承認申請_場所
            fire_service_app_place = "場所"

            # 消防法_危険物承認申請_場所
            fire_service_app_action = "扱い"

            # 消防法_危険物届
            fire_service_ntfc = False

            # 消防法_危険物届_場所
            fire_service_ntfc_place = "場所"

            # 消防法_危険物届_場所
            fire_service_ntfc_amendment = "扱い"

            # 消防法_危険物品名数量倍数変更届
            fire_service_quantity_ntfc = False

            # 消防法_危険物品名数量倍数変更届_場所
            fire_service_quantity_ntfc_place = "場所"

            # 消防法_圧縮アセチレンガス等貯蔵取扱届出
            fire_service_acetylene_gas_ntfc = False

            # 消防法_圧縮アセチレンガス等貯蔵取扱届出_改廃
            fire_service_acetylene_gas_ntfc_amendment = "改廃"

            # 消防法_危険物仮承認申請
            fire_service_tentative_app = False

            # 消防法_危険物仮承認申請_扱い
            fire_service_tentative_app_action = "扱い"

            # 市火災予防条例_危険物貯蔵取扱届
            fire_prevent_storage_ntfc = False

            # 市火災予防条例_危険物貯蔵取扱届_種類
            fire_prevent_storage_ntfc_category = "種類"

            # 市火災予防条例_危険物貯蔵取扱届_改廃
            fire_prevent_storage_ntfc_amendment = "改廃"

            # 市火災予防条例_設備設置届
            fire_prevent_equip_ntfc = False

            # 市火災予防条例_設備設置届_種類
            fire_prevent_equip_ntfc_category = "種類"

            # 市火災予防条例_防火対象物使用開始届
            fire_prevent_commencement_ntfc = False

            # 市火災予防条例_消防用設備等　工事計画書
            fire_prevent_construction_plan = False

            # 市火災予防条例_消防用設備等　設置届
            fire_prevent_installation_ntfc = False

            # 市火災予防条例_危険作業　開始届
            fire_prevent_hazardous_work_ntfc = False

            # 市火災予防条例_発煙・発火行為届出書
            fire_prevent_fires_smoke_ntfc = False

            # 劇毒物取締法_劇毒物製造業品目登録 申請
            deleterious_substances_list_app = False

            # 劇毒物取締法_劇毒物変更届
            deleterious_substances_ntfc = False

            # 劇毒物取締法_劇毒物変更届_取扱
            deleterious_substances_ntfc_purpose = "取扱"

            # 高圧ガス保安法_特定高圧ガス設備申請
            press_gas_app = False

            # 高圧ガス保安法_特定高圧ガス設備申請_設置/変更
            press_gas_app_motive = "設置/変更"

            # 高圧ガス保安法_液化石油高圧ガス設備申請
            press_gas_lpg_app = False

            # 高圧ガス保安法_液化石油高圧ガス設備申請_設置/変更
            press_gas_lpg_app_motive = "設置/変更"

            # 高圧ガス保安法_冷凍高圧ガス設備申請
            press_gas_frozen_gas_app = False

            # 高圧ガス保安法_冷凍高圧ガス設備申請_設置/変更
            press_gas_frozen_gas_app_motive = "設置/変更"

            # 高圧ガス保安法_特定高圧ガス設備届
            press_gas_ntfc = False

            # 高圧ガス保安法_特定高圧ガス設備届_改廃
            press_gas_ntfc_amendment = "改廃"

            # 高圧ガス保安法_液化石油高圧ガス設備届
            press_gas_lpg_ntfc = False

            # 高圧ガス保安法_液化石油高圧ガス設備届_改廃
            press_gas_lpg_ntfc_amendment = "改廃"

            # 高圧ガス保安法_冷凍高圧ガス設備届
            press_gas_frozen_gas_ntfc = False

            # 高圧ガス保安法_冷凍高圧ガス設備届_改廃
            press_gas_frozen_gas_ntfc_amendment = "改廃"

            # 高圧ガス保安法_特定高圧ガス消費設備届
            press_gas_consumption_ntfc = False

            # 高圧ガス保安法_特定高圧ガス消費設備届_改廃
            press_gas_consumption_ntfc_amendment = "改廃"

            # 労働安全衛生法_設置物届
            safety_health_equip_ntfc = False

            # 労働安全衛生法_設置物届_種類
            safety_health_equip_ntfc_category = "種類"

            # 労働安全衛生法_設置物届_設置/変更
            safety_health_equip_ntfc_motive = "設置/変更"

            # 労働安全衛生法_有害物質届
            safety_health_deleterious_ntfc = False

            # 労働安全衛生法_有害物質届_種類
            safety_health_deleterious_ntfc_category = "種類"

            # 労働安全衛生法_有害物質届_設置/変更
            safety_health_deleterious_ntfc_motive = "設置/変更"

            # 労働安全衛生法_石綿障害予防規則
            safety_health_asbestos = False

            # 労働安全衛生法_設備届
            safety_health_specified_equip_ntfc = False

            # 労働安全衛生法_設備届_種類
            safety_health_specified_equip_ntfc_category = "種類"

            # 労働安全衛生法_設備届_設置/変更
            safety_health_specified_equip_ntfc_motive = "設置/変更"

            # 労働安全衛生法_設備設置報告
            safety_health_installation_report = False

            # 労働安全衛生法_設備設置報告_種類
            safety_health_installation_report_category = "種類"

            # # 労働安全衛生法_設備設置報告_設置/変更
            # safety_health_installation_report_motive = "設置/変更"

            # 放射線障害防止法_放射性同位元素申請
            radiation_hazards_app = False

            # 放射線障害防止法_放射性同位元素申請_使用/変更
            radiation_hazards_app_motive = "使用/変更"

            # 石災法
            petroleum_complexes_act = False

            # 備考
            note = ""

            if first_open_flag == 1:
                cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)
                cs_no = cs_manage_data.cs_no
                str_cs_no = str(cs_no)
                str_target_budget_id = str(cs_manage_data.budget_id)
            else:
                cs_no = 0
                str_cs_no = ""
                str_target_budget_id = ""
            cs_rev_no = 0
            department_name = ""
            step_name = ""
            previous_step = 0
            present_step = new_step
            next_division = user_division_cd
            next_department = user_department_cd
            charge_department_class = "BD"
            charge_data = ""
            charge_name = ""
            old_cs_data_num = 0

            # フラグOFF
            first_open_flag = 0

        # マスタソースとなるリスト抽出
        # 消防法_危険物承認申請_場所リスト
        fire_service_app_place_list = FireServiceAppPlaceMaster.objects.filter(lost_flag=0).all()

        # 消防法_危険物承認申請_扱いリスト
        fire_service_app_action_list = FireServiceAppActionMaster.objects.filter(lost_flag=0).all()

        # 消防法_危険物届_場所リスト
        fire_service_ntfc_place_list = FireServiceNtfcPlaceMaster.objects.filter(lost_flag=0).all()

        # 消防法_危険物届_改廃リスト
        fire_service_ntfc_amendment_list = FireServiceNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 消防法_危険物_品名数量倍数変更届_場所リスト
        fire_service_quantity_ntfc_place_list = FireServiceQuantityNtfcPlaceMaster.objects.filter(lost_flag=0).all()

        # 消防法_圧縮アセチレンガス等貯蔵取扱届出_改廃リスト
        fire_service_acetylene_gas_ntfc_amendment_list = FireServiceAcetyleneGasNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 消防法_危険物仮承認申請_扱いリスト
        fire_service_tentative_app_action_list = FireServiceTentativeAppActionMaster.objects.filter(lost_flag=0).all()

        # 市火災予防条例_危険物貯蔵取扱届_種類リスト
        fire_prevent_storage_ntfc_category_list = FirePreventStorageNtfcCategoryMaster.objects.filter(lost_flag=0).all()

        # 市火災予防条例_危険物貯蔵取扱届_改廃リスト
        fire_prevent_storage_ntfc_amendment_list = FirePreventStorageNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 市火災予防条例_設備設置届_種類リスト
        fire_prevent_equip_ntfc_category_list = FirePreventEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()

        # 劇毒物取締法_劇毒物変更届_取扱リスト
        deleterious_substances_ntfc_purpose_list = DeleteriousSubstancesNtfcPurposeMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_特定高圧ガス設備申請_製造/変更リスト
        press_gas_app_motive_list = PressGasAppMotiveMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_液化石油高圧ガス設備申請_製造/変更リスト
        press_gas_lpg_app_motive_list = PressGasLpgAppMotiveMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_冷凍高圧ガス設備申請_製造/変更リスト
        press_gas_frozen_gas_app_motive_list = PressGasFrozenGasAppMotiveMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_特定高圧ガス設備届_改廃リスト
        press_gas_ntfc_amendment_list = PressGasNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_液化石油高圧ガス設備届_改廃リスト
        press_gas_lpg_ntfc_amendment_list = PressGasLpgNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_冷凍高圧ガス設備届_改廃リスト
        press_gas_frozen_gas_ntfc_amendment_list = PressGasFrozenGasNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 高圧ガス保安法_特定高圧ガス消費設備届_改廃リスト
        press_gas_consumption_ntfc_amendment_list = PressGasConsumptionNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_設置物届_種類リスト
        safety_health_equip_ntfc_category_list = SafetyHealthEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_設置物届_設置/変更リスト
        safety_health_equip_ntfc_motive_list = SafetyHealthEquipNtfcMotiveMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_有害物質届_種類リスト
        safety_health_deleterious_ntfc_category_list = SafetyHealthDeleteriousNtfcCategoryMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_有害物質届_設置/変更リスト
        safety_health_deleterious_ntfc_motive_list = SafetyHealthDeleteriousMotiveNtfcMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_設備届_種類リスト
        safety_health_specified_equip_ntfc_category_list = SafetyHealthSpecifiedEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_設備届_設置/変更リスト
        safety_health_specified_equip_ntfc_motive_list = SafetyHealthSpecifiedEquipNtfcMotiveMaster.objects.filter(lost_flag=0).all()

        # 労働安全衛生法_設備設置報告_種類リスト
        safety_health_installation_report_category_list = SafetyHealthInstallationReportCategoryMaster.objects.filter(lost_flag=0).all()

        # 放射線障害防止法_放射性同位元素申請_使用/変更リスト
        radiation_hazards_app_motive_list = RadiationHazardsAppMotiveMaster.objects.filter(lost_flag=0).all()

        # rev_no比較
        if old_cs_data_num > 0:
            old_cs_data = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).all().order_by('-id')[0]
        else:
            old_cs_data = ""

        # データ編集機能要否判定
        cs_edit_action_num = 0

        cs_edit_action_num = cs_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                     target_table='cs_safety_health').count()

        edit_flag = 0

        if cs_edit_action_num > 0:
            edit_flag = 1

        # データ保存
        data = {
            'cs_safety_health_data': cs_safety_health_data,
            'old_cs_data_num': old_cs_data_num,
            'old_cs_data': old_cs_data,
            't_username': t_username,
            't_user_last_name': t_user_last_name,
            't_user_first_name': t_user_first_name,
            'department_name': department_name,
            'charge_name': charge_name,
            'charge_data': charge_data,
            'step_name': step_name,
            'previous_step': previous_step,
            'charge_department_class': charge_department_class,
            'next_division': next_division,
            'next_department': next_department,
            'fire_service_app': fire_service_app,
            'fire_service_app_place': fire_service_app_place,
            'fire_service_app_place_list': fire_service_app_place_list,
            'fire_service_app_action': fire_service_app_action,
            'fire_service_app_action_list': fire_service_app_action_list,
            'fire_service_ntfc': fire_service_ntfc,
            'fire_service_ntfc_place': fire_service_ntfc_place,
            'fire_service_ntfc_place_list': fire_service_ntfc_place_list,
            'fire_service_ntfc_amendment': fire_service_ntfc_amendment,
            'fire_service_ntfc_amendment_list': fire_service_ntfc_amendment_list,
            'fire_service_quantity_ntfc': fire_service_quantity_ntfc,
            'fire_service_quantity_ntfc_place': fire_service_quantity_ntfc_place,
            'fire_service_quantity_ntfc_place_list': fire_service_quantity_ntfc_place_list,
            'fire_service_acetylene_gas_ntfc': fire_service_acetylene_gas_ntfc,
            'fire_service_acetylene_gas_ntfc_amendment': fire_service_acetylene_gas_ntfc_amendment,
            'fire_service_acetylene_gas_ntfc_amendment_list': fire_service_acetylene_gas_ntfc_amendment_list,
            'fire_service_tentative_app': fire_service_tentative_app,
            'fire_service_tentative_app_action': fire_service_tentative_app_action,
            'fire_service_tentative_app_action_list': fire_service_tentative_app_action_list,
            'fire_prevent_storage_ntfc': fire_prevent_storage_ntfc,
            'fire_prevent_storage_ntfc_category': fire_prevent_storage_ntfc_category,
            'fire_prevent_storage_ntfc_category_list': fire_prevent_storage_ntfc_category_list,
            'fire_prevent_storage_ntfc_amendment': fire_prevent_storage_ntfc_amendment,
            'fire_prevent_storage_ntfc_amendment_list': fire_prevent_storage_ntfc_amendment_list,
            'fire_prevent_equip_ntfc': fire_prevent_equip_ntfc,
            'fire_prevent_equip_ntfc_category': fire_prevent_equip_ntfc_category,
            'fire_prevent_equip_ntfc_category_list': fire_prevent_equip_ntfc_category_list,
            'fire_prevent_commencement_ntfc': fire_prevent_commencement_ntfc,
            'fire_prevent_construction_plan': fire_prevent_construction_plan,
            'fire_prevent_installation_ntfc': fire_prevent_installation_ntfc,
            'fire_prevent_hazardous_work_ntfc': fire_prevent_hazardous_work_ntfc,
            'fire_prevent_fires_smoke_ntfc': fire_prevent_fires_smoke_ntfc,
            'deleterious_substances_list_app': deleterious_substances_list_app,
            'deleterious_substances_ntfc': deleterious_substances_ntfc,
            'deleterious_substances_ntfc_purpose': deleterious_substances_ntfc_purpose,
            'deleterious_substances_ntfc_purpose_list': deleterious_substances_ntfc_purpose_list,
            'press_gas_app': press_gas_app,
            'press_gas_app_motive': press_gas_app_motive,
            'press_gas_app_motive_list': press_gas_app_motive_list,
            'press_gas_lpg_app': press_gas_lpg_app,
            'press_gas_lpg_app_motive': press_gas_lpg_app_motive,
            'press_gas_lpg_app_motive_list': press_gas_lpg_app_motive_list,
            'press_gas_frozen_gas_app': press_gas_frozen_gas_app,
            'press_gas_frozen_gas_app_motive': press_gas_frozen_gas_app_motive,
            'press_gas_frozen_gas_app_motive_list': press_gas_frozen_gas_app_motive_list,
            'press_gas_ntfc': press_gas_ntfc,
            'press_gas_ntfc_amendment': press_gas_ntfc_amendment,
            'press_gas_ntfc_amendment_list': press_gas_ntfc_amendment_list,
            'press_gas_lpg_ntfc': press_gas_lpg_ntfc,
            'press_gas_lpg_ntfc_amendment': press_gas_lpg_ntfc_amendment,
            'press_gas_lpg_ntfc_amendment_list': press_gas_lpg_ntfc_amendment_list,
            'press_gas_frozen_gas_ntfc': press_gas_frozen_gas_ntfc,
            'press_gas_frozen_gas_ntfc_amendment': press_gas_frozen_gas_ntfc_amendment,
            'press_gas_frozen_gas_ntfc_amendment_list': press_gas_frozen_gas_ntfc_amendment_list,
            'press_gas_consumption_ntfc': press_gas_consumption_ntfc,
            'press_gas_consumption_ntfc_amendment': press_gas_consumption_ntfc_amendment,
            'press_gas_consumption_ntfc_amendment_list': press_gas_consumption_ntfc_amendment_list,
            'safety_health_equip_ntfc': safety_health_equip_ntfc,
            'safety_health_equip_ntfc_category': safety_health_equip_ntfc_category,
            'safety_health_equip_ntfc_category_list': safety_health_equip_ntfc_category_list,
            'safety_health_equip_ntfc_motive': safety_health_equip_ntfc_motive,
            'safety_health_equip_ntfc_motive_list': safety_health_equip_ntfc_motive_list,
            'safety_health_deleterious_ntfc': safety_health_deleterious_ntfc,
            'safety_health_deleterious_ntfc_category': safety_health_deleterious_ntfc_category,
            'safety_health_deleterious_ntfc_category_list': safety_health_deleterious_ntfc_category_list,
            'safety_health_deleterious_ntfc_motive': safety_health_deleterious_ntfc_motive,
            'safety_health_deleterious_ntfc_motive_list': safety_health_deleterious_ntfc_motive_list,
            'safety_health_asbestos': safety_health_asbestos,
            'safety_health_specified_equip_ntfc': safety_health_specified_equip_ntfc,
            'safety_health_specified_equip_ntfc_category': safety_health_specified_equip_ntfc_category,
            'safety_health_specified_equip_ntfc_category_list': safety_health_specified_equip_ntfc_category_list,
            'safety_health_specified_equip_ntfc_motive': safety_health_specified_equip_ntfc_motive,
            'safety_health_specified_equip_ntfc_motive_list': safety_health_specified_equip_ntfc_motive_list,
            'safety_health_installation_report': safety_health_installation_report,
            'safety_health_installation_report_category': safety_health_installation_report_category,
            'safety_health_installation_report_category_list': safety_health_installation_report_category_list,
            # 'safety_health_installation_report_motive': safety_health_installation_report_motive,
            'radiation_hazards_app': radiation_hazards_app,
            'radiation_hazards_app_motive': radiation_hazards_app_motive,
            'radiation_hazards_app_motive_list': radiation_hazards_app_motive_list,
            'petroleum_complexes_act': petroleum_complexes_act,
            'cs_no': str_cs_no,
            'target_budget_id': str_target_budget_id,
            # 'relation_budget_id': str_relation_budget_id,
            'target_id': cs_no,
            # 'user_authority': user_authority,
            # 'confirm_user': confirm_user,
            # 'permit_user': permit_user,
            # 'level5_step_id': level5_step_id,
            'note': note,
            'cs_rev_no': cs_rev_no,
            'sh_edit_flag': edit_flag,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/check_sheet/cs_safety_health_edit.html', data)

        else:
            return render(request, 'fms/parts/check_sheet/cs_safety_health_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 環境管轄の法令一覧画面を表示
@login_required
@require_POST
def cs_environment_data_info(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_id = int(request.POST['target_unique_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        first_open_flag = 0

        # 新規登録(target_id=0)を判定
        # 新規ではないときの処理
        if target_unique_id > 0:
            # 対象データの現在の工程IDを取得
            cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)

            if CsEnvironment.objects.filter(cs_no=cs_manage_data.cs_no, lost_flag=0).count() == 0:
                first_open_flag = 1
            else:
                cs_environment_data = CsEnvironment.objects.get(cs_no=cs_manage_data.cs_no, lost_flag=0)

                # 大気汚染防止法_大気汚染物質発生施設届
                if cs_environment_data.air_pollution_equip_ntfc is not None:
                    air_pollution_equip_ntfc = cs_environment_data.air_pollution_equip_ntfc
                else:
                    air_pollution_equip_ntfc = False

                # 大気汚染防止法_大気汚染物質発生施設届_種類
                if cs_environment_data.air_pollution_equip_ntfc_category is not None:
                    air_pollution_equip_ntfc_category = cs_environment_data.air_pollution_equip_ntfc_category
                else:
                    air_pollution_equip_ntfc_category = "大気汚染物質種類"

                # 大気汚染防止法_大気汚染物質発生施設届_設置/変更
                if cs_environment_data.air_pollution_equip_ntfc_motive is not None:
                    air_pollution_equip_ntfc_motive = cs_environment_data.air_pollution_equip_ntfc_motive
                else:
                    air_pollution_equip_ntfc_motive = "設置/変更"

                # 大気汚染防止法_大気汚染物質発生施設廃止届
                if cs_environment_data.air_pollution_repeal_equip_ntfc is not None:
                    air_pollution_repeal_equip_ntfc = cs_environment_data.air_pollution_repeal_equip_ntfc
                else:
                    air_pollution_repeal_equip_ntfc = False

                # 大気汚染防止法_大気汚染物質発生施設廃止届_種類
                if cs_environment_data.air_pollution_repeal_equip_ntfc_category is not None:
                    air_pollution_repeal_equip_ntfc_category = cs_environment_data.air_pollution_repeal_equip_ntfc_category
                else:
                    air_pollution_repeal_equip_ntfc_category = "大気汚染物質種類"

                # 大気汚染防止法_揮発性有機化合物発生施設届
                if cs_environment_data.air_pollution_voc_ntfc is not None:
                    air_pollution_voc_ntfc = cs_environment_data.air_pollution_voc_ntfc
                else:
                    air_pollution_voc_ntfc = False

                # 大気汚染防止法_揮発性有機化合物発生施設届_扱い
                if cs_environment_data.air_pollution_voc_ntfc_action is not None:
                    air_pollution_voc_ntfc_action = cs_environment_data.air_pollution_voc_ntfc_action
                else:
                    air_pollution_voc_ntfc_action = "扱い"

                # 大気汚染防止法_特定粉じん排出等作業実施届出
                if cs_environment_data.air_pollution_particulates_ntfc is not None:
                    air_pollution_particulates_ntfc = cs_environment_data.air_pollution_particulates_ntfc
                else:
                    air_pollution_particulates_ntfc = False

                # 水質汚濁防止法_特定施設届
                if cs_environment_data.water_pollution_ntfc is not None:
                    water_pollution_ntfc = cs_environment_data.water_pollution_ntfc
                else:
                    water_pollution_ntfc = False

                # 水質汚濁防止法_特定施設届_扱い
                if cs_environment_data.water_pollution_ntfc_action is not None:
                    water_pollution_ntfc_action = cs_environment_data.water_pollution_ntfc_action
                else:
                    water_pollution_ntfc_action = "扱い"

                # 土壌汚染対策法_土地形質変更届
                if cs_environment_data.soil_contamination_ntfc is not None:
                    soil_contamination_ntfc = cs_environment_data.soil_contamination_ntfc
                else:
                    soil_contamination_ntfc = False

                # 廃棄物処理法_産業廃棄物処理施設申請
                if cs_environment_data.waste_equip_app is not None:
                    waste_equip_app = cs_environment_data.waste_equip_app
                else:
                    waste_equip_app = False

                # 廃棄物処理法_産業廃棄物処理施設申請_設置/変更
                if cs_environment_data.waste_equip_app_motive is not None:
                    waste_equip_app_motive = cs_environment_data.waste_equip_app_motive
                else:
                    waste_equip_app_motive = "設置/変更"

                # 廃棄物処理法_産業廃棄物処理施設廃止届
                if cs_environment_data.waste_repeal_equip_ntfc is not None:
                    waste_repeal_equip_ntfc = cs_environment_data.waste_repeal_equip_ntfc
                else:
                    waste_repeal_equip_ntfc = False

                # フロン排出抑制法_工程管理票
                if cs_environment_data.management_freon_plan is not None:
                    management_freon_plan = cs_environment_data.management_freon_plan
                else:
                    management_freon_plan = False

                # 県生活環境保全条例_指定施設届
                if cs_environment_data.living_env_equip_ntfc is not None:
                    living_env_equip_ntfc = cs_environment_data.living_env_equip_ntfc
                else:
                    living_env_equip_ntfc = False

                # 県生活環境保全条例_指定施設届_種類
                if cs_environment_data.living_env_equip_ntfc_category is not None:
                    living_env_equip_ntfc_category = cs_environment_data.living_env_equip_ntfc_category
                else:
                    living_env_equip_ntfc_category = "大気汚染物質種類"

                # 県生活環境保全条例_指定施設届_扱い
                if cs_environment_data.living_env_equip_ntfc_action is not None:
                    living_env_equip_ntfc_action = cs_environment_data.living_env_equip_ntfc_action
                else:
                    living_env_equip_ntfc_action = "扱い"

                # 県生活環境保全条例_窒素酸化物排出計画届
                if cs_environment_data.living_env_nox_emission_plan_ntfc is not None:
                    living_env_nox_emission_plan_ntfc = cs_environment_data.living_env_nox_emission_plan_ntfc
                else:
                    living_env_nox_emission_plan_ntfc = False

                # 県生活環境保全条例_土壌調査
                if cs_environment_data.living_env_soil_survey is not None:
                    living_env_soil_survey = cs_environment_data.living_env_soil_survey
                else:
                    living_env_soil_survey = False

                # 県生活環境保全条例_揚水設備届出/申請
                if cs_environment_data.living_env_water_pumping_app is not None:
                    living_env_water_pumping_app = cs_environment_data.living_env_water_pumping_app
                else:
                    living_env_water_pumping_app = False

                # 市公害防止協定_公害防止協定事前協議
                if cs_environment_data.pollution_agree_consultation is not None:
                    pollution_agree_consultation = cs_environment_data.pollution_agree_consultation
                else:
                    pollution_agree_consultation = False

                # チタン鉱石問題対応方針_報告書
                if cs_environment_data.titanium_compatible_report is not None:
                    titanium_compatible_report = cs_environment_data.titanium_compatible_report
                else:
                    titanium_compatible_report = False

                # 浄化槽法_浄化槽届出
                if cs_environment_data.water_purification_tanks_ntfc is not None:
                    water_purification_tanks_ntfc = cs_environment_data.water_purification_tanks_ntfc
                else:
                    water_purification_tanks_ntfc = False

                # 浄化槽法_浄化槽届出_改廃
                if cs_environment_data.water_purification_tanks_ntfc_amendment is not None:
                    water_purification_tanks_ntfc_amendment = cs_environment_data.water_purification_tanks_ntfc_amendment
                else:
                    water_purification_tanks_ntfc_amendment = "改廃"

                # 備考
                if cs_environment_data.note is not None:
                    note = cs_environment_data.note
                else:
                    note = ""

                # rev_no
                # チェックシートデータののRevNO取得
                cs_rev_no = cs_environment_data.cs_rev_no

                # 継承する値を取得
                cs_no = cs_environment_data.cs_no
                str_cs_no = str(cs_no)
                target_budget_id = cs_manage_data.budget_id
                str_target_budget_id = str(target_budget_id)
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                # present_step_data = Progress.objects.get(target_id=cs_no, target='cs')
                # present_step = present_step_data.present_step
                present_step = int(request.POST['this_step'])
                step_data = StepMaster.objects.get(step_id=present_step, lost_flag=0)
                step_name = step_data.step_name
                previous_step = step_data.previous_step
                # 次のstepを取得
                next_step_data = StepRelation.objects.filter(step_id=present_step, lost_flag=0).order_by('display_order')[0]
                next_step = next_step_data.next_step
                # 次のstepの情報取得
                step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)

                charge_department_class = convert_charge_department(step_data.charge_department_class)

                charge_name = cs_manage_data.budget_charge_id
                if charge_name is not None:
                    charge_data = User.objects.get(username=charge_name, lost_flag=0)
                else:
                    charge_data = budget_data.budget_department_charge_person_id
                cs_department = cs_manage_data.wo_department_id
                if cs_department is None:
                    cs_department = budget_data.budget_main_department_id
                department_data = DepartmentMaster.objects.get(department_cd=cs_department)
                department_name = department_data.department_name
                if charge_department_class == 'BD':
                    next_division = department_data.division_cd
                    next_department = department_data.department_cd
                else:
                    next_division = ""
                    next_department = charge_department_class

                # rev_noの古い同じ予算IDのデータの有無を確認
                old_cs_data_num = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).count()

        if target_unique_id == 0 or first_open_flag == 1:
            # 新規登録時処理
            cs_environment_data = ""

            # 大気汚染防止法_大気汚染物質発生施設届
            air_pollution_equip_ntfc = False

            # 大気汚染防止法_大気汚染物質発生施設届_種類
            air_pollution_equip_ntfc_category = "種類"

            # 大気汚染防止法_大気汚染物質発生施設届_設置/変更
            air_pollution_equip_ntfc_motive = "設置/変更"

            # 大気汚染防止法_大気汚染物質発生施設廃止届
            air_pollution_repeal_equip_ntfc = False

            # 大気汚染防止法_大気汚染物質発生施設廃止届_種類
            air_pollution_repeal_equip_ntfc_category = "大気汚染物質種類"

            # 大気汚染防止法_揮発性有機化合物発生施設届
            air_pollution_voc_ntfc = False

            # 大気汚染防止法_揮発性有機化合物発生施設届_扱い
            air_pollution_voc_ntfc_action = "扱い"

            # 大気汚染防止法_特定粉じん排出等作業実施届出
            air_pollution_particulates_ntfc = False

            # 水質汚濁防止法_特定施設届
            water_pollution_ntfc = False

            # 水質汚濁防止法_特定施設届_扱い
            water_pollution_ntfc_action = "扱い"

            # 土壌汚染対策法_土地形質変更届
            soil_contamination_ntfc = False

            # 廃棄物処理法_産業廃棄物処理施設申請
            waste_equip_app = False

            # 廃棄物処理法_産業廃棄物処理施設申請_設置/変更
            waste_equip_app_motive = "設置/変更"

            # 廃棄物処理法_産業廃棄物処理施設廃止届
            waste_repeal_equip_ntfc = False

            # フロン排出抑制法_工程管理票
            management_freon_plan = False

            # 県生活環境保全条例_指定施設届
            living_env_equip_ntfc = False

            # 県生活環境保全条例_指定施設届_種類
            living_env_equip_ntfc_category = "大気汚染物質種類"

            # 県生活環境保全条例_指定施設届_扱い
            living_env_equip_ntfc_action = "扱い"

            # 県生活環境保全条例_窒素酸化物排出計画届
            living_env_nox_emission_plan_ntfc = False

            # 県生活環境保全条例_土壌調査
            living_env_soil_survey = False

            # 県生活環境保全条例_揚水設備届出/申請
            living_env_water_pumping_app = False

            # 市公害防止協定_公害防止協定事前協議
            pollution_agree_consultation = False

            # チタン鉱石問題対応方針_報告書
            titanium_compatible_report = False

            # 浄化槽法_浄化槽届出
            water_purification_tanks_ntfc = False

            # 浄化槽法_浄化槽届出_改廃
            water_purification_tanks_ntfc_amendment = "改廃"

            # 備考
            note = ""

            if first_open_flag == 1:
                cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)
                cs_no = cs_manage_data.cs_no
                str_cs_no = str(cs_no)
                str_target_budget_id = str(cs_manage_data.budget_id)
            else:
                cs_no = 0
                str_cs_no = ""
                str_target_budget_id = ""
            cs_rev_no = 0
            department_name = ""
            step_name = ""
            previous_step = 0
            present_step = new_step
            next_division = user_division_cd
            next_department = user_department_cd
            charge_department_class = "BD"
            charge_data = ""
            charge_name = ""
            old_cs_data_num = 0

            # フラグOFF
            first_open_flag = 0

        # マスタソースとなるリスト抽出
        # 大気汚染防止法大気汚染物質発生施設届種類マスタ
        air_pollution_equip_ntfc_category_list = AirPollutionEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法大気汚染物質発生施設届設置/変更マスタ
        air_pollution_equip_ntfc_motive_list = AirPollutionEquipNtfcMotiveMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法大気汚染物質発生施設廃止届種類マスタ
        air_pollution_repeal_equip_ntfc_category_list = AirPollutionRepealEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法揮発性有機化合物発生施設届扱いマスタ
        air_pollution_voc_ntfc_action_list = AirPollutionVocNtfcActionMaster.objects.filter(lost_flag=0).all()
        # 水質汚濁防止法特定施設届扱いマスタ
        water_pollution_ntfc_action_list = WaterPollutionNtfcActionMaster.objects.filter(lost_flag=0).all()
        # 廃棄物処理法産業廃棄物処理施設申請設置/変更マスタ
        waste_equip_app_motive_list = WasteEquipAppMotiveMaster.objects.filter(lost_flag=0).all()
        # 県生活環境保全条例指定施設届種類マスタ
        living_env_equip_ntfc_category_list = LivingEnvEquipNtfcCategoryMaster.objects.filter(lost_flag=0).all()
        # 県生活環境保全条例指定施設届扱いマスタ
        living_env_equip_ntfc_action_list = LivingEnvEquipNtfcActionMaster.objects.filter(lost_flag=0).all()
        # 浄化槽法浄化槽届出改廃マスタ
        water_purification_tanks_ntfc_amendment_list = WaterPurificationTanksNtfcAmendmentMaster.objects.filter(lost_flag=0).all()

        # rev_no比較
        if old_cs_data_num > 0:
            old_cs_data = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).all().order_by('-id')[0]
        else:
            old_cs_data = ""

        # データ編集機能要否判定
        cs_edit_action_num = 0

        cs_edit_action_num = cs_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                     target_table='cs_environment').count()

        edit_flag = 0

        if cs_edit_action_num > 0:
            edit_flag = 1

        # データ保存
        data = {
            'cs_environment_data': cs_environment_data,
            'old_cs_data_num': old_cs_data_num,
            'old_cs_data': old_cs_data,
            't_username': t_username,
            't_user_last_name': t_user_last_name,
            't_user_first_name': t_user_first_name,
            'department_name': department_name,
            'charge_name': charge_name,
            'charge_data': charge_data,
            'step_name': step_name,
            'previous_step': previous_step,
            'charge_department_class': charge_department_class,
            'next_division': next_division,
            'next_department': next_department,
            'air_pollution_equip_ntfc': air_pollution_equip_ntfc,
            'air_pollution_equip_ntfc_category': air_pollution_equip_ntfc_category,
            'air_pollution_equip_ntfc_category_list': air_pollution_equip_ntfc_category_list,
            'air_pollution_equip_ntfc_motive': air_pollution_equip_ntfc_motive,
            'air_pollution_equip_ntfc_motive_list': air_pollution_equip_ntfc_motive_list,
            'air_pollution_repeal_equip_ntfc': air_pollution_repeal_equip_ntfc,
            'air_pollution_repeal_equip_ntfc_category': air_pollution_repeal_equip_ntfc_category,
            'air_pollution_repeal_equip_ntfc_category_list': air_pollution_repeal_equip_ntfc_category_list,
            'air_pollution_voc_ntfc': air_pollution_voc_ntfc,
            'air_pollution_voc_ntfc_action': air_pollution_voc_ntfc_action,
            'air_pollution_voc_ntfc_action_list': air_pollution_voc_ntfc_action_list,
            'air_pollution_particulates_ntfc': air_pollution_particulates_ntfc,
            'water_pollution_ntfc': water_pollution_ntfc,
            'water_pollution_ntfc_action': water_pollution_ntfc_action,
            'water_pollution_ntfc_action_list': water_pollution_ntfc_action_list,
            'soil_contamination_ntfc': soil_contamination_ntfc,
            'waste_equip_app': waste_equip_app,
            'waste_equip_app_motive': waste_equip_app_motive,
            'waste_equip_app_motive_list': waste_equip_app_motive_list,
            'waste_repeal_equip_ntfc': waste_repeal_equip_ntfc,
            'management_freon_plan': management_freon_plan,
            'living_env_equip_ntfc': living_env_equip_ntfc,
            'living_env_equip_ntfc_category': living_env_equip_ntfc_category,
            'living_env_equip_ntfc_category_list': living_env_equip_ntfc_category_list,
            'living_env_equip_ntfc_action': living_env_equip_ntfc_action,
            'living_env_equip_ntfc_action_list': living_env_equip_ntfc_action_list,
            'living_env_nox_emission_plan_ntfc': living_env_nox_emission_plan_ntfc,
            'living_env_soil_survey': living_env_soil_survey,
            'living_env_water_pumping_app': living_env_water_pumping_app,
            'pollution_agree_consultation': pollution_agree_consultation,
            'titanium_compatible_report': titanium_compatible_report,
            'water_purification_tanks_ntfc': water_purification_tanks_ntfc,
            'water_purification_tanks_ntfc_amendment': water_purification_tanks_ntfc_amendment,
            'water_purification_tanks_ntfc_amendment_list': water_purification_tanks_ntfc_amendment_list,
            'cs_no': str_cs_no,
            'target_budget_id': str_target_budget_id,
            # 'relation_budget_id': str_relation_budget_id,
            'target_id': cs_no,
            # 'user_authority': user_authority,
            # 'confirm_user': confirm_user,
            # 'permit_user': permit_user,
            # 'level5_step_id': level5_step_id,
            'note': note,
            'cs_rev_no': cs_rev_no,
            'env_edit_flag': edit_flag,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/check_sheet/cs_environment_edit.html', data)

        else:
            return render(request, 'fms/parts/check_sheet/cs_environment_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工務管轄の法令一覧画面を表示
@login_required
@require_POST
def cs_engineering_data_info(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_id = int(request.POST['target_unique_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        first_open_flag = 0

        # 新規登録(target_id=0)を判定
        # 新規ではないときの処理
        if target_unique_id > 0:
            # 対象データの現在の工程IDを取得
            cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)

            if CsEngineering.objects.filter(cs_no=cs_manage_data.cs_no, lost_flag=0).count() == 0:
                first_open_flag = 1
            else:
                cs_engineering_data = CsEngineering.objects.get(cs_no=cs_manage_data.cs_no, lost_flag=0)

                # 建築基準法
                if cs_engineering_data.building_standards_act is not None:
                    building_standards_act = cs_engineering_data.building_standards_act
                else:
                    building_standards_act = False

                # 建築基準法_種類
                if cs_engineering_data.building_standards_act_category is not None:
                    building_standards_act_category = cs_engineering_data.building_standards_act_category
                else:
                    building_standards_act_category = "設置物種類"

                # 省エネ法
                if cs_engineering_data.energy_rationalization_act is not None:
                    energy_rationalization_act = cs_engineering_data.energy_rationalization_act
                else:
                    energy_rationalization_act = False

                # 省エネ法_種類
                if cs_engineering_data.energy_rationalization_act_category is not None:
                    energy_rationalization_act_category = cs_engineering_data.energy_rationalization_act_category
                else:
                    energy_rationalization_act_category = "第Ｘ種"

                # 省エネ法_扱い
                if cs_engineering_data.energy_rationalization_act_action is not None:
                    energy_rationalization_act_action = cs_engineering_data.energy_rationalization_act_action
                else:
                    energy_rationalization_act_action = "扱い"

                # 建設リサイクル法
                if cs_engineering_data.construction_recycling is not None:
                    construction_recycling = cs_engineering_data.construction_recycling
                else:
                    construction_recycling = False

                # 建設リサイクル法_種類
                if cs_engineering_data.construction_recycling_category is not None:
                    construction_recycling_category = cs_engineering_data.construction_recycling_category
                else:
                    construction_recycling_category = "届出種類"

                # 備考
                if cs_engineering_data.note is not None:
                    note = cs_engineering_data.note
                else:
                    note = ""

                # rev_no
                # チェックシートデータののRevNO取得
                cs_rev_no = cs_engineering_data.cs_rev_no

                # 継承する値を取得
                cs_no = cs_engineering_data.cs_no
                str_cs_no = str(cs_no)
                target_budget_id = cs_manage_data.budget_id
                str_target_budget_id = str(target_budget_id)
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                # present_step_data = Progress.objects.get(target_id=cs_no, target='cs')
                # present_step = present_step_data.present_step
                present_step = int(request.POST['this_step'])
                step_data = StepMaster.objects.get(step_id=present_step, lost_flag=0)
                step_name = step_data.step_name
                previous_step = step_data.previous_step
                # 次のstepを取得
                next_step_data = StepRelation.objects.filter(step_id=present_step, lost_flag=0).order_by('display_order')[0]
                next_step = next_step_data.next_step
                # 次のstepの情報取得
                step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)

                charge_department_class = convert_charge_department(step_data.charge_department_class)

                charge_name = cs_manage_data.budget_charge_id
                if charge_name is not None:
                    charge_data = User.objects.get(username=charge_name, lost_flag=0)
                else:
                    charge_data = budget_data.budget_department_charge_person_id
                cs_department = cs_manage_data.wo_department_id
                if cs_department is None:
                    cs_department = budget_data.budget_main_department_id
                department_data = DepartmentMaster.objects.get(department_cd=cs_department)
                department_name = department_data.department_name
                if charge_department_class == 'BD':
                    next_division = department_data.division_cd
                    next_department = department_data.department_cd
                else:
                    next_division = ""
                    next_department = charge_department_class

                # rev_noの古い同じ予算IDのデータの有無を確認
                old_cs_data_num = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).count()

        if target_unique_id == 0 or first_open_flag == 1:
            # 新規登録時処理
            cs_engineering_data = ""

            # 建築基準法
            building_standards_act = False

            # 建築基準法_種類
            building_standards_act_category = "設置物種類"

            # 省エネ法
            energy_rationalization_act = False

            # 省エネ法_種類
            energy_rationalization_act_category = "第Ｘ種"

            # 省エネ法_扱い
            energy_rationalization_act_action = "扱い"

            # 建設リサイクル法
            construction_recycling = False

            # 建設リサイクル法_種類
            construction_recycling_category = "届出種類"

            # 備考
            note = ""

            if first_open_flag == 1:
                cs_manage_data = CsManage.objects.get(id=target_unique_id, lost_flag=0)
                cs_no = cs_manage_data.cs_no
                str_cs_no = str(cs_no)
                str_target_budget_id = str(cs_manage_data.budget_id)
            else:
                cs_no = 0
                str_cs_no = ""
                str_target_budget_id = ""
            cs_rev_no = 0
            department_name = ""
            step_name = ""
            previous_step = 0
            present_step = new_step
            next_division = user_division_cd
            next_department = user_department_cd
            charge_department_class = "BD"
            charge_data = ""
            charge_name = ""
            old_cs_data_num = 0

            # フラグOFF
            irst_open_flag = 0

        # マスタソースとなるリスト抽出
        # 大気汚染防止法大気汚染物質発生施設届種類マスタ
        building_standards_act_category_list = BuildingStandardsActCategoryMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法大気汚染物質発生施設届設置/変更マスタ
        energy_rationalization_act_category_list = EnergyRationalizationActCategoryMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法大気汚染物質発生施設廃止届種類マスタ
        energy_rationalization_act_action_list = EnergyRationalizationActActionMaster.objects.filter(lost_flag=0).all()
        # 大気汚染防止法揮発性有機化合物発生施設届扱いマスタ
        construction_recycling_category_list = ConstructionRecyclingCategoryMaster.objects.filter(lost_flag=0).all()

        # rev_no比較
        if old_cs_data_num > 0:
            old_cs_data = CsManage.objects.filter(cs_no=cs_no, lost_flag=1).all().order_by('-id')[0]
        else:
            old_cs_data = ""

        # データ編集機能要否判定
        cs_edit_action_num = 0

        cs_edit_action_num = cs_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                     target_table='cs_engineering').count()

        edit_flag = 0

        if cs_edit_action_num > 0:
            edit_flag = 1

        # データ保存
        data = {
            'cs_engineering_data': cs_engineering_data,
            'old_cs_data_num': old_cs_data_num,
            'old_cs_data': old_cs_data,
            't_username': t_username,
            't_user_last_name': t_user_last_name,
            't_user_first_name': t_user_first_name,
            'department_name': department_name,
            'charge_name': charge_name,
            'charge_data': charge_data,
            'step_name': step_name,
            'previous_step': previous_step,
            'charge_department_class': charge_department_class,
            'next_division': next_division,
            'next_department': next_department,
            'building_standards_act': building_standards_act,
            'building_standards_act_category': building_standards_act_category,
            'building_standards_act_category_list': building_standards_act_category_list,
            'energy_rationalization_act': energy_rationalization_act,
            'energy_rationalization_act_category': energy_rationalization_act_category,
            'energy_rationalization_act_category_list': energy_rationalization_act_category_list,
            'energy_rationalization_act_action': energy_rationalization_act_action,
            'energy_rationalization_act_action_list': energy_rationalization_act_action_list,
            'construction_recycling': construction_recycling,
            'construction_recycling_category': construction_recycling_category,
            'construction_recycling_category_list': construction_recycling_category_list,
            'cs_no': str_cs_no,
            'target_budget_id': str_target_budget_id,
            # 'relation_budget_id': str_relation_budget_id,
            'target_id': cs_no,
            # 'user_authority': user_authority,
            # 'confirm_user': confirm_user,
            # 'permit_user': permit_user,
            # 'level5_step_id': level5_step_id,
            'note': note,
            'cs_rev_no': cs_rev_no,
            'eng_edit_flag': edit_flag,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/check_sheet/cs_engineering_edit.html', data)

        else:
            return render(request, 'fms/parts/check_sheet/cs_engineering_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次届出CS移動ボタン表示処理
@require_POST
@login_required
def next_button_display(request):
    try:
        target_cs_no = int(request.POST['target_cs_no'])

        list_data = get_cs_lists_data(request)
        cs_lists = list_data['cs_lists']

        pre_cs = None
        next_cs = None
        pre_flg = True
        next_flg = False
        for cs_data in cs_lists:
            if next_flg:
                next_cs = cs_data
                break

            if cs_data.cs_no == target_cs_no:
                next_flg = True
                pre_flg = False
            elif pre_flg:
                pre_cs = cs_data

        data = {
            'pre_cs': pre_cs,
            'next_cs': next_cs,
        }

        return render(request, 'fms/parts/check_sheet/cs_next_pb.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出データ一覧取得
@require_POST
def get_cs_lists_data(request):
    try:
        sel_step = request.POST['sel_step']
        sel_business_year = request.POST['sel_business_year']
        sel_budget_id = request.POST['sel_budget_id']
        sel_budget_no = request.POST['sel_budget_no']
        sel_budget_name = request.POST['sel_budget_name']
        sel_division = request.POST['sel_division']
        sel_department = request.POST['sel_department']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']
        sel_on_work = request.POST['sel_on_work']
        sel_cs_non_hold = request.POST['sel_cs_non_hold']
        sel_display_order = request.POST['sel_display_order']
        level5_step_id = int(request.POST['level5_step_id'])
        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000

        where_str = ""
        where_parm = []

        # 検索条件
        # 進捗状況
        if sel_step is not None and sel_step !='null' and sel_step != "":
            where_str += " AND fms_stepmaster.step_id = %s"
            where_parm.append(int(sel_step))
            # where_str += " AND fms_stepmaster.step_id =" + sel_step
        # 年度
        if sel_business_year != "":
            where_str += " AND fms_budget.business_year_id = %s"
            where_parm.append(int(sel_business_year))
            # where_str += " AND fms_budget.business_year_id =" + sel_business_year
        # 予算ID
        if sel_budget_id != "":
            where_str += " AND fms_budget.budget_id = %s"
            where_parm.append(int(sel_budget_id))
            # where_str += " AND fms_budget.budget_id =" + sel_budget_id
        # 予算NO
        if sel_budget_no != "":
            where_str += " AND fms_budget.budget_no = %s"
            where_parm.append(sel_budget_no)
            # where_str += " AND fms_budget.budget_no ='" + sel_budget_no + "'"
        # 予算名
        if sel_budget_name != "":
            where_str += " AND fms_budget.budget_name LIKE %s"
            where_parm.append('%' + sel_budget_name + '%')
            # where_str += " AND fms_budget.budget_name LIKE '%" + sel_budget_name + "%'"
        # 部門
        if sel_division != "":
            where_str += " AND fms_departmentmaster.division_cd = %s"
            where_parm.append(sel_division)
            # where_str += " AND fms_departmentmaster.division_cd ='" + sel_division + "'"
        # 部署
        if sel_department != "":
            where_str += " AND fms_departmentmaster.department_cd = %s"
            where_parm.append(sel_department)
            # where_str += " AND fms_departmentmaster.department_cd ='" + sel_department + "'"
        # 次作業部門
        if sel_next_division != "":
            where_str += " AND fms_progress.present_division = %s"
            where_parm.append(sel_next_division)
            # where_str += " AND fms_progress.present_division ='" + sel_next_division + "'"
        # 次作業部署
        if sel_next_department != "":
            where_str += " AND fms_progress.present_department = %s"
            where_parm.append(sel_next_department)
            # where_str += " AND fms_progress.present_department ='" + sel_next_department + "'"
        # 次作業者
        if sel_next_parson != "":
            where_str += " AND fms_progress.present_operator = %s"
            where_parm.append(sel_next_parson)
            # where_str += " AND fms_progress.present_operator ='" + sel_next_parson + "'"
        # 未処理のみにチェックがある場合、ユーザーを限定する
        if sel_on_work == 'true':
            where_str += " AND fms_stepmaster.step_id > %s"
            where_parm.append(step_st)
            # where_str += " AND fms_stepmaster.step_id > " + str(step_st)
            where_str += " AND fms_stepmaster.step_id < %s"
            where_parm.append(step_ed)
            # where_str += " AND fms_stepmaster.step_id < " + str(step_ed)
        # 未処理のみにチェックがある場合、ユーザーを限定する

        # 対象工事レコード抽出
        # sql = """ SELECT fms_csmanage.* """
        sql = """ SELECT fms_csmanage.*, fms_user.first_name, fms_user.last_name """
        sql = sql + """ ,fms_stepmaster.step_name, fms_progress.present_step, fms_stepmaster.step_id  """
        sql = sql + """ ,fms_departmentmaster.department_name  """
        sql = sql + """ ,fms_budget.budget_name,fms_businessyearmaster.business_year , fms_budget.id  as budget_unique_id"""
        sql = sql + """ ,fms_budget.budget_id as budget_id, fms_budget.budget_no as budget_no"""
        sql = sql + """ ,CASE WHEN budget_no IS NULL THEN '' ELSE budget_no END AS bd_no """
        sql = sql + """ ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_csmanage.entry_datetime, GETDATE()) """
        sql = sql + """                                     ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END """
        sql = sql + """ AS days_stay """
        # sql = sql + """ ,CASE WHEN log.last_operationtime = on_hold_log.last_operationtime THEN 1 """
        # sql = sql + """                                     ELSE 0 END """
        # sql = sql + """ As hold_flag """
        sql = sql + """ ,CASE WHEN [hold_flag] = 1 THEN [hold_flag] ELSE 0 END [hold_flag] """
        sql = sql + """ , CASE WHEN log_2.action = 'return' THEN 1 """
        sql = sql + """ ELSE 0 """
        sql = sql + """ END AS return_flag """
        # sql = sql + """ FROM fms_csmanage """
        sql = sql + """ FROM ((((((( fms_csmanage """
        sql = sql + """ LEFT JOIN fms_budget ON fms_csmanage.budget_id=fms_budget.budget_id )"""
        sql = sql + """ LEFT JOIN fms_budgetcondition ON fms_budget.budget_id=fms_budgetcondition.budget_id) """
        sql = sql + """ LEFT JOIN fms_progress ON fms_csmanage.cs_no=fms_progress.target_id AND fms_progress.target='cs' AND fms_progress.present_step IS NOT NULL) """
        sql = sql + """ LEFT JOIN fms_user ON fms_progress.present_operator=fms_user.username) """
        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id) """
        sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd) """
        sql = sql + """ LEFT JOIN fms_businessyearmaster ON fms_budget.business_year_id=fms_businessyearmaster.business_year """
        sql = sql + """ LEFT JOIN (SELECT """
        sql = sql + """             [target_id] """
        sql = sql + """             ,MAX([operation_datetime]) as last_operationtime """
        sql = sql + """             FROM [fms].[dbo].[fms_log] """
        sql = sql + """             WHERE [target]='cs' """
        sql = sql + """                             AND [action] != 'temporarily_saved' """
        sql = sql + """             group by [target_id]) as log """
        sql = sql + """ ON [fms].[dbo].[fms_csmanage].cs_no=log.target_id) """
        # sql = sql + """ LEFT JOIN (SELECT """
        # sql = sql + """             [target_id] """
        # sql = sql + """             ,MAX([operation_datetime]) as last_operationtime """
        # sql = sql + """             FROM [fms].[dbo].[fms_log] """
        # sql = sql + """             WHERE [target]='cs' """
        # sql = sql + """                             AND [action] = 'on_hold' """
        # sql = sql + """             group by [target_id]) as on_hold_log """
        # sql = sql + """ ON [fms].[dbo].[fms_csmanage].cs_no=on_hold_log.target_id """

        sql = sql + """ LEFT JOIN( """
        sql = sql + """ SELECT """
        sql = sql + """ 1 AS [hold_flag], """
        sql = sql + """ [fms_log].[target_id], """
        sql = sql + """ [fms_log].[step], """
        sql = sql + """ MAX([operation_datetime]) AS [operation_datetime] """
        sql = sql + """ FROM """
        sql = sql + """ [fms].[dbo].[fms_log] """
        sql = sql + """ WHERE """
        sql = sql + """ [target] = 'cs' """
        sql = sql + """ AND [action] = 'on_hold' """
        sql = sql + """ GROUP BY """
        sql = sql + """ [target_id], """
        sql = sql + """ [step] """
        sql = sql + """ ) AS [on_hold_log] """
        sql = sql + """ ON [fms].[dbo].[fms_csmanage].[cs_no] = [on_hold_log].[target_id] """
        sql = sql + """ AND [fms_progress].[present_step] = [on_hold_log].[step] """

        sql = sql + """ LEFT JOIN( """
        sql = sql + """ 
                        SELECT
                            main.*
                            , sub.[action]
                        FROM
                            (
                            SELECT
                                target_id
                                ,MAX(operation_datetime) AS operation_datetime
                            FROM 
                                [fms].[dbo].[fms_log] 
                            WHERE
                                [target] = 'cs' AND [action] != 'temporarily_saved'
                            GROUP BY [target_id]
                            ) AS main
                            INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime AND main.target_id=sub.target_id
                        WHERE
                            main.[operation_datetime] = sub.operation_datetime """
        sql = sql + """ ) AS log_2 """
        sql = sql + """ ON fms_csmanage.cs_no = log_2.target_id """

        sql = sql + """ WHERE fms_csmanage.lost_flag=0 AND fms_budget.lost_flag=0  AND fms_stepmaster.step_id is not NULL"""
        if where_str != "":
            sql += where_str

        # 保留非優先
        if sel_cs_non_hold == 'true':
            sql += " ORDER BY hold_flag, "
        else:
            sql += " ORDER BY "
        # 表示順
        if sel_display_order == "1":
            sql += " fms_budget.budget_id"
        elif sel_display_order == "2":
            sql += " fms_budget.budget_no"
        else:
            sql += " days_stay desc"

        print(sql)

        if len(where_parm) == 0:
            cs_lists = CsManage.objects.all().raw(sql)
        else:
            cs_lists = CsManage.objects.raw(sql, where_parm)
            # cs_lists = CsManage.objects.raw(sql)
        cs_lists_num = len(list(cs_lists))

        data = {
            'cs_lists': cs_lists,
            'cs_lists_num': cs_lists_num,
        }

        return data
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出データ一覧
@require_POST
def get_cs_lists(request):
    try:
        data = get_cs_lists_data(request)

        return render(request, 'fms/parts/check_sheet/cs_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出データ一覧抽出
def get_cs_related_laws_list():

    list_filter = {
        'cs_no': "",
        'cs_jurisdiction_department': "",
        'cs_business_year': "",
        'cs_budget_id': "",
        'cs_budget_no': "",
        'cs_budget_name': "",
        'cs_division': "",
        'cs_department': "",
        'cs_related_laws_progress': "",
        'cs_on_work': True,
    }

    cs_laws_list = get_cs_related_laws_list_forcus(list_filter)

    return cs_laws_list


def get_cs_related_laws_list_forcus(list_filter):
    cs_no = list_filter['cs_no']
    cs_jurisdiction_department = list_filter['cs_jurisdiction_department']
    cs_business_year = list_filter['cs_business_year']
    cs_budget_id = list_filter['cs_budget_id']
    cs_budget_no = list_filter['cs_budget_no']
    cs_budget_name = list_filter['cs_budget_name']
    cs_division = list_filter['cs_division']
    cs_department = list_filter['cs_department']
    cs_related_laws_progress = list_filter['cs_related_laws_progress']
    cs_on_work = list_filter['cs_on_work']

    sql = """ SELECT fms_csnotificationprogress.*, """
    sql += """ fms_csmanage.lost_flag, """
    sql += """ fms_csmanage.budget_id, """
    sql += """ fms_budget.business_year_id, """
    sql += """ fms_budget.budget_no, """
    sql += """ fms_budget.budget_name, """
    sql += """ fms_budget.cancel_flag, """
    sql += """ fms_departmentmaster.division_cd, """
    sql += """ fms_budget.budget_main_department_id, """
    sql += """ fms_departmentmaster.department_name as budget_department_name """
    sql += """ FROM [fms].[dbo].[fms_csnotificationprogress] """
    sql += """ LEFT JOIN  fms_csmanage ON fms_csnotificationprogress.cs_no = fms_csmanage.cs_no"""
    sql += """ LEFT JOIN  fms_budget ON fms_csmanage.budget_id = fms_budget.budget_id AND fms_budget.lost_flag = 0"""
    sql += """ LEFT JOIN  fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd """
    sql += """ WHERE fms_csmanage.lost_flag = 0"""
    if cs_no != "":
        sql += """ AND fms_csnotificationprogress.cs_no in (""" + str(cs_no) + """)"""
    if cs_jurisdiction_department != "":
        cs_jurisdiction_department_name = DepartmentMaster.objects.get(department_cd=cs_jurisdiction_department,
                                                                       lost_flag=0).department_name
        sql += """ AND fms_csnotificationprogress.department_name = '""" + str(cs_jurisdiction_department_name) + """'"""
    if cs_business_year != "":
        sql += """ AND fms_budget.business_year_id = """ + str(cs_business_year)
    if cs_budget_id != "":
        sql += """ AND fms_csmanage.budget_id = """ + str(cs_budget_id)
    if cs_budget_no != "":
        sql += """ AND fms_budget.budget_no = '""" + str(cs_budget_no) + """'"""
    if cs_budget_name != "":
        sql += """ AND fms_budget.budget_name LIKE '%%""" + str(cs_budget_name) + """%%'"""
    if cs_division != "":
        sql += """ AND fms_departmentmaster.division_cd = '""" + str(cs_division) + """'"""
    if cs_department != "":
        sql += """ AND fms_budget.budget_main_department_id = '""" + str(cs_department) + """'"""

    if cs_related_laws_progress == "null_submission_date":
        sql += """ AND fms_csnotificationprogress.submission_date is NULL"""

    if cs_related_laws_progress == "null_notification_date":
        sql += """ AND fms_csnotificationprogress.notification_date is NULL"""

    # 「許可待ち」or「未処理のみ」許可日と許可Noの両方が未入力の場合のみ
    if cs_related_laws_progress == "null_permit_date" or cs_on_work != "false":
        sql += """ AND ( (fms_csnotificationprogress.permit_date is NULL)"""
        sql += """ AND ( (LTRIM(RTRIM(fms_csnotificationprogress.permit_no)) is NULL)"""
        sql += """ OR (LTRIM(RTRIM(fms_csnotificationprogress.permit_no))='' ) )) """

    # 未処理のみの場合、予算が中止されている届出CSは除外
    if cs_on_work != "false":
        sql += """ AND fms_budget.cancel_flag = 0 """

    sql += """ ORDER BY fms_csnotificationprogress.law_code, fms_csmanage.budget_id """

    cs_laws_list = CsNotificationProgress.objects.all().raw(sql)

    return cs_laws_list

# 届出データ一覧
@login_required
@require_POST
def cs_related_laws_list_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_id = int(request.POST['target_unique_id'])
        target_budget_id = int(request.POST['budget_id'])
        if target_unique_id != 0:
            cs_manage_data = CsManage.objects.filter(id=target_unique_id, lost_flag=0)
        else:
            cs_manage_data = CsManage.objects.filter(budget_id=target_budget_id, lost_flag=0)

        cs_no = ""
        if len(cs_manage_data) != 0:
            loop = 0
            for cs_manage_data_item in cs_manage_data:
                if loop == 0:
                    cs_no = str(cs_manage_data_item.cs_no)
                else:
                    cs_no += ',' + str(cs_manage_data_item.cs_no)
                loop += 1
            # budget_id = cs_manage_data.budget_id
            # work_id = cs_manage_data.work_id
            # cs_rev_no = cs_manage_data.cs_rev_no

            list_filter = {
                'cs_no': cs_no,
                'cs_jurisdiction_department': "",
                'cs_business_year': "",
                'cs_budget_id': "",
                'cs_budget_no': "",
                'cs_budget_name': "",
                'cs_division': "",
                'cs_department': "",
                'cs_related_laws_progress': "",
                'cs_on_work': True,
            }

            # 選択済み法令リスト取得
            cs_laws_list = get_cs_related_laws_list_forcus(list_filter)
            cs_laws_list_num = len(cs_laws_list)
        else:
            cs_laws_list = ""
            cs_laws_list_num = 0

        # 日付入力許可フラグ
        able_date_entry_flag = 0

        data = {
            'cs_no': cs_no,
            'budget_id': target_budget_id,
            # 'work_id': work_id,
            'cs_laws_list': cs_laws_list,
            'cs_laws_list_num': cs_laws_list_num,
            'able_date_entry_flag': able_date_entry_flag,
        }

        return render(request, 'fms/parts/check_sheet/cs_related_laws_list_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 登録済の届出進捗状況リストを削除
@login_required
@require_POST
def delete_cs_notification_progress(request):
    cs_no = request.POST['cs_no']

    try:
        data_num = CsNotificationProgress.objects.filter(cs_no=cs_no).all().count()
        if data_num > 0:
            CsNotificationProgress.objects.filter(cs_no=cs_no).all().delete()

        result = 0
        msg = "届出進捗状況リストを削除完了"

    except Exception:
        output_log_exception(request, traceback.format_exc())
        result = 1
        msg = "ERROR!!"

    ary = {
        'result': result,
        'msg': msg
    }
    return JsonResponse(ary)


# 総務管轄届出情報登録･更新
@login_required
@require_POST
def cs_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]

        budget_id = int(request.POST["budget_id"])
        # work_id = int(request.POST["work_id"])

        if request.POST["cs_no"] is not "":
            cs_no = int(request.POST["cs_no"])
        else:
            cs_no = 0

        if request.POST["cs_rev_no"] is not "":
            cs_rev_no = int(request.POST["cs_rev_no"])
        else:
            cs_rev_no = 0

        factory_location_act = request.POST["factory_location_act"]
        if factory_location_act is "":
            factory_location_act = False

        motive = request.POST["motive"]
        if motive is "":
            motive = "設置/変更"

        port_harbour_act = request.POST["port_harbour_act"]
        if port_harbour_act is "":
            port_harbour_act = False

        port_regulations = request.POST["port_regulations"]
        if port_regulations is "":
            port_regulations = False

        buildings_regulations = request.POST["buildings_regulations"]
        if buildings_regulations is "":
            buildings_regulations = False

        cityscape_regulations = request.POST["cityscape_regulations"]
        if cityscape_regulations is "":
            cityscape_regulations = False

        comment = request.POST["comment"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # cs_data_num = CsGeneralAffairs.objects.all().count()
        cs_data_num = CsManage.objects.all().count()

        # 新規登録時の処理
        if cs_no == 0:
            # 届け出チェックシートのレコードがない時の処理･･･チェックシートid=1 とする
            if cs_data_num == 0:
                this_cs_no = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                # last_cs_data = CsGeneralAffairs.objects.all().order_by('-cs_no')[0]
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1
            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            cs_data, created = CsGeneralAffairs.objects.get_or_create(cs_no=this_cs_no)

            # データを格納
            cs_data.cs_rev_no = cs_rev_no
            cs_data.entry_datetime = now
            cs_data.entry_operator = operator
            cs_data.entry_on_progress_flag = 1
            cs_data.factory_location_act = factory_location_act
            cs_data.motive = motive
            cs_data.port_harbour_act = port_harbour_act
            cs_data.port_regulations = port_regulations
            cs_data.buildings_regulations = buildings_regulations
            cs_data.cityscape_regulations = cityscape_regulations
            cs_data.lost_flag = 0

            # データを保存
            cs_data.save()

            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)
            if created:
                cs_manage_data.budget_id = budget_id
                # cs_manage_data.work_id = work_id
                cs_manage_data.cs_rev_no = 0
                cs_manage_data.lost_flag = 0
                cs_manage_data.entry_on_progress_flag = 1
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
                cs_manage_data.save()

        # 更新時の処理
        else:
            # CSid(変数)に渡された予算idをセット
            this_cs_no = cs_no
            # 該当のCSidで作業中FLがONのレコード数をカウント
            on_progress_cs_num = CsGeneralAffairs.objects.filter(cs_no=cs_no, entry_on_progress_flag=1).count()
            # 該当のCSidで(入力)完了FLがONのレコード数をカウント
            complete_entry_cs_num = CsGeneralAffairs.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_cs_num > 0:
                # 該当のCSidで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                cs_data = CsGeneralAffairs.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得
                latest_rev_no = cs_data.cs_rev_no
                # 該当のレコードを無効
                cs_data.lost_flag = 1
                # CSのレコードを保存
                cs_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_cs_num == 0:
                # CSid、登録日時、登録者の情報で新規登録
                CsGeneralAffairs(cs_no=cs_no, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                cs_data = CsGeneralAffairs.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                cs_unique_id = cs_data.id
                # 主キーで予算レコードを抽出
                cs_data = CsGeneralAffairs.objects.get(id=cs_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                cs_data.cs_rev_no = latest_rev_no + 1
                cs_rev_no = latest_rev_no + 1
                cs_data.entry_on_progress_flag = 1
                cs_data.lost_flag = 0
                # データを格納
                cs_data.cs_rev_no = cs_rev_no
                cs_data.cs_no = cs_no
                cs_data.update_datetime = now
                cs_data.update_operator = operator
                cs_data.factory_location_act = factory_location_act
                cs_data.motive = motive
                cs_data.port_harbour_act = port_harbour_act
                cs_data.port_regulations = port_regulations
                cs_data.buildings_regulations = buildings_regulations
                cs_data.cityscape_regulations = cityscape_regulations

                # データを保存
                cs_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                cs_data = CsGeneralAffairs.objects.get(cs_no=cs_no, entry_on_progress_flag=1, lost_flag=0)
                # manage_data = CsManage.objects.get(cs_no=cs_no, entry_on_progress_flag=1)
                # 主キーを取得
                cs_unique_id = cs_data.id
                # データを格納
                cs_data.cs_rev_no = cs_rev_no
                cs_data.cs_no = cs_no
                cs_data.update_datetime = now
                cs_data.update_operator = operator
                cs_data.factory_location_act = factory_location_act
                cs_data.motive = motive
                cs_data.port_harbour_act = port_harbour_act
                cs_data.port_regulations = port_regulations
                cs_data.buildings_regulations = buildings_regulations
                cs_data.cityscape_regulations = cityscape_regulations
                cs_data.lost_flag = 0

                # データを保存
                cs_data.save()

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "総務管轄一時保存完了"

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = "総務管轄" + step_name + "完了"

        # 【！注意！】担当部署名をマスタ管理化する場合は関数「cs_go_next_step」も変更すること【！注意！】
        # if this_step != next_step:
        # 総務G関係の届出進捗テーブルを削除
        data_num = CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='総務部').all().count()
        if data_num > 0:
            CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='総務部').all().delete()
        # 届出進捗テーブルに情報記載
        if factory_location_act == '1':
            laws_detail_name = '特定工場（' + cs_data.motive + '）及び期間短縮申請'
            law_code_no = FactoryLocationActMotiveMaster.objects.get(motive=cs_data.motive).id
            law_code = 'A101-' + str(law_code_no) + '0'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '工場立地法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '総務部'
            cs_progress_data.limit_date = '90日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if port_harbour_act == '1':
            laws_detail_name = '水域占用内工作物占用・工事申請'
            law_code = 'A201-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '港湾法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '総務部'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if port_regulations == '1':
            laws_detail_name = '港内工事申請'
            law_code = 'A301-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '港則法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '総務部'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if buildings_regulations == '1':
            laws_detail_name = '標識設置届'
            law_code = 'A401-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市中高層建築物等に関する条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '総務部'
            cs_progress_data.limit_date = '60日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if cityscape_regulations == '1':
            laws_detail_name = '大規模建築物等行為届（高さ13m又は面積1,000㎡を超えるもの）'
            law_code = 'A501-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市都市景観条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '総務部'
            cs_progress_data.limit_date = '60日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 対象の「工事id」、「rev_no」で自由記入仕様のレコードを取得
            cs_general_affairs_data = CsGeneralAffairs.objects.filter(cs_no=cs_no, cs_rev_no=cs_rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for cs_general_affairs_data in cs_general_affairs_data:
                # 作業中FLに「0」をセット
                cs_general_affairs_data.entry_on_progress_flag = 0
                # 自由記入仕様のレコードを保存
                cs_general_affairs_data.save()

        ary = {
            'cs_no': this_cs_no,
            'cs_rev_no': cs_rev_no,
            'budget_id': budget_id,
            # 'work_id': work_id,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 安全衛生管轄届出情報登録･更新
@login_required
@require_POST
def cs_safety_health_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        # デッドロック回避のため1秒待ち
        time.sleep(1)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        sh_edit_flag = int(request.POST["sh_edit_flag"])

        budget_id = int(request.POST["budget_id"])
        # work_id = int(request.POST["work_id"])

        if request.POST["cs_no"] is not "":
            cs_no = int(request.POST["cs_no"])
        else:
            cs_no = 0

        if request.POST["cs_rev_no"] is not "":
            cs_rev_no = int(request.POST["cs_rev_no"])
        else:
            cs_rev_no = 0

        # 消防法_危険物承認申請
        fire_service_app = request.POST["fire_service_app"]
        if fire_service_app is "":
            fire_service_app = False

        # 消防法_危険物承認申請_場所
        fire_service_app_place = request.POST["fire_service_app_place"]
        if fire_service_app_place is "":
            fire_service_app_place = "場所"

        # 消防法_危険物承認申請_扱い
        fire_service_app_action = request.POST["fire_service_app_action"]
        if fire_service_app_action is "":
            fire_service_app_action = "扱い"

        # 消防法_危険物届
        fire_service_ntfc = request.POST["fire_service_ntfc"]
        if fire_service_ntfc is "":
            fire_service_ntfc = False

        # 消防法_危険物届_場所
        fire_service_ntfc_place = request.POST["fire_service_ntfc_place"]
        if fire_service_ntfc_place is "":
            fire_service_ntfc_place = "場所"

        # 消防法_危険物届_改廃
        fire_service_ntfc_amendment = request.POST["fire_service_ntfc_amendment"]
        if fire_service_ntfc_amendment is "":
            fire_service_ntfc_amendment = "改廃"

        # 消防法_危険物品名数量倍数変更届
        fire_service_quantity_ntfc = request.POST["fire_service_quantity_ntfc"]
        if fire_service_quantity_ntfc is "":
            fire_service_quantity_ntfc = False

        # 消防法_危険物品名数量倍数変更届_場所
        fire_service_quantity_ntfc_place = request.POST["fire_service_quantity_ntfc_place"]
        if fire_service_quantity_ntfc_place is "":
            fire_service_quantity_ntfc_place = "場所"

        # 消防法_圧縮アセチレンガス等貯蔵取扱届出
        fire_service_acetylene_gas_ntfc = request.POST["fire_service_acetylene_gas_ntfc"]
        if fire_service_acetylene_gas_ntfc is "":
            fire_service_acetylene_gas_ntfc = False

        # 消防法_圧縮アセチレンガス等貯蔵取扱届出_改廃
        fire_service_acetylene_gas_ntfc_amendment = request.POST["fire_service_acetylene_gas_ntfc_amendment"]
        if fire_service_acetylene_gas_ntfc_amendment is "":
            fire_service_acetylene_gas_ntfc_amendment = "改廃"

        # 消防法_危険物仮承認申請
        fire_service_tentative_app = request.POST["fire_service_tentative_app"]
        if fire_service_tentative_app is "":
            fire_service_tentative_app = False

        # 消防法_危険物仮承認申請_扱い
        fire_service_tentative_app_action = request.POST["fire_service_tentative_app_action"]
        if fire_service_tentative_app_action is "":
            fire_service_tentative_app_action = "扱い"

        # 市火災予防条例_危険物貯蔵取扱届
        fire_prevent_storage_ntfc = request.POST["fire_prevent_storage_ntfc"]
        if fire_prevent_storage_ntfc is "":
            fire_prevent_storage_ntfc = False

        # 市火災予防条例_危険物貯蔵取扱届_種類
        fire_prevent_storage_ntfc_category = request.POST["fire_prevent_storage_ntfc_category"]
        if fire_prevent_storage_ntfc_category is "":
            fire_prevent_storage_ntfc_category = "種類"

        # 市火災予防条例_危険物貯蔵取扱届_改廃
        fire_prevent_storage_ntfc_amendment = request.POST["fire_prevent_storage_ntfc_amendment"]
        if fire_prevent_storage_ntfc_amendment is "":
            fire_prevent_storage_ntfc_amendment = "改廃"

        # 市火災予防条例_設備設置届
        fire_prevent_equip_ntfc = request.POST["fire_prevent_equip_ntfc"]
        if fire_prevent_equip_ntfc is "":
            fire_prevent_equip_ntfc = False

        # 市火災予防条例_設備設置届_種類
        fire_prevent_equip_ntfc_category = request.POST["fire_prevent_equip_ntfc_category"]
        if fire_prevent_equip_ntfc_category is "":
            fire_prevent_equip_ntfc_category = "種類"

        # 市火災予防条例_防火対象物使用開始届
        fire_prevent_commencement_ntfc = request.POST["fire_prevent_commencement_ntfc"]
        if fire_prevent_commencement_ntfc is "":
            fire_prevent_commencement_ntfc = False

        # 市火災予防条例_消防用設備等　工事計画書
        fire_prevent_construction_plan = request.POST["fire_prevent_construction_plan"]
        if fire_prevent_construction_plan is "":
            fire_prevent_construction_plan = False

        # 市火災予防条例_消防用設備等　設置届
        fire_prevent_installation_ntfc = request.POST["fire_prevent_installation_ntfc"]
        if fire_prevent_installation_ntfc is "":
            fire_prevent_installation_ntfc = False

        # 市火災予防条例_危険作業　開始届
        fire_prevent_hazardous_work_ntfc = request.POST["fire_prevent_hazardous_work_ntfc"]
        if fire_prevent_hazardous_work_ntfc is "":
            fire_prevent_hazardous_work_ntfc = False

        # 市火災予防条例_発煙・発火行為届出書
        fire_prevent_fires_smoke_ntfc = request.POST["fire_prevent_fires_smoke_ntfc"]
        if fire_prevent_fires_smoke_ntfc is "":
            fire_prevent_fires_smoke_ntfc = False

        # 劇毒物取締法_劇毒物製造業品目登録 申請
        deleterious_substances_list_app = request.POST["deleterious_substances_list_app"]
        if deleterious_substances_list_app is "":
            deleterious_substances_list_app = False

        # 劇毒物取締法_劇毒物変更届
        deleterious_substances_ntfc = request.POST["deleterious_substances_ntfc"]
        if deleterious_substances_ntfc is "":
            deleterious_substances_ntfc = False

        # 劇毒物取締法_劇毒物変更届_取扱
        deleterious_substances_ntfc_purpose = request.POST["deleterious_substances_ntfc_purpose"]
        if deleterious_substances_ntfc_purpose is "":
            deleterious_substances_ntfc_purpose = "取扱"

        # 高圧ガス保安法_特定高圧ガス設備申請
        press_gas_app = request.POST["press_gas_app"]
        if press_gas_app is "":
            press_gas_app = False

        # 高圧ガス保安法_特定高圧ガス設備申請_設置/変更
        press_gas_app_motive = request.POST["press_gas_app_motive"]
        if press_gas_app_motive is "":
            press_gas_app_motive = "設置/変更"

        # 高圧ガス保安法_液化石油高圧ガス設備申請
        press_gas_lpg_app = request.POST["press_gas_lpg_app"]
        if press_gas_lpg_app is "":
            press_gas_lpg_app = False

        # 高圧ガス保安法_液化石油高圧ガス設備申請_設置/変更
        press_gas_lpg_app_motive = request.POST["press_gas_lpg_app_motive"]
        if press_gas_lpg_app_motive is "":
            press_gas_lpg_app_motive = "設置/変更"

        # 高圧ガス保安法_冷凍高圧ガス設備申請
        press_gas_frozen_gas_app = request.POST["press_gas_frozen_gas_app"]
        if press_gas_frozen_gas_app is "":
            press_gas_frozen_gas_app = False

        # 高圧ガス保安法_冷凍高圧ガス設備申請_設置/変更
        press_gas_frozen_gas_app_motive = request.POST["press_gas_frozen_gas_app_motive"]
        if press_gas_frozen_gas_app_motive is "":
            press_gas_frozen_gas_app_motive = "設置/変更"

        # 高圧ガス保安法_特定高圧ガス設備届
        press_gas_ntfc = request.POST["press_gas_ntfc"]
        if press_gas_ntfc is "":
            press_gas_ntfc = False

        # 高圧ガス保安法_特定高圧ガス設備届_改廃
        press_gas_ntfc_amendment = request.POST["press_gas_ntfc_amendment"]
        if press_gas_ntfc_amendment is "":
            press_gas_ntfc_amendment = "改廃"

        # 高圧ガス保安法_液化石油高圧ガス設備届
        press_gas_lpg_ntfc = request.POST["press_gas_lpg_ntfc"]
        if press_gas_lpg_ntfc is "":
            press_gas_lpg_ntfc = False

        # 高圧ガス保安法_液化石油高圧ガス設備届_改廃
        press_gas_lpg_ntfc_amendment = request.POST["press_gas_lpg_ntfc_amendment"]
        if press_gas_lpg_ntfc_amendment is "":
            press_gas_lpg_ntfc_amendment = "改廃"

        # 高圧ガス保安法_冷凍高圧ガス設備届
        press_gas_frozen_gas_ntfc = request.POST["press_gas_frozen_gas_ntfc"]
        if press_gas_frozen_gas_ntfc is "":
            press_gas_frozen_gas_ntfc = False

        # 高圧ガス保安法_冷凍高圧ガス設備届_改廃
        press_gas_frozen_gas_ntfc_amendment = request.POST["press_gas_frozen_gas_ntfc_amendment"]
        if press_gas_frozen_gas_ntfc_amendment is "":
            press_gas_frozen_gas_ntfc_amendment = "改廃"

        # 高圧ガス保安法_特定高圧ガス消費設備届
        press_gas_consumption_ntfc = request.POST["press_gas_consumption_ntfc"]
        if press_gas_consumption_ntfc is "":
            press_gas_consumption_ntfc = False

        # 高圧ガス保安法_特定高圧ガス消費設備届_改廃
        press_gas_consumption_ntfc_amendment = request.POST["press_gas_consumption_ntfc_amendment"]
        if press_gas_consumption_ntfc_amendment is "":
            press_gas_consumption_ntfc_amendment = "改廃"

        # 労働安全衛生法_設置物届
        safety_health_equip_ntfc = request.POST["safety_health_equip_ntfc"]
        if safety_health_equip_ntfc is "":
            safety_health_equip_ntfc = False

        # 労働安全衛生法_設置物届_種類
        safety_health_equip_ntfc_category = request.POST["safety_health_equip_ntfc_category"]
        if safety_health_equip_ntfc_category is "":
            safety_health_equip_ntfc_category = "種類"

        # 労働安全衛生法_設置物届_設置/変更
        safety_health_equip_ntfc_motive = request.POST["safety_health_equip_ntfc_motive"]
        if safety_health_equip_ntfc_motive is "":
            safety_health_equip_ntfc_motive = "設置/変更"

        # 労働安全衛生法_有害物質届
        safety_health_deleterious_ntfc = request.POST["safety_health_deleterious_ntfc"]
        if safety_health_deleterious_ntfc is "":
            safety_health_deleterious_ntfc = False

        # 労働安全衛生法_有害物質届_種類
        safety_health_deleterious_ntfc_category = request.POST["safety_health_deleterious_ntfc_category"]
        if safety_health_deleterious_ntfc_category is "":
            safety_health_deleterious_ntfc_category = "種類"

        # 労働安全衛生法_有害物質届_設置/変更
        safety_health_deleterious_ntfc_motive = request.POST["safety_health_deleterious_ntfc_motive"]
        if safety_health_deleterious_ntfc_motive is "":
            safety_health_deleterious_ntfc_motive = "設置/変更"

        # 労働安全衛生法_石綿障害予防規則
        safety_health_asbestos = request.POST["safety_health_asbestos"]
        if safety_health_asbestos is "":
            safety_health_asbestos = False

        # 労働安全衛生法_設備届
        safety_health_specified_equip_ntfc = request.POST["safety_health_specified_equip_ntfc"]
        if safety_health_specified_equip_ntfc is "":
            safety_health_specified_equip_ntfc = False

        # 労働安全衛生法_設備届_種類
        safety_health_specified_equip_ntfc_category = request.POST["safety_health_specified_equip_ntfc_category"]
        if safety_health_specified_equip_ntfc_category is "":
            safety_health_specified_equip_ntfc_category = "種類"

        # 労働安全衛生法_設備届_設置/変更
        safety_health_specified_equip_ntfc_motive = request.POST["safety_health_specified_equip_ntfc_motive"]
        if safety_health_specified_equip_ntfc_motive is "":
            safety_health_specified_equip_ntfc_motive = "設置/変更"

        # 労働安全衛生法_設備設置報告
        safety_health_installation_report = request.POST["safety_health_installation_report"]
        if safety_health_installation_report is "":
            safety_health_installation_report = False

        # 労働安全衛生法_設備設置報告_種類
        safety_health_installation_report_category = request.POST["safety_health_installation_report_category"]
        if safety_health_installation_report_category is "":
            safety_health_installation_report_category = "種類"

        # # 労働安全衛生法_設備設置報告_設置/変更
        # safety_health_installation_report_motive = request.POST["safety_health_installation_report_motive"]
        # if safety_health_installation_report_motive is "":
        #     safety_health_installation_report_motive = "設置/変更"

        # 放射線障害防止法_放射性同位元素申請
        radiation_hazards_app = request.POST["radiation_hazards_app"]
        if radiation_hazards_app is "":
            radiation_hazards_app = False

        # 放射線障害防止法_放射性同位元素申請_使用/変更
        radiation_hazards_app_motive = request.POST["radiation_hazards_app_motive"]
        if radiation_hazards_app_motive is "":
            radiation_hazards_app_motive = "使用/変更"

        # 石災法
        petroleum_complexes_act = request.POST["petroleum_complexes_act"]
        if petroleum_complexes_act is "":
            petroleum_complexes_act = False

        comment = request.POST["comment"]

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # cs_data_num = CsSafetyHealth.objects.all().count()
        cs_data_num = CsManage.objects.all().count()

        # 新規登録時の処理
        if cs_no == 0:
            # 届け出チェックシートのレコードがない時の処理･･･チェックシートid=1 とする
            if cs_data_num == 0:
                this_cs_no = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                # last_cs_data = CsSafetyHealth.objects.all().order_by('-cs_no')[0]
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1
            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            cs_safety_health_entry_data, created = CsSafetyHealth.objects.get_or_create(cs_no=this_cs_no)

            # データを格納
            cs_safety_health_entry_data.cs_rev_no = cs_rev_no
            cs_safety_health_entry_data.entry_datetime = now
            cs_safety_health_entry_data.entry_operator = operator
            cs_safety_health_entry_data.entry_on_progress_flag = 1
            cs_safety_health_entry_data.fire_service_app = fire_service_app
            cs_safety_health_entry_data.fire_service_app_place = fire_service_app_place
            cs_safety_health_entry_data.fire_service_app_action = fire_service_app_action
            cs_safety_health_entry_data.fire_service_ntfc = fire_service_ntfc
            cs_safety_health_entry_data.fire_service_ntfc_place = fire_service_ntfc_place
            cs_safety_health_entry_data.fire_service_ntfc_amendment = fire_service_ntfc_amendment
            cs_safety_health_entry_data.fire_service_quantity_ntfc = fire_service_quantity_ntfc
            cs_safety_health_entry_data.fire_service_quantity_ntfc_place = fire_service_quantity_ntfc_place
            cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc = fire_service_acetylene_gas_ntfc
            cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc_amendment = fire_service_acetylene_gas_ntfc_amendment
            cs_safety_health_entry_data.fire_service_tentative_app = fire_service_tentative_app
            cs_safety_health_entry_data.fire_service_tentative_app_action = fire_service_tentative_app_action
            cs_safety_health_entry_data.fire_prevent_storage_ntfc = fire_prevent_storage_ntfc
            cs_safety_health_entry_data.fire_prevent_storage_ntfc_category = fire_prevent_storage_ntfc_category
            cs_safety_health_entry_data.fire_prevent_storage_ntfc_amendment = fire_prevent_storage_ntfc_amendment
            cs_safety_health_entry_data.fire_prevent_equip_ntfc = fire_prevent_equip_ntfc
            cs_safety_health_entry_data.fire_prevent_equip_ntfc_category = fire_prevent_equip_ntfc_category
            cs_safety_health_entry_data.fire_prevent_commencement_ntfc = fire_prevent_commencement_ntfc
            cs_safety_health_entry_data.fire_prevent_construction_plan = fire_prevent_construction_plan
            cs_safety_health_entry_data.fire_prevent_installation_ntfc = fire_prevent_installation_ntfc
            cs_safety_health_entry_data.fire_prevent_hazardous_work_ntfc = fire_prevent_hazardous_work_ntfc
            cs_safety_health_entry_data.fire_prevent_fires_smoke_ntfc = fire_prevent_fires_smoke_ntfc
            cs_safety_health_entry_data.deleterious_substances_list_app = deleterious_substances_list_app
            cs_safety_health_entry_data.deleterious_substances_ntfc = deleterious_substances_ntfc
            cs_safety_health_entry_data.deleterious_substances_ntfc_purpose = deleterious_substances_ntfc_purpose
            cs_safety_health_entry_data.press_gas_app = press_gas_app
            cs_safety_health_entry_data.press_gas_app_motive = press_gas_app_motive
            cs_safety_health_entry_data.press_gas_lpg_app = press_gas_lpg_app
            cs_safety_health_entry_data.press_gas_lpg_app_motive = press_gas_lpg_app_motive
            cs_safety_health_entry_data.press_gas_frozen_gas_app = press_gas_frozen_gas_app
            cs_safety_health_entry_data.press_gas_frozen_gas_app_motive = press_gas_frozen_gas_app_motive
            cs_safety_health_entry_data.press_gas_ntfc = press_gas_ntfc
            cs_safety_health_entry_data.press_gas_ntfc_amendment = press_gas_ntfc_amendment
            cs_safety_health_entry_data.press_gas_lpg_ntfc = press_gas_lpg_ntfc
            cs_safety_health_entry_data.press_gas_lpg_ntfc_amendment = press_gas_lpg_ntfc_amendment
            cs_safety_health_entry_data.press_gas_frozen_gas_ntfc = press_gas_frozen_gas_ntfc
            cs_safety_health_entry_data.press_gas_frozen_gas_ntfc_amendment = press_gas_frozen_gas_ntfc_amendment
            cs_safety_health_entry_data.press_gas_consumption_ntfc = press_gas_consumption_ntfc
            cs_safety_health_entry_data.press_gas_consumption_ntfc_amendment = press_gas_consumption_ntfc_amendment
            cs_safety_health_entry_data.safety_health_equip_ntfc = safety_health_equip_ntfc
            cs_safety_health_entry_data.safety_health_equip_ntfc_category = safety_health_equip_ntfc_category
            cs_safety_health_entry_data.safety_health_equip_ntfc_motive = safety_health_equip_ntfc_motive
            cs_safety_health_entry_data.safety_health_deleterious_ntfc = safety_health_deleterious_ntfc
            cs_safety_health_entry_data.safety_health_deleterious_ntfc_category = safety_health_deleterious_ntfc_category
            cs_safety_health_entry_data.safety_health_deleterious_ntfc_motive = safety_health_deleterious_ntfc_motive
            cs_safety_health_entry_data.safety_health_asbestos = safety_health_asbestos
            cs_safety_health_entry_data.safety_health_specified_equip_ntfc = safety_health_specified_equip_ntfc
            cs_safety_health_entry_data.safety_health_specified_equip_ntfc_category = safety_health_specified_equip_ntfc_category
            cs_safety_health_entry_data.safety_health_specified_equip_ntfc_motive = safety_health_specified_equip_ntfc_motive
            cs_safety_health_entry_data.safety_health_installation_report = safety_health_installation_report
            cs_safety_health_entry_data.safety_health_installation_report_category = safety_health_installation_report_category
            # cs_safety_health_entry_data.safety_health_installation_report_motive = safety_health_installation_report_motive
            cs_safety_health_entry_data.radiation_hazards_app = radiation_hazards_app
            cs_safety_health_entry_data.radiation_hazards_app_motive = radiation_hazards_app_motive
            cs_safety_health_entry_data.petroleum_complexes_act = petroleum_complexes_act
            cs_safety_health_entry_data.lost_flag = 0

            # データを保存
            cs_safety_health_entry_data.save()

            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)
            if created:
                cs_manage_data.budget_id = budget_id
                # cs_manage_data.work_id = work_id
                cs_manage_data.cs_rev_no = 0
                cs_manage_data.lost_flag = 0
                cs_manage_data.entry_on_progress_flag = 1
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
                cs_manage_data.save()

        # 更新時の処理
        else:
            # CSid(変数)に渡された予算idをセット
            this_cs_no = cs_no
            # 該当のCSidで作業中FLがONのレコード数をカウント
            on_progress_cs_num = CsSafetyHealth.objects.filter(cs_no=cs_no, entry_on_progress_flag=1).count()
            # 該当のCSidで(入力)完了FLがONのレコード数をカウント
            complete_entry_cs_num = CsSafetyHealth.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_cs_num > 0:
                # 該当のCSidで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                cs_safety_health_entry_data = CsSafetyHealth.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得
                latest_rev_no = cs_safety_health_entry_data.cs_rev_no
                # 該当のレコードを無効
                cs_safety_health_entry_data.lost_flag = 1
                # CSのレコードを保存
                cs_safety_health_entry_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_cs_num == 0:
                # CSid、登録日時、登録者の情報で新規登録
                CsSafetyHealth(cs_no=cs_no, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                cs_safety_health_entry_data = CsSafetyHealth.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                cs_unique_id = cs_safety_health_entry_data.id
                # 主キーで予算レコードを抽出
                cs_safety_health_entry_data = CsSafetyHealth.objects.get(id=cs_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                cs_safety_health_entry_data.cs_rev_no = latest_rev_no + 1
                cs_rev_no = latest_rev_no + 1
                cs_safety_health_entry_data.entry_on_progress_flag = 1
                cs_safety_health_entry_data.lost_flag = 0
                # データを格納
                cs_safety_health_entry_data.cs_rev_no = cs_rev_no
                cs_safety_health_entry_data.cs_no = cs_no
                cs_safety_health_entry_data.update_datetime = now
                cs_safety_health_entry_data.update_operator = operator
                cs_safety_health_entry_data.fire_service_app = fire_service_app
                cs_safety_health_entry_data.fire_service_app_place = fire_service_app_place
                cs_safety_health_entry_data.fire_service_app_action = fire_service_app_action
                cs_safety_health_entry_data.fire_service_ntfc = fire_service_ntfc
                cs_safety_health_entry_data.fire_service_ntfc_place = fire_service_ntfc_place
                cs_safety_health_entry_data.fire_service_ntfc_amendment = fire_service_ntfc_amendment
                cs_safety_health_entry_data.fire_service_quantity_ntfc = fire_service_quantity_ntfc
                cs_safety_health_entry_data.fire_service_quantity_ntfc_place = fire_service_quantity_ntfc_place
                cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc = fire_service_acetylene_gas_ntfc
                cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc_amendment = fire_service_acetylene_gas_ntfc_amendment
                cs_safety_health_entry_data.fire_service_tentative_app = fire_service_tentative_app
                cs_safety_health_entry_data.fire_service_tentative_app_action = fire_service_tentative_app_action
                cs_safety_health_entry_data.fire_prevent_storage_ntfc = fire_prevent_storage_ntfc
                cs_safety_health_entry_data.fire_prevent_storage_ntfc_category = fire_prevent_storage_ntfc_category
                cs_safety_health_entry_data.fire_prevent_storage_ntfc_amendment = fire_prevent_storage_ntfc_amendment
                cs_safety_health_entry_data.fire_prevent_equip_ntfc = fire_prevent_equip_ntfc
                cs_safety_health_entry_data.fire_prevent_equip_ntfc_category = fire_prevent_equip_ntfc_category
                cs_safety_health_entry_data.fire_prevent_commencement_ntfc = fire_prevent_commencement_ntfc
                cs_safety_health_entry_data.fire_prevent_construction_plan = fire_prevent_construction_plan
                cs_safety_health_entry_data.fire_prevent_installation_ntfc = fire_prevent_installation_ntfc
                cs_safety_health_entry_data.fire_prevent_hazardous_work_ntfc = fire_prevent_hazardous_work_ntfc
                cs_safety_health_entry_data.fire_prevent_fires_smoke_ntfc = fire_prevent_fires_smoke_ntfc
                cs_safety_health_entry_data.deleterious_substances_list_app = deleterious_substances_list_app
                cs_safety_health_entry_data.deleterious_substances_ntfc = deleterious_substances_ntfc
                cs_safety_health_entry_data.deleterious_substances_ntfc_purpose = deleterious_substances_ntfc_purpose
                cs_safety_health_entry_data.press_gas_app = press_gas_app
                cs_safety_health_entry_data.press_gas_app_motive = press_gas_app_motive
                cs_safety_health_entry_data.press_gas_lpg_app = press_gas_lpg_app
                cs_safety_health_entry_data.press_gas_lpg_app_motive = press_gas_lpg_app_motive
                cs_safety_health_entry_data.press_gas_frozen_gas_app = press_gas_frozen_gas_app
                cs_safety_health_entry_data.press_gas_frozen_gas_app_motive = press_gas_frozen_gas_app_motive
                cs_safety_health_entry_data.press_gas_ntfc = press_gas_ntfc
                cs_safety_health_entry_data.press_gas_ntfc_amendment = press_gas_ntfc_amendment
                cs_safety_health_entry_data.press_gas_lpg_ntfc = press_gas_lpg_ntfc
                cs_safety_health_entry_data.press_gas_lpg_ntfc_amendment = press_gas_lpg_ntfc_amendment
                cs_safety_health_entry_data.press_gas_frozen_gas_ntfc = press_gas_frozen_gas_ntfc
                cs_safety_health_entry_data.press_gas_frozen_gas_ntfc_amendment = press_gas_frozen_gas_ntfc_amendment
                cs_safety_health_entry_data.press_gas_consumption_ntfc = press_gas_consumption_ntfc
                cs_safety_health_entry_data.press_gas_consumption_ntfc_amendment = press_gas_consumption_ntfc_amendment
                cs_safety_health_entry_data.safety_health_equip_ntfc = safety_health_equip_ntfc
                cs_safety_health_entry_data.safety_health_equip_ntfc_category = safety_health_equip_ntfc_category
                cs_safety_health_entry_data.safety_health_equip_ntfc_motive = safety_health_equip_ntfc_motive
                cs_safety_health_entry_data.safety_health_deleterious_ntfc = safety_health_deleterious_ntfc
                cs_safety_health_entry_data.safety_health_deleterious_ntfc_category = safety_health_deleterious_ntfc_category
                cs_safety_health_entry_data.safety_health_deleterious_ntfc_motive = safety_health_deleterious_ntfc_motive
                cs_safety_health_entry_data.safety_health_asbestos = safety_health_asbestos
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc = safety_health_specified_equip_ntfc
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc_category = safety_health_specified_equip_ntfc_category
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc_motive = safety_health_specified_equip_ntfc_motive
                cs_safety_health_entry_data.safety_health_installation_report = safety_health_installation_report
                cs_safety_health_entry_data.safety_health_installation_report_category = safety_health_installation_report_category
                # cs_safety_health_entry_data.safety_health_installation_report_motive = safety_health_installation_report_motive
                cs_safety_health_entry_data.radiation_hazards_app = radiation_hazards_app
                cs_safety_health_entry_data.radiation_hazards_app_motive = radiation_hazards_app_motive
                cs_safety_health_entry_data.petroleum_complexes_act = petroleum_complexes_act

                # データを保存
                cs_safety_health_entry_data.save()

                # 他のタブに対するrev_noアップ処理
                # 1つ前のrev_noのレコードを抽出･･･複数あれば全て抽出
                # cs_safety_health_data = CsSafetyHealth.objects.filter(cs_no=cs_no, cs_rev_no=latest_rev_no)
                # # 抽出されたレコードに対し繰り返し処理
                # for cs_safety_health_data in cs_safety_health_data:
                #     # 次のrevに引き継ぐデータを取得
                #     fire_service_app = cs_safety_health_data.fire_service_app
                #     fire_service_app_place = cs_safety_health_data.fire_service_app_place
                #     fire_service_app_action = cs_safety_health_data.fire_service_app_action
                #     fire_service_ntfc = cs_safety_health_data.fire_service_ntfc
                #     fire_service_ntfc_place = cs_safety_health_data.fire_service_ntfc_place
                #     fire_service_ntfc_amendment = cs_safety_health_data.fire_service_ntfc_amendment
                #     fire_service_quantity_ntfc = cs_safety_health_data.fire_service_quantity_ntfc
                #     fire_service_quantity_ntfc_place = cs_safety_health_data.fire_service_quantity_ntfc_place
                #     fire_service_acetylene_gas_ntfc = cs_safety_health_data.fire_service_acetylene_gas_ntfc
                #     fire_service_acetylene_gas_ntfc_amendment = cs_safety_health_data.fire_service_acetylene_gas_ntfc_amendment
                #     fire_service_tentative_app = cs_safety_health_data.fire_service_tentative_app
                #     fire_service_tentative_app_action = cs_safety_health_data.fire_service_tentative_app_action
                #     fire_prevent_storage_ntfc = cs_safety_health_data.fire_prevent_storage_ntfc
                #     fire_prevent_storage_ntfc_category = cs_safety_health_data.fire_prevent_storage_ntfc_category
                #     fire_prevent_storage_ntfc_amendment = cs_safety_health_data.fire_prevent_storage_ntfc_amendment
                #     fire_prevent_equip_ntfc = cs_safety_health_data.fire_prevent_equip_ntfc
                #     fire_prevent_equip_ntfc_category = cs_safety_health_data.fire_prevent_equip_ntfc_category
                #     fire_prevent_commencement_ntfc = cs_safety_health_data.fire_prevent_commencement_ntfc
                #     fire_prevent_construction_plan = cs_safety_health_data.fire_prevent_construction_plan
                #     fire_prevent_installation_ntfc = cs_safety_health_data.fire_prevent_installation_ntfc
                #     fire_prevent_hazardous_work_ntfc = cs_safety_health_data.fire_prevent_hazardous_work_ntfc
                #     fire_prevent_fires_smoke_ntfc = cs_safety_health_data.fire_prevent_fires_smoke_ntfc
                #     deleterious_substances_list_app = cs_safety_health_data.deleterious_substances_list_app
                #     deleterious_substances_ntfc = cs_safety_health_data.deleterious_substances_ntfc
                #     deleterious_substances_ntfc_purpose = cs_safety_health_data.deleterious_substances_ntfc_purpose
                #     press_gas_app = cs_safety_health_data.press_gas_app
                #     press_gas_app_motive = cs_safety_health_data.press_gas_app_motive
                #     press_gas_lpg_app = cs_safety_health_data.press_gas_lpg_app
                #     press_gas_lpg_app_motive = cs_safety_health_data.press_gas_lpg_app_motive
                #     press_gas_frozen_gas_app = cs_safety_health_data.press_gas_frozen_gas_app
                #     press_gas_frozen_gas_app_motive = cs_safety_health_data.press_gas_frozen_gas_app_motive
                #     press_gas_ntfc = cs_safety_health_data.press_gas_ntfc
                #     press_gas_ntfc_amendment = cs_safety_health_data.press_gas_ntfc_amendment
                #     press_gas_lpg_ntfc = cs_safety_health_data.press_gas_lpg_ntfc
                #     press_gas_lpg_ntfc_amendment = cs_safety_health_data.press_gas_lpg_ntfc_amendment
                #     press_gas_frozen_gas_ntfc = cs_safety_health_data.press_gas_frozen_gas_ntfc
                #     press_gas_frozen_gas_ntfc_amendment = cs_safety_health_data.press_gas_frozen_gas_ntfc_amendment
                #     press_gas_consumption_ntfc = cs_safety_health_data.press_gas_consumption_ntfc
                #     press_gas_consumption_ntfc_amendment = cs_safety_health_data.press_gas_consumption_ntfc_amendment
                #     safety_health_equip_ntfc = cs_safety_health_data.safety_health_equip_ntfc
                #     safety_health_equip_ntfc_category = cs_safety_health_data.safety_health_equip_ntfc_category
                #     safety_health_equip_ntfc_motive = cs_safety_health_data.safety_health_equip_ntfc_motive
                #     safety_health_deleterious_ntfc = cs_safety_health_data.safety_health_deleterious_ntfc
                #     safety_health_deleterious_ntfc_category = cs_safety_health_data.safety_health_deleterious_ntfc_category
                #     safety_health_deleterious_ntfc_motive = cs_safety_health_data.safety_health_deleterious_ntfc_motive
                #     safety_health_asbestos = cs_safety_health_data.safety_health_asbestos
                #     safety_health_specified_equip_ntfc = cs_safety_health_data.safety_health_specified_equip_ntfc
                #     safety_health_specified_equip_ntfc_category = cs_safety_health_data.safety_health_specified_equip_ntfc_category
                #     safety_health_specified_equip_ntfc_motive = cs_safety_health_data.safety_health_specified_equip_ntfc_motive
                #     safety_health_installation_report = cs_safety_health_data.safety_health_installation_report
                #     safety_health_installation_report_category = cs_safety_health_data.safety_health_installation_report_category
                #     safety_health_installation_report_motive = cs_safety_health_data.safety_health_installation_report_motive
                #     radiation_hazards_app = cs_safety_health_data.radiation_hazards_app
                #     radiation_hazards_app_motive = cs_safety_health_data.radiation_hazards_app_motive
                #     petroleum_complexes_act = cs_safety_health_data.petroleum_complexes_act
                #     note = cs_safety_health_data.note
                #
                #     # レコードの無効化(lost_flag = 1)
                #     cs_safety_health_data.lost_flag = 1
                #     # 提出書類のレコードを保存
                #     cs_safety_health_data.save()
                #
                #     # 「work_id」、「rev_no」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                #     cs_safety_health_data, created = CsSafetyHealth.objects.get_or_create(cs_no=cs_no, cs_rev_no=cs_rev_no)
                #     # 各項目の値(1つ前のrevでの値)を格納
                #     cs_safety_health_data.lost_flag = 0
                #     cs_safety_health_data.entry_on_progress_flag = 1
                #     cs_safety_health_data.entry_datetime = now
                #     cs_safety_health_data.entry_operator = operator
                #     # 提出書類のレコードを保存
                #     cs_safety_health_data.save()
                #
                # # 1つ前のrev_noの工事関連法令のレコードを抽出･･･複数あれば全て抽出
                # cs_environment_data = CsEnvironment.objects.filter(cs_no=cs_no, rev_no=latest_rev_no)
                # # 抽出されたレコードに対し繰り返し処理
                # for cs_environment_data in cs_environment_data:
                #     # 次のrevに引き継ぐデータを取得
                #     air_pollution_equip_ntfc = cs_environment_data.air_pollution_equip_ntfc
                #     air_pollution_equip_ntfc_category = cs_environment_data.air_pollution_equip_ntfc_category
                #     air_pollution_equip_ntfc_motive = cs_environment_data.air_pollution_equip_ntfc_motive
                #     air_pollution_repeal_equip_ntfc = cs_environment_data.air_pollution_repeal_equip_ntfc
                #     air_pollution_repeal_equip_ntfc_category = cs_environment_data.air_pollution_repeal_equip_ntfc_category
                #     air_pollution_voc_ntfc = cs_environment_data.air_pollution_voc_ntfc
                #     air_pollution_voc_ntfc_action = cs_environment_data.air_pollution_voc_ntfc_action
                #     air_pollution_particulates_ntfc = cs_environment_data.air_pollution_particulates_ntfc
                #     water_pollution_ntfc = cs_environment_data.water_pollution_ntfc
                #     water_pollution_ntfc_action = cs_environment_data.water_pollution_ntfc_action
                #     soil_contamination_ntfc = cs_environment_data.soil_contamination_ntfc
                #     waste_equip_app = cs_environment_data.waste_equip_app
                #     waste_equip_app_motive = cs_environment_data.waste_equip_app_motive
                #     waste_repeal_equip_ntfc = cs_environment_data.waste_repeal_equip_ntfc
                #     management_freon_plan = cs_environment_data.management_freon_plan
                #     living_env_equip_ntfc = cs_environment_data.living_env_equip_ntfc
                #     living_env_equip_ntfc_category = cs_environment_data.living_env_equip_ntfc_category
                #     living_env_equip_ntfc_action = cs_environment_data.living_env_equip_ntfc_action
                #     living_env_nox_emission_plan_ntfc = cs_environment_data.living_env_nox_emission_plan_ntfc
                #     living_env_soil_survey = cs_environment_data.living_env_soil_survey
                #     living_env_water_pumping_app = cs_environment_data.living_env_water_pumping_app
                #     pollution_agree_consultation = cs_environment_data.pollution_agree_consultation
                #     titanium_compatible_report = cs_environment_data.titanium_compatible_report
                #     water_purification_tanks_ntfc = cs_environment_data.water_purification_tanks_ntfc
                #     water_purification_tanks_ntfc_amendment = cs_environment_data.water_purification_tanks_ntfc_amendment
                #     note = cs_environment_data.note
                #     # レコードの無効化(lost_flag = 1)
                #     cs_environment_data.lost_flag = 1
                #     # 工事関連法令のレコードを保存
                #     cs_environment_data.save()
                #
                #     # 「work_id」、「rev_no」で工事関連法令のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                #     cs_environment_data, created = CsEnvironment.objects.get_or_create(cs_no=cs_no, cs_rev_no=cs_rev_no)
                #     # 各項目の値(1つ前のrevでの値)を格納
                #     cs_environment_data.lost_flag = 0
                #     cs_environment_data.entry_on_progress_flag = 1
                #     cs_environment_data.entry_datetime = now
                #     cs_environment_data.entry_operator = operator
                #     # 工事関連法令のレコードを保存
                #     cs_environment_data.save()
                #
                # # 1つ前のrev_noの工事支給品のレコードを抽出･･･複数あれば全て抽出
                # cs_engineering_data = CsEngineering.objects.filter(cs_no=cs_no, rev_no=latest_rev_no)
                # # 抽出されたレコードに対し繰り返し処理
                # for cs_engineering_data in cs_engineering_data:
                #     # 次のrevに引き継ぐデータを取得
                #     building_standards_act = cs_engineering_data.building_standards_act
                #     building_standards_act_category = cs_engineering_data.building_standards_act_category
                #     energy_rationalization_act = cs_engineering_data.energy_rationalization_act
                #     energy_rationalization_act_category = cs_engineering_data.energy_rationalization_act_category
                #     energy_rationalization_act_action = cs_engineering_data.energy_rationalization_act_action
                #     construction_recycling = cs_engineering_data.construction_recycling
                #     construction_recycling_category = cs_engineering_data.construction_recycling_category
                #     note = cs_engineering_data.note
                #     # レコードの無効化(lost_flag = 1)
                #     cs_engineering_data.lost_flag = 1
                #     # 工事支給品のレコードを保存
                #     cs_engineering_data.save()
                #
                #     # 「work_id」、「rev_no」で工事支給品のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                #     cs_engineering_data, created = CsEngineering.objects.get_or_create(cs_no=cs_no, cs_rev_no=cs_rev_no)
                #     # 各項目の値(1つ前のrevでの値)を格納
                #     cs_engineering_data.lost_flag = 0
                #     cs_engineering_data.entry_on_progress_flag = 1
                #     cs_engineering_data.entry_datetime = now
                #     cs_engineering_data.entry_operator = operator
                #     # 工事支給品のレコードを保存
                #     cs_engineering_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                cs_safety_health_entry_data = CsSafetyHealth.objects.get(cs_no=cs_no, entry_on_progress_flag=1, lost_flag=0)
                # manage_data = CsManage.objects.get(cs_no=cs_no, entry_on_progress_flag=1)
                # 主キーを取得
                cs_unique_id = cs_safety_health_entry_data.id
                # データを格納
                cs_safety_health_entry_data.cs_rev_no = cs_rev_no
                cs_safety_health_entry_data.cs_no = cs_no
                cs_safety_health_entry_data.update_datetime = now
                cs_safety_health_entry_data.update_operator = operator
                cs_safety_health_entry_data.fire_service_app = fire_service_app
                cs_safety_health_entry_data.fire_service_app_place = fire_service_app_place
                cs_safety_health_entry_data.fire_service_app_action = fire_service_app_action
                cs_safety_health_entry_data.fire_service_ntfc = fire_service_ntfc
                cs_safety_health_entry_data.fire_service_ntfc_place = fire_service_ntfc_place
                cs_safety_health_entry_data.fire_service_ntfc_amendment = fire_service_ntfc_amendment
                cs_safety_health_entry_data.fire_service_quantity_ntfc = fire_service_quantity_ntfc
                cs_safety_health_entry_data.fire_service_quantity_ntfc_place = fire_service_quantity_ntfc_place
                cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc = fire_service_acetylene_gas_ntfc
                cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc_amendment = fire_service_acetylene_gas_ntfc_amendment
                cs_safety_health_entry_data.fire_service_tentative_app = fire_service_tentative_app
                cs_safety_health_entry_data.fire_service_tentative_app_action = fire_service_tentative_app_action
                cs_safety_health_entry_data.fire_prevent_storage_ntfc = fire_prevent_storage_ntfc
                cs_safety_health_entry_data.fire_prevent_storage_ntfc_category = fire_prevent_storage_ntfc_category
                cs_safety_health_entry_data.fire_prevent_storage_ntfc_amendment = fire_prevent_storage_ntfc_amendment
                cs_safety_health_entry_data.fire_prevent_equip_ntfc = fire_prevent_equip_ntfc
                cs_safety_health_entry_data.fire_prevent_equip_ntfc_category = fire_prevent_equip_ntfc_category
                cs_safety_health_entry_data.fire_prevent_commencement_ntfc = fire_prevent_commencement_ntfc
                cs_safety_health_entry_data.fire_prevent_construction_plan = fire_prevent_construction_plan
                cs_safety_health_entry_data.fire_prevent_installation_ntfc = fire_prevent_installation_ntfc
                cs_safety_health_entry_data.fire_prevent_hazardous_work_ntfc = fire_prevent_hazardous_work_ntfc
                cs_safety_health_entry_data.fire_prevent_fires_smoke_ntfc = fire_prevent_fires_smoke_ntfc
                cs_safety_health_entry_data.deleterious_substances_list_app = deleterious_substances_list_app
                cs_safety_health_entry_data.deleterious_substances_ntfc = deleterious_substances_ntfc
                cs_safety_health_entry_data.deleterious_substances_ntfc_purpose = deleterious_substances_ntfc_purpose
                cs_safety_health_entry_data.press_gas_app = press_gas_app
                cs_safety_health_entry_data.press_gas_app_motive = press_gas_app_motive
                cs_safety_health_entry_data.press_gas_lpg_app = press_gas_lpg_app
                cs_safety_health_entry_data.press_gas_lpg_app_motive = press_gas_lpg_app_motive
                cs_safety_health_entry_data.press_gas_frozen_gas_app = press_gas_frozen_gas_app
                cs_safety_health_entry_data.press_gas_frozen_gas_app_motive = press_gas_frozen_gas_app_motive
                cs_safety_health_entry_data.press_gas_ntfc = press_gas_ntfc
                cs_safety_health_entry_data.press_gas_ntfc_amendment = press_gas_ntfc_amendment
                cs_safety_health_entry_data.press_gas_lpg_ntfc = press_gas_lpg_ntfc
                cs_safety_health_entry_data.press_gas_lpg_ntfc_amendment = press_gas_lpg_ntfc_amendment
                cs_safety_health_entry_data.press_gas_frozen_gas_ntfc = press_gas_frozen_gas_ntfc
                cs_safety_health_entry_data.press_gas_frozen_gas_ntfc_amendment = press_gas_frozen_gas_ntfc_amendment
                cs_safety_health_entry_data.press_gas_consumption_ntfc = press_gas_consumption_ntfc
                cs_safety_health_entry_data.press_gas_consumption_ntfc_amendment = press_gas_consumption_ntfc_amendment
                cs_safety_health_entry_data.safety_health_equip_ntfc = safety_health_equip_ntfc
                cs_safety_health_entry_data.safety_health_equip_ntfc_category = safety_health_equip_ntfc_category
                cs_safety_health_entry_data.safety_health_equip_ntfc_motive = safety_health_equip_ntfc_motive
                cs_safety_health_entry_data.safety_health_deleterious_ntfc = safety_health_deleterious_ntfc
                cs_safety_health_entry_data.safety_health_deleterious_ntfc_category = safety_health_deleterious_ntfc_category
                cs_safety_health_entry_data.safety_health_deleterious_ntfc_motive = safety_health_deleterious_ntfc_motive
                cs_safety_health_entry_data.safety_health_asbestos = safety_health_asbestos
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc = safety_health_specified_equip_ntfc
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc_category = safety_health_specified_equip_ntfc_category
                cs_safety_health_entry_data.safety_health_specified_equip_ntfc_motive = safety_health_specified_equip_ntfc_motive
                cs_safety_health_entry_data.safety_health_installation_report = safety_health_installation_report
                cs_safety_health_entry_data.safety_health_installation_report_category = safety_health_installation_report_category
                # cs_safety_health_entry_data.safety_health_installation_report_motive = safety_health_installation_report_motive
                cs_safety_health_entry_data.radiation_hazards_app = radiation_hazards_app
                cs_safety_health_entry_data.radiation_hazards_app_motive = radiation_hazards_app_motive
                cs_safety_health_entry_data.petroleum_complexes_act = petroleum_complexes_act
                cs_safety_health_entry_data.lost_flag = 0

                # データを保存
                cs_safety_health_entry_data.save()

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "安全衛生管轄一時保存完了"

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = "安全衛生管轄" + step_name + "完了"

        # if this_step != next_step:
        # 安全衛生･保安G関係の届出進捗テーブルを削除
        data_num = CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='安全衛生･保安G').all().count()
        if data_num > 0:
            CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='安全衛生･保安G').all().delete()
        # 届出進捗テーブルに情報記載
        if fire_service_app == '1':
            laws_detail_name = '危険物（' + cs_safety_health_entry_data.fire_service_app_place + '）（'\
                               + cs_safety_health_entry_data.fire_service_app_action + '）及び仮使用承認申請'
            law_code_no1 = FireServiceAppPlaceMaster.objects.get(place=cs_safety_health_entry_data.fire_service_app_place, lost_flag=0).id
            law_code_no2 = FireServiceAppActionMaster.objects.get(action=cs_safety_health_entry_data.fire_service_app_action, lost_flag=0).id
            law_code = 'B101-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '消防法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '60日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_service_ntfc == '1':
            laws_detail_name = '危険物（' + cs_safety_health_entry_data.fire_service_ntfc_place + '）（'\
                               + cs_safety_health_entry_data.fire_service_ntfc_amendment + '）届'
            law_code_no1 = FireServiceNtfcPlaceMaster.objects.get(place=cs_safety_health_entry_data.fire_service_ntfc_place, lost_flag=0).id
            law_code_no2 = FireServiceNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.fire_service_ntfc_amendment, lost_flag=0).id
            law_code = 'B102-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '消防法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_service_quantity_ntfc == '1':
            laws_detail_name = '危険物（' + cs_safety_health_entry_data.fire_service_quantity_ntfc_place + '）品名数量倍数変更届'
            law_code_no1 = FireServiceQuantityNtfcPlaceMaster.objects.get(place=cs_safety_health_entry_data.fire_service_quantity_ntfc_place, lost_flag=0).id
            law_code = 'B103-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '消防法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_service_acetylene_gas_ntfc == '1':
            laws_detail_name = '圧縮アセチレンガス等貯蔵取扱（' \
                               + cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc_amendment + '）届'
            law_code_no1 = FireServiceAcetyleneGasNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.fire_service_acetylene_gas_ntfc_amendment, lost_flag=0).id
            law_code = 'B104-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '消防法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_service_tentative_app == '1':
            laws_detail_name = '危険物仮（' \
                               + cs_safety_health_entry_data.fire_service_tentative_app_action + '）承認申請'
            law_code_no1 = FireServiceTentativeAppActionMaster.objects.get(action=cs_safety_health_entry_data.fire_service_tentative_app_action, lost_flag=0).id
            law_code = 'B105-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '消防法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_storage_ntfc == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.fire_prevent_storage_ntfc_category + '）貯蔵取扱（' \
                               + cs_safety_health_entry_data.fire_prevent_storage_ntfc_amendment + '）届'
            law_code_no1 = FirePreventStorageNtfcCategoryMaster.objects.get(category=cs_safety_health_entry_data.fire_prevent_storage_ntfc_category, lost_flag=0).id
            law_code_no2 = FirePreventStorageNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.fire_prevent_storage_ntfc_amendment, lost_flag=0).id
            law_code = 'B201-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_equip_ntfc == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.fire_prevent_equip_ntfc_category + '）設置届'
            law_code_no1 = FirePreventEquipNtfcCategoryMaster.objects.get(category=cs_safety_health_entry_data.fire_prevent_equip_ntfc_category, lost_flag=0).id
            law_code = 'B202-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_commencement_ntfc == '1':
            laws_detail_name = '防火対象物使用開始届'
            law_code = 'B203-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '7日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_construction_plan == '1':
            laws_detail_name = '消防用設備等工事計画書'
            law_code = 'B204-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '建築申請と同時'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_installation_ntfc == '1':
            laws_detail_name = '消防用設備等設置届'
            law_code = 'B205-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '7日以内(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_hazardous_work_ntfc == '1':
            laws_detail_name = '危険作業開始届'
            law_code = 'B206-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '3日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if fire_prevent_fires_smoke_ntfc == '1':
            laws_detail_name = '火災と紛らわしい煙 又は火災を発するおそれのある行為届出書'
            law_code = 'B207-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市火災予防条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if deleterious_substances_list_app == '1':
            laws_detail_name = '毒物劇物製造業品目登録申請'
            law_code = 'B502-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '劇毒物取締法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '60日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if deleterious_substances_ntfc == '1':
            laws_detail_name = '毒物劇物（' + cs_safety_health_entry_data.deleterious_substances_ntfc_purpose + '）変更届'
            law_code_no1 = DeleteriousSubstancesNtfcPurposeMaster.objects.get(purpose=cs_safety_health_entry_data.deleterious_substances_ntfc_purpose, lost_flag=0).id
            law_code = 'B503-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '劇毒物取締法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_app == '1':
            laws_detail_name = '特定高圧ガス設備（' + cs_safety_health_entry_data.press_gas_app_motive + '）申請'
            law_code_no1 = PressGasAppMotiveMaster.objects.get(motive=cs_safety_health_entry_data.press_gas_app_motive, lost_flag=0).id
            law_code = 'B301-4' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_lpg_app == '1':
            laws_detail_name = '液化石油高圧ガス設備（' + cs_safety_health_entry_data.press_gas_lpg_app_motive + '）申請'
            law_code_no1 = PressGasLpgAppMotiveMaster.objects.get(motive=cs_safety_health_entry_data.press_gas_lpg_app_motive, lost_flag=0).id
            law_code = 'B301-2' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_frozen_gas_app == '1':
            laws_detail_name = '冷凍高圧ガス設備（' + cs_safety_health_entry_data.press_gas_frozen_gas_app_motive + '）申請'
            law_code_no1 = PressGasFrozenGasAppMotiveMaster.objects.get(motive=cs_safety_health_entry_data.press_gas_frozen_gas_app_motive, lost_flag=0).id
            law_code = 'B301-3' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_ntfc == '1':
            laws_detail_name = '特定高圧ガス設備（' + cs_safety_health_entry_data.press_gas_ntfc_amendment + '）届'
            law_code_no1 = PressGasNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.press_gas_ntfc_amendment, lost_flag=0).id
            law_code = 'B302-4' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '遅滞なく'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_lpg_ntfc == '1':
            laws_detail_name = '液化石油高圧ガス設備（' + cs_safety_health_entry_data.press_gas_lpg_ntfc_amendment + '）届'
            law_code_no1 = PressGasLpgNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.press_gas_lpg_ntfc_amendment, lost_flag=0).id
            law_code = 'B302-2' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '遅滞なく'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_frozen_gas_ntfc == '1':
            laws_detail_name = '冷凍高圧ガス設備（' + cs_safety_health_entry_data.press_gas_frozen_gas_ntfc_amendment + '）届'
            law_code_no1 = PressGasFrozenGasNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.press_gas_frozen_gas_ntfc_amendment, lost_flag=0).id
            law_code = 'B302-3' + str(law_code_no1)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '遅滞なく'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if press_gas_consumption_ntfc == '1':
            laws_detail_name = '特定高圧ガス消費設備（' + cs_safety_health_entry_data.press_gas_consumption_ntfc_amendment + '）届'
            law_code_no1 = PressGasConsumptionNtfcAmendmentMaster.objects.get(amendment=cs_safety_health_entry_data.press_gas_consumption_ntfc_amendment, lost_flag=0).id
            law_code = 'B303-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '高圧ガス保安法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '20日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if safety_health_equip_ntfc == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.safety_health_equip_ntfc_category + '）（' \
                                + cs_safety_health_entry_data.safety_health_equip_ntfc_motive + '）届'
            law_code_no1 = SafetyHealthEquipNtfcCategoryMaster.objects.get(category=cs_safety_health_entry_data.safety_health_equip_ntfc_category, lost_flag=0).id
            law_code_no2 = SafetyHealthEquipNtfcMotiveMaster.objects.get(motive=cs_safety_health_entry_data.safety_health_equip_ntfc_motive, lost_flag=0).id
            law_code = 'B401-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '労働安全衛生法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if safety_health_deleterious_ntfc == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.safety_health_deleterious_ntfc_category + '）（' \
                               + cs_safety_health_entry_data.safety_health_deleterious_ntfc_motive + '）届'
            law_code_no1 = SafetyHealthDeleteriousNtfcCategoryMaster.objects.get(category=cs_safety_health_entry_data.safety_health_deleterious_ntfc_category, lost_flag=0).id
            law_code_no2 = SafetyHealthDeleteriousMotiveNtfcMaster.objects.get(motive=cs_safety_health_entry_data.safety_health_deleterious_ntfc_motive, lost_flag=0).id
            law_code = 'B402-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '労働安全衛生法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if safety_health_asbestos == '1':
            laws_detail_name = '石綿障害予防規則'
            law_code = 'B405-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '労働安全衛生法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '14日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if safety_health_specified_equip_ntfc == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.safety_health_specified_equip_ntfc_category + '）（' \
                               + cs_safety_health_entry_data.safety_health_specified_equip_ntfc_motive + '）届'
            law_code_no1 = SafetyHealthSpecifiedEquipNtfcCategoryMaster.objects.get(category=cs_safety_health_entry_data.safety_health_specified_equip_ntfc_category, lost_flag=0).id
            law_code_no2 = SafetyHealthSpecifiedEquipNtfcMotiveMaster.objects.get(motive=cs_safety_health_entry_data.safety_health_specified_equip_ntfc_motive, lost_flag=0).id
            law_code = 'B403-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '労働安全衛生法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if safety_health_installation_report == '1':
            laws_detail_name = '（' + cs_safety_health_entry_data.safety_health_installation_report_category + '）設置報告'
            law_code_no1 = SafetyHealthInstallationReportCategoryMaster.objects.get(category=cs_safety_health_entry_data.safety_health_installation_report_category, lost_flag=0).id
            law_code = 'B404-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '労働安全衛生法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if radiation_hazards_app == '1':
            laws_detail_name = '放射性同位元素（' + cs_safety_health_entry_data.radiation_hazards_app_motive + '）申請'
            law_code_no1 = RadiationHazardsAppMotiveMaster.objects.get(motive=cs_safety_health_entry_data.radiation_hazards_app_motive, lost_flag=0).id
            law_code = 'B601-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '放射線障害防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = '30日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if petroleum_complexes_act == '1':
            laws_detail_name = '特定防災施設等設置計画書/消防車用屋外給水施設設置届出書'
            law_code = 'B701-00'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '石災法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '安全衛生･保安G'
            cs_progress_data.limit_date = 'あらかじめ・事後'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 対象の「工事id」、「rev_no」で自由記入仕様のレコードを取得
            cs_safety_health_data_data = CsSafetyHealth.objects.filter(cs_no=cs_no, cs_rev_no=cs_rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for cs_safety_health_data_data in cs_safety_health_data_data:
                # 作業中FLに「0」をセット
                cs_safety_health_data_data.entry_on_progress_flag = 0
                # 自由記入仕様のレコードを保存
                cs_safety_health_data_data.save()

        ary = {
            'cs_no': this_cs_no,
            'cs_rev_no': cs_rev_no,
            'budget_id': budget_id,
            # 'work_id': work_id,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 環境管轄届出情報登録･更新
@login_required
@require_POST
def cs_environment_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        # デッドロック回避のため1秒待ち
        time.sleep(1)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]

        budget_id = int(request.POST["budget_id"])
        # work_id = int(request.POST["work_id"])
        env_edit_flag = int(request.POST["env_edit_flag"])

        if request.POST["cs_no"] is not "":
            cs_no = int(request.POST["cs_no"])
        else:
            cs_no = 0

        if request.POST["cs_rev_no"] is not "":
            cs_rev_no = int(request.POST["cs_rev_no"])
        else:
            cs_rev_no = 0

        # 大気汚染防止法_大気汚染物質発生施設届
        air_pollution_equip_ntfc = request.POST["air_pollution_equip_ntfc"]
        if air_pollution_equip_ntfc is "":
            air_pollution_equip_ntfc = False

        # 大気汚染防止法_大気汚染物質発生施設届_種類
        air_pollution_equip_ntfc_category = request.POST["air_pollution_equip_ntfc_category"]
        if air_pollution_equip_ntfc_category is "":
            air_pollution_equip_ntfc_category = "大気汚染物質種類"

        # 大気汚染防止法_大気汚染物質発生施設届_設置/変更
        air_pollution_equip_ntfc_motive = request.POST["air_pollution_equip_ntfc_motive"]
        if air_pollution_equip_ntfc_motive is "":
            air_pollution_equip_ntfc_motive = "設置/変更"

        # 大気汚染防止法_大気汚染物質発生施設廃止届
        air_pollution_repeal_equip_ntfc = request.POST["air_pollution_repeal_equip_ntfc"]
        if air_pollution_repeal_equip_ntfc is "":
            air_pollution_repeal_equip_ntfc = False

        # 大気汚染防止法_大気汚染物質発生施設廃止届_種類
        air_pollution_repeal_equip_ntfc_category = request.POST["air_pollution_repeal_equip_ntfc_category"]
        if air_pollution_repeal_equip_ntfc_category is "":
            air_pollution_repeal_equip_ntfc_category = "大気汚染物質種類"

        # 大気汚染防止法_揮発性有機化合物発生施設届
        air_pollution_voc_ntfc = request.POST["air_pollution_voc_ntfc"]
        if air_pollution_voc_ntfc is "":
            air_pollution_voc_ntfc = False

        # 大気汚染防止法_揮発性有機化合物発生施設届_扱い
        air_pollution_voc_ntfc_action = request.POST["air_pollution_voc_ntfc_action"]
        if air_pollution_voc_ntfc_action is "":
            air_pollution_voc_ntfc_action = "扱い"

        # 大気汚染防止法_特定粉じん排出等作業実施届出
        air_pollution_particulates_ntfc = request.POST["air_pollution_particulates_ntfc"]
        if air_pollution_particulates_ntfc is "":
            air_pollution_particulates_ntfc = False

        # 水質汚濁防止法_特定施設届
        water_pollution_ntfc = request.POST["water_pollution_ntfc"]
        if water_pollution_ntfc is "":
            water_pollution_ntfc = False

        # 水質汚濁防止法_特定施設届_扱い
        water_pollution_ntfc_action = request.POST["water_pollution_ntfc_action"]
        if water_pollution_ntfc_action is "":
            water_pollution_ntfc_action = "扱い"

        # 土壌汚染対策法_土地形質変更届
        soil_contamination_ntfc = request.POST["soil_contamination_ntfc"]
        if soil_contamination_ntfc is "":
            soil_contamination_ntfc = False

        # 廃棄物処理法_産業廃棄物処理施設申請
        waste_equip_app = request.POST["waste_equip_app"]
        if waste_equip_app is "":
            waste_equip_app = False

        # 廃棄物処理法_産業廃棄物処理施設申請_設置/変更
        waste_equip_app_motive = request.POST["waste_equip_app_motive"]
        if waste_equip_app_motive is "":
            waste_equip_app_motive = "設置/変更"

        # 廃棄物処理法_産業廃棄物処理施設廃止届
        waste_repeal_equip_ntfc = request.POST["waste_repeal_equip_ntfc"]
        if waste_repeal_equip_ntfc is "":
            waste_repeal_equip_ntfc = False

        # フロン排出抑制法_工程管理票
        management_freon_plan = request.POST["management_freon_plan"]
        if management_freon_plan is "":
            management_freon_plan = False

        # 県生活環境保全条例_指定施設届
        living_env_equip_ntfc = request.POST["living_env_equip_ntfc"]
        if living_env_equip_ntfc is "":
            living_env_equip_ntfc = False

        # 県生活環境保全条例_指定施設届_種類
        living_env_equip_ntfc_category = request.POST["living_env_equip_ntfc_category"]
        if living_env_equip_ntfc_category is "":
            living_env_equip_ntfc_category = "大気汚染物質種類"

        # 県生活環境保全条例_指定施設届_扱い
        living_env_equip_ntfc_action = request.POST["living_env_equip_ntfc_action"]
        if living_env_equip_ntfc_action is "":
            living_env_equip_ntfc_action = "扱い"

        # 県生活環境保全条例_窒素酸化物排出計画届
        living_env_nox_emission_plan_ntfc = request.POST["living_env_nox_emission_plan_ntfc"]
        if living_env_nox_emission_plan_ntfc is "":
            living_env_nox_emission_plan_ntfc = False

        # 県生活環境保全条例_土壌調査
        living_env_soil_survey = request.POST["living_env_soil_survey"]
        if living_env_soil_survey is "":
            living_env_soil_survey = False

        # 県生活環境保全条例_揚水設備届出/申請
        living_env_water_pumping_app = request.POST["living_env_water_pumping_app"]
        if living_env_water_pumping_app is "":
            living_env_water_pumping_app = False

        # 市公害防止協定_公害防止協定事前協議
        pollution_agree_consultation = request.POST["pollution_agree_consultation"]
        if pollution_agree_consultation is "":
            pollution_agree_consultation = False

        # チタン鉱石問題対応方針_報告書
        titanium_compatible_report = request.POST["titanium_compatible_report"]
        if titanium_compatible_report is "":
            titanium_compatible_report = False

        # 浄化槽法_浄化槽届出
        water_purification_tanks_ntfc = request.POST["water_purification_tanks_ntfc"]
        if water_purification_tanks_ntfc is "":
            water_purification_tanks_ntfc = False

        # 浄化槽法_浄化槽届出_改廃
        water_purification_tanks_ntfc_amendment = request.POST["water_purification_tanks_ntfc_amendment"]
        if water_purification_tanks_ntfc_amendment is "":
            water_purification_tanks_ntfc_amendment = "改廃"

        comment = request.POST["comment"]

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # cs_data_num = CsSafetyHealth.objects.all().count()
        cs_data_num = CsManage.objects.all().count()

        # 新規登録時の処理
        if cs_no == 0:
            # 届け出チェックシートのレコードがない時の処理･･･チェックシートid=1 とする
            if cs_data_num == 0:
                this_cs_no = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                # last_cs_data = CsSafetyHealth.objects.all().order_by('-cs_no')[0]
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1
            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            cs_environment_data, created = CsEnvironment.objects.get_or_create(cs_no=this_cs_no)

            # データを格納
            cs_environment_data.cs_rev_no = cs_rev_no
            cs_environment_data.entry_datetime = now
            cs_environment_data.entry_operator = operator
            cs_environment_data.entry_on_progress_flag = 1
            cs_environment_data.air_pollution_equip_ntfc = air_pollution_equip_ntfc
            cs_environment_data.air_pollution_equip_ntfc_category = air_pollution_equip_ntfc_category
            cs_environment_data.air_pollution_equip_ntfc_motive = air_pollution_equip_ntfc_motive
            cs_environment_data.air_pollution_repeal_equip_ntfc = air_pollution_repeal_equip_ntfc
            cs_environment_data.air_pollution_repeal_equip_ntfc_category = air_pollution_repeal_equip_ntfc_category
            cs_environment_data.air_pollution_voc_ntfc = air_pollution_voc_ntfc
            cs_environment_data.air_pollution_voc_ntfc_action = air_pollution_voc_ntfc_action
            cs_environment_data.air_pollution_particulates_ntfc = air_pollution_particulates_ntfc
            cs_environment_data.water_pollution_ntfc = water_pollution_ntfc
            cs_environment_data.water_pollution_ntfc_action = water_pollution_ntfc_action
            cs_environment_data.soil_contamination_ntfc = soil_contamination_ntfc
            cs_environment_data.waste_equip_app = waste_equip_app
            cs_environment_data.waste_equip_app_motive = waste_equip_app_motive
            cs_environment_data.waste_repeal_equip_ntfc = waste_repeal_equip_ntfc
            cs_environment_data.management_freon_plan = management_freon_plan
            cs_environment_data.living_env_equip_ntfc = living_env_equip_ntfc
            cs_environment_data.living_env_equip_ntfc_category = living_env_equip_ntfc_category
            cs_environment_data.living_env_equip_ntfc_action = living_env_equip_ntfc_action
            cs_environment_data.living_env_nox_emission_plan_ntfc = living_env_nox_emission_plan_ntfc
            cs_environment_data.living_env_soil_survey = living_env_soil_survey
            cs_environment_data.living_env_water_pumping_app = living_env_water_pumping_app
            cs_environment_data.pollution_agree_consultation = pollution_agree_consultation
            cs_environment_data.titanium_compatible_report = titanium_compatible_report
            cs_environment_data.water_purification_tanks_ntfc = water_purification_tanks_ntfc
            cs_environment_data.water_purification_tanks_ntfc_amendment = water_purification_tanks_ntfc_amendment
            cs_environment_data.lost_flag = 0

            # データを保存
            cs_environment_data.save()

            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)
            if created:
                cs_manage_data.budget_id = budget_id
                # cs_manage_data.work_id = work_id
                cs_manage_data.cs_rev_no = 0
                cs_manage_data.lost_flag = 0
                cs_manage_data.entry_on_progress_flag = 1
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
                cs_manage_data.save()

        # 更新時の処理
        else:
            # CSid(変数)に渡された予算idをセット
            this_cs_no = cs_no
            # 該当のCSidで作業中FLがONのレコード数をカウント
            on_progress_cs_num = CsEnvironment.objects.filter(cs_no=cs_no, entry_on_progress_flag=1).count()
            # 該当のCSidで(入力)完了FLがONのレコード数をカウント
            complete_entry_cs_num = CsEnvironment.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_cs_num > 0:
                # 該当のCSidで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                cs_environment_data = CsEnvironment.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得
                latest_rev_no = cs_environment_data.cs_rev_no
                # 該当のレコードを無効
                cs_environment_data.lost_flag = 1
                # CSのレコードを保存
                cs_environment_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_cs_num == 0:
                # CSid、登録日時、登録者の情報で新規登録
                CsEnvironment(cs_no=cs_no, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                cs_environment_data = CsEnvironment.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                cs_unique_id = cs_environment_data.id
                # 主キーで予算レコードを抽出
                cs_environment_data = CsEnvironment.objects.get(id=cs_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                cs_environment_data.cs_rev_no = latest_rev_no + 1
                cs_rev_no = latest_rev_no + 1
                cs_environment_data.entry_on_progress_flag = 1
                cs_environment_data.lost_flag = 0
                # データを格納
                cs_environment_data.cs_rev_no = cs_rev_no
                cs_environment_data.cs_no = cs_no
                cs_environment_data.update_datetime = now
                cs_environment_data.update_operator = operator
                cs_environment_data.air_pollution_equip_ntfc = air_pollution_equip_ntfc
                cs_environment_data.air_pollution_equip_ntfc_category = air_pollution_equip_ntfc_category
                cs_environment_data.air_pollution_equip_ntfc_motive = air_pollution_equip_ntfc_motive
                cs_environment_data.air_pollution_repeal_equip_ntfc = air_pollution_repeal_equip_ntfc
                cs_environment_data.air_pollution_repeal_equip_ntfc_category = air_pollution_repeal_equip_ntfc_category
                cs_environment_data.air_pollution_voc_ntfc = air_pollution_voc_ntfc
                cs_environment_data.air_pollution_voc_ntfc_action = air_pollution_voc_ntfc_action
                cs_environment_data.air_pollution_particulates_ntfc = air_pollution_particulates_ntfc
                cs_environment_data.water_pollution_ntfc = water_pollution_ntfc
                cs_environment_data.water_pollution_ntfc_action = water_pollution_ntfc_action
                cs_environment_data.soil_contamination_ntfc = soil_contamination_ntfc
                cs_environment_data.waste_equip_app = waste_equip_app
                cs_environment_data.waste_equip_app_motive = waste_equip_app_motive
                cs_environment_data.waste_repeal_equip_ntfc = waste_repeal_equip_ntfc
                cs_environment_data.management_freon_plan = management_freon_plan
                cs_environment_data.living_env_equip_ntfc = living_env_equip_ntfc
                cs_environment_data.living_env_equip_ntfc_category = living_env_equip_ntfc_category
                cs_environment_data.living_env_equip_ntfc_action = living_env_equip_ntfc_action
                cs_environment_data.living_env_nox_emission_plan_ntfc = living_env_nox_emission_plan_ntfc
                cs_environment_data.living_env_soil_survey = living_env_soil_survey
                cs_environment_data.living_env_water_pumping_app = living_env_water_pumping_app
                cs_environment_data.pollution_agree_consultation = pollution_agree_consultation
                cs_environment_data.titanium_compatible_report = titanium_compatible_report
                cs_environment_data.water_purification_tanks_ntfc = water_purification_tanks_ntfc
                cs_environment_data.water_purification_tanks_ntfc_amendment = water_purification_tanks_ntfc_amendment

                # データを保存
                cs_environment_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                cs_environment_data = CsEnvironment.objects.get(cs_no=cs_no, entry_on_progress_flag=1, lost_flag=0)
                # manage_data = CsManage.objects.get(cs_no=cs_no, entry_on_progress_flag=1)
                # 主キーを取得
                cs_unique_id = cs_environment_data.id
                # データを格納
                cs_environment_data.cs_rev_no = cs_rev_no
                cs_environment_data.cs_no = cs_no
                cs_environment_data.update_datetime = now
                cs_environment_data.update_operator = operator
                cs_environment_data.air_pollution_equip_ntfc = air_pollution_equip_ntfc
                cs_environment_data.air_pollution_equip_ntfc_category = air_pollution_equip_ntfc_category
                cs_environment_data.air_pollution_equip_ntfc_motive = air_pollution_equip_ntfc_motive
                cs_environment_data.air_pollution_repeal_equip_ntfc = air_pollution_repeal_equip_ntfc
                cs_environment_data.air_pollution_repeal_equip_ntfc_category = air_pollution_repeal_equip_ntfc_category
                cs_environment_data.air_pollution_voc_ntfc = air_pollution_voc_ntfc
                cs_environment_data.air_pollution_voc_ntfc_action = air_pollution_voc_ntfc_action
                cs_environment_data.air_pollution_particulates_ntfc = air_pollution_particulates_ntfc
                cs_environment_data.water_pollution_ntfc = water_pollution_ntfc
                cs_environment_data.water_pollution_ntfc_action = water_pollution_ntfc_action
                cs_environment_data.soil_contamination_ntfc = soil_contamination_ntfc
                cs_environment_data.waste_equip_app = waste_equip_app
                cs_environment_data.waste_equip_app_motive = waste_equip_app_motive
                cs_environment_data.waste_repeal_equip_ntfc = waste_repeal_equip_ntfc
                cs_environment_data.management_freon_plan = management_freon_plan
                cs_environment_data.living_env_equip_ntfc = living_env_equip_ntfc
                cs_environment_data.living_env_equip_ntfc_category = living_env_equip_ntfc_category
                cs_environment_data.living_env_equip_ntfc_action = living_env_equip_ntfc_action
                cs_environment_data.living_env_nox_emission_plan_ntfc = living_env_nox_emission_plan_ntfc
                cs_environment_data.living_env_soil_survey = living_env_soil_survey
                cs_environment_data.living_env_water_pumping_app = living_env_water_pumping_app
                cs_environment_data.pollution_agree_consultation = pollution_agree_consultation
                cs_environment_data.titanium_compatible_report = titanium_compatible_report
                cs_environment_data.water_purification_tanks_ntfc = water_purification_tanks_ntfc
                cs_environment_data.water_purification_tanks_ntfc_amendment = water_purification_tanks_ntfc_amendment
                cs_environment_data.lost_flag = 0

                # データを保存
                cs_environment_data.save()

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "環境管轄一時保存完了"

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = "環境管轄" + step_name + "完了"

        # if this_step != next_step:
        # 環境G関係の届出進捗テーブルを削除
        data_num = CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='環境G').all().count()
        if data_num > 0:
            CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='環境G').all().delete()
        # 届出進捗テーブルに情報記載
        if air_pollution_equip_ntfc == '1':
            laws_detail_name = '（' + cs_environment_data.air_pollution_equip_ntfc_category + '）発生施設（' + \
                               cs_environment_data.air_pollution_equip_ntfc_motive + '）届'
            law_code_no1 = AirPollutionEquipNtfcCategoryMaster.objects.get(category=cs_environment_data.air_pollution_equip_ntfc_category, lost_flag=0).id
            law_code_no2 = AirPollutionEquipNtfcMotiveMaster.objects.get(motive=cs_environment_data.air_pollution_equip_ntfc_motive, lost_flag=0).id
            law_code = 'C101-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '大気汚染防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '60日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if air_pollution_repeal_equip_ntfc == '1':
            laws_detail_name = '（' + cs_environment_data.air_pollution_repeal_equip_ntfc_category + '）発生施設廃止届'
            law_code_no1 = AirPollutionRepealEquipNtfcCategoryMaster.objects.get(category=cs_environment_data.air_pollution_repeal_equip_ntfc_category, lost_flag=0).id
            law_code = 'C101-' + str(law_code_no1) + '3'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '大気汚染防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '廃止後30日'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if air_pollution_voc_ntfc == '1':
            laws_detail_name = '揮発性有機化合物発生施設（' + cs_environment_data.air_pollution_voc_ntfc_action + '）届'
            law_code_no1 = AirPollutionVocNtfcActionMaster.objects.get(action=cs_environment_data.air_pollution_voc_ntfc_action, lost_flag=0).id
            law_code = 'C102-' + str(law_code_no1) + '0'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '大気汚染防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '60日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if air_pollution_particulates_ntfc == '1':
            laws_detail_name = '特定粉じん排出等作業実施届出'
            law_code = 'C103-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '大気汚染防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '14日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if water_pollution_ntfc == '1':
            laws_detail_name = '特定施設（' + cs_environment_data.water_pollution_ntfc_action + '）届'
            law_code_no1 = WaterPollutionNtfcActionMaster.objects.get(action=cs_environment_data.water_pollution_ntfc_action, lost_flag=0).id
            law_code = 'C201-' + str(law_code_no1) + '0'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '水質汚濁防止法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '60日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if soil_contamination_ntfc == '1':
            laws_detail_name = '土地の形質の変更届出（900㎡以上）'
            law_code = 'C701-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '土壌汚染対策法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '30日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if waste_equip_app == '1':
            laws_detail_name = '産業廃棄物処理施設（' + cs_environment_data.waste_equip_app_motive + '）申請'
            law_code_no1 = WasteEquipAppMotiveMaster.objects.get(motive=cs_environment_data.waste_equip_app_motive, lost_flag=0).id
            law_code = 'C301-' + str(law_code_no1) + '0'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '廃棄物処理法'
            law_code_no1 = WasteEquipAppMotiveMaster.objects.get(
                motive=cs_environment_data.waste_equip_app_motive, lost_flag=0).id
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if waste_repeal_equip_ntfc == '1':
            laws_detail_name = '産業廃棄物処理施設廃止届'
            law_code = 'C302-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '廃棄物処理法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if management_freon_plan == '1':
            laws_detail_name = '行程管理票の交付'
            law_code = 'C601-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = 'フロン排出抑制法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '処分時'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if living_env_equip_ntfc == '1':
            laws_detail_name = '（' + cs_environment_data.living_env_equip_ntfc_category + '）指定施設（' + \
                               cs_environment_data.living_env_equip_ntfc_action + '）届'
            law_code_no1 = LivingEnvEquipNtfcCategoryMaster.objects.get(category=cs_environment_data.living_env_equip_ntfc_category, lost_flag=0).id
            law_code_no2 = LivingEnvEquipNtfcActionMaster.objects.get(action=cs_environment_data.living_env_equip_ntfc_action, lost_flag=0).id
            law_code = 'C401-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '県生活環境保全条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '60日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if living_env_nox_emission_plan_ntfc == '1':
            laws_detail_name = '窒素酸化物排出計画届'
            law_code = 'C402-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '県生活環境保全条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '60日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if living_env_soil_survey == '1':
            laws_detail_name = '土地の形質変更時の土壌調査(300㎡以上)'
            law_code = 'C403-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '県生活環境保全条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if living_env_water_pumping_app == '1':
            laws_detail_name = '揚水設備にかかる届出/申請'
            law_code = 'C404-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '県生活環境保全条例'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = 'あらかじめ(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if pollution_agree_consultation == '1':
            laws_detail_name = '協定に基づく事前協議'
            law_code = 'C501-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '市公害防止協定'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = '大気・水質届前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if titanium_compatible_report == '1':
            laws_detail_name = '旧処分場/旧沈殿池の跡地利用を実施するときの報告'
            law_code = 'C801-00'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = 'チタン鉱石問題対応方針'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = 'あらかじめ'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if water_purification_tanks_ntfc == '1':
            laws_detail_name = '浄化槽（' + cs_environment_data.water_purification_tanks_ntfc_amendment + '）届出'
            law_code_no1 = WaterPurificationTanksNtfcAmendmentMaster.objects.get(amendment=cs_environment_data.water_purification_tanks_ntfc_amendment, lost_flag=0).id
            law_code = 'B801-' + str(law_code_no1) + '0'
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no,
                                                                                     law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '浄化槽法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '環境G'
            cs_progress_data.limit_date = 'あらかじめ・事後'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 対象の「工事id」、「rev_no」で自由記入仕様のレコードを取得
            cs_environment_data = CsEnvironment.objects.filter(cs_no=cs_no, cs_rev_no=cs_rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for cs_environment_data in cs_environment_data:
                # 作業中FLに「0」をセット
                cs_environment_data.entry_on_progress_flag = 0
                # 自由記入仕様のレコードを保存
                cs_environment_data.save()

        ary = {
            'cs_no': this_cs_no,
            'cs_rev_no': cs_rev_no,
            'budget_id': budget_id,
            # 'work_id': work_id,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工務管轄届出情報登録･更新
@login_required
@require_POST
def cs_engineering_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        # デッドロック回避のため1秒待ち
        time.sleep(1)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]

        budget_id = int(request.POST["budget_id"])
        # work_id = int(request.POST["work_id"])
        eng_edit_flag = int(request.POST["eng_edit_flag"])

        if request.POST["cs_no"] is not "":
            cs_no = int(request.POST["cs_no"])
        else:
            cs_no = 0

        if request.POST["cs_rev_no"] is not "":
            cs_rev_no = int(request.POST["cs_rev_no"])
        else:
            cs_rev_no = 0

        # 建築基準法_確認申請
        building_standards_act = request.POST["building_standards_act"]
        if building_standards_act is "":
            building_standards_act = False

        # 建築基準法_確認申請_種類
        building_standards_act_category = request.POST["building_standards_act_category"]
        if building_standards_act_category is "":
            building_standards_act_category = "設置物種類"

        # 省エネ法_特定建築物届出
        energy_rationalization_act = request.POST["energy_rationalization_act"]
        if energy_rationalization_act is "":
            energy_rationalization_act = False

        # 省エネ法_特定建築物届出_種類
        energy_rationalization_act_category = request.POST["energy_rationalization_act_category"]
        if energy_rationalization_act_category is "":
            energy_rationalization_act_category = "第Ｘ種"

        # 省エネ法_特定建築物届出_扱い
        energy_rationalization_act_action = request.POST["energy_rationalization_act_action"]
        if energy_rationalization_act_action is "":
            energy_rationalization_act_action = "扱い"

        # 建設リサイクル法
        construction_recycling = request.POST["construction_recycling"]
        if construction_recycling is "":
            construction_recycling = False

        # 建設リサイクル法_種類
        construction_recycling_category = request.POST["construction_recycling_category"]
        if construction_recycling_category is "":
            construction_recycling_category = "届出種類"

        comment = request.POST["comment"]

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        cs_data_num = CsManage.objects.all().count()

        # 新規登録時の処理
        if cs_no == 0:
            # 届け出チェックシートのレコードがない時の処理･･･チェックシートid=1 とする
            if cs_data_num == 0:
                this_cs_no = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1
            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            cs_engineering_data, created = CsEngineering.objects.get_or_create(cs_no=this_cs_no)

            # データを格納
            cs_engineering_data.cs_rev_no = cs_rev_no
            cs_engineering_data.entry_datetime = now
            cs_engineering_data.entry_operator = operator
            cs_engineering_data.entry_on_progress_flag = 1
            cs_engineering_data.building_standards_act = building_standards_act
            cs_engineering_data.building_standards_act_category = building_standards_act_category
            cs_engineering_data.energy_rationalization_act = energy_rationalization_act
            cs_engineering_data.energy_rationalization_act_category = energy_rationalization_act_category
            cs_engineering_data.energy_rationalization_act_action = energy_rationalization_act_action
            cs_engineering_data.construction_recycling = construction_recycling
            cs_engineering_data.construction_recycling_category = construction_recycling_category
            cs_engineering_data.lost_flag = 0

            # データを保存
            cs_engineering_data.save()

            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)
            if created:
                cs_manage_data.budget_id = budget_id
                # cs_manage_data.work_id = work_id
                cs_manage_data.cs_rev_no = 0
                cs_manage_data.lost_flag = 0
                cs_manage_data.entry_on_progress_flag = 1
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
                cs_manage_data.save()

        # 更新時の処理
        else:
            # CSid(変数)に渡された予算idをセット
            this_cs_no = cs_no
            # 該当のCSidで作業中FLがONのレコード数をカウント
            on_progress_cs_num = CsEngineering.objects.filter(cs_no=cs_no, entry_on_progress_flag=1).count()
            # 該当のCSidで(入力)完了FLがONのレコード数をカウント
            complete_entry_cs_num = CsEngineering.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_cs_num > 0:
                # 該当のCSidで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                cs_engineering_data = CsEngineering.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得
                latest_rev_no = cs_engineering_data.cs_rev_no
                # 該当のレコードを無効
                cs_engineering_data.lost_flag = 1
                # CSのレコードを保存
                cs_engineering_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_cs_num == 0:
                # CSid、登録日時、登録者の情報で新規登録
                CsEngineering(cs_no=cs_no, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                cs_engineering_data = CsEngineering.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                cs_unique_id = cs_engineering_data.id
                # 主キーで予算レコードを抽出
                cs_engineering_data = CsEngineering.objects.get(id=cs_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                cs_engineering_data.cs_rev_no = latest_rev_no + 1
                cs_rev_no = latest_rev_no + 1
                cs_engineering_data.entry_on_progress_flag = 1
                cs_engineering_data.lost_flag = 0
                # データを格納
                cs_engineering_data.cs_rev_no = cs_rev_no
                cs_engineering_data.cs_no = cs_no
                cs_engineering_data.update_datetime = now
                cs_engineering_data.update_operator = operator
                cs_engineering_data.building_standards_act = building_standards_act
                cs_engineering_data.building_standards_act_category = building_standards_act_category
                cs_engineering_data.energy_rationalization_act = energy_rationalization_act
                cs_engineering_data.energy_rationalization_act_category = energy_rationalization_act_category
                cs_engineering_data.energy_rationalization_act_action = energy_rationalization_act_action
                cs_engineering_data.construction_recycling = construction_recycling
                cs_engineering_data.construction_recycling_category = construction_recycling_category

                # データを保存
                cs_engineering_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                cs_engineering_data = CsEngineering.objects.get(cs_no=cs_no, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                cs_unique_id = cs_engineering_data.id
                # データを格納
                cs_engineering_data.cs_rev_no = cs_rev_no
                cs_engineering_data.cs_no = cs_no
                cs_engineering_data.update_datetime = now
                cs_engineering_data.update_operator = operator
                cs_engineering_data.building_standards_act = building_standards_act
                cs_engineering_data.building_standards_act_category = building_standards_act_category
                cs_engineering_data.energy_rationalization_act = energy_rationalization_act
                cs_engineering_data.energy_rationalization_act_category = energy_rationalization_act_category
                cs_engineering_data.energy_rationalization_act_action = energy_rationalization_act_action
                cs_engineering_data.construction_recycling = construction_recycling
                cs_engineering_data.construction_recycling_category = construction_recycling_category
                cs_engineering_data.lost_flag = 0

                # データを保存
                cs_engineering_data.save()

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "工務管轄一時保存完了"

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = "工務管轄" + step_name + "完了"

        # if this_step != next_step:
        # 工務G関係の届出進捗テーブルを削除
        data_num = CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='工務G').all().count()
        if data_num > 0:
            CsNotificationProgress.objects.filter(cs_no=cs_no, department_name='工務G').all().delete()
        # 届出進捗テーブルに情報記載
        if building_standards_act == '1':
            laws_detail_name = '（' + cs_engineering_data.building_standards_act_category + '）確認申請'
            law_code_no1 = BuildingStandardsActCategoryMaster.objects.get(category=cs_engineering_data.building_standards_act_category, lost_flag=0).id
            law_code = 'A601-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '建築基準法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '工務G'
            cs_progress_data.limit_date = '30日前(立)'
            cs_progress_data.witness_inspection = 1

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if energy_rationalization_act == '1':
            laws_detail_name = '（' + cs_engineering_data.energy_rationalization_act_category + '）特定建築物（' + \
                               cs_engineering_data.energy_rationalization_act_action + '）届出'
            law_code_no1 = EnergyRationalizationActCategoryMaster.objects.get(category=cs_engineering_data.energy_rationalization_act_category, lost_flag=0).id
            law_code_no2 = EnergyRationalizationActActionMaster.objects.get(action=cs_engineering_data.energy_rationalization_act_action, lost_flag=0).id
            law_code = 'E201-' + str(law_code_no1) + str(law_code_no2)
            cs_progress_data, created = CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '省エネ法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '工務G'
            cs_progress_data.limit_date = '21日前(立)'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        if construction_recycling == '1':
            law_code_no1 = ConstructionRecyclingCategoryMaster.objects.get(
                category=cs_engineering_data.construction_recycling_category, lost_flag=0).id
            laws_detail_name = cs_engineering_data.construction_recycling_category + '書(第10条様式第' + \
                               str(law_code_no1) + '号)'
            law_code = 'C901-' + str(law_code_no1) + '0'
            cs_progress_data, created = \
                CsNotificationProgress.objects.get_or_create(cs_no=cs_no, law_code=law_code)
            cs_progress_data.cs_no = this_cs_no
            cs_progress_data.laws_name = '建設リサイクル法'
            cs_progress_data.law_code = law_code
            cs_progress_data.laws_detail_name = laws_detail_name
            cs_progress_data.department_name = '工務G'
            cs_progress_data.limit_date = '工事着手7日前'
            cs_progress_data.witness_inspection = 0

            # 進捗状況のレコードを保存
            cs_progress_data.save()

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 対象の「工事id」、「rev_no」で自由記入仕様のレコードを取得
            cs_engineering_data = CsEngineering.objects.filter(cs_no=cs_no, cs_rev_no=cs_rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for cs_engineering_data in cs_engineering_data:
                # 作業中FLに「0」をセット
                cs_engineering_data.entry_on_progress_flag = 0
                # 自由記入仕様のレコードを保存
                cs_engineering_data.save()

        ary = {
            'cs_no': this_cs_no,
            'cs_rev_no': cs_rev_no,
            'budget_id': budget_id,
            # 'work_id': work_id,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事共通情報登録
@login_required
@require_POST
def cs_common_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、日付処理、リレーション対応処理を含む
        cs_no = int(request.POST["cs_no"])
        cs_rev_no = int(request.POST["cs_rev_no"])
        budget_id = int(request.POST["budget_id"])
        # work_id = int(request.POST["work_id"])
        this_budget_id = budget_id
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        comment = request.POST["comment"]
        action_cd = request.POST["action_cd"]
        budget_charge_id = request.POST["budget_charge_id"]
        budget_charge_comment = request.POST["budget_charge_comment"]
        remand_comment = request.POST["remand_comment"]
        confirmer_id = request.POST["confirmer_id"]
        confirmer_comment = request.POST["confirmer_comment"]
        confirmer_remand_comment = request.POST["confirmer_remand_comment"]
        authorizer_id = request.POST["authorizer_id"]
        authorizer_comment = request.POST["authorizer_comment"]
        authorizer_remand_comment = request.POST["authorizer_remand_comment"]
        wod_charge_id = request.POST["wod_charge_id"]
        wod_charge_comment = request.POST["wod_charge_comment"]
        env_g_confirmer_id_1 = request.POST["env_g_confirmer_id_1"]
        env_g_confirmer_comment_1 = request.POST["env_g_confirmer_comment_1"]
        env_g_confirmer_id_2 = request.POST["env_g_confirmer_id_2"]
        env_g_confirmer_comment_2 = request.POST["env_g_confirmer_comment_2"]
        env_g_authorizer_id = request.POST["env_g_authorizer_id"]
        env_g_authorizer_comment = request.POST["env_g_authorizer_comment"]
        hse_director_id = request.POST["hse_director_id"]
        hse_director_comment = request.POST["hse_director_comment"]
        hse_director_remand_comment = request.POST["hse_director_remand_comment"]
        ed_director_id = request.POST["ed_director_id"]
        ed_director_comment = request.POST["ed_director_comment"]
        hs_director_id = request.POST["hs_director_id"]
        hs_director_comment = request.POST["hs_director_comment"]
        wod_director_id = request.POST["wod_director_id"]
        wod_director_comment = request.POST["wod_director_comment"]
        gad_director_id = request.POST["gad_director_id"]
        gad_director_comment = request.POST["gad_director_comment"]
        cd_director_id = request.POST["cd_director_id"]
        cd_director_comment = request.POST["cd_director_comment"]
        env_department_id = request.POST["env_department_id"]
        env_department_comment = request.POST["env_department_comment"]
        hs_department_id = request.POST["hs_department_id"]
        hs_department_comment = request.POST["hs_department_comment"]
        wo_department_id = request.POST["wo_department_id"]
        wo_department_comment = request.POST["wo_department_comment"]
        ga_department_id = request.POST["ga_department_id"]
        ga_department_comment = request.POST["ga_department_comment"]
        constr_department_id = request.POST["constr_department_id"]
        constr_department_comment = request.POST["constr_department_comment"]
        entry_on_progress_flag = request.POST["entry_on_progress_flag"]
        # entry_datetime = request.POST["entry_datetime"]
        # entry_datetime = entry_datetime.replace('年', '-')
        # entry_datetime = entry_datetime.replace('月', '-')
        # entry_datetime = entry_datetime.replace('日', ' ')
        # entry_operator = request.POST["entry_operator"]
        # entry_operator = entry_operator.replace('年', '-')
        # entry_operator = entry_operator.replace('月', '-')
        # entry_operator = entry_operator.replace('日', ' ')
        update_datetime = request.POST["update_datetime"]
        update_datetime = update_datetime.replace('年', '-')
        update_datetime = update_datetime.replace('月', '-')
        update_datetime = update_datetime.replace('日', ' ')
        update_operator = request.POST["update_operator"]
        update_operator = update_operator.replace('年', '-')
        update_operator = update_operator.replace('月', '-')
        update_operator = update_operator.replace('日', ' ')

        # cs_data_num = CsGeneralAffairs.objects.all().count()
        cs_data_num = CsManage.objects.all().count()

        # 新規登録時の処理
        if cs_no == 0:
            # 届け出チェックシートのレコードがない時の処理･･･チェックシートid=1 とする
            if cs_data_num == 0:
                this_cs_no = 1
            else:
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1

            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)
            cs_no = this_cs_no
            cs_rev_no = 0
            if created:
                cs_manage_data.budget_id = budget_id
                # cs_manage_data.work_id = work_id
                cs_manage_data.cs_rev_no = cs_rev_no
                cs_manage_data.lost_flag = 0
                cs_manage_data.entry_on_progress_flag = 1
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
                cs_manage_data.save()

        # 次の工程(step)に進まない(=一時保存等)場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "共通データ一時保存完了！！"
        # 次の工程(step)に進む(=作成完了等)場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = step_name + "共通データ作成完了！！"

        # 対象の工事idで、作業中のレコード数を取得
        on_progress_cs_manage_num = CsManage.objects.filter(cs_no=cs_no, entry_on_progress_flag=1).count()
        # 対象の工事idで、完了(作業中でない)のレコード数を取得
        complete_entry_cs_manage_num = CsManage.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).count()

        # 対象の工事idで、完了(作業中でない)のレコードがある場合の処理
        if complete_entry_cs_manage_num > 0:
            # 対象の工事id、作業中でないレコードの最新(主キーが大きい)もののレコードを抽出
            cs_manage_data = CsManage.objects.filter(cs_no=cs_no, entry_on_progress_flag=0).order_by('-id')[0]
            # 最終のrev_noを取得
            latest_rev_no = cs_manage_data.cs_rev_no
            # 対象のレコードを無効化(lost_flag = 1)
            cs_manage_data.lost_flag = 1
            # 工事情報のレコードを保存
            cs_manage_data.save()

            # 対象の工事idで、完了(作業中でない)のレコードがない場合の処理
        else:
            # 最終のrev_noを「-1」に設定
            latest_rev_no = -1

            # 対象の工事idで、作業中のレコードがない場合
        if on_progress_cs_manage_num == 0:
            # 「work_id」、「登録日時」、「登録者」で工事情報に新規登録
            CsManage(cs_no=cs_no, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
            # 「登録日時」、「登録者」の値で登録した工事情報のレコード抽出
            cs_manage_data = CsManage.objects.get(entry_datetime=now, entry_operator=operator)
            # 主キーの値を取得
            cs_manage_unique_id = cs_manage_data.id
            # 「主キー」の値で工事情報からレコード抽出
            cs_manage_data = CsManage.objects.get(id=cs_manage_unique_id)
            # 各項目の値を格納
            cs_manage_data.cs_rev_no = latest_rev_no + 1
            cs_rev_no = latest_rev_no + 1
            cs_manage_data.entry_on_progress_flag = 1
            cs_manage_data.lost_flag = 0
            # 工事情報のレコード保存
            cs_manage_data.save()

        # 対象の工事idで、作業中のレコードがある場合
        else:
            # 「work_id」と「作業中FL」で工事情報のレコードを取得
            cs_manage_data = CsManage.objects.get(cs_no=cs_no, entry_on_progress_flag=1)
            # rev_noを取得
            cs_rev_no = cs_manage_data.cs_rev_no

            # 「cs_no」、「cs_rev_no」で届け出チェックシートのレコードを抽出
        manage_data = CsManage.objects.get(cs_no=cs_no, cs_rev_no=cs_rev_no, lost_flag=0)
        # 各項目の値を格納
        manage_data.budget_id = budget_id
        # manage_data.work_id = work_id
        manage_data.cs_no = cs_no
        manage_data.cs_rev_no = cs_rev_no
        # manage_data.related_cs_no = related_cs_no
        manage_data.comment = comment
        if type(budget_charge_id) is not int:
            manage_data.budget_charge_id = None
        else:
            manage_data.budget_charge_id = budget_charge_id
        manage_data.budget_charge_comment = budget_charge_comment
        manage_data.remand_comment = remand_comment
        if type(confirmer_id) is not int:
            manage_data.confirmer_id = None
        else:
            manage_data.confirmer_id = confirmer_id
        manage_data.confirmer_comment = confirmer_comment
        manage_data.confirmer_remand_comment = confirmer_remand_comment
        if type(authorizer_id) is not int:
            manage_data.authorizer_id = None
        else:
            manage_data.authorizer_id = authorizer_id
        manage_data.authorizer_comment = authorizer_comment
        manage_data.authorizer_remand_comment = authorizer_remand_comment
        if type(wod_charge_id) is not int:
            manage_data.wod_charge_id = None
        else:
            manage_data.wod_charge_id = wod_charge_id
        manage_data.wod_charge_comment = wod_charge_comment
        if type(env_g_confirmer_id_1) is not int:
            manage_data.env_g_confirmer_id_1 = None
        else:
            manage_data.env_g_confirmer_id_1 = env_g_confirmer_id_1
        manage_data.env_g_confirmer_comment_1 = env_g_confirmer_comment_1
        if type(env_g_confirmer_id_2) is not int:
            manage_data.env_g_confirmer_id_2 = None
        else:
            manage_data.env_g_confirmer_id_2 = env_g_confirmer_id_2
        manage_data.env_g_confirmer_comment_2 = env_g_confirmer_comment_2
        if type(env_g_authorizer_id) is not int:
            manage_data.env_g_authorizer_id = None
        else:
            manage_data.env_g_authorizer_id = env_g_authorizer_id
        manage_data.env_g_authorizer_comment = env_g_authorizer_comment
        if type(hse_director_id) is not int:
            manage_data.hse_director_id = None
        else:
            manage_data.hse_director_id = hse_director_id
        manage_data.hse_director_comment = hse_director_comment
        manage_data.hse_director_remand_comment = hse_director_remand_comment
        if type(ed_director_id) is not int:
            manage_data.ed_director_id = None
        else:
            manage_data.ed_director_id = ed_director_id
        manage_data.ed_director_comment = ed_director_comment
        if type(hs_director_id) is not int:
            manage_data.hs_director_id = None
        else:
            manage_data.hs_director_id = hs_director_id
        manage_data.hs_director_comment = hs_director_comment
        if type(wod_director_id) is not int:
            manage_data.wod_director_id = None
        else:
            manage_data.wod_director_id = wod_director_id
        manage_data.wod_director_comment = wod_director_comment
        if type(gad_director_id) is not int:
            manage_data.gad_director_id = None
        else:
            manage_data.gad_director_id = gad_director_id
        manage_data.gad_director_comment = gad_director_comment
        if type(cd_director_id) is not int:
            manage_data.cd_director_id = None
        else:
            manage_data.cd_director_id = cd_director_id
        manage_data.cd_director_comment = cd_director_comment
        if type(env_department_id) is not int:
            manage_data.env_department_id = None
        else:
            manage_data.env_department_id = env_department_id
        manage_data.env_department_comment = env_department_comment
        if type(hs_department_id) is not int:
            manage_data.hs_department_id = None
        else:
            manage_data.hs_department_id = hs_department_id
        manage_data.hs_department_comment = hs_department_comment
        if type(wo_department_id) is not int:
            manage_data.wo_department_id = None
        else:
            manage_data.wo_department_id = wo_department_id
        manage_data.wo_department_comment = wo_department_comment
        if type(ga_department_id) is not int:
            manage_data.ga_department_id = None
        else:
            manage_data.ga_department_id = ga_department_id
        manage_data.ga_department_comment = ga_department_comment
        if type(constr_department_id) is not int:
            manage_data.constr_department_id = None
        else:
            manage_data.constr_department_id = constr_department_id
        manage_data.constr_department_comment = constr_department_comment
        manage_data.entry_on_progress_flag = entry_on_progress_flag
        # manage_data.entry_datetime = entry_datetime
        # manage_data.entry_operator = entry_operator
        manage_data.update_datetime = now
        manage_data.update_operator = operator

        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 作業中FLに「0」を設定
            manage_data.entry_on_progress_flag = 0
        # 次の工程(step)に進まない場合
        else:
            # 作業中FLに「1」を設定
            manage_data.entry_on_progress_flag = 1

        # 工事関連法令のレコードを保存
        manage_data.save()

        if action_cd != "entry_permit":
            # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
            if user_attribute_id > 0:
                user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
                next_person = user_attribute_data.username
                next_division = user_attribute_data.division
                next_department = user_attribute_data.department
            else:
                next_department = this_department
                next_person = operator

            # 「target="cs"」と「cs_no」で進捗状況の対象レコードを抽出･･･あれば読み込み、なければ新規登録
            progress_exist_check = Progress.objects.filter(target="cs", target_id=cs_no,
                                                           present_step=next_step).all().count()

            if progress_exist_check > 0:
                progress_data, created = Progress.objects.get_or_create(target="cs", target_id=cs_no,
                                                                        present_step=next_step)
            else:
                progress_data, created = Progress.objects.get_or_create(target="cs", target_id=cs_no,
                                                                        present_step=this_step)
            # 各項目の値を格納
            progress_data.present_step = next_step
            progress_data.present_operator = next_person
            progress_data.present_department = next_department
            department_data = DepartmentMaster.objects.get(department_cd=next_department)
            progress_data.present_division = department_data.division_cd

            # 本工程と次工程が違うとき、進捗データ更新
            if this_step != next_step:
                # 履歴情報を格納
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

            # ログを新規登録
            Log(target='cs', target_id=cs_no, action=action, operator=operator, operation_datetime=now, step=this_step,
                comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id
                ).save()

        ary = {
            'cs_no': cs_no,
            'cs_rev_no': cs_rev_no,
            'budget_id': this_budget_id,
            'msg': msg,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出一覧の絞込のパーツ表示
@require_POST
def cs_filter(request):
    from fms.views.common_def_views import get_next_target
    try:
        # 年度選択ソース抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1).all()
        # 部門選択ソース抽出
        division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 部署選択ソース抽出
        departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        step_st = math.floor(level5_step_id / 1000000) * 1000000
        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        data = {
            'step_list': step_list,
            'business_year_list': business_year_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'user_department_cd': target_department,
            'user_division_cd': target_division,
            'user': target_person,
            'level5_step_id': level5_step_id + 1,
        }

        return render(request, 'fms/parts/check_sheet/cs_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出進捗画面表示処理
@login_required
@require_POST
def cs_laws_progress_top_page(request):
    try:
        # ステップ名称の取得
        this_step = 134009000
        step_name = StepMaster.objects.get(step_id=this_step, lost_flag=0)

        # ユーザ情報の取得
        this_user = request.user.username
        user_data = UserAttribute.objects.filter(username=this_user, lost_flag=0).all().order_by('display_order')[0]
        user_division_cd = user_data.division
        user_department_cd = user_data.department
        user_authority = user_data.authority
        confirm_user = user_data.confirm_username
        permit_user = user_data.permit_username

        data = {
            'this_step': this_step,
            'step_name': step_name,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
        }

        return render(request, 'fms/parts/check_sheet/cs_laws_progress_top_page.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 対象の法令への日付記入処理
@login_required
@require_POST
def cs_laws_progress_date_entry(request):
    from .common_views import date_to_hyphen
    try:
        DIFF_JST_FROM_UTC = 9

        # JSからのPOST引数を取得
        # 届出No
        laws_no = request.POST['laws_no']
        # 提出日
        submission_date = request.POST['submission_date']
        # 許可日
        permit_date = request.POST['permit_date']
        # 届出日
        notification_date = request.POST['notification_date']
        # 許可番号
        permit_no = request.POST['permit_no']

        if laws_no != "":
            # データ保存先のレコードを抽出
            cs_notification_progress_data = CsNotificationProgress.objects.get(id=laws_no)

            # 取得したデータが空欄でなければテーブルに保存
            if submission_date != "":
                submission_date = date_to_hyphen(submission_date)
                cs_notification_progress_data.submission_date = submission_date

            if permit_date != "":
                permit_date = date_to_hyphen(permit_date)
                cs_notification_progress_data.permit_date = permit_date

            if notification_date != "":
                notification_date = date_to_hyphen(notification_date)
                cs_notification_progress_data.notification_date = notification_date

            if permit_no != "":
                cs_notification_progress_data.permit_no = permit_no

            cs_notification_progress_data.save()
            msg = "届出進捗データ更新完了！！"
        else:
            msg = "届出が選択されていません！！"

        data = {
            'msg': msg
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出一覧の絞込のパーツ表示
@require_POST
def cs_laws_progress_filter(request):
    try:
        # 進捗工程選択ソース抽出
        user_department_cd = request.POST["user_department_cd"]
        department_data = DepartmentMaster.objects.get(department_cd=user_department_cd)
        user_division_cd = department_data.division_cd

        # 所管部署ソース抽出cursol
        with connections['fmsdb'].cursor() as cursor:
            sql = """ SELECT id, """
            sql += """ username, """
            sql += """ department, """
            sql += """ department_name, """
            sql += """ division, """
            sql += """ authority, """
            sql += """ confirm_username, """
            sql += """ permit_username, """
            sql += """ department_charge_flag, """
            sql += """ fms_userattribute.lost_flag, """
            sql += """ fms_userattribute.display_order """
            sql += """ FROM fms.dbo.fms_userattribute """
            sql += """ LEFT JOIN fms_departmentmaster on fms_userattribute.department = fms_departmentmaster.department_cd """
            sql += """       AND fms_departmentmaster.lost_flag=0 """
            sql += """ WHERE fms_userattribute.lost_flag=0 """
            sql += """   AND fms_userattribute.department_charge_flag='cs' """

            res = cursor.execute(sql)

            jurisdiction_department_list = res.fetchall()
            jurisdiction_department_list_num = len(jurisdiction_department_list)

        # 年度選択ソース抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1).all()
        # 部門選択ソース抽出
        division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 部署選択ソース抽出
        departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')

        data = {
            'jurisdiction_department_list': jurisdiction_department_list,
            'jurisdiction_department_list_num': jurisdiction_department_list_num,
            'business_year_list': business_year_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'user_department_cd': user_department_cd,
            'user_division_cd': user_division_cd,
        }

        return render(request, 'fms/parts/check_sheet/cs_laws_progress_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出進捗一覧フィルタリング処理
@login_required
@require_POST
def get_cs_laws_progress_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        sel_cs_jurisdiction_department = request.POST['sel_cs_jurisdiction_department']
        sel_business_year = request.POST['sel_business_year']
        sel_budget_id = request.POST['sel_budget_id']
        sel_budget_no = request.POST['sel_budget_no']
        sel_budget_name = request.POST['sel_budget_name']
        sel_division = request.POST['sel_division']
        sel_department = request.POST['sel_department']
        sel_cs_related_laws_progress = request.POST['sel_cs_related_laws_progress']
        sel_on_work = request.POST['sel_on_work']

        list_filter = {
            'cs_no': "",
            'cs_jurisdiction_department': sel_cs_jurisdiction_department,
            'cs_business_year': sel_business_year,
            'cs_budget_id': sel_budget_id,
            'cs_budget_no': sel_budget_no,
            'cs_budget_name': sel_budget_name,
            'cs_division': sel_division,
            'cs_department': sel_department,
            'cs_related_laws_progress': sel_cs_related_laws_progress,
            'cs_on_work': sel_on_work,
        }

        # 選択済み法令リスト取得
        cs_laws_list = get_cs_related_laws_list_forcus(list_filter)
        cs_laws_list_num = len(cs_laws_list)

        data = {
            'cs_laws_list': cs_laws_list,
            'cs_laws_list_num': cs_laws_list_num,
        }

        return render(request, 'fms/parts/check_sheet/cs_laws_progress_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 追加届出用の予算ID一覧絞込のパーツ表示
@require_POST
def cs_budget_id_filter(request):
    try:
        # 進捗工程選択ソース抽出
        business_year = request.POST["business_year"]
        budget_id = request.POST["budget_id"]
        budget_no = request.POST["budget_no"]
        division = request.POST["division"]
        department = request.POST["department"]
        budget_class = request.POST["budget_class"]

        filter_data = {
            'business_year': business_year,
            'budget_id': budget_id,
            'budget_no': budget_no,
            'division': division,
            'department': department,
            'budget_class': budget_class,
        }

        data = get_cs_budget_id_list(filter_data)

        return render(request, 'fms/parts/check_sheet/cs_budget_id_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def get_cs_budget_id_list(filter_data):

    # 進捗工程選択ソース抽出
    business_year = filter_data["business_year"]
    budget_id = filter_data["budget_id"]
    budget_no = filter_data["budget_no"]
    division = filter_data["division"]
    department = filter_data["department"]
    budget_class = filter_data["budget_class"]

    with connections['fmsdb'].cursor() as cursor:
        sql = """   SELECT	fms_budget.*
                            ,fms_departmentmaster.division_cd
                            ,fms_departmentmaster.department_cd 
                            ,fms_progress.present_step
                    FROM	fms_budget 
                    LEFT JOIN fms_departmentmaster  
                            on fms_budget.budget_main_department_id=fms_departmentmaster.department_cd 
                            AND fms_departmentmaster.lost_flag=0 
                    LEFT JOIN fms_progress on fms_budget.budget_id = fms_progress.target_id and fms_progress.target='budget'
                    WHERE	fms_budget.lost_flag=0
                        and fms_progress.present_step is not null
                        and budget_department_charge_person_id is not null """
        if business_year != "":
            sql += """ AND	fms_budget.business_year_id= """ + str(business_year)
        if budget_id != "":
            sql += """ AND	fms_budget.budget_id= """ + str(budget_id)
        if budget_no != "":
            sql += """ AND	fms_budget.budget_no='""" + budget_no + """' """
        if division != "":
            sql += """ AND	fms_departmentmaster.division_cd='""" + division + """' """
        if department != "":
            sql += """ AND	fms_budget.budget_main_department_id='""" + department + """' """
        if budget_class != "":
            sql += """ AND	fms_budget.budget_class_id= """ + str(budget_class)

        res = cursor.execute(sql)
        budget_id_list = res.fetchall()
        budget_id_num = len(budget_id_list)

    data = {
        'budget_id_list': budget_id_list,
        'budget_id_num': budget_id_num,
    }

    return data


# 絞込の門選択時の部署のリスト更新
@require_POST
@login_required
def cs_department_list_filter(request):
    try:
        # JSからのPOST引数を取得
        filter_division = request.POST['division']

        filter_departments_list = DepartmentMaster.objects.filter(lost_flag=0, division_cd=filter_division).all().order_by('display_order')

        data = {
            'filter_departments_list': filter_departments_list,
        }

        return render(request, 'fms/parts/check_sheet/cs_sel_department_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# form用views
@login_required
def cs_edit(request):
    return


# 届出チェック進捗レコード作成
def cs_progress_record_add_budget(budget_id, operator, this_step):
    DIFF_JST_FROM_UTC = 9
    now_naive = datetime.datetime.now()
    now = make_aware(now_naive)

    target_budget_data_list_num = Budget.objects.filter(budget_id=budget_id, lost_flag=0, cancel_flag=0).all().count()

    if target_budget_data_list_num > 0:
        target_budget_data_list = Budget.objects.filter(budget_id=budget_id, lost_flag=0, cancel_flag=0).all()

        for target_budget_data_list in target_budget_data_list:
            target_budget_id = target_budget_data_list.budget_id
            department = target_budget_data_list.budget_main_department.department_cd
            next_operator = target_budget_data_list.budget_department_charge_person.username

            cs_data_list = CsManage.objects.filter(budget_id=budget_id, lost_flag=0).all()

            if cs_data_list.count() != 0:
                # すでにレコードが生成されている場合はスキップ
                continue

            cs_data_num = CsManage.objects.all().count()

            # 届け出チェックシートのレコードがない時の処理・・・チェックシートid=1 とする
            if cs_data_num == 0:
               this_cs_no = 1
            # 届け出チェックシートがある時の処理・・・最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
                # 今回のCSidを設定(=最終のCSid+1)
                this_cs_no = last_cs_data.cs_no + 1


            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成・・・ないはずなので、新規作成
            cs_manage_data_num = CsManage.objects.filter(cs_no=this_cs_no).count()
            cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)

            cs_manage_data.budget_id = target_budget_id
            # cs_manage_data.work_id = work_id
            cs_manage_data.cs_rev_no = 0
            cs_manage_data.lost_flag = 0
            cs_manage_data.entry_on_progress_flag = 1
            if cs_manage_data_num == 0:
                cs_manage_data.entry_datetime = now
                cs_manage_data.entry_operator = operator
            else:
                cs_manage_data.update_datetime = now
                cs_manage_data.update_operator = operator

            cs_manage_data.save()

            # 届出チェック状況を対象(notification_check)と予算idで抽出・・・あれば呼び出し、なければ新規登録
            progress_data, created = Progress.objects.get_or_create(target="cs", target_id=this_cs_no)
            # 各項目を設定
            progress_data.present_step = 134001001
            progress_data.present_operator = next_operator
            progress_data.present_department = department
            department_data = DepartmentMaster.objects.get(department_cd=department)
            progress_data.present_division = department_data.division_cd
            progress_data.last_operation_step = this_step
            progress_data.last_operator = operator
            progress_data.last_operation_datetime = now

            progress_data.save()

            # 進捗通知機能
            if this_step != 134001001:
                step_notice(progress_data)


# 届出チェック進捗レコード作成（追加予算側）
def cs_progress_record_append(budget_data, operator, last_operation_step):
    DIFF_JST_FROM_UTC = 9
    now_naive = datetime.datetime.now()
    now = make_aware(now_naive)

    target_budget_id = budget_data.budget_id
    department = budget_data.budget_main_department.department_cd
    next_operator = budget_data.budget_department_charge_person.username

    # 届出CS作成済であれば作成しない
    if CsManage.objects.filter(budget_id=target_budget_id, lost_flag=0).all().count() > 0:
        return

    # 届け出チェックシートのレコード新規作成
    cs_data_num = CsManage.objects.all().count()
    if cs_data_num == 0:
        this_cs_no = 1
    else:
        last_cs_data = CsManage.objects.all().order_by('-cs_no')[0]
        this_cs_no = last_cs_data.cs_no + 1

    # 設定したcs_noでレコードを抽出し、あれば呼出、なければ新規作成
    cs_manage_data_num = CsManage.objects.filter(cs_no=this_cs_no).count()
    cs_manage_data, created = CsManage.objects.get_or_create(cs_no=this_cs_no)

    cs_manage_data.budget_id = target_budget_id
    cs_manage_data.cs_rev_no = 0
    cs_manage_data.lost_flag = 0
    cs_manage_data.entry_on_progress_flag = 1
    if cs_manage_data_num == 0:
        cs_manage_data.entry_datetime = now
        cs_manage_data.entry_operator = operator
    else:
        cs_manage_data.update_datetime = now
        cs_manage_data.update_operator = operator

    cs_manage_data.save()

    # 届出チェック状況を対象(cs)とcs_noで抽出・・・あれば呼び出し、なければ新規登録
    progress_data, created = Progress.objects.get_or_create(target="cs", target_id=this_cs_no)
    # 各項目を設定
    progress_data.present_step = 134001001
    progress_data.present_operator = next_operator
    progress_data.present_department = department
    department_data = DepartmentMaster.objects.get(department_cd=department)
    progress_data.present_division = department_data.division_cd
    progress_data.last_operation_step = last_operation_step
    progress_data.last_operator = operator
    progress_data.last_operation_datetime = now

    progress_data.save()

    # 進捗通知機能
    if last_operation_step != 134001001:
        step_notice(progress_data)


# 工事情報を表示する基礎画面を表示
@login_required
@require_POST
def cs_detail_template(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target = request.POST['target']
        level5_step_id = int(request.POST['level5_step_id'])

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        # 共通
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        select_tab = int(request.POST['select_tab'])

        # 以下で取得する変数を事前定義、数値は0、文字は空欄
        last_operation_step = 0
        last_operator = ""
        last_operator_department = ""
        last_operator_division = ""

        target_id = int(request.POST['cs_no'])
        target_unique_cs_id = int(request.POST['cs_unique_id'])
        budget_id_edit_flg = int(request.POST['budget_id_edit_flg'])

        # 新規登録(target_id=0)を判定
        if target_id == 0:
            # 新規登録時処理
            # 新規登録の場合、Lv5の工程IDの「+1」が最初の工程、その工程を指定
            target_step_id = level5_step_id + 1
        else:
            # 更新時処理
            # 対象データの現在の工程IDを取得
            # progress_data = Progress.objects.get(target='cs', target_id=target_id, present_department=user_department_cd)
            # target_step_id = progress_data.present_step
            target_step_id = int(request.POST['this_step'])
            # cs_data = CsGeneralAffairs.objects.get(id=target_unique_cs_id)
            cs_manage_data = CsManage.objects.get(id=target_unique_cs_id, lost_flag=0)
            target_id = cs_manage_data.cs_no

        # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
        this_step = target_step_id

        # 更新処理かを判定(対象のIDが「0」でないとき=更新処理）　※IDはチェックシートIDではなく、レコードのID(主キー)
        if target_unique_cs_id != 0:
            # 更新処理
            # 対象のチェックシートレコード取得
            cs_manage_data = CsManage.objects.get(id=target_unique_cs_id, lost_flag=0)
            # 予算IDを取得
            budget_id = cs_manage_data.budget_id
            # 工事IDを取得
            # work_id = cs_manage_data.work_id
            # チェックシートデータのRevNO取得
            cs_rev_no = cs_manage_data.cs_rev_no
            # チェックシートテーブルの部署データ取得
            budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
            budget_unique_id = budget_data.id
            cs_department = budget_data.budget_main_department
            if cs_department == "":
                cs_department = user_department_cd
            # 予算名を取得
            budget_name = budget_data.budget_name
            # 部署マスターの対象レコード取得　※リレーションを設定しているときは、
            # マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
            department_data = DepartmentMaster.objects.get(department_name=cs_department, lost_flag=0)
            # チェックシートテーブルの部署のコードを取得
            this_department = department_data.department_cd

            # 共通管理用データを取得
            if cs_manage_data.related_cs_no is not None:
                related_cs_no = cs_manage_data.related_cs_no
            else:
                related_cs_no = None

            if cs_manage_data.lost_flag is not None:
                lost_flag = cs_manage_data.lost_flag
            else:
                lost_flag = 0

            if cs_manage_data.budget_charge_id is not None:
                budget_charge_id = cs_manage_data.budget_charge_id
            else:
                budget_charge_id = None

            if cs_manage_data.budget_charge_comment is not None:
                budget_charge_comment = cs_manage_data.budget_charge_comment
            else:
                budget_charge_comment = ""

            if cs_manage_data.remand_comment is not None:
                remand_comment = cs_manage_data.remand_comment
            else:
                remand_comment = ""

            if cs_manage_data.confirmer_id is not None:
                confirmer_id = cs_manage_data.confirmer_id
            else:
                confirmer_id = None

            if cs_manage_data.confirmer_comment is not None:
                confirmer_comment = cs_manage_data.confirmer_comment
            else:
                confirmer_comment = ""

            if cs_manage_data.confirmer_remand_comment is not None:
                confirmer_remand_comment = cs_manage_data.confirmer_remand_comment
            else:
                confirmer_remand_comment = ""

            if cs_manage_data.authorizer_id is not None:
                authorizer_id = cs_manage_data.authorizer_id
            else:
                authorizer_id = None

            if cs_manage_data.authorizer_comment is not None:
                authorizer_comment = cs_manage_data.authorizer_comment
            else:
                authorizer_comment = ""

            if cs_manage_data.authorizer_remand_comment is not None:
                authorizer_remand_comment = cs_manage_data.authorizer_remand_comment
            else:
                authorizer_remand_comment = ""

            if cs_manage_data.wod_charge_id is not None:
                wod_charge_id = cs_manage_data.wod_charge_id
            else:
                wod_charge_id = None

            if cs_manage_data.wod_charge_comment is not None:
                wod_charge_comment = cs_manage_data.wod_charge_comment
            else:
                wod_charge_comment = ""

            if cs_manage_data.env_g_confirmer_id_1 is not None:
                env_g_confirmer_id_1 = cs_manage_data.env_g_confirmer_id_1
            else:
                env_g_confirmer_id_1 = None

            if cs_manage_data.env_g_confirmer_comment_1 is not None:
                env_g_confirmer_comment_1 = cs_manage_data.env_g_confirmer_comment_1
            else:
                env_g_confirmer_comment_1 = ""

            if cs_manage_data.env_g_confirmer_id_2 is not None:
                env_g_confirmer_id_2 = cs_manage_data.env_g_confirmer_id_2
            else:
                env_g_confirmer_id_2 = None

            if cs_manage_data.env_g_confirmer_comment_2 is not None:
                env_g_confirmer_comment_2 = cs_manage_data.env_g_confirmer_comment_2
            else:
                env_g_confirmer_comment_2 = ""

            if cs_manage_data.env_g_authorizer_id is not None:
                env_g_authorizer_id = cs_manage_data.env_g_authorizer_id
            else:
                env_g_authorizer_id = None

            if cs_manage_data.env_g_authorizer_comment is not None:
                env_g_authorizer_comment = cs_manage_data.env_g_authorizer_comment
            else:
                env_g_authorizer_comment = ""

            if cs_manage_data.hse_director_id is not None:
                hse_director_id = cs_manage_data.hse_director_id
            else:
                hse_director_id = None

            if cs_manage_data.hse_director_comment is not None:
                hse_director_comment = cs_manage_data.hse_director_comment
            else:
                hse_director_comment = ""

            if cs_manage_data.hse_director_remand_comment is not None:
                hse_director_remand_comment = cs_manage_data.hse_director_remand_comment
            else:
                hse_director_remand_comment = ""

            if cs_manage_data.ed_director_id is not None:
                ed_director_id = cs_manage_data.ed_director_id
            else:
                ed_director_id = None

            if cs_manage_data.ed_director_comment is not None:
                ed_director_comment = cs_manage_data.ed_director_comment
            else:
                ed_director_comment = ""

            if cs_manage_data.hs_director_id is not None:
                hs_director_id = cs_manage_data.hs_director_id
            else:
                hs_director_id = None

            if cs_manage_data.hs_director_comment is not None:
                hs_director_comment = cs_manage_data.hs_director_comment
            else:
                hs_director_comment = ""

            if cs_manage_data.wod_director_id is not None:
                wod_director_id = cs_manage_data.wod_director_id
            else:
                wod_director_id = None

            if cs_manage_data.wod_director_comment is not None:
                wod_director_comment = cs_manage_data.wod_director_comment
            else:
                wod_director_comment = ""

            if cs_manage_data.gad_director_id is not None:
                gad_director_id = cs_manage_data.gad_director_id
            else:
                gad_director_id = None

            if cs_manage_data.gad_director_comment is not None:
                gad_director_comment = cs_manage_data.gad_director_comment
            else:
                gad_director_comment = ""

            if cs_manage_data.cd_director_id is not None:
                cd_director_id = cs_manage_data.cd_director_id
            else:
                cd_director_id = None

            if cs_manage_data.cd_director_comment is not None:
                cd_director_comment = cs_manage_data.cd_director_comment
            else:
                cd_director_comment = ""

            if cs_manage_data.env_department_id is not None:
                env_department_id = cs_manage_data.env_department_id
            else:
                env_department_id = None

            if cs_manage_data.env_department_comment is not None:
                env_department_comment = cs_manage_data.env_department_comment
            else:
                env_department_comment = ""

            if cs_manage_data.hs_department_id is not None:
                hs_department_id = cs_manage_data.hs_department_id
            else:
                hs_department_id = None

            if cs_manage_data.hs_department_comment is not None:
                hs_department_comment = cs_manage_data.hs_department_comment
            else:
                hs_department_comment = ""

            if cs_manage_data.wo_department_id is not None:
                wo_department_id = cs_manage_data.wo_department_id
            else:
                wo_department_id = None

            if cs_manage_data.wo_department_comment is not None:
                wo_department_comment = cs_manage_data.wo_department_comment
            else:
                wo_department_comment = ""

            if cs_manage_data.ga_department_id is not None:
                ga_department_id = cs_manage_data.ga_department_id
            else:
                ga_department_id = None

            if cs_manage_data.ga_department_comment is not None:
                ga_department_comment = cs_manage_data.ga_department_comment
            else:
                ga_department_comment =""

            if cs_manage_data.constr_department_id is not None:
                constr_department_id = cs_manage_data.constr_department_id
            else:
                constr_department_id = None

            if cs_manage_data.constr_department_comment is not None:
                constr_department_comment = cs_manage_data.constr_department_comment
            else:
                constr_department_comment = ""

            if cs_manage_data.entry_on_progress_flag is not None:
                entry_on_progress_flag = cs_manage_data.entry_on_progress_flag
            else:
                entry_on_progress_flag = 0

            if cs_manage_data.entry_datetime is not None:
                entry_datetime = cs_manage_data.entry_datetime
            else:
                entry_datetime = ""

            if cs_manage_data.entry_operator is not None:
                entry_operator = cs_manage_data.entry_operator
            else:
                entry_operator = ""

            if cs_manage_data.update_datetime is not None:
                update_datetime = cs_manage_data.update_datetime
            else:
                update_datetime = ""

            if cs_manage_data.update_operator is not None:
                update_operator = cs_manage_data.update_operator
            else:
                update_operator = ""

            # 対象のチェックシートに関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
            log_data_num = Log.objects.filter(target="cs", target_id=target_id, step__lte=this_step).exclude(
                action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
            # logデータがあった(過去に対象のチェックシートに操作がされていた)場合
            if log_data_num > 0:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data = Log.objects.filter(target="cs", target_id=target_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                    '-operation_datetime').all()[0:1]
            else:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                log_data = Log.objects.filter(target="cs", target_id=target_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

            # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
            for log_data in log_data:
                last_operation_step = log_data.step
                last_operator = log_data.operator
                last_operator_department = log_data.operator_department
                last_operator_division = log_data.operator_division

        # 対象のIDが「0」のとき(=新規登録処理)の処理
        else:
            budget_id = int(request.POST['budget_id'])
            budget_unique_id = 0
            # work_id = int(request.POST['work_id'])
            # 新規登録処理
            cs_department = user_department_cd
            # チェックシートデータのRevNOに「0」を代入
            cs_rev_no = 0
            # ユーザー部署名を取得
            this_department = user_department_cd
            department_data = DepartmentMaster.objects.get(department_cd=this_department)
            # 部署にユーザー部署名を代入
            cs_department = department_data.department_name
            # 予算名の初期値を入力
            budget_name = ""
            # 前作業の情報を初期値に設定(数値項目=0、文字項目は空欄)
            last_operation_step = 0
            last_operator = ""
            last_operator_department = ""
            last_operator_division = ""
            # 共通管理用データを格納
            related_cs_no = None
            lost_flag = 0
            budget_charge_id = None
            budget_charge_comment = ""
            remand_comment = ""
            confirmer_id = None
            confirmer_comment = ""
            confirmer_remand_comment = ""
            authorizer_id = None
            authorizer_comment = ""
            authorizer_remand_comment = ""
            wod_charge_id = None
            wod_charge_comment = ""
            env_g_confirmer_id_1 = None
            env_g_confirmer_comment_1 = ""
            env_g_confirmer_id_2 = None
            env_g_confirmer_comment_2 = ""
            env_g_authorizer_id = None
            env_g_authorizer_comment = ""
            hse_director_id = None
            hse_director_comment = ""
            hse_director_remand_comment = ""
            ed_director_id = None
            ed_director_comment = ""
            hs_director_id = None
            hs_director_comment = ""
            wod_director_id = None
            wod_director_comment = ""
            gad_director_id = None
            gad_director_comment = ""
            cd_director_id = None
            cd_director_comment = ""
            env_department_id = None
            env_department_comment = ""
            hs_department_id = None
            hs_department_comment = ""
            wo_department_id = None
            wo_department_comment = ""
            ga_department_id = None
            ga_department_comment = ""
            constr_department_id = None
            constr_department_comment = ""
            entry_on_progress_flag = 1
            entry_datetime = ""
            entry_operator = ""
            update_datetime = ""
            update_operator = ""

            # フラグOFF
            first_open_flag = 0

        # 部門情報を取得 ・・・通常処理
        department_data = DepartmentMaster.objects.get(department_cd=this_department)
        this_division = department_data.division_cd

        # 進捗工程名取得
        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        budget_step_name = step_data.step_name
        # 次stepの対処部署分類を取得（依頼部署か特定部署か）
        next_step = StepRelation.objects.filter(step_id=this_step, lost_flag=0).all().order_by('display_order')[0].next_step
        next_step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)
        charge_department_class = convert_charge_department(next_step_data.charge_department_class)

        # 対処部署分類が依頼部署の場合、次作業部門、次作業部署に自部門、自部署を代入
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        # 「届出CS 承認/確認」の確認の場合、次作業部門、次作業部署に自部門、自部署を代入
        elif target_step_id == 134001011 or target_step_id == 135001011:
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        # 対処部署分類が特定部署の場合、次作業部署に特定部署を代入
        else:
            next_division = DepartmentMaster.objects.get(department_cd=charge_department_class).division_cd
            next_department = charge_department_class

        # 対象のstepで表示するページ情報一覧を取得
        page_lists = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0).order_by('page')
        # 対象のstepで表示するページ数を取得
        page_lists_num = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0).count()
        # 対象のstepでデフォルトで表示するページを取得 # TODO:デフォルトページ番号確認
        default_page = page_lists.get(default_page=1)
        default_tab = default_page.page

        # タブ数にページ数を設定
        tab_num = page_lists_num

        # step名を取得
        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        step_name = step_data.step_name

        # 使用するtemplateを取得
        template_class = step_data.template_class

        # 予算IDリストを取得
        # budget_id_list = Budget.objects.filter(lost_flag='0')
        filter_data = {
            'business_year': "",
            'budget_id': "",
            'budget_no': "",
            'division': "",
            'department': "",
            'budget_class': "",
        }

        data = get_cs_budget_id_list(filter_data)
        budget_id_list = data['budget_id_list']
        # 年度選択ソース抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1).all()
        # 部門選択ソース抽出
        division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 部署選択ソース抽出
        departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 工事区分選択リソース抽出
        budget_class_list = BudgetClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')

        # 該当stepでの対象を指定
        if template_class == "cs_base":
            target = "cs"

        # コメントログの確認
        cs_approval_stepmaster_data = StepMaster.objects.get(step_name='届出CS 承認/確認', target='cs')
        if this_step <= cs_approval_stepmaster_data.step_id:
            # 届出CS 承認/確認での差戻ログデータ数を取得
            return_log_count = Log.objects.filter(target="cs", target_id=target_id, action="return",
                                                  step=cs_approval_stepmaster_data.step_id).count()
            # 届出CS 承認/確認でのコメントログデータ数を取得・・・   取得条件：届出CS 承認/確認での差戻ログ
            comment_log_count = Log.objects.filter(target="cs", target_id=target_id,
                                                   step=cs_approval_stepmaster_data.step_id).exclude(comment="").count()

        else:
            # 届出CS 承認/確認での差戻ログデータ数を取得
            return_log_count = Log.objects.filter(target="cs", target_id=target_id, action="return",
                                                  step__gte=cs_approval_stepmaster_data.step_id).count()
            # 届出CS 承認/確認でのコメントログデータ数を取得・・・   取得条件：届出CS 承認/確認での差戻ログ
            comment_log_count = Log.objects.filter(target="cs", target_id=target_id,
                                                   step__gte=cs_approval_stepmaster_data.step_id).exclude(comment="").count()

        # 禁止文字リスト取得
        ng_character_list = get_ng_character_list()

        # 届出CS 総務G確認ステップ以降、nextボタンを表示
        next_button_display_flag = 0
        if 134002001 <= target_step_id < 135000000 or 135002001 <= target_step_id < 136000000:
            next_button_display_flag = 1

        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_unique_cs_id': target_unique_cs_id,
            'target_id': target_id,
            'budget_id': budget_id,
            'budget_unique_id': budget_unique_id,
            'budget_id_list': budget_id_list,
            'business_year_list': business_year_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'budget_class_list': budget_class_list,
            'budget_name': budget_name,
            'target_step_id': this_step,
            't_username': t_username,
            't_user_is_superuser': t_user_is_superuser,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'step_name': step_name,
            'level5_step_id': level5_step_id,
            'next_division': next_division,
            'next_department': next_department,
            'this_step': this_step,
            'this_department': this_department,
            'this_division': this_division,
            'last_operation_step': last_operation_step,
            'last_operator': last_operator,
            'last_operator_department': last_operator_department,
            'last_operator_division': last_operator_division,
            # 'work_id': work_id,
            'budget_id_edit_flg': budget_id_edit_flg,
            'tab_num': tab_num,
            'cs_rev_no': cs_rev_no,
            'target': target,
            'default_tab': default_tab,
            'page_lists': page_lists,
            'select_tab': select_tab,
            'related_cs_no': related_cs_no,
            'lost_flag': lost_flag,
            'budget_charge_id': budget_charge_id,
            'budget_charge_comment': budget_charge_comment,
            'remand_comment': remand_comment,
            'confirmer_id': confirmer_id,
            'confirmer_comment': confirmer_comment,
            'confirmer_remand_comment': confirmer_remand_comment,
            'authorizer_id': authorizer_id,
            'authorizer_comment': authorizer_comment,
            'authorizer_remand_comment': authorizer_remand_comment,
            'wod_charge_id': wod_charge_id,
            'wod_charge_comment': wod_charge_comment,
            'env_g_confirmer_id_1': env_g_confirmer_id_1,
            'env_g_confirmer_comment_1': env_g_confirmer_comment_1,
            'env_g_confirmer_id_2': env_g_confirmer_id_2,
            'env_g_confirmer_comment_2': env_g_confirmer_comment_2,
            'env_g_authorizer_id': env_g_authorizer_id,
            'env_g_authorizer_comment': env_g_authorizer_comment,
            'hse_director_id': hse_director_id,
            'hse_director_comment': hse_director_comment,
            'hse_director_remand_comment': hse_director_remand_comment,
            'ed_director_id': ed_director_id,
            'ed_director_comment': ed_director_comment,
            'hs_director_id': hs_director_id,
            'hs_director_comment': hs_director_comment,
            'wod_director_id': wod_director_id,
            'wod_director_comment': wod_director_comment,
            'gad_director_id': gad_director_id,
            'gad_director_comment': gad_director_comment,
            'cd_director_id': cd_director_id,
            'cd_director_comment': cd_director_comment,
            'env_department_id': env_department_id,
            'env_department_comment': env_department_comment,
            'hs_department_id': hs_department_id,
            'hs_department_comment': hs_department_comment,
            'wo_department_id': wo_department_id,
            'wo_department_comment': wo_department_comment,
            'ga_department_id': ga_department_id,
            'ga_department_comment': ga_department_comment,
            'constr_department_id': constr_department_id,
            'constr_department_comment': constr_department_comment,
            'entry_on_progress_flag': entry_on_progress_flag,
            'entry_datetime': entry_datetime,
            'entry_operator': entry_operator,
            'update_datetime': update_datetime,
            'update_operator': update_operator,
            'return_log_count': return_log_count,
            'comment_log_count': comment_log_count,
            'ng_character_list': ng_character_list,
            'next_button_display_flag': next_button_display_flag,
        }

        return render(request, 'fms/parts/check_sheet/cs_detail_template.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 次の進捗工程(step)に進む処理
def cs_go_next_step(send_data):
    DIFF_JST_FROM_UTC = 9
    # JST = timezone(timedelta(hours=+9), 'JST')

    # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    now_naive = datetime.datetime.now()
    now = make_aware(now_naive)

    # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
    operator = send_data["operator"]

    # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
    this_step = send_data["this_step"]

    next_step = send_data["next_step"]
    next_person_id = send_data["next_person_id"]
    next_division = send_data["next_division"]
    next_department = send_data["next_department"]
    target_id = send_data["target_id"]
    this_department = send_data["this_department"]
    this_division = send_data["this_division"]
    action = send_data["action"]
    comment = send_data["comment"]
    target = send_data["target"]
    target_budget_id = send_data["target_budget_id"]
    err_count = 0

    # 次作業者データをユーザー属性マスタから取得
    if UserAttribute.objects.filter(id=next_person_id).count() > 0:
        user_attribute_data = UserAttribute.objects.get(id=next_person_id)
        next_person = user_attribute_data.username
    else:
        next_person = None

    # 進捗状況に対して「target」と「target_id」で該当するものがあれば、呼び出し、なければ新規登録
    progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=this_step)

    # 各項目を設定
    progress_data.present_step = next_step
    # 所管部署承認状態へのstep移行時に次作業者と次部署、次部門を削除
    if next_step is not None and 135003000 <= next_step < 135004000:
        progress_data.present_operator = None
        progress_data.present_department = None
        progress_data.present_division = None
    else:
        progress_data.present_operator = next_person
        progress_data.present_department = next_department
        progress_data.present_division = next_division
    progress_data.last_operation_step = this_step
    progress_data.last_operator = operator
    progress_data.last_operation_datetime = now

    # 進捗状況のレコードを保存
    progress_data.save()

    # 進捗通知機能
    if this_step != next_step:
        step_notice(progress_data)

    # ログデータに新規登録
    Log(target=target, target_id=target_id, action=action, operator=operator, operation_datetime=now,
        step=this_step,
        comment=comment, operator_department=this_department, operator_division=this_division,
        budget_id=target_budget_id).save()

    # 届出CSでの並列処理に対応するため処理を分岐
    if action != 'M_confirm':
        cs_approval_stepmaster_data = StepMaster.objects.get(step_name='追届 承認/確認', target='cs')
        cs_ga_confirm_stepmaster_data = StepMaster.objects.get(step_name='追届総務G確認', target='cs')
        cs_sh_confirm_stepmaster_data = StepMaster.objects.get(step_name='追届安全衛生G確認', target='cs')
        cs_env_confirm_stepmaster_data = StepMaster.objects.get(step_name='追届環境G確認', target='cs')
        cs_eng_confirm_stepmaster_data = StepMaster.objects.get(step_name='追届工務G確認', target='cs')
        cs_ga_stepmaster_data = StepMaster.objects.get(step_name='追届総務G承認', target='cs')
        cs_sh_stepmaster_data = StepMaster.objects.get(step_name='追届安全衛生G承認', target='cs')
        cs_env_stepmaster_data = StepMaster.objects.get(step_name='追届環境G承認', target='cs')
        cs_eng_stepmaster_data = StepMaster.objects.get(step_name='追届工務G承認', target='cs')
        cs_ga_wait_stepmaster_data = StepMaster.objects.get(step_name='追届総務G承認状態', target='cs')
        cs_sh_wait_stepmaster_data = StepMaster.objects.get(step_name='追届安全衛生G承認状態', target='cs')
        cs_env_wait_stepmaster_data = StepMaster.objects.get(step_name='追届環境G承認状態', target='cs')
        cs_eng_wait_stepmaster_data = StepMaster.objects.get(step_name='追届工務G承認状態', target='cs')
        cs_order_department_approve_confirm_stepmaster_data = StepMaster.objects.get(step_name='追届原課承認者確認',
                                                                                     target='cs')
        cs_end_step_stepmaster_data = StepMaster.objects.get(step_name='追加届出 工程完了', target='cs')

        if this_step == cs_ga_stepmaster_data.step_id \
                or this_step == cs_sh_stepmaster_data.step_id \
                or this_step == cs_env_stepmaster_data.step_id \
                or this_step == cs_eng_stepmaster_data.step_id:

            go_next_step = 0
            with connections['fmsdb'].cursor() as cursor:
                try:
                    # DBテーブル「fms_progress」をロック
                    cursor.execute("SELECT * FROM fms_progress WITH(TABLOCKX)")
                    end_count = Progress.objects.filter(target='cs', target_id=target_id,
                                                        present_step=cs_ga_wait_stepmaster_data.step_id).count()
                    end_count += Progress.objects.filter(target='cs', target_id=target_id,
                                                         present_step=cs_sh_wait_stepmaster_data.step_id).count()
                    end_count += Progress.objects.filter(target='cs', target_id=target_id,
                                                         present_step=cs_env_wait_stepmaster_data.step_id).count()
                    end_count += Progress.objects.filter(target='cs', target_id=target_id,
                                                         present_step=cs_eng_wait_stepmaster_data.step_id).count()

                    if end_count == 4:
                        # 担当の所管部署の承認が下りたら次ステップへの移行を許可
                        go_next_step = 1

                except ImportError as exc:
                    err_count = 1

                # finally:
                    # DBテーブル「fms_progress」のロックを解除
                    # cursor.execute("UNLOCK TABLES", ['fms_progress'])

            # 4GLが承認済みの場合
            if go_next_step == 1:
                # 追加届出の承認者の情報を取得
                log_data = Log.objects.filter(target="cs", target_id=target_id, action='permit',
                                              step=cs_approval_stepmaster_data.step_id).all().order_by('-id')[0]

                # 次ステップ(追加届出原課承認者登録内容確認)を作成
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_order_department_approve_confirm_stepmaster_data.step_id)
                # 各項目を設定
                progress_data.present_operator = log_data.operator
                progress_data.last_operation_step = this_step
                progress_data.present_department = log_data.operator_department
                progress_data.present_division = log_data.operator_division
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # # 4GL承認状態で待機していたstepを入力完了状態にする
                # 総務
                # 総務GL承認状態のステップを呼び出し
                progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                     present_step=cs_ga_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 安全
                # 安全GL承認状態のステップを呼び出し
                progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                     present_step=cs_sh_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 環境
                # 環境GL承認状態のステップを呼び出し
                progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                     present_step=cs_env_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 工務
                # 工務GL承認状態のステップを呼び出し
                progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                     present_step=cs_eng_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

        # 各所管部署承認処理へ分岐
        elif this_step == cs_approval_stepmaster_data.step_id and next_step != this_step:
            # 所管部署ごとの登録届け出数を取得
            cs_ga_notification_progress_data_num = CsNotificationProgress.objects.filter(cs_no=target_id,
                                                                                         department_name='総務部'
                                                                                         ).count()
            cs_sh_notification_progress_data_num = CsNotificationProgress.objects.filter(cs_no=target_id,
                                                                                         department_name='安全衛生･保安G'
                                                                                         ).count()
            cs_env_notification_progress_data_num = CsNotificationProgress.objects.filter(cs_no=target_id,
                                                                                          department_name='環境G'
                                                                                          ).count()
            cs_eng_notification_progress_data_num = CsNotificationProgress.objects.filter(cs_no=target_id,
                                                                                          department_name='工務G'
                                                                                          ).count()

            if cs_ga_notification_progress_data_num + cs_sh_notification_progress_data_num + \
                    cs_env_notification_progress_data_num + cs_eng_notification_progress_data_num == 0:

                # 次stepに移行しているprogressを引き戻し
                progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                     present_step=cs_ga_confirm_stepmaster_data.step_id)

                log_data = Log.objects.filter(target=target, target_id=target_id, step=this_step).order_by('-id')[0]

                # 各項目を設定
                progress_data.present_step = this_step
                progress_data.present_operator = log_data.operator
                progress_data.present_department = log_data.operator_department
                progress_data.present_division = log_data.operator_division
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                msg = "登録する届出が0件です\n必ず1件以上登録してください！"
                ary = {
                    'target_id': target_id,
                    'msg': msg
                }
                return ary

            # 総務
            if cs_ga_notification_progress_data_num > 0:
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_ga_confirm_stepmaster_data.step_id)

                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_ga_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_ga_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_ga_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗通知機能
                if this_step != progress_data.present_step:
                    step_notice(progress_data)

            else:
                # 総務GL承認状態のステップを作成
                # 所管部署への分岐処理の前に現ステップは「追届総務G確認」へ移行しているため呼び出しは「追届総務G確認」
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_ga_confirm_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_step = cs_ga_wait_stepmaster_data.step_id
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
            # 進捗状況のレコードを保存
            progress_data.save()

            # 安全衛生
            if cs_sh_notification_progress_data_num > 0:
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_sh_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_sh_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_sh_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_sh_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗通知機能
                if this_step != progress_data.present_step:
                    step_notice(progress_data)

            else:
                # 安全GL承認状態のステップを作成
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_sh_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
            # 進捗状況のレコードを保存
            progress_data.save()

            # 環境
            if cs_env_notification_progress_data_num > 0:
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_env_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_env_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_env_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_env_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗通知機能
                if this_step != progress_data.present_step:
                    step_notice(progress_data)

            else:
                # 環境GL承認状態のステップを作成
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_env_wait_stepmaster_data.step_id)

                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()

            # 工務
            if cs_eng_notification_progress_data_num > 0:
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_eng_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_eng_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_eng_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_eng_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗通知機能
                if this_step != progress_data.present_step:
                    step_notice(progress_data)

            else:
                # 工務GL承認状態のステップを作成
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_eng_wait_stepmaster_data.step_id)
                # 各項目を設定
                progress_data.present_operator = None
                progress_data.last_operation_step = this_step
                progress_data.present_department = None
                progress_data.present_division = None
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()

    # メッセージのためのstep名、アクション名を取得
    step_data = StepMaster.objects.get(step_id=this_step)
    step_name = step_data.step_name
    action_data = ActionMaster.objects.get(action_cd=action)
    action_name = action_data.action_name

    if err_count > 0:
        msg = "システムエラー データベースへのアクセスに失敗しました"
    elif action == "complete" or action == "entry" or action == "entry_complete":
        msg = step_name + action_name
    elif action == "permit" or action == "accept":
        msg = step_name + "完了"
    else:
        msg = step_name + action_name + "完了"

    ary = {
        'target_id': target_id,
        'msg': msg
    }

    return ary


# 関連予算付随届出チェック完了判定
def get_cs_complete_relation(budget_id):
    # 1:完了可能、2:完了NG
    complete_flag = 1

    budget_list = Budget.objects.filter(relation_budget_id=budget_id, lost_flag=0)
    for budget_item in budget_list:
        cs_list = CsManage.objects.filter(budget_id=budget_item.budget_id, lost_flag=0)
        if len(cs_list) > 0:
            # CsManageがある場合、progressの有無を判定
            for cs_item in cs_list:
                if Progress.objects.filter(target='cs', target_id=cs_item.cs_no).count() > 0:
                    # progressが完了しているか判定
                    if get_cs_complete_progress(cs_item.cs_no) == 0:
                        complete_flag = 2
                        break
                elif budget_item.budget_id == budget_item.relation_budget_id:
                    # 主予算の場合、progress完了が必須
                    complete_flag = 2
                    break

        elif budget_item.budget_id == budget_item.relation_budget_id:
            # 主予算の場合、CsManageは必須
            complete_flag = 2
            break

        # 完了NGの場合は以降のBudgetは判定しない
        if complete_flag == 2:
            break

    return complete_flag


# 届出CS Progress完了判定
def get_cs_complete_progress(cs_no):
    # 0:完了NG、1:完了可能
    complete_flag = 0
    progress_list = Progress.objects.filter(target='cs', target_id=cs_no)
    for progress_item in progress_list:
        if progress_item.present_step == 134009901 or progress_item.present_step == 135009901:
            complete_flag = 1
            break

    return complete_flag


# 予算付随届出チェック完了数取得
def get_cs_complete_count(budget_id, relation_budget_flag):
    complete_count = 0
    cs_list = CsManage.objects.filter(budget_id=budget_id, lost_flag=0)
    total_count = cs_list.count()

    for cs_item in cs_list:
        complete_flag_progress = 0
        complete_flag_notification = 0

        if Progress.objects.filter(target='cs', target_id=cs_item.cs_no).count() > 0:
            complete_flag_progress = get_cs_complete_progress(cs_item.cs_no)
        elif relation_budget_flag == 1:
            complete_flag_progress = 1

        # 届出通知進捗判定
        notification_list = CsNotificationProgress.objects.filter(cs_no=cs_item.cs_no)

        # 届出通知進捗レコードが無い場合は完了
        if len(notification_list) < 1:
            complete_flag_notification = 1

        # 届出通知進捗レコードがある場合、全てが完了していなければ未完了とする
        else:
            not_complete_flag = 0
            for notification_item in notification_list:
                # 完了判定(許可日または許可番号にデータが入っていれば完了)
                if notification_item.permit_date is None and \
                        (notification_item.permit_no is None or notification_item.permit_no == ''):
                    not_complete_flag = 1
                    break
            if not_complete_flag != 1:
                complete_flag_notification = 1

        if complete_flag_progress == 1 and complete_flag_notification == 1:
            complete_count = complete_count + 1

    return total_count, complete_count


# 届出CS完了STEP取得
def cs_check_complete_step(present_step):

    complete_step = 999999999

    if 134000000 < present_step < 135000000:
        # 通常届出の場合
        # 各所管G 確認/承認ステップかを確認
        if 134002000 < present_step < 134003000:
            # 総務G 確認/承認
            if present_step == 134002001 or present_step == 134002051:
                # 総務G承認状態へ以降
                complete_step = 134003001
            # 安全衛生G 確認/承認
            elif present_step == 134002011 or present_step == 134002061:
                # 安全衛生G承認状態へ以降
                complete_step = 134003011
            # 環境G 確認/承認
            elif present_step == 134002021 or present_step == 134002071:
                # 環境G承認状態へ以降
                complete_step = 134003021
            # 工務G 確認/承認
            elif present_step == 134002031 or present_step == 134002081:
                # 工務G承認状態へ以降
                complete_step = 134003031
        # すでに承認状態であればそのまま
        elif present_step == 134009901 or 134003000 < present_step < 134004000:
            complete_step = present_step
        # 各所管G 確認/承認状態でなければ工程完了へ
        else:
            complete_step = 134009901
    elif 135000000 < present_step < 136000000:
        # 追加届出の場合
        # 追加届出各所管G 確認/承認ステップかを確認
        if 135002000 < present_step < 135003000:
            # 総務G 確認/承認
            if present_step == 135002001 or present_step == 135002051:
                # 総務G承認状態へ以降
                complete_step = 135003001
            # 安全衛生G 確認/承認
            elif present_step == 135002011 or present_step == 135002061:
                # 安全衛生G承認状態へ以降
                complete_step = 135003011
            # 環境G 確認/承認
            elif present_step == 135002021 or present_step == 135002071:
                # 環境G承認状態へ以降
                complete_step = 135003021
            # 工務G 確認/承認
            elif present_step == 135002031 or present_step == 135002081:
                # 工務G承認状態へ以降
                complete_step = 135003031
        # すでに承認状態であればそのまま
        elif present_step == 135009901 or 135003000 < present_step < 135004000:
            complete_step = present_step
        # 各所管G 確認/承認状態でなければ工程完了へ
        else:
            complete_step = 135009901

    return complete_step
