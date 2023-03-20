
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.db import connections
import math
import copy
# datetimeをインポート
import datetime
import traceback
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_aware
# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction, BusinessYearMaster
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import WorkClassMaster, RegulationMaster
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
from fms.models import ProSpecificationUnit, ProBudgetUnit
from fms.models import StopWorkCause, StopWorkCauseMaster
from fms.models import ErpConstruction, MCFrame
from fms.models import CsManage, CsNotificationProgress
from fms.views.common_def_views import get_return_person, get_job_count, get_filter_planning_charge_person_list
from fms.views.common_views import blank_to_None, None_to_blank
from common.common_def import date_to_many_type
from fms.views.work_views import check_work_estimates_complete
from .execution_views import execution_work_common_data, execution_budget_common_data
from fms.views.estimate_views import price_value_update
from fms.views.cs_views import cs_check_complete_step
from fms.views.common_def_views import output_log_exception, check_operator_permission, get_operator_permission
from fms.views.notice_mail_views import step_notice


# イレギュラー処理一覧表示
def irregular_menu(request):
    try:
        # サイドメニュー用継承データ取得
        t_username = request.user.username
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = request.POST['user_authority']
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']

        data = {
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'operator_permission_list': get_operator_permission(t_username),
        }

        return render(request, 'fms/parts/irregular/irregular_menu.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# level5のトップページ表示処理
@login_required
@require_POST
def level5_step_stop(request):
    try:
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser
        user_name = t_user_last_name + t_user_first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        level5_step_id_string = request.POST['level5_step_id']
        level5_step_id = int(request.POST['level5_step_id'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        target = request.POST['target']
        select_tab = int(request.POST['select_tab'])

        # 対象となる始まりのstepを取得
        start_level5_step_id = level5_step_id
        # 対象となる終わりのstepを設定･･･始まりのstep+1000
        end_level5_step_id = level5_step_id + 1000
        # 対象のstep_levelを「5」
        step_level = 5

        level4_step = level5_step_id / 1000

        level4_step_id = math.floor(level4_step) * 1000

        level3_step = level5_step_id / 1000000

        level3_step_id = math.floor(level3_step) * 1000000

        # ユーザーの部署名を取得
        department_data = DepartmentMaster.objects.get(department_cd=user_department_cd)
        user_department = department_data.department_name

        # ユーザーの部門名を取得
        division_data = DivisionMaster.objects.get(division_cd=user_division_cd)
        user_division = division_data.division_name

        # level5のstep名を取得
        target_step_data = StepMaster.objects.get(step_id=level5_step_id)
        step_name = target_step_data.step_name

        # 新規登録の有無を確認
        target_step_data = StepMaster.objects.get(step_id=level4_step_id)
        new_entry_flag = target_step_data.new_entry_flag

        # 共通関数「common_def_views.py」の「get_job_count」を呼び出し、件数の格納された2次元配列を取得
        step_num_list = get_job_count(start_level5_step_id, end_level5_step_id, step_level, user_division_cd,
                                      user_department_cd, t_username)

        if level5_step_id == 213004000:
            default_tab = 1
        else:
            default_tab = 1

        # 中止処理開始フラグ
        start_work_stop_flag = 1

        data = {
            't_user_name': t_username,
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            't_user_is_superuser': t_user_is_superuser,
            'user_name': user_name,
            'user_department': user_department,
            'user_division': user_division,
            'step_name': step_name,
            'level5_step_id': level5_step_id,
            'level4_step_id': level4_step_id,
            'level3_step_id': level3_step_id,
            'new_entry_flag': new_entry_flag,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'step_num_list': step_num_list,
            'select_tab': select_tab,
            'default_tab': default_tab,
            'target': target,
            'start_work_stop_flag': start_work_stop_flag,
        }

        return render(request, 'fms/parts/common/level5_step_execution.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 仕様中止処理
@login_required
@require_POST
def stop_work_info(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        budget_id = int(request.POST["target_budget_id"])
        construction_id = int(request.POST["target_work_id"])
        this_step = int(request.POST["this_step"])
        present_operator = request.POST["present_operator"]
        target_step_id = int(request.POST["target_step_id"])
        user_division_cd = request.POST["user_division_cd"]
        user_department_cd = request.POST["user_department_cd"]
        user_authority = request.POST["user_authority"]
        confirm_user = request.POST["confirm_user"]
        permit_user = request.POST["permit_user"]
        level5_step_id = int(request.POST["level5_step_id"])
        target = request.POST["target"]
        target_budget_id = request.POST["target_budget_id"]
        target_work_id = request.POST["target_work_id"]
        # target_div_id_name = request.POST["target_div_id_name"]
        div_id_name = request.POST["div_id_name"]
        copy_check = request.POST["copy_check"]
        current_tab = request.POST["current_tab"]

        if target == 'work' or target == 'prospecificationunit':
            cause_list_target = 'work'
        elif target == 'budget' or target == 'probudgetunit':
            cause_list_target = 'budget'
        else:
            cause_list_target = ''

        stop_work_cause_list = StopWorkCauseMaster.objects.filter(Q(target=cause_list_target) | Q(target='common'),
                                                                  Q(lost_flag=0)).all().order_by('display_order')

        stop_work_cause_data_num = StopWorkCause.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                lost_flag=0).count()

        if stop_work_cause_data_num > 0:
            stop_work_cause_data = StopWorkCause.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                             target=target, lost_flag=0)
            stop_work_cause_name = stop_work_cause_data.stop_work_cause_name
            if stop_work_cause_name is None:
                stop_work_cause_name = ""

            stop_work_reason = stop_work_cause_data.stop_work_reason
            if stop_work_reason is None:
                stop_work_reason = ""

            stop_work_risk = stop_work_cause_data.stop_work_risk
            if stop_work_risk is None:
                stop_work_risk = ""

            present_step = stop_work_cause_data.present_step
            if present_step is None:
                present_step = 0

            present_operator = stop_work_cause_data.present_operator
            if present_operator is None:
                present_operator = ""

            approval_no = stop_work_cause_data.approval_no
            if approval_no is None:
                approval_no = ""

            # 無効となった(=1つ前のrev_noの)対象の工事データのレコード数を取得
            old_stop_work_cause_data_num = StopWorkCause.objects.filter(budget_id=budget_id,
                                                                        construction_id=construction_id,
                                                                        lost_flag=1).count()
            # 無効となった(=1つ前のrev_noの)対象の工事データのレコードがある場合
            if old_stop_work_cause_data_num > 0:
                # 無効となった(=1つ前のrev_noの)対象の工事データを取得
                old_stop_work_cause_data = StopWorkCause.objects.filter(budget_id=budget_id,
                                                                        construction_id=construction_id,
                                                                        lost_flag=1).all().order_by('-id')[0]
            else:
                old_stop_work_cause_data = ""

        else:
            stop_work_cause_name = ""
            stop_work_reason = ""
            stop_work_risk = ""
            present_step = 0
            present_operator = present_operator
            old_stop_work_cause_data = ""
            old_stop_work_cause_data_num = 0
            approval_no = ""

        if div_id_name == "proindividualcontractdoc" or div_id_name == "work":
            stepdisplayitem_data = StepDisplayItem.objects.get(step=target_step_id, div_id_name='stop_work_info',
                                                               lost_flag=0)
        else:
            stepdisplayitem_data = StepDisplayItem.objects.get(step=target_step_id, div_id_name='stop_budget_info',
                                                               lost_flag=0)
        this_page = stepdisplayitem_data.page
        # action_button_id = 'stop_work' + str(this_page) + '_action_button'
        action_button_id = target + str(this_page) + '_action_button'

        # ProSpecificationUnitの読込
        if 212001000 <= level5_step_id < 213000000 or level5_step_id >= 231001000:
            base_data = execution_work_common_data(budget_id, construction_id)

            data = {
                'work_common_data': base_data,
                'prospecificationunit_data': base_data['prospecificationunit_data'],
                'budget_id':  base_data['budget_id'],
                'work_rev_no':  base_data['rev_no'],
                'budget_no':  base_data['budget_no'],
                'budget_name':  base_data['budget_name'],
                'construction_id':  base_data['construction_id'],
                'work_name': base_data['work_name'],
                'sub_id':  base_data['sub_id'],
                'division':  base_data['division'],
                'division_name':  base_data['division_name'],
                'department':  base_data['department'],
                'department_name':  base_data['department_name'],
                'format_kbn':  base_data['format_kbn'],
                'goods_construct_kbn_name':  base_data['goods_construct_kbn_name'],
                'goods_construct_kbn':  base_data['goods_construct_kbn'],
                'specification_person_in_charge':  base_data['specification_person_in_charge'],
                'specification_person_in_charge_name': base_data['specification_person_in_charge_name'],
                'delivery_location':  base_data['delivery_location'],
                'desired_construct_period_from':  base_data['desired_construct_period_from'],
                'desired_construct_period_to':  base_data['desired_construct_period_to'],
                'desired_delivery_date':  base_data['desired_delivery_date'],
                'estimate_submission_date':  base_data['estimate_submission_date'],
                'estimated_deadline_date':  base_data['estimated_deadline_date'],
                'order_limited_date': base_data['order_limited_date'],
                'fixed_delivery_location':  base_data['fixed_delivery_location'],
                'fixed_delivery_date_from':  base_data['fixed_delivery_date_from'],
                'fixed_delivery_date_to':  base_data['fixed_delivery_date_to'],
                'fixed_delivery_date':  base_data['fixed_delivery_date'],
                'scheduled_inspection_date_from':  base_data['scheduled_inspection_date_from'],
                'scheduled_inspection_date_to':  base_data['scheduled_inspection_date_to'],
                'scheduled_acceptance_date_from': base_data['scheduled_acceptance_date_from'],
                'scheduled_acceptance_date_to': base_data['scheduled_acceptance_date_to'],
                'preparation_delivery_date': base_data['preparation_delivery_date'],
                'specification_data':  base_data['specification_data'],
                'construction_outline':  base_data['construction_outline'],
                'division_lists':  base_data['division_lists'],
                'department_lists':  base_data['department_lists'],
                'work_class_lists':  base_data['work_class_lists'],
                'work_charge_process': base_data['work_charge_process'],
                'work_charge_process_name': base_data['work_charge_process_name'],
                'old_prospecificationunit_data_num': base_data['old_prospecificationunit_data_num'],
                'old_prospecificationunit_data': base_data['old_prospecificationunit_data'],
                'old_proestimate_data_num': base_data['old_proestimate_data_num'],
                'old_proestimate_data': base_data['old_proestimate_data'],
                'procurement_person_in_charge': base_data['procurement_person_in_charge'],
                'procurement_person_in_charge_name': base_data['procurement_person_in_charge_name'],
                'management_class_cd': base_data['management_class_cd'],
                'management_class_name': base_data['management_class_name'],

                'stop_work_cause_list': stop_work_cause_list,
                'old_stop_work_cause_data': old_stop_work_cause_data,
                'old_stop_work_cause_data_num': old_stop_work_cause_data_num,
                't_username': t_username,
                'action_button_id': action_button_id,
                'this_page': this_page,
                'target': request.POST['target'],
                'target_budget_id': request.POST['target_budget_id'],
                'target_work_id': target_work_id,
                # 'div_id_name': request.POST['div_id_name'],
                'div_id_name': div_id_name,
                'stop_work_cause_name': stop_work_cause_name,
                'stop_work_reason': stop_work_reason,
                'stop_work_risk': stop_work_risk,
                'present_step': present_step,
                'present_operator': present_operator,
                'parent_template': 'fms/parts/execution/execution_detail/execution_work_info_base.html',
            }
        elif 213004000 <= level5_step_id < 220000000:
            # 予算データを取得
            base_data = execution_budget_common_data(target_budget_id, request.user.username)
            if base_data['probudgetunit_data'] == '' or base_data['probudgetunit_data'] is None:
                base_data['probudgetunit_data'] = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)

            data = {
                'probudgetunit_data': base_data['probudgetunit_data'],
                'budget_id': base_data['budget_id'],
                'rev_no': base_data['rev_no'],
                'budget_no': base_data['budget_no'],
                'budget_name': base_data['budget_name'],
                'division': base_data['division'],
                'division_name': base_data['division_name'],
                'department': base_data['department'],
                'department_name': base_data['department_name'],
                'jurisdiction_area': base_data['jurisdiction_area'],
                'area_person_in_charge': base_data['area_person_in_charge'],
                'original_sec_person_in_charge': base_data['original_sec_person_in_charge'],
                'sche_gov_inspection_date': base_data['sche_gov_inspection_date'],
                'division_lists': base_data['division_lists'],
                'department_lists': base_data['department_lists'],
                'area_person_in_charge_list': base_data['area_person_in_charge_list'],
                'area_person_in_charge_name': base_data['area_person_in_charge_name'],
                'original_sec_person_in_charge_list': base_data['original_sec_person_in_charge_list'],
                'original_sec_person_in_charge_name': base_data['original_sec_person_in_charge_name'],
                'old_probudgetunit_data_num': base_data['old_probudgetunit_data_num'],
                'old_probudgetunit_data': base_data['old_probudgetunit_data'],

                'stop_work_cause_list': stop_work_cause_list,
                'old_stop_work_cause_data': old_stop_work_cause_data,
                'old_stop_work_cause_data_num': old_stop_work_cause_data_num,
                't_username': t_username,
                'action_button_id': action_button_id,
                'this_page': this_page,
                'target': request.POST['target'],
                'target_budget_id': request.POST['target_budget_id'],
                'target_work_id': target_work_id,
                # 'div_id_name': request.POST['div_id_name'],
                'div_id_name': div_id_name,
                #'div_id_name': current_tab,
                'stop_work_cause_name': stop_work_cause_name,
                'stop_work_reason': stop_work_reason,
                'approval_no': approval_no,
                'present_step': present_step,
                'present_operator': present_operator,
                'parent_template': 'fms/parts/execution/execution_detail/execution_budget_info_base.html',
            }
        else:

            data = {
                'stop_work_cause_list': stop_work_cause_list,
                'old_stop_work_cause_data': old_stop_work_cause_data,
                'old_stop_work_cause_data_num': old_stop_work_cause_data_num,
                't_username': t_username,
                'action_button_id': action_button_id,
                'this_page': this_page,
                'target': request.POST['target'],
                'target_budget_id': request.POST['target_budget_id'],
                'budget_no': "",
                'target_work_id': target_work_id,
                # 'div_id_name': request.POST['div_id_name'],
                'div_id_name': div_id_name,
                'stop_work_cause_name': stop_work_cause_name,
                'stop_work_reason': stop_work_reason,
                'stop_work_risk': stop_work_risk,
                'approval_no': approval_no,
                'present_step': present_step,
                'present_operator': present_operator,
            }

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「work」がデータ更新対象か確認
        work_edit_action_num += DataEntryStepMaster.objects.filter(step_id=target_step_id, target_table='stop_work_cause'
                                                                   ).count()
        work_edit_action_num += DataEntryStepMaster.objects.filter(step_id=target_step_id, target_table='stop_budget_cause'
                                                                   ).count()
        edit_flag = 0
        if level5_step_id == 920000000:
            work_edit_action_num = 0

        if work_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            # if level5_step_id > 211001000:
            if level5_step_id > 212000000:
                return render(request, 'fms/parts/irregular/execution_stop_work_cause_edit.html', data)
            else:
                return render(request, 'fms/parts/irregular/stop_work_cause_edit.html', data)
        else:
            # if level5_step_id > 211001000:
            if level5_step_id > 212000000:
                return render(request, 'fms/parts/irregular/execution_stop_work_cause_info.html', data)
            else:
                return render(request, 'fms/parts/irregular/stop_work_cause_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事一覧絞込パーツ表示処理
@require_POST
def stop_work_filter(request):
    from fms.views.common_def_views import get_filter_master, get_next_target
    try:

        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        # エリア管理者の中止申請対象は発注処理(step = 241000000)に入ってから工事・検査実行(step = 252000000)まで
        step_st = 241000000
        step_ed = 252000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed,
                                              step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        data = {
            'budget_condition_list': budget_condition_list,
            'step_list': step_list,
            'business_year_list': business_year_list,
            'budget_class_list': budget_class_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'process_list': process_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'user_department_cd': target_department,
            'user_division_cd': target_division,
            'user': target_person,
        }

        return render(request, 'fms/parts/irregular/stop_work_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 仕様書情報テーブル一覧
@require_POST
def get_stop_execution_work_lists(request):
    try:
        execution_work_lists = ""
        execution_work_lists_num = ""
        sel_budget_condition = request.POST['sel_budget_condition']
        sel_step = request.POST['sel_step']
        sel_business_year = request.POST['sel_business_year']
        sel_budget_class = request.POST['sel_budget_class']
        sel_budget_id = request.POST['sel_budget_id']
        sel_budget_no = request.POST['sel_budget_no']
        sel_budget_name = request.POST['sel_budget_name']
        sel_division = request.POST['sel_division']
        sel_department = request.POST['sel_department']
        sel_process = request.POST['sel_process']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']
        # sel_on_work = request.POST['sel_on_work']
        level5_step_id = int(request.POST['level5_step_id'])
        sel_display_order = request.POST['sel_display_order']
        list_kind = request.POST['list_kind']
        sel_work_id = request.POST['sel_work_id']
        sel_work_name = request.POST['sel_work_name']
        sel_specification_person_in_charge = request.POST['sel_specification_person_in_charge']
        sel_planning_charge_person = request.POST['sel_planning_charge_person']
        sel_area_manager_parson = request.POST['sel_area_manager_parson']

        target = request.POST['target']
        start_work_stop_flag = int(request.POST['start_work_stop_flag'])
        username = request.user.username

        # irregular_menuから開いた場合
        if start_work_stop_flag == 1:
            # エリア管理者の中止申請対象は発注処理(step = 241000000)に入ってから工事・検査実行(step = 252000000)まで
            step_st = 241000000
            step_ed = 252000000
        else:
            # level4_topから開いた場合
            step_st = math.floor(level5_step_id / 1000) * 1000
            step_ed = step_st + 1000

        where_str = ""
        where_parm = []

        ex_select_str = ""
        budget_join_str = ""
        work_join_str = ""

        # 検索条件
        # 予算状態
        if sel_budget_condition != "":
            where_str += " AND fms_budgetconditionmaster.condition_id = %s"
            where_parm.append(int(sel_budget_condition))
        # 進捗状況
        if sel_step != "":
            where_str += " AND fms_stepmaster.step_id = %s"
            where_parm.append(int(sel_step))
        # 年度
        if sel_business_year != "":
            # if budget_join_str == "":
            #     budget_join_str = " LEFT JOIN fms_budget ON fms_prospecificationunit.budget_id=fms_budget.budget_id "
            ex_select_str = ", fms_budget.business_year_id"
            where_str += " AND fms_budget.business_year_id = %s"
            where_parm.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            # if budget_join_str == "":
            #     budget_join_str = " LEFT JOIN fms_budget ON fms_prospecificationunit.budget_id=fms_budget.budget_id "
            ex_select_str = ", fms_budget.budget_class_id"
            where_str += " AND fms_budget.budget_class_id = %s"
            where_parm.append(int(sel_budget_class))
        # 予算ID
        if sel_budget_id != "":
            where_str += " AND fms_prospecificationunit.budget_id = %s"
            where_parm.append(int(sel_budget_id))
        # 予算NO
        if sel_budget_no != "":
            where_str += " AND fms_budget.budget_no = %s"
            where_parm.append(sel_budget_no)
        # 予算名
        if sel_budget_name != "":
            where_str += " AND fms_budget.budget_name LIKE %s"
            where_parm.append('%' + sel_budget_name + '%')
        # 部門
        if sel_division != "":
            where_str += " AND fms_departmentmaster.division_cd = %s"
            where_parm.append(sel_division)
        # 部署
        if sel_department != "":
            where_str += " AND fms_departmentmaster.department_cd = %s"
            where_parm.append(sel_department)
        # 行程
        if sel_process != "":
            if budget_join_str == "":
                budget_join_str = " LEFT JOIN fms_budget ON fms_prospecificationunit.budget_id=fms_budget.budget_id "
            ex_select_str = ", fms_budget.facility_process_id"
            where_str += " AND fms_budget.facility_process_id = %s"
            where_parm.append(sel_process)
        # 次作業部門
        if sel_next_division != "":
            where_str += " AND fms_progress.present_division = %s"
            where_parm.append(sel_next_division)
        # 次作業部署
        if sel_next_department != "":
            where_str += " AND fms_progress.present_department = %s"
            where_parm.append(sel_next_department)
        # 次作業者
        if sel_next_parson != "":
            where_str += " AND fms_progress.present_operator = %s"
            where_parm.append(sel_next_parson)
        # 工事ID
        if sel_work_id != "":
            where_str += " AND fms_prospecificationunit.construction_id = %s"
            where_parm.append(sel_work_id)
        # 工事名
        if sel_work_name != "":
            if work_join_str == "":
                work_join_str = " LEFT JOIN fms_work ON fms_prospecificationunit.construction_id=fms_work.work_id "
            ex_select_str = ", fms_work.work_name"
            where_str += " AND fms_work.work_name LIKE %s"
            where_parm.append('%' + sel_work_name + '%')
        # 仕様担当者
        if sel_specification_person_in_charge != "":
            where_str += " AND fms_prospecificationunit.specification_person_in_charge = %s"
            where_parm.append(sel_specification_person_in_charge)
        # 計画担当者
        if sel_planning_charge_person != "":
            # 計画担当者名をリストに表示するためのusernameを追加
            ex_select_str += ", planningchargepersondata.first_name AS planningchargepersondata_first_name"
            ex_select_str += ", planningchargepersondata.last_name AS planningchargepersondata_last_name"
            where_str += " AND fms_planningchargeperson.charge_person = %s"
            where_parm.append(sel_planning_charge_person)
            planning_charge_person_join_str = 'LEFT JOIN fms_planningchargeperson on fms_budget.budget_id = fms_planningchargeperson.budget_id ' \
                                              'and fms_planningchargeperson.lost_flag = 0'
            # 計画担当者名をリストに表示するためのusernameをJOIN
            planning_charge_person_join_str += 'LEFT JOIN fms_user as planningchargepersondata ON fms_planningchargeperson.charge_person=planningchargepersondata.username ' \
                                              'and planningchargepersondata.lost_flag = 0 '
        else:
            planning_charge_person_join_str = ''

        # エリア管理者
        if sel_area_manager_parson != "":
            where_str += " AND fms_probudgetunit.area_person_in_charge = %s"
            where_parm.append(sel_area_manager_parson)

        # 範囲を発注処理(step = 241000000)に入ってから工事・検査実行(step = 252000000)までに限定する
        where_str += " AND fms_stepmaster.step_id > %s"
        where_str += " AND fms_stepmaster.step_id < %s"
        where_parm.append(step_st)
        where_parm.append(step_ed)

        # 仕様書情報テーブル抽出
        sql = """
            SELECT
                  fms_prospecificationunit.*
                """ + ex_select_str + """
                , CASE WHEN fms_budget.id IS NULL THEN 0 ELSE fms_budget.id END AS budget_unique_id  
                , fms_budget.budget_id
                , fms_budget.budget_name as budget_budget_name
                , fms_budget.business_year_id
                , fms_progress.target
                , fms_progress.present_step
                , fms_progress.present_operator
                ,fms_budgetclassmaster.budget_class_name as  budget_class
                ,fms_processmaster.process_cd2 as process_cd, fms_processmaster.process_name as process_name
                , U1.first_name AS U1_first_name
                , U1.last_name AS U1_last_name
                , U2.first_name AS U2_first_name
                , U2.last_name AS U2_last_name
                , fms_stepmaster.step_name
                , fms_stepmaster.step_id 
                , CASE WHEN fms_budget.budget_no IS NULL THEN '' ELSE fms_budget.budget_no END AS bd_no
                , fms_departmentmaster.department_name
                , fms_divisionmaster.division_name
                , CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_prospecificationunit.entry_datetime, GETDATE()) 
                                                            ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END 
                  AS days_stay
                , CASE WHEN log_2.action = 'return' THEN 1 ELSE 0 END AS return_flag
            FROM fms_prospecificationunit
                """ + budget_join_str + work_join_str + """
                LEFT JOIN fms_budget ON (fms_prospecificationunit.budget_id=fms_budget.budget_id and fms_budget.lost_flag=0)
                LEFT JOIN fms_budgetcondition ON fms_prospecificationunit.budget_id=fms_budgetcondition.budget_id
                LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id
                INNER JOIN fms_progress ON fms_prospecificationunit.construction_id=fms_progress.target_id 
                        AND fms_progress.target='prospecificationunit'
                LEFT JOIN fms_user as U1 ON fms_progress.present_operator=U1.username
                LEFT JOIN fms_user as U2 ON fms_prospecificationunit.specification_person_in_charge=U2.username
                LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id
                LEFT JOIN fms_departmentmaster ON fms_prospecificationunit.department=fms_departmentmaster.department_cd
                LEFT JOIN fms_divisionmaster ON fms_departmentmaster.division_cd=fms_divisionmaster.division_cd
                LEFT JOIN fms_budgetclassmaster ON fms_budget.budget_class_id=fms_budgetclassmaster.budget_class_cd
                LEFT JOIN fms_processmaster ON fms_budget.facility_process_id=fms_processmaster.process_cd2
                LEFT JOIN fms_probudgetunit ON (fms_prospecificationunit.budget_id=fms_probudgetunit.budget_id and fms_probudgetunit.lost_flag=0)
                                
                LEFT JOIN (SELECT 
                             [target_id] 
                            ,MAX([operation_datetime]) as last_operationtime 
                            FROM [fms].[dbo].[fms_log] 
                            WHERE [target]='prospecificationunit' AND [action] != 'temporarily_saved' 
                            group by [target_id]) as log 
                            ON [fms].[dbo].[fms_prospecificationunit].construction_id=log.target_id 
                LEFT JOIN(SELECT
                            TOP 1 [target_id], [action] 
                            FROM[fms].[dbo].[fms_log] 
                            WHERE[target] = 'prospecificationunit' AND[action] != 'temporarily_saved' 
                            order by operation_datetime DESC) as log_2 
                            ON fms_prospecificationunit.construction_id = log_2.target_id 
                """ + planning_charge_person_join_str + """ 
            WHERE fms_prospecificationunit.lost_flag=0 
         """
        if where_str != "":
            sql += where_str

        if sel_display_order == "1":
            sql += " ORDER BY fms_budget.budget_id"
        elif sel_display_order == "2":
            sql += " ORDER BY fms_budget.budget_no"
        elif sel_display_order == "3":
            sql += " ORDER BY days_stay desc"
        else:  # sel_display_order == "4":
            sql += " ORDER BY fms_prospecificationunit.construction_id"

        try:
            execution_work_lists = ProSpecificationUnit.objects.raw(sql, where_parm)
            execution_work_lists_num = len(list(execution_work_lists))

        except Exception:
            msg = "ERROR!!"

        data = {
            'execution_work_lists': execution_work_lists,
            'execution_work_lists_num': execution_work_lists_num,
            'level5_step_id': level5_step_id,
        }

        if list_kind == 'stop_work':
            return render(request, 'fms/parts/irregular/stop_work_list.html', data)
        else:
            return
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 仕様中止処理
@login_required
@require_POST
def stop_work_cause_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        next_person = request.POST["next_person"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]
        comment = request.POST["comment"]
        budget_id = int(request.POST["budget_id"])
        budget_no = request.POST["budget_no"]
        budget_name = request.POST["budget_name"]
        construction_id = int(request.POST["construction_id"])
        present_operator = request.POST["present_operator"]
        level5_step_id = int(request.POST["level5_step_id"])
        target = request.POST["target"]
        start_work_stop_flag = request.POST["start_work_stop_flag"]

        stop_work_cause_name = request.POST["stop_work_cause_name"]
        stop_work_reason = request.POST["stop_work_reason"]
        stop_work_risk = request.POST["stop_work_risk"]
        approval_no = request.POST["approval_no"]
        before_stop_step = int(request.POST["before_stop_step"])

        entry_success_flag = 0

        if start_work_stop_flag != "1":
            # 中止前step確認
            stop_work_cause_data_num = StopWorkCause.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                    target=target, lost_flag=0).count()
            if stop_work_cause_data_num == 1:
                stop_work_cause_data = StopWorkCause.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                                 target=target, lost_flag=0)

                before_stop_step = stop_work_cause_data.present_step

            elif stop_work_cause_data_num > 1:
                entry_success_flag = 0
                ary = {
                    'msg': "登録された中止原因レコードが複数HITしました！！",
                    'entry_success_flag': entry_success_flag,
                }
                return JsonResponse(ary)

        # if approval_no != "":
        if target == "budget" or target == "probudgetunit":
            no_budget_no_count = Budget.objects.filter(budget_no=None, relation_budget_id=budget_id, lost_flag=0).count()

            # 未中止工事仕様数検出
            not_stopped_relation_psunit_count_data = not_stopped_relation_psunit_data_count(budget_id)

            not_stopped_relation_psunit_data = not_stopped_relation_psunit_count_data['not_stopped_relation_psunit_data']
            not_stopped_relation_work_data = not_stopped_relation_psunit_count_data['not_stopped_relation_work_data']
            not_stopped_relation_psunit_data_num = not_stopped_relation_psunit_count_data['not_stopped_relation_psunit_data_num']

            if not_stopped_relation_psunit_data_num > 0:
                entry_success_flag = 0
                ary = {
                    'msg': "中止していない仕様書があります！！",
                    'entry_success_flag': entry_success_flag,
                }
                return JsonResponse(ary)

            # 中止対象予算の抽出処理
            ans = get_target_budget_list(budget_id)

            target_budget_list = ans['target_budget_list']
            target_budget_list_num = ans['target_budget_list_num']

        else:
            target_budget_list = Budget.objects.filter(budget_id=budget_id, lost_flag=0)

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        for target_budget_list_item in target_budget_list:
            # budget_id単位の中止対象予算リスト整形処理
            target_data = {
                'target': target,
                'present_operator': present_operator,
                'before_stop_step': before_stop_step,
                'target_budget_list_item': target_budget_list_item,
            }

            target_list = convert_budget_list(target_data)

            stop_cause_data = {
                'budget_id': target_budget_list_item.budget_id,
                'work_id': construction_id,
                'operator': operator,
                'now': now,

                'stop_work_cause_name': stop_work_cause_name,
                'stop_work_reason': stop_work_reason,
                'stop_work_risk': stop_work_risk,
                'approval_no': approval_no,

                'target_list': target_list,
            }

            # 中止理由保存処理
            entry_stop_cause(stop_cause_data)

            stop_target_data = {
                'budget_id': budget_id,
                'budget_target': target,
                'target_budget_id': target_budget_list_item.budget_id,
                'work_id': construction_id,
                'start_work_stop_flag': start_work_stop_flag,
                'level5_step_id': level5_step_id,
                'this_step': this_step,
                'operator': operator,
                'this_department': this_department,
                'this_division': this_division,
                'comment': comment,
                'now': now,
                'next_person': next_person,
                'next_division': next_division,
                'next_department': next_department,
                'next_step': next_step,

                'target_list': target_list,
            }

            # 仕様書中止処理
            ans = stop_work_progress(stop_target_data)

        if this_step == 212001002 and before_stop_step >= 241003002:
            # 購買データ
            erpconstruction_num = ErpConstruction.objects.filter(order_id=construction_id, budget_id=budget_id).count()

            if erpconstruction_num == 1:
                erpconstruction_date = ErpConstruction.objects.get(order_id=construction_id, budget_id=budget_id)
                new_total_price = 0 - erpconstruction_date.total_price
                new_discount_price = 0 - erpconstruction_date.discount_price
                new_erpconstruction_date, created = ErpConstruction.objects.get_or_create(order_id=construction_id,
                                                                                          budget_id=budget_id,
                                                                                          total_price=new_total_price)
                # 購買データのコピー
                new_erpconstruction_date.detail_no = erpconstruction_date.detail_no
                new_erpconstruction_date.vendor_code = erpconstruction_date.vendor_code
                new_erpconstruction_date.purchase_group_code = erpconstruction_date.purchase_group_code
                new_erpconstruction_date.purchase_person = erpconstruction_date.purchase_person
                new_erpconstruction_date.currency_code = erpconstruction_date.currency_code
                new_erpconstruction_date.account_class = erpconstruction_date.account_class
                new_erpconstruction_date.item_code = erpconstruction_date.item_code
                new_erpconstruction_date.item_text = erpconstruction_date.item_text
                new_erpconstruction_date.order_amount = 1
                new_erpconstruction_date.ordering_unit = erpconstruction_date.ordering_unit
                new_erpconstruction_date.delivery_date = erpconstruction_date.delivery_date
                new_erpconstruction_date.amount_per_base_unit = erpconstruction_date.amount_per_base_unit
                new_erpconstruction_date.base_unit_amount = erpconstruction_date.base_unit_amount
                new_erpconstruction_date.purchase_order_no = erpconstruction_date.purchase_order_no
                new_erpconstruction_date.erp_errormsg = erpconstruction_date.erp_errormsg
                new_erpconstruction_date.item_group_code = erpconstruction_date.item_group_code
                new_erpconstruction_date.item_code_status = erpconstruction_date.item_code_status
                new_erpconstruction_date.plant_code = erpconstruction_date.plant_code
                new_erpconstruction_date.storage_space_code = erpconstruction_date.storage_space_code
                new_erpconstruction_date.purchase_trace_no = erpconstruction_date.purchase_trace_no
                new_erpconstruction_date.order_person = erpconstruction_date.order_person
                new_erpconstruction_date.rem = erpconstruction_date.rem
                new_erpconstruction_date.storage_space_rem = erpconstruction_date.storage_space_rem
                new_erpconstruction_date.discount_price = new_discount_price
                new_erpconstruction_date.account_code = erpconstruction_date.account_code
                new_erpconstruction_date.cost_center = erpconstruction_date.cost_center
                new_erpconstruction_date.instruction_code = erpconstruction_date.instruction_code
                new_erpconstruction_date.consumption_tax_code = erpconstruction_date.consumption_tax_code
                new_erpconstruction_date.order_no = erpconstruction_date.order_no
                new_erpconstruction_date.work_class = erpconstruction_date.work_class
                new_erpconstruction_date.relation_no = erpconstruction_date.relation_no
                new_erpconstruction_date.item_detail_text = erpconstruction_date.item_detail_text
                new_erpconstruction_date.construction_start_date = erpconstruction_date.construction_start_date
                new_erpconstruction_date.status = erpconstruction_date.status
                new_erpconstruction_date.department = erpconstruction_date.department
                new_erpconstruction_date.division = erpconstruction_date.division
                new_erpconstruction_date.entry_operator = operator
                new_erpconstruction_date.entry_datetime = now
                new_erpconstruction_date.order_date = date_to_many_type(now).str_type_date_erp
                new_erpconstruction_date.save()

                # 新ERP刷新対応
                mcframe_data = MCFrame.objects.get(order_id=construction_id, budget_id=budget_id)
                new_total_price = 0 - mcframe_data.total_price
                new_discount_price = 0 - mcframe_data.discount_price
                new_mcframe_data, created = MCFrame.objects.get_or_create(order_id=construction_id, budget_id=budget_id, total_price=new_total_price)
                # 購買データのコピー
                new_mcframe_data.vendor_code = mcframe_data.vendor_code
                new_mcframe_data.purchase_group_code = mcframe_data.purchase_group_code
                new_mcframe_data.purchase_person = mcframe_data.purchase_person
                new_mcframe_data.currency_code = mcframe_data.currency_code
                new_mcframe_data.account_class = mcframe_data.account_class
                new_mcframe_data.item_code = mcframe_data.item_code
                new_mcframe_data.item_text = mcframe_data.item_text
                new_mcframe_data.order_amount = 1
                new_mcframe_data.ordering_unit = mcframe_data.ordering_unit
                new_mcframe_data.delivery_date = mcframe_data.delivery_date
                new_mcframe_data.amount_per_base_unit = mcframe_data.amount_per_base_unit
                new_mcframe_data.base_unit_amount = mcframe_data.base_unit_amount
                new_mcframe_data.purchase_order_no = mcframe_data.purchase_order_no
                new_mcframe_data.erp_errormsg = mcframe_data.erp_errormsg
                new_mcframe_data.item_group_code = mcframe_data.item_group_code
                new_mcframe_data.item_code_status = mcframe_data.item_code_status
                new_mcframe_data.plant_code = mcframe_data.plant_code
                new_mcframe_data.storage_space_code = mcframe_data.storage_space_code
                new_mcframe_data.purchase_trace_no = mcframe_data.purchase_trace_no
                new_mcframe_data.order_person = mcframe_data.order_person
                new_mcframe_data.rem = mcframe_data.rem
                new_mcframe_data.storage_space_rem = mcframe_data.storage_space_rem
                new_mcframe_data.discount_price = new_discount_price
                new_mcframe_data.account_code = mcframe_data.account_code
                new_mcframe_data.cost_center = mcframe_data.cost_center
                new_mcframe_data.instruction_code = mcframe_data.instruction_code
                new_mcframe_data.consumption_tax_code = mcframe_data.consumption_tax_code
                new_mcframe_data.work_class = mcframe_data.work_class
                new_mcframe_data.relation_no = mcframe_data.relation_no
                new_mcframe_data.item_detail_text = mcframe_data.item_detail_text
                new_mcframe_data.construction_start_date = mcframe_data.construction_start_date
                new_mcframe_data.status = mcframe_data.status
                new_mcframe_data.department = mcframe_data.department
                new_mcframe_data.division = mcframe_data.division
                new_mcframe_data.division = mcframe_data.division
                new_mcframe_data.order_no = mcframe_data.order_no
                new_mcframe_data.order_type_classification = mcframe_data.order_type_classification
                new_mcframe_data.numbering = 2
                new_mcframe_data.year = mcframe_data.year
                new_mcframe_data.detail_no = mcframe_data.detail_no
                new_mcframe_data.entry_operator = operator
                new_mcframe_data.entry_datetime = now
                new_mcframe_data.order_date = date_to_many_type(now).str_type_date_erp
                new_mcframe_data.save()
                # 新ERP刷新対応

            elif erpconstruction_num > 1:
                new_erpconstruction_date = ErpConstruction.objects.get(order_id=construction_id,
                                                                       budget_id=budget_id,
                                                                       total_price__lt=0
                                                                       )
                new_erpconstruction_date.update_operator = operator
                new_erpconstruction_date.update_datetime = now
                new_erpconstruction_date.save()

                # 新ERP刷新対応
                new_mcframe_data = MCFrame.objects.get(order_id=construction_id, budget_id=budget_id, total_price__lt=0)
                new_mcframe_data.update_operator = operator
                new_mcframe_data.update_datetime = now
                new_mcframe_data.save()
                # 新ERP刷新対応

        elif target == 'work':
            # 予算情報の見積額を更新
            price_value_update(budget_id, now, operator)

        msg = StepMaster.objects.get(step_id=this_step, lost_flag=0).step_name + "完了"
        entry_success_flag = 1

        work_data_num = Work.objects.filter(work_id=construction_id, lost_flag=0).count()

        if work_data_num == 1:
            work_name = Work.objects.get(work_id=construction_id, lost_flag=0).work_name
        else:
            work_name = ""

        if target == 'work':
            # 仕様書予算見積完了チェック
            check_result = check_work_estimates_complete(construction_id)
        else:
            check_result = ''

        ary = {
            'msg': msg,
            'work_name': work_name,
            'entry_success_flag': entry_success_flag,
            'check_result': check_result,

        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 中止理由保存処理
def entry_stop_cause(stop_cause_data):
    budget_id = int(stop_cause_data['budget_id'])
    work_id = int(stop_cause_data['work_id'])
    operator = stop_cause_data['operator']
    now = stop_cause_data['now']

    stop_work_cause_name = stop_cause_data["stop_work_cause_name"]
    stop_work_reason = stop_cause_data["stop_work_reason"]
    stop_work_risk = stop_cause_data["stop_work_risk"]
    approval_no = stop_cause_data["approval_no"]

    target_list = stop_cause_data["target_list"]

    for target_list_item in target_list:

        target = target_list_item["target"]
        present_operator = target_list_item["present_operator"]
        before_stop_step = target_list_item["before_stop_step"]

        # 中止理由テーブルのレコード存在チェック
        stop_work_cause_data_num = StopWorkCause.objects.filter(budget_id=budget_id, construction_id=work_id,
                                                                target=target, lost_flag=0).count()

        # 更新
        if stop_work_cause_data_num > 0:

            old_stop_work_cause_data = StopWorkCause.objects.get(budget_id=budget_id, construction_id=work_id,
                                                                 target=target, lost_flag=0)

            before_stop_step = old_stop_work_cause_data.present_step

            define_check_new = (stop_work_cause_name, stop_work_reason, stop_work_risk, approval_no)
            define_check_old = (old_stop_work_cause_data.stop_work_cause_name,
                                old_stop_work_cause_data.stop_work_reason,
                                old_stop_work_cause_data.stop_work_risk,
                                old_stop_work_cause_data.approval_no)

            # 既に登録されているデータと比較し違いがあれば登録済みデータのlost_flagを立てる
            # さらに新規データのrev_noを+1して、登録済みデータの中止前stepと中止前作業者を継承
            if define_check_new != define_check_old:
                old_stop_work_cause_data.lost_flag = 1
                old_stop_work_cause_data.save()

                rev_no = old_stop_work_cause_data.rev_no + 1
                present_operator = old_stop_work_cause_data.present_operator
            else:
                rev_no = old_stop_work_cause_data.rev_no

        # 新規登録
        else:
            rev_no = 0

        stop_work_cause_data, created = StopWorkCause.objects.get_or_create(budget_id=budget_id,
                                                                            construction_id=work_id,
                                                                            target=target, lost_flag=0)

        if created:
            stop_work_cause_data.rev_no = rev_no
            stop_work_cause_data.stop_work_cause_name = stop_work_cause_name
            stop_work_cause_data.stop_work_reason = stop_work_reason
            stop_work_cause_data.stop_work_risk = stop_work_risk
            stop_work_cause_data.approval_no = approval_no
            stop_work_cause_data.present_step = before_stop_step
            stop_work_cause_data.present_operator = present_operator
            stop_work_cause_data.entry_datetime = now
            stop_work_cause_data.entry_operator = operator
        else:
            stop_work_cause_data.rev_no = rev_no
            stop_work_cause_data.update_datetime = now
            stop_work_cause_data.update_operator = operator

        # 調達仕様書情報テーブルのレコードを保存
        stop_work_cause_data.save()

    return


def stop_work_progress(stop_target_data):
    from fms.views.common_def_views import get_progress_end_user

    budget_id = int(stop_target_data['budget_id'])
    budget_target = stop_target_data['budget_target']
    target_budget_id = int(stop_target_data['target_budget_id'])
    work_id = int(stop_target_data['work_id'])
    start_work_stop_flag = stop_target_data['start_work_stop_flag']
    level5_step_id = int(stop_target_data['level5_step_id'])
    this_step = int(stop_target_data['this_step'])
    operator = stop_target_data['operator']
    this_department = stop_target_data['this_department']
    this_division = stop_target_data['this_division']
    comment = stop_target_data['comment']
    now = stop_target_data['now']
    next_person = stop_target_data['next_person']
    next_division = stop_target_data['next_division']
    next_department = stop_target_data['next_department']
    next_step = int(stop_target_data['next_step'])

    target_list = stop_target_data['target_list']

    budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)

    for target_list_item in target_list:

        target = target_list_item["target"]
        before_stop_step = target_list_item["before_stop_step"]

        if target == 'work' or target == 'prospecificationunit':
            target_id = work_id
        else:
            target_id = target_budget_id

        # ログデータを新規登録
        Log(target=target, target_id=target_id, action='stop', operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=target_budget_id).save()

        # 「budget_noが設定された」「予算」が「中止処理の最終steo以外」の場合は実行しない
        # if not(target == 'budget' and before_stop_step == 133009905):
        if not ((target == 'budget'or target == 'probudgetunit')
                and (budget_data.budget_no != "" and budget_data.budget_no is not None)
                and level5_step_id != 213008000):

            if start_work_stop_flag != "1":
                # 中止前step確認
                stop_work_cause_data = StopWorkCause.objects.get(budget_id=target_budget_id, construction_id=work_id,
                                                                 target=target, lost_flag=0)

                before_stop_step = stop_work_cause_data.present_step

            # 進捗状況をtargetとtarget_idで抽出
            progress_data_num = Progress.objects.filter(target=target, target_id=target_id).count()
            if progress_data_num == 1:
                progress_data = Progress.objects.get(target=target, target_id=target_id)
                # 各項目を設定
                # 工事仕様書中止の場合(発注前) ⇒ 中止フロー使用せず即中止
                if (this_step == 212001002 and before_stop_step < 241003002) \
                        or (this_step < 212001000 and (target == 'work'or target == 'prospecificationunit')):
                    if target == 'work':
                        progress_data.present_step = 212009901
                    elif target == 'prospecificationunit':
                        progress_data.present_step = 212009902

                    # ユーザ情報を工程終了状態に変更
                    user_attribute_data = get_progress_end_user()
                    next_person = user_attribute_data.username
                    next_division = user_attribute_data.division
                    next_department = user_attribute_data.department

                # 予算中止の場合(予算No未決定、または関連予算) ⇒ 中止フロー使用せず即中止
                elif (target == 'budget'or target == 'probudgetunit') \
                    and (budget_data.budget_no == "" or budget_data.budget_no is None
                         or budget_data.relation_budget_id != target_budget_id):
                    if target == 'budget':
                        # progress_data.present_step = 213008012
                        progress_data.present_step = 133009906
                    elif target == 'probudgetunit':
                        progress_data.present_step = 213008011

                    # ユーザ情報を工程終了状態に変更
                    user_attribute_data = get_progress_end_user()
                    next_person = user_attribute_data.username
                    next_division = user_attribute_data.division
                    next_department = user_attribute_data.department
                # 上記以外 ⇒ 中止フローを使用する
                else:
                    progress_data.present_step = next_step

                progress_data.present_operator = next_person
                progress_data.present_department = next_department
                department_data = DepartmentMaster.objects.get(department_cd=next_department, lost_flag=0)
                progress_data.present_division = department_data.division_cd

                # 今のstepと次のstepが違う場合の処理･･･追加で項目(最終工程、最終作業者、最終処理日時)に値を設定
                if this_step != next_step:
                    progress_data.last_operation_step = this_step
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now

                # 進捗状況のレコードを保存
                progress_data.save()

            else:
                print('【WARNING:progress_num】target: %s, id: %d, progress_data_num: %d ' % (target, target_id, progress_data_num))

            # 中止対象の工事を中止状態に変更
            if target == 'prospecificationunit' and start_work_stop_flag != "1":
                prospecificationunit_data_num = ProSpecificationUnit.objects.filter(budget_id=target_budget_id,
                                                                                    construction_id=work_id,
                                                                                    lost_flag=0).count()
                if prospecificationunit_data_num == 1 and this_step != next_step:
                    prospecificationunit_data, created = ProSpecificationUnit.objects.get_or_create(budget_id=target_budget_id,
                                                                                                    construction_id=work_id,
                                                                                                    lost_flag=0)
                    # prospecificationunit_data.lost_flag = 1
                    prospecificationunit_data.cancel_flag = 1
                    prospecificationunit_data.update_operator = operator
                    prospecificationunit_data.update_datetime = now

                    prospecificationunit_data.save()

            elif target == 'work':
                work_data_num = Work.objects.filter(work_budget_id=target_budget_id,
                                                    work_id=work_id, lost_flag=0).count()

                if work_data_num == 1:
                    work_data, created = Work.objects.get_or_create(work_budget_id=target_budget_id,
                                                                    work_id=work_id, lost_flag=0)
                    # work_data.lost_flag = 1
                    work_data.cancel_flag = 1
                    work_data.update_operator = operator
                    work_data.update_datetime = now

                    work_data.save()

            elif target == 'probudgetunit':
                probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).count()
                if probudgetunit_data_num == 1:
                    probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)
                    # probudgetunit_data.lost_flag = 1
                    probudgetunit_data.cancel_flag = 1
                    probudgetunit_data.update_operator = operator
                    probudgetunit_data.update_datetime = now

                    probudgetunit_data.save()

            elif target == 'budget':
                budget_data_num = Budget.objects.filter(budget_id=target_budget_id, lost_flag=0).count()

                if budget_data_num == 1:
                    budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                    # budget_data.lost_flag = 1
                    budget_data.cancel_flag = 1
                    budget_data.update_operator = operator
                    budget_data.update_datetime = now

                    budget_data.save()

                    # probudgetunitが存在するならbudget側を完了状態にする
                    probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).count()
                    if probudgetunit_data_num == 1:
                        probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)
                        if budget_data.relation_budget_id == probudgetunit_data.budget_id:
                            # probudgetunitが存在するならbudgetのprogress_dataは存在するはず
                            # progress_data.present_step = 213008012
                            progress_data.present_step = 133009906
                            # ユーザ情報を工程終了状態に変更
                            user_attribute_data = get_progress_end_user()
                            progress_data.present_operator = user_attribute_data.username
                            next_department = user_attribute_data.department

                            progress_data.present_department = next_department
                            department_data = DepartmentMaster.objects.get(department_cd=next_department, lost_flag=0)
                            progress_data.present_division = department_data.division_cd

                            progress_data.last_operation_step = this_step
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now

                            # 進捗状況のレコードを保存
                            progress_data.save()
        # 関連予算リストのbudget_idと画面に表示したBudget_idが同じ場合はフローを進める
        elif target_budget_id == budget_id and target == budget_target:
            progress_data_num = Progress.objects.filter(target=target, target_id=target_budget_id).count()
            if progress_data_num == 1:
                progress_data = Progress.objects.get(target=target, target_id=target_budget_id)
                progress_data.present_step = next_step

                progress_data.present_operator = next_person
                progress_data.present_department = next_department
                department_data = DepartmentMaster.objects.get(department_cd=next_department, lost_flag=0)
                progress_data.present_division = department_data.division_cd

                # 今のstepと次のstepが違う場合の処理･･･追加で項目(最終工程、最終作業者、最終処理日時)に値を設定
                if this_step != next_step:
                    progress_data.last_operation_step = this_step
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now

                # 進捗状況のレコードを保存
                progress_data.save()

        # 進捗通知機能
        # if this_step != next_step:
        if this_step != next_step and (target == budget_target or not (target == 'budget' or target == 'probudgetunit')):
            step_notice(progress_data)

    msg = "target_stopped"

    return msg


# 届出CS進捗終了処理
@require_POST
def cs_forced_termination(request):
    from fms.views.common_def_views import get_progress_end_user
    try:
        budget_id = int(request.POST["budget_id"])

        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username

        cs_data_num = 0

        relation_budget_data = Budget.objects.filter(relation_budget_id=budget_id, lost_flag=0)

        for target_budget_data in relation_budget_data:
            cs_data = CsManage.objects.filter(budget_id=target_budget_data.budget_id, lost_flag=0)

            for cs_data_item in cs_data:
                cs_progress = Progress.objects.filter(target='cs', target_id=cs_data_item.cs_no)

                for cs_progress_item in cs_progress:
                    cs_progress_data = Progress.objects.get(id=cs_progress_item.id, target='cs')

                    present_step = cs_check_complete_step(cs_progress_data.present_step)

                    user_attribute_data = get_progress_end_user()
                    next_person = user_attribute_data.username
                    next_division = user_attribute_data.division
                    next_department = user_attribute_data.department

                    last_operation_step = cs_progress_data.present_step
                    last_operator = operator
                    last_operation_datetime = now

                    cs_progress_data.present_step = present_step
                    cs_progress_data.present_department = next_department
                    cs_progress_data.present_division = next_division
                    cs_progress_data.present_operator = next_person
                    cs_progress_data.last_operation_step = last_operation_step
                    cs_progress_data.last_operator = last_operator
                    cs_progress_data.last_operation_datetime = last_operation_datetime

                    cs_progress_data.save()

                    # 進捗通知機能
                    if last_operation_step != present_step:
                        step_notice(cs_progress_data)

                    cs_data_num += 1

                # 届出進捗状況の項目「permit_no」に追記
                cs_notification_progress_list = CsNotificationProgress.objects.filter(cs_no=cs_data_item.cs_no)

                for cs_notification_progress_list_item in cs_notification_progress_list:
                    cs_notification_progress_data = CsNotificationProgress.objects.get(id=cs_notification_progress_list_item.id)

                    if cs_notification_progress_data.permit_no != "" and cs_notification_progress_data.permit_no is not None:
                        new_permit_no = cs_notification_progress_data.permit_no + chr(13) + chr(10) + "予算中止のため届け出不要"
                        cs_notification_progress_data.permit_no = new_permit_no[:100]
                    else:
                        cs_notification_progress_data.permit_no = "予算中止のため届け出不要"

                    cs_notification_progress_data.save()

        msg = "cs data " + str(cs_data_num) + " completed"

        data = {
            'msg': msg,
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

def not_stopped_relation_psunit_data_count(budget_id):
    not_stopped_relation_psunit_data_num = 0

    # PSUnitの未中止工事仕様件数
    with connections['fmsdb'].cursor() as cursor:
        sql = """ SELECT		fms_budget.budget_id
                                ,fms_budget.relation_budget_id
                                ,fms_budget.lost_flag as budget_lost_flag
                                ,[fms_prospecificationunit].budget_id as psunit_budget_id
                                ,[fms_prospecificationunit].construction_id
                                ,[fms_prospecificationunit].lost_flag as psunit_lost_flag
                                ,[fms_prospecificationunit].cancel_flag
                    from		fms_budget
                    left join	[fms_prospecificationunit] on fms_budget.budget_id = [fms_prospecificationunit].budget_id
                                                          and [fms_prospecificationunit].lost_flag = 0
                    where		fms_budget.lost_flag=0
                      and		fms_budget.relation_budget_id=""" + str(budget_id)
        sql += """ and		[fms_prospecificationunit].cancel_flag=0 """
        res = cursor.execute(sql)
        not_stopped_relation_psunit_data = res.fetchall()
        not_stopped_relation_psunit_data_num = len(not_stopped_relation_psunit_data)

    # workの未中止または未完了工事仕様件数
    with connections['fmsdb'].cursor() as cursor:
        sql = """ SELECT		fms_budget.budget_id
                              ,fms_budget.relation_budget_id
                              ,fms_budget.lost_flag as budget_lost_flag
                              ,[fms_work].work_budget_id as work_budget_id
                              ,[fms_work].work_id
                              ,[fms_work].lost_flag as work_lost_flag
                              ,[fms_work].cancel_flag as work_cancel_flag
                              ,[fms_progress].target
                              ,[fms_progress].target_id
                              ,[fms_progress].present_step
                  from		fms_budget
                  left join	[fms_work] on fms_budget.budget_id = [fms_work].work_budget_id
                                                        and [fms_work].lost_flag = 0
                  left join [fms_progress] on [fms_work].work_id = [fms_progress].target_id
                                                        and [fms_progress].target = 'work'
                  where		fms_budget.lost_flag=0
                    and		fms_budget.relation_budget_id=""" + str(budget_id)
        sql += """ and		([fms_progress].present_step != 133009904 and [fms_progress].present_step != 212009901) """
        res = cursor.execute(sql)
        not_stopped_relation_work_data = res.fetchall()
        not_stopped_relation_psunit_data_num += len(not_stopped_relation_work_data)

    ary = {
        'not_stopped_relation_psunit_data': not_stopped_relation_psunit_data,
        'not_stopped_relation_work_data': not_stopped_relation_work_data,
        'not_stopped_relation_psunit_data_num': not_stopped_relation_psunit_data_num,
    }

    return ary


def get_target_budget_list(budget_id):
    with connections['fmsdb'].cursor() as cursor:
        sql = """ SELECT		fms_budget.budget_id
                                        ,fms_budget.relation_budget_id
                                        ,fms_budget.lost_flag as budget_lost_flag
                                        ,fms_budget.cancel_flag as budget_cancel_flag
                                        ,budget_progress.target as budget_progress_target
                                        ,budget_progress.present_operator as budget_progress_present_operator
                                        ,budget_progress.present_step as budget_progress_present_step
                                        ,[fms_probudgetunit].budget_id as probudgetunit_budget_id
                                        ,[fms_probudgetunit].lost_flag as probudgetunit_lost_flag
                                        ,[fms_probudgetunit].cancel_flag as probudgetunit_cancel_flag
                                        ,probudgetunit_progress.target as probudgetunit_progress_target
                                        ,probudgetunit_progress.present_operator as probudgetunit_progress_present_operator
                                        ,probudgetunit_progress.present_step as probudgetunit_progress_present_step
                            from		fms_budget
                            left join	[fms_probudgetunit] on fms_budget.budget_id = [fms_probudgetunit].budget_id
                                                           and [fms_probudgetunit].lost_flag = 0
    						left join	[fms_progress] as budget_progress on fms_budget.budget_id = budget_progress.target_id
    																	 and budget_progress.target = 'budget'
    						left join	[fms_progress] as probudgetunit_progress on fms_budget.budget_id = probudgetunit_progress.target_id
    																			and probudgetunit_progress.target = 'probudgetunit'
                            where		fms_budget.lost_flag=0
                              and		fms_budget.relation_budget_id=""" + str(budget_id)
        sql += """ and		(fms_budget.cancel_flag=0 or [fms_probudgetunit].cancel_flag=0) """
        res = cursor.execute(sql)
        target_budget_list = res.fetchall()
        target_budget_list_num = len(target_budget_list)

    ary = {
        'target_budget_list': target_budget_list,
        'target_budget_list_num': target_budget_list_num,
    }

    return ary


def convert_budget_list(target_data):
    target = target_data['target']
    present_operator = target_data['present_operator']
    before_stop_step = target_data['before_stop_step']
    target_budget_list_item = target_data['target_budget_list_item']

    target_list = []

    if target == 'budget' or target == 'probudgetunit':
        main_target = target_budget_list_item.budget_progress_target
        main_present_operator = target_budget_list_item.budget_progress_present_operator
        main_before_stop_step = target_budget_list_item.budget_progress_present_step
        another_target = target_budget_list_item.probudgetunit_progress_target
        another_present_operator = target_budget_list_item.probudgetunit_progress_present_operator
        another_before_stop_step = target_budget_list_item.probudgetunit_progress_present_step
    else:
        main_target = target
        main_present_operator = present_operator
        main_before_stop_step = before_stop_step
        another_target = ""
        another_present_operator = ""
        another_before_stop_step = ""

    main_target_list = {'target': main_target,
                        'present_operator': main_present_operator,
                        'before_stop_step': main_before_stop_step
                        }

    another_target_list = {'target': another_target,
                           'present_operator': another_present_operator,
                           'before_stop_step': another_before_stop_step
                           }

    if main_target_list["present_operator"] != "" \
            and main_target_list["present_operator"] is not None \
            and main_target_list["before_stop_step"] != "" \
            and main_target_list["before_stop_step"] is not None:
        target_list.append(main_target_list)

    if another_target_list["present_operator"] != "" \
            and another_target_list["present_operator"] is not None \
            and another_target_list["before_stop_step"] != "" \
            and another_target_list["before_stop_step"] is not None:
        target_list.append(another_target_list)

    return target_list


# 中止対象予算step終了処理
@require_POST
def stop_budget_progress(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        next_person = request.POST["next_person"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]
        comment = request.POST["comment"]
        budget_id = int(request.POST["budget_id"])
        construction_id = int(request.POST["construction_id"])
        present_operator = request.POST["present_operator"]
        level5_step_id = int(request.POST["level5_step_id"])
        target = request.POST["target"]
        start_work_stop_flag = request.POST["start_work_stop_flag"]

        before_stop_step = int(request.POST["before_stop_step"])

        # 中止対象予算の抽出処理
        ans = get_target_budget_list(budget_id)

        target_budget_list = ans['target_budget_list']
        target_budget_list_num = ans['target_budget_list_num']

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        for target_budget_list_item in target_budget_list:
            # budget_id単位の中止対象予算リスト整形処理
            target_data = {
                'target': target,
                'present_operator': present_operator,
                'before_stop_step': before_stop_step,
                'target_budget_list_item': target_budget_list_item,
            }

            target_list = convert_budget_list(target_data)

            stop_target_data = {
                'budget_id': budget_id,
                'budget_target': target,
                'target_budget_id': target_budget_list_item.budget_id,
                'work_id': construction_id,
                'start_work_stop_flag': start_work_stop_flag,
                'level5_step_id': level5_step_id,
                'this_step': this_step,
                'operator': operator,
                'this_department': this_department,
                'this_division': this_division,
                'comment': comment,
                'now': now,
                'next_person': next_person,
                'next_division': next_division,
                'next_department': next_department,
                'next_step': next_step,

                'target_list': target_list,
            }

            # 仕様書中止処理
            ans = stop_work_progress(stop_target_data)

        msg = "中止対象予算step終了処理完了"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 業者マスタ修正ページ表示
@login_required
@require_POST
def edit_supplier_master_page(request):
    from fms.models import SupplierMaster
    try:
        t_username = request.user.username
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']

        # アクセス権チェック
        if not check_operator_permission(t_username, 'edit_supplier_master'):
            return HttpResponse("<script>alert('アクセス権がありません!');window.history.back(-1);</script>")

        # lost_flag=1のデータも含めて表示
        supplier_master_list = SupplierMaster.objects.all().order_by('supplier_cd')
        data = {
            't_user_name': t_username,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'supplier_master_list': supplier_master_list,
        }
        return render(request, 'fms/parts/irregular/edit_supplier_master_page.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 業者マスタ登録処理
@login_required
@require_POST
def edit_supplier_master_entry(request):
    from fms.models import SupplierMaster
    try:
        # JSからのPOST引数を取得
        # 仕入先コードと、仕入先名は変更不可とする
        # supplier_cd = request.POST["supplier_cd"]
        # supplier_name = request.POST["supplier_name"]
        sel_lost_flag = int(request.POST["sel_lost_flag"])
        msg = '修正対象が特定できません！！！'

        # 新規登録は禁止、編集のみ許可する
        if request.POST["supplier_id"] is not "":
            supplier_id = int(request.POST["supplier_id"])
            supplier_master_list = SupplierMaster.objects.filter(id=supplier_id)
            if supplier_master_list.count() == 1:
                supplier_master_item = supplier_master_list[0]
                # supplier_master_item.supplier_cd = supplier_cd
                # supplier_master_item.supplier_name = supplier_name
                supplier_master_item.lost_flag = sel_lost_flag
                supplier_master_item.save()
                msg = '修正完了'

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
