import math
import os
import logging
import datetime
import time
import re
import traceback

from django.db import connections
from django.db.models import Q

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from fms.models import ProcessMaster, StepMaster, Progress
from fms.models import Log, Budget, StepAction, ActionMaster, DataEntryStepMaster, AttachmentDocuments, WorkEquipment
from django.contrib.auth.models import User
from fms.models import Phenomenon, Measure
# from common.models import UserAttribute, DivisionMaster, DepartmentMaster
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work, BudgetLaw, BudgetEquipment, Supplies, SubmissionDocument
from fms.models import Estimate
from fms.models import FunctionMaster, BudgetRequiredFunction, StepMaster
import datetime
from fms.models import PlanningChargePerson
from fms.models import CsManage, CsGeneralAffairs, CsSafetyHealth, CsEnvironment, CsEngineering, FreeSpecDetail
from fms.views.common_def_views import get_return_person, get_job_count, convert_charge_department, \
    get_next_operator_cs, get_next_department_list
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception, get_department_person_list
from fms.views.common_def_views import get_ng_character_list, get_job_count_filter
from fms.views.common_def_views import is_edit_budget_step
from fms.views.estimate_work_list import estimate_send_back
from fms.views.risks_views import risks_go_next_step, risk_send_back
from fms.views.cs_views import cs_go_next_step
from fms.models import ProSpecificationUnit, ProEstimates, WorkLaw
from socket import gethostname
from fms.views.file_loader_views import file_upload, file_upload_file_list
from django.utils.timezone import make_aware
from common.common_def import date_to_many_type
from fms.views.notice_mail_views import step_notice


# 設備管理のトップページを開くときの処理
@login_required
def index(request):
    # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser
    user_name = t_user_last_name + t_user_first_name

    sql = """ SELECT fms_userattribute.*, fms_departmentmaster.department_name """
    sql = sql + """ FROM fms_userattribute """
    sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_userattribute.department = fms_departmentmaster.department_cd """
    sql = sql + """ WHERE fms_userattribute.username='""" + t_username + """' AND fms_userattribute.lost_flag=0 """
    sql = sql + """ order by fms_userattribute.display_order """

    # トップページの部署選択ソース取得
    user_departments_list = UserAttribute.objects.raw(sql)
    # 初期で表示する部署、部門、権限、確認者、承認者情報を取得

    user_departments = UserAttribute.objects.get(username=t_username, lost_flag=0, display_order=1)
    user_division_cd = user_departments.division
    user_department_cd = user_departments.department
    user_authority = user_departments.authority
    confirm_user = user_departments.confirm_username
    permit_user = user_departments.permit_username
    # 初期で表示する部門名取得
    user_division_data = DivisionMaster.objects.get(division_cd=user_division_cd)
    user_division_name = user_division_data.division_name

    user_attribute_list = UserAttribute.objects.filter(username=t_username, lost_flag=0).order_by('display_order')
    department_cd_list = [data.department for data in user_attribute_list]
    department_data_list = DepartmentMaster.objects.filter(department_cd__in=department_cd_list, lost_flag=0)
    division_cd_list = [data.division for data in user_attribute_list]
    division_data_list = DivisionMaster.objects.filter(division_cd__in=division_cd_list, lost_flag=0)

    data = {
        't_user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser,
        'user_name': user_name,
        'user_division_cd': user_division_cd,
        'user_department_cd': user_department_cd,
        'user_departments_list': user_departments_list,
        'user_authority': user_authority,
        'confirm_user': confirm_user,
        'permit_user': permit_user,
        'user_division_name': user_division_name,
        'user_attribute_list': user_attribute_list,
        'department_data_list': department_data_list,
        'division_data_list': division_data_list,
    }

    return render(request, 'fms/fms_top_page.html', data)


@login_required
@require_POST
def top_page_detail(request):

    try:
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username
        # JSからのPOST引数を取得
        user_department_cd = request.POST['department']
        user_division_cd = request.POST['division']

        start_step_id = 0
        end_step_id = 999999999
        step_level = 3
        step_num_list = get_job_count(start_step_id, end_step_id, step_level,
                                      user_division_cd, user_department_cd, t_username)

        data = {
            'step_num_list': step_num_list
        }
        return render(request, 'fms/parts/common/fms_top_page_body.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# level4のトップページ表示処理
@login_required
@require_POST
def level4_step_top(request):
    try:

        logger = logging.getLogger("file")
        logger.info(request.POST['user_department_cd'] + 'G　' + request.user.username + 'さん　ステップID：' + request.POST['level4_step_id'])

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser
        user_name = t_user_last_name + t_user_first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        level4_step_id = int(request.POST['level4_step_id'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        target = 'budget'

        # 対象となる始まりのstepを取得
        start_level4_step_id = level4_step_id
        # 対象となる終わりのstepを設定･･･始まりのstep+1000000
        end_level4_step_id = level4_step_id + 1000000
        # 対象のstep_levelを「4」
        step_level = 4

        # ユーザーの部署名を取得
        department_data = DepartmentMaster.objects.get(department_cd=user_department_cd)
        user_department = department_data.department_name

        # ユーザーの部門名を取得
        division_data = DivisionMaster.objects.get(division_cd=user_division_cd)
        user_division = division_data.division_name
        # level4のstep名を取得
        target_step_data = StepMaster.objects.get(step_id=level4_step_id)
        step_name = target_step_data.step_name

        # 共通関数「common_def_views.py」の「get_job_count」を呼び出し、件数の格納された2次元配列を取得
        step_num_list = get_job_count(start_level4_step_id, end_level4_step_id, step_level, user_division_cd, user_department_cd, t_username)

        data = {
            't_user_name': t_username,
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            't_user_is_superuser': t_user_is_superuser,
            'user_name': user_name,
            'user_department': user_department,
            'user_division': user_division,
            'step_name': step_name,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'step_num_list': step_num_list,
            'level4_step_id': level4_step_id,
        }

        return render(request, 'fms/parts/common/level4_step_top_page.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# level5のトップページ表示処理
@login_required
@require_POST
def level5_step_top(request):
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
        target = 'budget'
        # select_tab 確認
        # select_tab_str = request.POST['select_tab']
        # print(select_tab_str)
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

        if level5_step_id != 213000000 and level5_step_id != 213009000:
            # level5のデフォルトのリストタブを取得
            target_step_data = StepMaster.objects.get(step_id=level4_step_id)
            tab_target = target_step_data.target

            # level5のstep名を取得
            target_step_data = StepMaster.objects.get(step_id=level5_step_id)
            step_name = target_step_data.step_name

            # 新規登録の有無を確認
            target_step_data = StepMaster.objects.get(step_id=level4_step_id)
            new_entry_flag = target_step_data.new_entry_flag

            # 計画側トップページには仕様書発行中は表示しない
            if level5_step_id == 211001000:
                end_level5_step_id = 211001011

            # 共通関数「common_def_views.py」の「get_job_count」を呼び出し、件数の格納された2次元配列を取得
            step_num_list = get_job_count(start_level5_step_id, end_level5_step_id, step_level, user_division_cd, user_department_cd, t_username)
        elif level5_step_id == 213009000:
            # 実行中予算一覧画面は特殊処理(該当ステップを持たない)
            tab_target = 'probudgetunit'
            step_name = '実行中予算一覧（予算繰越開始）'
            new_entry_flag = 0
            step_num_list = []
        else:
            # 実行中予算一覧画面は特殊処理(該当ステップを持たない)
            tab_target = 'probudgetunit'
            step_name = '実行中予算一覧（予算完了開始）'
            new_entry_flag = 0
            # 仕様書発行中の件数表示
            step_num_list = get_job_count(213000000, 213000000, 5, user_division_cd, user_department_cd, t_username)

        default_tab = 1
        if tab_target == 'work' or tab_target == 'prospecificationunit' or tab_target == 'ph_nc':
            default_tab = 2

        edit_budget_step_flag = 0
        if is_edit_budget_step(level5_step_id):
            edit_budget_step_flag = 1

        data = {
            't_user_name': t_username,
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            't_user_is_superuser': t_user_is_superuser,
            'user_name': user_name,
            'user_department': user_department,
            'user_division': user_division,
            'step_name': step_name,
            'level3_step_id': level3_step_id,
            'level4_step_id': level4_step_id,
            'level5_step_id': level5_step_id,
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
            'edit_budget_step_flag': edit_budget_step_flag,
        }

        if level5_step_id_string[0:3] == '131' or level5_step_id_string[0:3] == '132' \
                or level5_step_id_string[0:3] == '133' or level5_step_id_string[0:3] == '136':
            return render(request, 'fms/parts/common/level5_step_budget.html', data)
        elif level5_step_id_string[0:3] == '134' or level5_step_id_string[0:3] == '135':
            return render(request, 'fms/parts/common/level5_step_cs.html', data)
        elif level5_step_id_string[0:5] == '21301':
            return render(request, 'fms/parts/common/level5_step_carry_forward.html', data)
        elif level5_step_id_string[0:3] == '211' \
                or level5_step_id_string[0:3] == '241' or level5_step_id_string[0:3] == '242' \
                or level5_step_id_string[0:3] == '251' or level5_step_id_string[0:3] == '252' \
                or level5_step_id_string[0:3] == '212' or level5_step_id_string[0:3] == '213':
            return render(request, 'fms/parts/common/level5_step_execution.html', data)
        elif level5_step_id_string[0:3] == '231' or level5_step_id_string[0:3] == '232'\
                or level5_step_id_string[0:3] == '233':
            return render(request, 'fms/parts/common/level5_step_maintenance.html', data)
        else:
            return render(request, 'fms/parts/common/level5_step_top_page.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# アクションボタン表示処理
@require_POST
@login_required
def action_button_display(request):
    from fms.models import NotificationCheck, CheckList
    try:
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        next_department = request.POST['next_department']
        next_division = request.POST['next_division']
        target_table = request.POST['target_table']
        target_id = int(request.POST['target_id'])
        level5_step_id = int(request.POST['level5_step_id'])
        permit_user = request.POST['permit_user']
        target_step_id = int(request.POST['target_step_id'])
        last_operation_step = int(request.POST['last_operation_step'])
        my_department = request.POST['user_department_cd']
        next_person_username = permit_user
        target = request.POST['target']
        target_budget_id = request.POST['target_budget_id']
        start_work_stop_flag = request.POST['start_work_stop_flag']

        # 次部署が自部署の場合のみ、次作業者は承認者を選択
        if my_department != next_department:
            next_person_username = ''

        # 自分の部門CDを取得
        department_data = DepartmentMaster.objects.get(department_cd=my_department)
        my_division = department_data.division_cd

        # 権限情報を取得
        userattribute_data = UserAttribute.objects.get(username=t_username, department=my_department)
        my_authority = userattribute_data.authority

        # 新規登録ではないときの処理
        if target_id != 0:
            # 進捗状況データから現在のstep情報を取得(this_stepに格納)
            if target == 'cs':
                # present_step_data = Progress.objects.get(target_id=target_id, target=target_table, present_step=target_step_id)
                present_step_data = Progress.objects.get(target_id=target_id, target=target, present_step=target_step_id)
            elif target_step_id == 213004001:
                present_step_data = Progress.objects.get(target_id=target_id, target=target)
            elif 233001000 <= target_step_id < 233010000 and target == 'phenomenon':
                # 届出チェックステップは特殊処理
                this_progress_id = int(request.POST["this_progress_id"])
                present_step_data = Progress.objects.get(id=this_progress_id)
            else:
                # present_step_data = Progress.objects.get(target_id=target_id, target=target_table)
                present_step_data = Progress.objects.get(target_id=target_id, target=target, present_step=target_step_id)

            present_step = present_step_data.present_step
            this_step = present_step

            if start_work_stop_flag == "1" and target == "probudgetunit":
                # 原課の部門情報を取得
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                this_step_division = budget_data.budget_main_department.division_cd
                this_step_department = budget_data.budget_main_department.department_cd
                present_step = target_step_id
            else:
                # 現stepの部門情報を取得
                this_step_division = present_step_data.present_division
                this_step_department = present_step_data.present_department
                present_step = present_step_data.present_step

            this_step = present_step

            # 「一時保存」と「差戻」は除き、現在の進捗工程(step)以下のログデータを新しい順に1件のみ抽出
            # log_data = Log.objects.filter(target=target_table, target_id=target_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by('-operation_datetime').all()[0:1]
            log_data = Log.objects.filter(target=target, target_id=target_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by('-operation_datetime').all()[0:1]

            # 1件のみの抽出なので、「for」の意味はなし
            for log_data in log_data:
                # 最終処理のstepを取得
                last_operation_step = log_data.step

        # 新規登録のときの処理
        else:
            # 現在のstep(present_step=this_step)に対象のtarget_step_id(JSからのPOST引数)を代入
            present_step_data = ''
            present_step = target_step_id
            this_step = present_step
            # 最終処理のstepに「0」を代入
            last_operation_step = 0
            # 最終処理の部門に自分の部門を代入
            this_step_division = my_division
            this_step_department = my_department

        # 実行中予算詳細画面のみ特殊処理 targetのステップ番号とは無関係に完了ボタンを表示する
        if level5_step_id == 213000000:
            present_step = 213000000

        # 実行中予算詳細画面(予算繰越)のみ特殊処理
        if level5_step_id == 213009000:
            present_step = 213010000

        # 現在のstep、targetに対する操作設定数を取得
        action_num = StepAction.objects.filter(step_id=present_step, target=target).count()

        # 操作リストを取得 「my_authority」はユーザー権限用
        sql = """ SELECT fms_stepaction.*, fms_actionmaster.status_after_action, fms_actionmaster.action_class, fms_actionmaster.action_name """
        sql = sql + """ FROM fms_stepaction """
        sql = sql + """ LEFT JOIN fms_actionmaster"""
        sql = sql + """ ON fms_stepaction.action_cd = fms_actionmaster.action_cd """
        sql = sql + """ WHERE fms_stepaction.step_id = """ + str(present_step)
        sql = sql + """ AND fms_stepaction.lost_flag = 0"""
        sql = sql + """ AND fms_stepaction.target = '""" + target + """' """
        sql = sql + """ AND fms_actionmaster.action_authority < """ + str(my_authority)
        sql = sql + """ AND fms_actionmaster.lost_flag = 0"""
        sql = sql + """ ORDER BY fms_stepaction.display_order """
        action_list = StepAction.objects.all().raw(sql)

        if not is_edit_budget_step(level5_step_id):
            # 次のstep候補リストを取得
            sql = """ SELECT fms_steprelation.*, fms_stepmaster.step_name """
            sql = sql + """ FROM fms_steprelation """
            sql = sql + """ LEFT JOIN fms_stepmaster ON fms_steprelation.next_step=fms_stepmaster.step_id """
            sql = sql + """ WHERE fms_steprelation.lost_flag=0 and fms_steprelation.step_id=""" + str(present_step)
            sql = sql + """ ORDER BY fms_steprelation.display_order """

            next_step_list = StepRelation.objects.all().raw(sql)

            # 小口届出の所管部署ステップは、他部署の選択禁止
            if not present_step_data == '' and present_step_data.target.startswith('ph_nc_') and present_step_data.present_step == 233002001:
                department_cd_str = present_step_data.target.replace('ph_nc_', '')
                next_person_department_list = DepartmentMaster.objects.filter(department_cd=department_cd_str, lost_flag=0)
                next_department_name = next_person_department_list[0].department_name
                next_department = next_person_department_list[0].department_cd
                next_person_list = get_department_person_list(next_department)
                if len(next_person_list) == 1:
                    next_person_username = next_person_list[0].username

            # CS 「届出CS 承認/確認ステップ」　次作業者情報表示不具合対応 現在のprogressの値をそのまま表示する
            elif level5_step_id == 134001000:
                target_id = CsManage.objects.get(budget_id=int(request.POST['target_budget_id']), lost_flag=0).cs_no
                present_step_data_org = Progress.objects.get(target_id=target_id, target='cs')
                next_person_department_list = DepartmentMaster.objects.filter(division_cd=present_step_data_org.present_division, lost_flag=0)
                next_department_name = next_person_department_list[0].department_name
                next_department = next_person_department_list[0].department_cd
                next_person_list = get_department_person_list(next_department)
                if len(next_person_list) == 1:
                    next_person_username = next_person_list[0].username

            # CS 「追加届出 作成/編集」　次作業者情報表示不具合対応 現在のprogressの値をそのまま表示する
            elif level5_step_id == 135001000 and request.POST['target_budget_id'] != '0':
                target_id = CsManage.objects.filter(budget_id=int(request.POST['target_budget_id']), lost_flag=0).values('cs_no')
                target_id = list(target_id)
                target_id_list = [d.get('cs_no') for d in target_id]
                present_step_data_org = Progress.objects.get(target_id__in=target_id_list, target='cs', present_step__gte=135001000)
                next_person_department_list = DepartmentMaster.objects.filter(division_cd=present_step_data_org.present_division, lost_flag=0)
                next_department_name = next_person_department_list[0].department_name
                next_department = next_person_department_list[0].department_cd
                next_person_list = get_department_person_list(next_department)
                if len(next_person_list) == 1:
                    next_person_username = next_person_list[0].username

            else:
                # 候補リストの先頭のステップの部署リストを取得
                next_step_data = StepMaster.objects.get(step_id=next_step_list[0].next_step, lost_flag=0)
                next_department_data = get_next_department_list(next_step_data.charge_department_class,
                                                                next_step_data.target,
                                                                target_id,
                                                                my_department)
                next_person_department_list = next_department_data['next_departments_list']
                next_department_name = next_department_data['department_name']
                next_department = next_department_data['department_id']
                next_person_list = get_department_person_list(next_department)
                if len(next_person_list) == 1:
                    next_person_username = next_person_list[0].username

        else:
            # 予算基本情報修正ステップのみ特殊処理 現在のprogressの値をそのまま表示する
            present_step_data_org = Progress.objects.get(target_id=int(request.POST['target_budget_id']), target='budget')
            next_step_list = StepMaster.objects.filter(step_id=present_step_data_org.present_step, lost_flag=0)
            next_person_department_list = DepartmentMaster.objects.filter(department_cd=present_step_data_org.present_department, lost_flag=0)
            next_department_name = next_person_department_list[0].department_name
            sql = """SELECT fms_userattribute.* , fms_user.last_name +' '+fms_user.first_name as full_name """
            sql = sql + """ FROM (fms_userattribute """
            sql = sql + """ LEFT JOIN fms_user ON fms_userattribute.username=fms_user.username)"""
            sql = sql + """ WHERE fms_userattribute.lost_flag=0 AND fms_userattribute.department='""" + present_step_data_org.present_department + """' """
            sql = sql + """ AND fms_userattribute.username='""" + present_step_data_org.present_operator + """' """
            sql = sql + """ ORDER BY user_order  """
            next_person_list = UserAttribute.objects.all().raw(sql)
            next_person_username = next_person_list[0].username

        # 対象となる始まりのstepを取得
        start_step_id = level5_step_id
        # 対象となる終わりのstepを設定･･･始まりのstep+1000
        end_step_id = level5_step_id + 1000
        # 現stepが始まりのstepと終わりのstepの間にあれば「pb_display_flag = 1」、それ以外は「pb_display_flag = 0」
        if level5_step_id == 213000000:
            pb_display_flag = 1
        elif level5_step_id == 213009000:
            pb_display_flag = 1
        elif this_step < start_step_id:
            pb_display_flag = 0
        elif this_step > end_step_id:
            pb_display_flag = 0
        else:
            pb_display_flag = 1

        # 新規登録時は「send_back_pb_flag = 0」、それ以外は「send_back_pb_flag = 1」
        if last_operation_step == 0:
            send_back_pb_flag = 0
        else:
            send_back_pb_flag = 1

        # 現stepの部門とログインユーザーの部門が違う場合、「action_num = 0」(＝操作ボタンを表示しない)
        if level5_step_id == 213000000 or level5_step_id == 213009000:
            action_num = action_num
        if this_step_division != my_division:
            action_num = 0
        elif this_step_department != my_department and 134002000 < target_step_id < 134004000:
            action_num = 0
        elif this_step_department != my_department and 135002000 < target_step_id < 135004000:
            action_num = 0

        data = {
            'this_step': this_step,
            'next_person_list': next_person_list,
            'next_department_name': next_department_name,
            'pb_display_flag': pb_display_flag,
            'next_person_username': next_person_username,
            'send_back_pb_flag': send_back_pb_flag,
            'action_list': action_list,
            'action_num': action_num,
            'next_step_list': next_step_list,
            'next_person_department_list': next_person_department_list,
            'next_department': next_department,
            'this_step_division': this_step_division,
            'user_department_cd': my_department,

        }
        return render(request, 'fms/parts/common/action_pb.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# アクションボタン数算出処理
def action_num_count(t_username, department_cd, step_id, target, target_id):

    if step_id == '' or step_id is None:
        int_step_id = 0
    else:
        int_step_id = int(step_id)

    # 自分の部門CDを取得
    department_data = DepartmentMaster.objects.get(department_cd=department_cd)
    my_division = department_data.division_cd

    # 権限情報を取得
    userattribute_data = UserAttribute.objects.get(username=t_username, department=department_cd)
    my_authority = userattribute_data.authority

    if Progress.objects.filter(target_id=target_id, target=target).count() == 1 and target_id != 0:
        present_step_data = Progress.objects.get(target_id=target_id, target=target, present_step=int_step_id)
        present_step = present_step_data.present_step
        # 現stepの部門情報を取得
        this_step_division = present_step_data.present_division
        this_step_department = present_step_data.present_department
    else:
        this_step_division = my_division
        this_step_department = department_cd
        present_step = int_step_id

    # 現在のstep、targetに対する操作設定数を取得
    # action_num = StepAction.objects.filter(step_id=present_step, target=target).count()

    # 操作リストを取得 「my_authority」はユーザー権限用
    sql = """ SELECT fms_stepaction.*, fms_actionmaster.status_after_action, fms_actionmaster.action_class, fms_actionmaster.action_name """
    sql = sql + """ FROM fms_stepaction """
    sql = sql + """ LEFT JOIN fms_actionmaster"""
    sql = sql + """ ON fms_stepaction.action_cd = fms_actionmaster.action_cd """
    sql = sql + """ WHERE fms_stepaction.step_id = """ + str(present_step)
    sql = sql + """ AND fms_stepaction.lost_flag = 0"""
    sql = sql + """ AND fms_stepaction.target = '""" + target + """' """
    sql = sql + """ AND fms_actionmaster.action_authority < """ + str(my_authority)
    sql = sql + """ AND fms_actionmaster.lost_flag = 0"""
    sql = sql + """ ORDER BY fms_stepaction.display_order """
    action_list = StepAction.objects.all().raw(sql)

    action_num = len(action_list)

    # 現stepの部門とログインユーザーの部門が違う場合、「action_num = 0」(＝操作ボタンを表示しない)
    if this_step_division != my_division:
        action_num = 0
    elif this_step_department != department_cd and 134002000 < int_step_id < 134004000:
        action_num = 0
    elif this_step_department != department_cd and 135002000 < int_step_id < 135004000:
        action_num = 0

    return action_num


# ログリスト表示処理
@require_POST
def get_log_lists(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = request.POST['target_id']
        target = request.POST['target']
        log_source = int(request.POST['log_source'])
        target_budget_id = request.POST['target_budget_id']
        this_target = request.POST['this_target']
        log_lists_num = 0

        sql = """ SELECT fms_log.*, fms_stepmaster.step_name, fms_actionmaster.action_name, """
        sql = sql + """ [isk_tools_base].[dbo].[auth_user].first_name, [isk_tools_base].[dbo].[auth_user].last_name, """
        sql = sql + """ fms_targetmaster.target_name """
        sql = sql + """ FROM (((fms_log """
        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_log.step=fms_stepmaster.step_id) """
        sql = sql + """ LEFT JOIN fms_actionmaster ON fms_log.action=fms_actionmaster.action_cd) """
        sql = sql + """ LEFT JOIN [isk_tools_base].[dbo].[auth_user] ON fms_log.operator=[isk_tools_base].[dbo].[auth_user].username) """
        sql = sql + """ LEFT JOIN fms_targetmaster ON fms_log.target=fms_targetmaster.target_cd"""
        # ログリストのソースが「予算単位」か「工事単位」、「届出チェックシート」の場合の処理
        if log_source == 1 or log_source == 2 or log_source == 4 or log_source == 5:
            if target == this_target or log_source == 1:
                # 絞込条件に「target」と「対象のid(予算なら予算id、工事なら工事id)」を追加
                sql = sql + """ WHERE fms_log.target='""" + target + """' AND fms_log.target_id=""" + target_id
                # 「target」が一致し、idが一致するレコード数取得
                log_lists_num = Log.objects.filter(target=target, target_id=target_id).count()
            else:
                first_loop = True
                sql = sql + """ WHERE fms_log.target='""" + target + """'"""
                if target == 'work':
                    target_data_num = Work.objects.filter(work_budget_id=target_budget_id, lost_flag=0).all().count()
                    if target_data_num > 0:
                        target_data = Work.objects.filter(work_budget_id=target_budget_id, lost_flag=0).all()
                        for loop_data in target_data:
                            if first_loop:
                                sql += """ AND (fms_log.target_id=""" + str(loop_data.work_id)
                                first_loop = False
                            else:
                                sql += """ OR fms_log.target_id=""" + str(loop_data.work_id)

                            log_lists_num += Log.objects.filter(target=target, target_id=loop_data.work_id).count()
                        if first_loop == False:
                            sql += """)"""
                elif target == 'prospecificationunit':
                    target_data_num = ProSpecificationUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).all().count()
                    if target_data_num > 0:
                        target_data = ProSpecificationUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).all()
                        for loop_data in target_data:
                            if first_loop:
                                sql += """ AND (fms_log.target_id=""" + str(loop_data.construction_id)
                                first_loop = False
                            else:
                                sql += """ OR fms_log.target_id=""" + str(loop_data.construction_id)

                            log_lists_num += Log.objects.filter(target=target, target_id=loop_data.construction_id).count()
                        if first_loop == False:
                            sql += """)"""
                elif target == 'cs':
                    target_data_num = CsManage.objects.filter(budget_id=target_budget_id, lost_flag=0).all().count()
                    if target_data_num > 0:
                        target_data = CsManage.objects.filter(budget_id=target_budget_id, lost_flag=0).all()
                        for loop_data in target_data:
                            if first_loop:
                                sql += """ AND (fms_log.target_id=""" + str(loop_data.cs_no)
                                first_loop = False
                            else:
                                sql += """ OR fms_log.target_id=""" + str(loop_data.cs_no)

                            log_lists_num += Log.objects.filter(target=target, target_id=loop_data.cs_no).count()
                        if first_loop == False:
                            sql += """)"""
                elif target == 'phenomenon':
                    target_data_num = Phenomenon.objects.filter(phenomenon_id=target_id, lost_flag=0).all().count()
                    if target_data_num > 0:
                        target_data = Phenomenon.objects.filter(phenomenon_id=target_id, lost_flag=0).all()
                        for loop_data in target_data:
                            if first_loop:
                                sql += """ AND (fms_log.target_id=""" + str(loop_data.phenomenon_id)
                                first_loop = False
                            else:
                                sql += """ OR fms_log.target_id=""" + str(loop_data.phenomenon_id)

                            log_lists_num += Log.objects.filter(target=target, target_id=loop_data.phenomenon_id).count()
                        if first_loop == False:
                            sql += """)"""

        # ログリストのソースが「予算+工事単位」の場合の処理
        elif log_source == 3:
            # 絞込条件に、targetがbudgetかworkで、budget_idが該当するbudget_idを追加
            sql = sql + """ WHERE (fms_log.target='budget' OR fms_log.target='work' ) AND fms_log.budget_id=""" + target_id
            # budget_idが該当するbudget_idのレコード数取得
            log_lists_num = Log.objects.filter(budget_id=target_id).count()
        elif log_source == 9:
            # 絞込条件に、budget_idが該当するbudget_idを追加
            sql = sql + """ WHERE fms_log.budget_id=""" + target_id
            # budget_idが該当するbudget_idのレコード数取得
            log_lists_num = Log.objects.filter(budget_id=target_id).count()
        sql = sql + """ ORDER BY fms_log.operation_datetime DESC """

        log_lists = Log.objects.all().raw(sql)

        data = {
            'log_lists': log_lists,
            'log_lists_num': log_lists_num,
        }

        return render(request, 'fms/parts/common/log.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# トップページの部署変更時の処理
@require_POST
@login_required
def change_department(request):
    try:
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得
        department = request.POST['department']

        # 部署、部門、権限、確認者、承認者情報を取得
        user_departments = UserAttribute.objects.get(username=t_username, lost_flag=0, department=department)
        user_division_cd = user_departments.division
        user_department_cd = user_departments.department
        user_authority = user_departments.authority
        confirm_user = user_departments.confirm_username
        permit_user = user_departments.permit_username

        # 部門名を取得
        user_division_data = DivisionMaster.objects.get(division_cd=user_division_cd)
        user_division_name = user_division_data.division_name

        ary = {
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'user_division_name': user_division_name,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次の進捗工程(step)に進む処理
@login_required
@require_POST
def go_next_step(request):
    from fms.views.execution_views import probudget_complete_progress
    from fms.views.budget_views import set_budget_status
    from fms.views.work_views import check_work_estimates_complete
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # 4G長差戻フラグ
        four_department_send_back_flag = 0
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        if request.POST["action"] == "return" and this_step == 134007001:
            next_step = None
            next_person_id = None
            next_person = None
            next_division = None
            next_department = None
            send_buck_target = request.POST.getlist("next_step[]")
            four_department_send_back_flag = 1
        else:
            next_step = int(request.POST["next_step"])
            next_person_id = int(request.POST["next_person_id"])
            next_division = request.POST["next_division"]
            next_department = request.POST["next_department"]
            send_buck_target = []
        target_id = int(request.POST["target_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        action = request.POST["action"]
        comment = request.POST["comment"]
        target = request.POST["target"]
        target_budget_id = int(request.POST["target_budget_id"])
        err_count = 0

        # 次作業者データをユーザー属性マスタから取得
        if UserAttribute.objects.filter(id=next_person_id).count() > 0:
            user_attribute_data = UserAttribute.objects.get(id=next_person_id)
            next_person = user_attribute_data.username
        else:
            next_person = None

        # 担当者未入力時受付不可制限対応
        if target == 'budget':
            budget_progress = Progress.objects.get(target=target, target_id=target_id)
            # 「last_operation_step=133001011」要求仕様検討済、「present_step=133002001」承認済、データなし
            if (budget_progress.present_step == 133002001 or budget_progress.present_step == 132002001) \
                    and PlanningChargePerson.objects.filter(budget_id=target_id, main_charge_flag=1, lost_flag=0).count() == 0:
                ary = {
                    'msg': '担当者を入力してください'
                }
                return JsonResponse(ary)

        # 見積採用可否未入力時完了不可制限対応
        elif target == 'work':
            # 「last_operation_step=133001011」要求仕様検討済、「present_step=133002001」承認済、データなし
            if next_step == 133009904 or next_step == 132009911:
                estimate_list = Estimate.objects.filter(work_id=target_id, lost_flag=0, entry_class='計画', adoption_flag=1).count()
                if estimate_list == 0:
                    ary = {
                        'target_id': 0,
                        'msg': 'いずれかの見積に対して必ず1件、採用状態としてください'
                    }
                    return JsonResponse(ary)
                elif estimate_list > 1:
                    ary = {
                        'target_id': 0,
                        'msg': '採用状態となっている見積が多すぎます 採用状態の見積は1件だけにしてください'
                    }
                    return JsonResponse(ary)

        # 進捗状況に対して「target」と「target_id」で該当するprogress_dataを取得(※注意:上のifとは別判定)
        if target == 'cs' and this_step < 135000000:
            progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=this_step)
        elif target == 'cs' and this_step > 135000000:
            send_data = {
                'operator': operator,
                'this_step': this_step,
                'next_step': next_step,
                'next_person_id': next_person_id,
                'next_division': next_division,
                'next_department': next_department,
                'target_id': target_id,
                'this_department': this_department,
                'this_division': this_division,
                'action': action,
                'comment': comment,
                'target': target,
                'target_budget_id': target_budget_id,
            }
            ary = cs_go_next_step(send_data)

            return JsonResponse(ary)

        # 異常報告は、複数のprogressが平行するため、this_stepで絞り込む
        elif target == 'phenomenon':
            progress_data = Progress.objects.get(target=target, target_id=target_id, present_step=this_step)
        # その他は、target_idのみで絞込
        else:
            progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id)

        # 単年度計画案作成1～単年度予算No付与までのステップ区間は複数の予算IDを同時にステップ移行させる
        # 注意:単年度予算No付与ステップにいる予算は、単独で予算完了に進むため、除外
        if 133005001 <= this_step < 133006031 and next_step != 133005002 and next_step != 133005022 and next_step != 133006002 and next_step != 133006032:
            data = {'target': target,
                    'target_id': target_id,
                    'target_budget_id': target_budget_id,
                    'action': action,
                    'operator': operator,
                    'now': now,
                    'this_step': this_step,
                    'this_department': this_department,
                    'this_division': this_division,
                    'comment': comment,
                    'next_step': next_step,
                    'next_person': next_person,
                    'next_department': next_department,
                    }
            risks_go_next_step(data)
        else:
            # 各項目を設定
            progress_data.present_step = next_step
            # 所管部署承認状態へのstep移行時に次作業者と次部署、次部門を削除
            if next_step is not None and 134003000 <= next_step < 134004000:
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

            # ログデータに新規登録
            Log(target=target, target_id=target_id, action=action, operator=operator, operation_datetime=now,
                step=this_step,
                comment=comment, operator_department=this_department, operator_division=this_division,
                budget_id=target_budget_id).save()

            # probudgetunitの完了時、関連予算がある場合は同時に完了させる
            if target == 'probudgetunit' and next_step == 213003011:
                probudget_complete_progress(request)

            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

        err_count = 0

        # 届出CSでの並列処理に対応するため処理を分岐
        if target == 'cs' and action != 'M_confirm':
            cs_approval_stepmaster_data = StepMaster.objects.get(step_name='届出CS 承認/確認', target='cs')
            cs_ga_confirm_stepmaster_data = StepMaster.objects.get(step_name='総務G確認', target='cs')
            cs_sh_confirm_stepmaster_data = StepMaster.objects.get(step_name='安全衛生G確認', target='cs')
            cs_env_confirm_stepmaster_data = StepMaster.objects.get(step_name='環境G確認', target='cs')
            cs_eng_confirm_stepmaster_data = StepMaster.objects.get(step_name='工務G確認', target='cs')
            cs_ga_stepmaster_data = StepMaster.objects.get(step_name='総務G承認', target='cs')
            cs_sh_stepmaster_data = StepMaster.objects.get(step_name='安全衛生G承認', target='cs')
            cs_env_stepmaster_data = StepMaster.objects.get(step_name='環境G承認', target='cs')
            cs_eng_stepmaster_data = StepMaster.objects.get(step_name='工務G承認', target='cs')
            cs_ga_wait_stepmaster_data = StepMaster.objects.get(step_name='総務G承認状態', target='cs')
            cs_sh_wait_stepmaster_data = StepMaster.objects.get(step_name='安全衛生G承認状態', target='cs')
            cs_env_wait_stepmaster_data = StepMaster.objects.get(step_name='環境G承認状態', target='cs')
            cs_eng_wait_stepmaster_data = StepMaster.objects.get(step_name='工務G承認状態', target='cs')
            cs_order_department_stepmaster_data = StepMaster.objects.get(step_name='原課部長承認', target='cs')
            cs_esh_stepmaster_data = StepMaster.objects.get(step_name='環境安全衛生部長承認', target='cs')
            cs_order_department_approve_confirm_stepmaster_data = StepMaster.objects.get(step_name='原課承認者変更内容確認',
                                                                                        target='cs')
            cs_end_step_stepmaster_data = StepMaster.objects.get(step_name='届出CS 工程完了', target='cs')

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
                            # 4部長の承認が下りたら次ステップへの移行を許可
                            go_next_step = 1

                    except ImportError as exc:
                        err_count = 1

                    # finally:
                        # DBテーブル「fms_progress」のロックを解除
                        # cursor.execute("UNLOCK TABLES", ['fms_progress'])

                # 4GLが承認済みの場合
                if go_next_step == 1:
                    # 原課の情報を取得
                    cs_manage_data = CsManage.objects.get(cs_no=target_id, lost_flag=0)
                    # budget_department_charge_person_name = Budget.objects.get(budget_id=cs_manage_data.budget_id, lost_flag=0).budget_department_charge_person_id
                    budget_division = Budget.objects.get(budget_id=cs_manage_data.budget_id, lost_flag=0).budget_main_department.division_cd

                    # 兼任ユーザ対策処理
                    # work_order_data = UserAttribute.objects.filter(division=budget_division, lost_flag=0).all().order_by('display_order')[0]

                    # work_order_division = work_order_data.division
                    work_order_permit_user_data = UserAttribute.objects.filter(division=budget_division,
                                                                               authority=302, lost_flag=0
                                                                               ).all().order_by('display_order')[0]
                    work_order_permit_username = work_order_permit_user_data.username
                    work_order_division = work_order_permit_user_data.division

                    # 次ステップ(原課部長承認)を作成
                    progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                            present_step=cs_order_department_stepmaster_data.step_id)
                    # 各項目を設定
                    progress_data.present_step = cs_order_department_stepmaster_data.step_id
                    progress_data.present_operator = work_order_permit_username
                    progress_data.last_operation_step = this_step
                    progress_data.present_department = work_order_division
                    progress_data.present_division = work_order_division
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now
                    # 進捗状況のレコードを保存
                    progress_data.save()

                    # # 4部GL承認状態で待機していたstepを入力完了状態にする
                    # 総務
                    # 総務GL承認状態のステップを呼び出し
                    progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                         present_step=cs_ga_wait_stepmaster_data.step_id)

                    # 各項目を設定
                    # progress_data.present_step = cs_ga_wait_stepmaster_data.step_id
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
                    # progress_data.present_step = cs_sh_wait_stepmaster_data.step_id
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
                    # progress_data.present_step = cs_env_wait_stepmaster_data.step_id
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
                    # progress_data.present_step = cs_eng_wait_stepmaster_data.step_id
                    progress_data.present_operator = None
                    progress_data.last_operation_step = this_step
                    progress_data.present_department = None
                    progress_data.present_division = None
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now
                    # 進捗状況のレコードを保存
                    progress_data.save()

            # 各部長承認処理へ分岐
            elif this_step == cs_approval_stepmaster_data.step_id and next_step != this_step:

                # 総務
                # 総務は自動的に移動するため不要
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_ga_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_ga_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_step = cs_ga_confirm_stepmaster_data.step_id
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_ga_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_ga_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 安全衛生
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_sh_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_sh_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_step = cs_sh_confirm_stepmaster_data.step_id
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_sh_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_sh_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 環境
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_env_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_env_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_step = cs_env_confirm_stepmaster_data.step_id
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_env_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_env_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

                # 工務
                progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id,
                                                                        present_step=cs_eng_confirm_stepmaster_data.step_id)
                # 次作業者を抽出
                next_operator = get_next_operator_cs(cs_eng_confirm_stepmaster_data.charge_department_class)

                # 各項目を設定
                progress_data.present_step = cs_eng_confirm_stepmaster_data.step_id
                progress_data.present_operator = next_operator.username
                progress_data.last_operation_step = this_step
                progress_data.present_department = cs_eng_confirm_stepmaster_data.charge_department_class
                progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_eng_confirm_stepmaster_data.charge_department_class,
                                                                              lost_flag=0).division_cd
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

            elif this_step == cs_esh_stepmaster_data.step_id and next_step != this_step:
                # コメントログの確認
                # 対象のチェックシートに関するlogデータ数を取得・・・   取得条件：このチェックシートのログ　　
                #                                                       除外条件：「一時保存」、コメントなし
                log_data_num = Log.objects.filter(target="cs", target_id=target_id,
                                                  step__gt=cs_approval_stepmaster_data.step_id).exclude(
                    action="temporarily_saved").exclude(comment="").count()
                # 差戻処理の時
                if four_department_send_back_flag == 1:
                    cs_env_wait_stepmaster_data = StepMaster.objects.get(step_name='環境G承認状態', target='cs')
                    cs_eng_wait_stepmaster_data = StepMaster.objects.get(step_name='工務G承認状態', target='cs')

                    for send_buck_target in send_buck_target:
                        if send_buck_target == "1":
                            # 総務
                            # 総務部長承認状態のステップを呼び出し
                            progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                                 present_step=cs_ga_wait_stepmaster_data.step_id)
                            # 次作業者を抽出
                            next_operator = get_next_operator_cs(cs_ga_confirm_stepmaster_data.charge_department_class)

                            # 各項目を設定
                            progress_data.present_step = cs_ga_confirm_stepmaster_data.step_id
                            progress_data.present_operator = next_operator.username
                            progress_data.last_operation_step = this_step
                            progress_data.present_department = cs_ga_confirm_stepmaster_data.charge_department_class
                            progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_ga_confirm_stepmaster_data.charge_department_class,
                                                                                          lost_flag=0).division_cd
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now
                            # 進捗状況のレコードを保存
                            progress_data.save()

                        elif send_buck_target == "2":
                            # 安全
                            # 安全部長承認状態のステップを呼び出し
                            progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                                 present_step=cs_sh_wait_stepmaster_data.step_id)
                            # 次作業者を抽出
                            next_operator = get_next_operator_cs(cs_sh_confirm_stepmaster_data.charge_department_class)

                            # 各項目を設定
                            progress_data.present_step = cs_sh_confirm_stepmaster_data.step_id
                            progress_data.present_operator = next_operator.username
                            progress_data.last_operation_step = this_step
                            progress_data.present_department = cs_sh_confirm_stepmaster_data.charge_department_class
                            progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_sh_confirm_stepmaster_data.charge_department_class,
                                                                                          lost_flag=0).division_cd
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now
                            # 進捗状況のレコードを保存
                            progress_data.save()

                        elif send_buck_target == "3":
                            # 環境
                            # 環境部長承認状態のステップを呼び出し
                            progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                                 present_step=cs_env_wait_stepmaster_data.step_id)
                            # 次作業者を抽出
                            next_operator = get_next_operator_cs(cs_env_confirm_stepmaster_data.charge_department_class)

                            # 各項目を設定
                            progress_data.present_step = cs_env_confirm_stepmaster_data.step_id
                            progress_data.present_operator = next_operator.username
                            progress_data.last_operation_step = this_step
                            progress_data.present_department = cs_env_confirm_stepmaster_data.charge_department_class
                            progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_env_confirm_stepmaster_data.charge_department_class,
                                                                                          lost_flag=0).division_cd
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now
                            # 進捗状況のレコードを保存
                            progress_data.save()

                        elif send_buck_target == "4":
                            # 工務
                            # 工務部長承認状態のステップを呼び出し
                            progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                                 present_step=cs_eng_wait_stepmaster_data.step_id)
                            # 次作業者を抽出
                            next_operator = get_next_operator_cs(cs_eng_confirm_stepmaster_data.charge_department_class)

                            # 各項目を設定
                            progress_data.present_step = cs_eng_confirm_stepmaster_data.step_id
                            progress_data.present_operator = next_operator.username
                            progress_data.last_operation_step = this_step
                            progress_data.present_department = cs_eng_confirm_stepmaster_data.charge_department_class
                            progress_data.present_division = DepartmentMaster.objects.get(department_cd=cs_eng_confirm_stepmaster_data.charge_department_class,
                                                                                          lost_flag=0).division_cd
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now
                            # 進捗状況のレコードを保存
                            progress_data.save()

                elif log_data_num > 0:
                    # 環境安全衛生部長承認のステップを呼び出し(念のため)
                    progress_count = Progress.objects.filter(target=target, target_id=target_id,
                                                             present_step=cs_esh_stepmaster_data.step_id).count()
                    if progress_count == 1:
                        progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                             present_step=cs_esh_stepmaster_data.step_id)
                    elif progress_count == 0:
                        # progress_data = Progress.objects.get(target=target, target_id=target_id, present_step=cs_end_step_stepmaster_data.step_id)
                        progress_data = Progress.objects.get(target=target, target_id=target_id, present_step=cs_order_department_approve_confirm_stepmaster_data.step_id)
                    # 次作業者を抽出
                    log_data = Log.objects.filter(target=target, target_id=target_id,
                                                  step=cs_approval_stepmaster_data.step_id
                                                  ).all().order_by('-operation_datetime')[0]
                    # 各項目を設定
                    progress_data.present_step = cs_order_department_approve_confirm_stepmaster_data.step_id
                    progress_data.present_operator = log_data.operator
                    progress_data.last_operation_step = this_step
                    progress_data.present_department = log_data.operator_department
                    progress_data.present_division = log_data.operator_division
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now
                    # 進捗状況のレコードを保存
                    progress_data.save()

                elif log_data_num == 0:

                    # progress_data.present_step = 999999999
                    if 134000000 < this_step <= 134009901:
                        progress_data.present_step = 134009901
                    elif 135000000 < this_step <= 135009901:
                        progress_data.present_step = 135009901
                    progress_data.present_operator = 'end'
                    progress_data.last_operation_step = this_step
                    progress_data.present_department = 'END'
                    progress_data.present_division = 'END'
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now
                    # 進捗状況のレコードを保存
                    progress_data.save()

        # メッセージのためのstep名、アクション名を取得
        step_data = StepMaster.objects.get(step_id=this_step)
        step_name = step_data.step_name
        action_data = ActionMaster.objects.get(action_cd=action)
        action_name = action_data.action_name

        # 進捗通知機能
        step_notice(progress_data)

        if err_count > 0:
            msg = "システムエラー データベースへのアクセスに失敗しました"
        elif action == "complete" or action == "entry" or action == "entry_complete":
            msg = step_name + action_name
        elif action == "permit" or  action == "accept":
            msg = step_name + "完了"
        else:
            msg = step_name + action_name + "完了"

        # 仕様書予算見積完了チェック
        if target == 'work':
            check_result = check_work_estimates_complete(target_id)
        else:
            check_result = ''

        ary = {
            'target_id': target_id,
            'msg': msg,
            'check_result': check_result,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 指定行数まで改行追加
def add_new_line(value, line_count):
    return_value = value
    new_line_list = re.findall(r"(\r\n|\n|\r)", value)

    lines = len(new_line_list)
    if lines < line_count:
        for i in range(line_count - lines):
            return_value += "\n"
    return return_value

# CSV出力処理(画面上から取得の方法に変える？)
@login_required
@require_POST
def print_csv(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        delivery_date_str = ""

        import csv
        # ターゲット
        target = request.POST["target"]
        current_tab = request.POST["current_tab"]
        work_id = request.POST["target_work_id"]
        Fold = ""

        # ターゲットにより振り分け
        if target == "work":
            Fold = "work"

            if Work.objects.filter(work_id=work_id, lost_flag=0).count() < 1:
                print('工事データが保存されていません、一時保存してください')
                data = {
                    'msg': '工事データが保存されていません、一時保存してください',
                    'div_id_name': 'Error',
                }
                return JsonResponse(data)

            work_data = Work.objects.get(work_id=work_id, lost_flag=0)

            # サブタイトル
            sub_title = "予算見積"
            # 予算ID
            budget_id = work_data.work_budget_id
            # リビジョンNO
            rev_no = work_data.work_rev_no
            # 予算NO
            budget_no = Budget.objects.get(budget_id=budget_id, lost_flag=0).budget_no
            # 工事ID
            work_id = work_data.work_id
            # 工事件名
            work_name = work_data.work_name
            # 適用法規
            law_name = ''
            i = 0
            budgetlaw_data = BudgetLaw.objects.filter(budget_id=budget_id, lost_flag=0)
            if len(budgetlaw_data) >= 1:
                for budgetlaw in budgetlaw_data:
                    if i == 0:
                        law_name += budgetlaw.law_name
                    else:
                        law_name += '/' + budgetlaw.law_name
                    # law_name += budgetlaw.law_name + '/'

                    i += 1
            else:
                law_name = '該当なし'
            # 納入/工事場所
            delivery_location = work_data.delivery_location
            # 納入/工事希望日開始・終了
            work_start_date = work_data.work_start_date
            work_end_date = work_data.work_end_date
            # 納期
            work_delivery_date = work_data.work_delivery_date

            # 希望工期FORM
            if work_data.work_start_date is not None and work_data.work_start_date != "":
                work_start_date = work_data.work_start_date
                work_start_date_str = date_to_many_type(work_start_date).str_type_date_slash
            else:
                work_start_date_str = ""
            # 希望工期TO
            if work_data.work_end_date is not None and work_data.work_end_date != "":
                work_end_date = work_data.work_end_date
                work_end_date_str = date_to_many_type(work_end_date).str_type_date_slash
            else:
                work_end_date_str = ""
            # 希望納期
            if work_data.work_delivery_date is not None and work_data.work_delivery_date != "":
                work_delivery_date = work_data.work_delivery_date
                work_delivery_date_str = date_to_many_type(work_delivery_date).str_type_date_slash
            else:
                work_delivery_date_str = ""

            # 納期/工期欄文字列作成
            if work_delivery_date_str != "":
                delivery_date_str = "納期：" + work_delivery_date_str
                if work_start_date_str != "":
                    delivery_date_str = delivery_date_str + "　　　工期：" + work_start_date_str
                    if work_end_date_str != "":
                        delivery_date_str = delivery_date_str + "～" + work_end_date_str
                else:
                    if work_end_date_str != "":
                        delivery_date_str = delivery_date_str + "　　　工期：" + work_end_date_str
            else:
                if work_start_date_str != "":
                    delivery_date_str = delivery_date_str + "工期：" + work_start_date_str
                    if work_end_date_str != "":
                        delivery_date_str = delivery_date_str + "～" + work_end_date_str
                else:
                    if work_end_date_str != "":
                        delivery_date_str = delivery_date_str + "工期：" + work_end_date_str
            # >見積提出先分岐処理挿入
            # 見積提出期日
            estimate_date = date_to_many_type(work_data.work_estimate_limited_date).str_type_date_slash
            # 当社支給機材
            supplies_name = ''
            i = 0
            supplies_data = Supplies.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0)
            if len(supplies_data) >= 1:
                for supplies in supplies_data:
                    if i == 0:
                        supplies_name += supplies.supplies_name
                    else:
                        supplies_name += '/' + supplies.supplies_name

                    # supplies_name += supplies.supplies_name + '/'
                    i += 1
            else:
                supplies_name = '該当なし'

            # 調達担当者
            procurement_person_in_charge = ''

            # 担当者
            if work_data.work_planning_charge_person is None:
                person_in_charge = ''
            else:
                person_in_charge = '工事企画G：' + str(work_data.work_planning_charge_person)

            # 仕様詳細
            inspection_period = ''

            for FreeSpec_num in FreeSpecDetail.objects.filter(work_id=work_id, rev_no=rev_no, entry_class='計画', lost_flag=0):
                FreeSpec_detail = add_new_line(FreeSpec_num.detail, 53)
                inspection_period += FreeSpec_detail.replace("\n", "^@").replace("\r\n", "^@").replace("\r", "^@")
                inspection_period += "^@"

                # 原課名
            department_id = Work.objects.get(work_id=work_id, work_rev_no=rev_no , lost_flag=0).work_order_department_id
            department_name = DepartmentMaster.objects.get(department_cd=department_id).department_name
            # >工場名挿入
            # 機器番号・機器名称
            equip_no = ''
            equip_name = ''
            loop_num = 0
            work_equipment_lists = WorkEquipment.objects.filter(budget_id=budget_id, work_id=work_id, lost_flag=0)
            if work_equipment_lists.count() >= 1:
                for work_equipment_item in work_equipment_lists:
                    if work_equipment_item.equip_no is not None:
                        equip_no += work_equipment_item.equip_no + '/'
                    if work_equipment_item.equip_name is not None:
                        equip_name += work_equipment_item.equip_name + '/'

                    loop_num += 1
                    if loop_num == 2:
                        break

                if work_equipment_lists.count() > loop_num:
                    equip_no += '他' + str(work_equipment_lists.count() - loop_num) + '件'
                    equip_name += '他' + str(work_equipment_lists.count() - loop_num) + '件'

            # 見積提出先
            Estimate_Submission_Destination = '設備管理部 工事企画G'

            # 提出書類
            document_name = ''
            submission_deadline = ''
            number_of_copies = ''

            submissiondocument_data = SubmissionDocument.objects.filter(work_id=work_id, lost_flag=0, entry_class='計画')
            if len(submissiondocument_data) >= 1:
                for submissiondocument in submissiondocument_data:
                    # 書類名
                    document_name += submissiondocument.document_name + '^@'
                    # 提出期限
                    submission_deadline += None_to_blank(submissiondocument.submission_deadline) + '^@'
                    # 部数
                    number_of_copies += str(None_to_blank(submissiondocument.number_of_copies)) + '^@'

        elif target == "prospecificationunit":
            # タブ名「見積依頼」
            Fold = "proestimates"
            prospecificationunit_data = ProSpecificationUnit.objects.get(construction_id=work_id,
                                                                         lost_flag=0)
            # サブタイトル
            sub_title = ""
            # 予算ID
            budget_id = prospecificationunit_data.budget_id
            # リビジョンNO
            rev_no = prospecificationunit_data.rev_no
            # 予算NO
            budget_no = Budget.objects.get(budget_id=budget_id, lost_flag=0).budget_no
            # 工事ID
            work_id = prospecificationunit_data.construction_id
            # 工事件名
            work_name = prospecificationunit_data.work_name
            # 適用法規
            law_name = ''
            i = 0

            worklow_data = WorkLaw.objects.filter(work_id=work_id, entry_class='実行', lost_flag=0)
            if len(worklow_data) >= 1:
                for worklow in worklow_data:
                    if i == 0:
                        law_name += worklow.law_name
                    else:
                        law_name += '/' + worklow.law_name
                    # law_name += worklow.law_name + '/'

                    i += 1
            else:
                law_name = '該当なし'

            # >見積提出先分岐処理挿入
            if ProEstimates.objects.filter(construction_id=work_id, lost_flag=0).count() > 0:

                estimate_data = ProEstimates.objects.get(construction_id=work_id, lost_flag=0)
                # 見積提出期日
                estimate_date = date_to_many_type(estimate_data.estimated_deadline_date).str_type_date_slash

                # 決定納入場所
                delivery_location = estimate_data.fixed_delivery_location
                # 決定工期FORM
                if estimate_data.fixed_delivery_date_from is not None and estimate_data.fixed_delivery_date_from != "":
                    work_start_date = estimate_data.fixed_delivery_date_from
                    work_start_date_str = date_to_many_type(work_start_date).str_type_date_slash
                else:
                    work_start_date_str = ""
                # 決定工期TO
                if estimate_data.fixed_delivery_date_to is not None and estimate_data.fixed_delivery_date_to != "":
                    work_end_date = estimate_data.fixed_delivery_date_to
                    work_end_date_str = date_to_many_type(work_end_date).str_type_date_slash
                else:
                    work_end_date_str = ""
                # 決定納期
                if estimate_data.fixed_delivery_date is not None and estimate_data.fixed_delivery_date != "":
                    work_delivery_date = estimate_data.fixed_delivery_date
                    work_delivery_date_str = date_to_many_type(work_delivery_date).str_type_date_slash
                else:
                    work_delivery_date_str = ""

                # 納期/工期欄文字列作成
                if work_delivery_date_str != "":
                    delivery_date_str = "納期：" + work_delivery_date_str
                    if work_start_date_str != "":
                        delivery_date_str = delivery_date_str + "　　　工期：" + work_start_date_str
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "～" + work_end_date_str
                    else:
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "　　　工期：" + work_end_date_str
                else:
                    if work_start_date_str != "":
                        delivery_date_str = delivery_date_str + "工期：" + work_start_date_str
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "～" + work_end_date_str
                    else:
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "工期：" + work_end_date_str
            else:
                # 見積提出期日
                estimate_date = ""

                # 納入/工事場所
                delivery_location = prospecificationunit_data.delivery_location
                # prospecificationunit_data = ProSpecificationUnit.objects.get(construction_id=request.POST["target_work_id"], lost_flag=0)
                # 納入/工事希望日開始・終了
                # work_start_date = ProSpecificationUnit.objects.get(construction_id=request.POST["target_work_id"], lost_flag=0).desired_construct_period_from
                # work_end_date = ProSpecificationUnit.objects.get(construction_id=request.POST["target_work_id"], lost_flag=0).desired_construct_period_to
                # desired_delivery_date = ProSpecificationUnit.objects.get(construction_id=request.POST["target_work_id"], lost_flag=0).desired_delivery_date

                # 希望工期FORM
                if prospecificationunit_data.desired_construct_period_from is not None and prospecificationunit_data.desired_construct_period_from != "":
                    work_start_date = prospecificationunit_data.desired_construct_period_from
                    work_start_date_str = date_to_many_type(work_start_date).str_type_date_slash
                else:
                    work_start_date_str = ""
                # 希望工期TO
                if prospecificationunit_data.desired_construct_period_to is not None and prospecificationunit_data.desired_construct_period_to != "":
                    work_end_date = prospecificationunit_data.desired_construct_period_to
                    work_end_date_str = date_to_many_type(work_end_date).str_type_date_slash
                else:
                    work_end_date_str = ""
                # 希望納期
                if prospecificationunit_data.desired_delivery_date is not None and prospecificationunit_data.desired_delivery_date != "":
                    work_delivery_date = prospecificationunit_data.desired_delivery_date
                    work_delivery_date_str = date_to_many_type(work_delivery_date).str_type_date_slash
                else:
                    work_delivery_date_str = ""

                # 納期/工期欄文字列作成
                if work_delivery_date_str != "":
                    delivery_date_str = "納期：" + work_delivery_date_str
                    if work_start_date_str != "":
                        delivery_date_str = delivery_date_str + "　　　工期：" + work_start_date_str
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "～" + work_end_date_str
                    else:
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "　　　工期：" + work_end_date_str
                else:
                    if work_start_date_str != "":
                        delivery_date_str = delivery_date_str + "工期：" + work_start_date_str
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "～" + work_end_date_str
                    else:
                        if work_end_date_str != "":
                            delivery_date_str = delivery_date_str + "工期：" + work_end_date_str
                # 納入/工事場所
                work_delivery_date = prospecificationunit_data.desired_delivery_date
            # 当社支給機材
            supplies_name = ''
            i = 0
            supplies_data = Supplies.objects.filter(work_id=request.POST["target_work_id"], entry_class='実行', lost_flag=0)
            if len(supplies_data) >= 1:
                for supplies in supplies_data:
                    if i == 0:
                        supplies_name += supplies.supplies_name
                    else:
                        supplies_name += '/' + supplies.supplies_name
                    # supplies_name += supplies.supplies_name + '/'
                    i += 1
            else:
                supplies_name = '該当なし'

            # 調達担当者
            if prospecificationunit_data.procurement_person_in_charge is None:
                procurement_person_in_charge = ''
            else:
                procurement_person_in_charge_id = prospecificationunit_data.procurement_person_in_charge
                user_data = User.objects.get(username=procurement_person_in_charge_id)
                procurement_person_in_charge = '設備管理部 調達G：' + user_data.last_name + '　' + user_data.first_name

            # 担当者
            if prospecificationunit_data.specification_person_in_charge is None:
                specification_person_in_charge = ''
            else:
                specification_person_in_charge_id = prospecificationunit_data.specification_person_in_charge
                user_data = User.objects.get(username=specification_person_in_charge_id)
                specification_person_in_charge = '工務G：' + user_data.last_name + '　' \
                                                            + user_data.first_name

            # 担当者
            person_in_charge = procurement_person_in_charge + '     ' + specification_person_in_charge

            # 仕様詳細(内容詳細)
            if prospecificationunit_data.contents_detail1 is None:
                inspection_period = ''
            else:
                inspection_period = add_new_line(prospecificationunit_data.contents_detail1, 54)

            if prospecificationunit_data.contents_detail2 is None:
                inspection_period += ''
            else:
                inspection_period += add_new_line(prospecificationunit_data.contents_detail2, 54)

            if prospecificationunit_data.contents_detail3 is None:
                inspection_period += ''
            else:
                inspection_period += add_new_line(prospecificationunit_data.contents_detail3, 54)

            if prospecificationunit_data.contents_detail4 is None:
                inspection_period += ''
            else:
                inspection_period += add_new_line(prospecificationunit_data.contents_detail4, 54)

            if prospecificationunit_data.contents_detail5 is None:
                inspection_period += ''
            else:
                inspection_period += add_new_line(prospecificationunit_data.contents_detail5, 54)

            inspection_period = inspection_period.replace("\r\n", "^@").replace("\n", "^@").replace("\r", "^@")

            # 原課名
            department_id = prospecificationunit_data.department
            department_name = DepartmentMaster.objects.get(department_cd=department_id).department_name

            # >工場名挿入
            # 機器番号・機器名称
            equip_no = ''
            equip_name = ''
            budgetequipment_data = BudgetEquipment.objects.filter(budget_id=budget_id, lost_flag=0)
            if len(budgetequipment_data) >= 1:
                for budgetequipment in budgetequipment_data:
                    if budgetequipment.equip_no is not None:
                        equip_no += budgetequipment.equip_no + '/'
                    if budgetequipment.equip_name is not None:
                        equip_name += budgetequipment.equip_name + '/'

            # 見積提出先
            Estimate_Submission_Destination = '設備管理部 調達G'

            # 提出書類
            document_name = ''
            submission_deadline = ''
            number_of_copies = ''

            submissiondocument_data = SubmissionDocument.objects.filter(work_id=request.POST["target_work_id"],
                                                                        lost_flag=0, entry_class='実行')
            if len(submissiondocument_data) >= 1:
                for submissiondocument in submissiondocument_data:
                    # 書類名
                    document_name += submissiondocument.document_name + '^@'
                    # 提出期限
                    submission_deadline += None_to_blank(submissiondocument.submission_deadline) + '^@'
                    # 部数
                    number_of_copies += str(None_to_blank(submissiondocument.number_of_copies)) + '^@'

        else:
            print('targetが存在しないため保存先がありません target:' + target)

            data = {
                'msg': 'targetが存在しないため保存先がありません',
                'div_id_name': Fold,
            }
            return JsonResponse(data)

        # coding: shift_jis
        # ベースディレクトリ
        if gethostname() == 'YWEBSERV1':  # 本番
            Base_Dir = r'\\Ydomnserv\common\部門間フォルダ\FacilityData\Production'
            Base_SVF = r'\\ssvfserv\system\SVF\PDF\業務管理システム\工事情報管理ツール\工事基本情報.csv'
            SVF_Name = ' Specification '
            # 帳票タグ
            svf_xml1 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\R_仕様書_1.xml', '4'], ['<end>']]
            svf_xml2 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\R_仕様書_2.xml', '4'],
                        ['VrComout=ALNK 2'], ['<end>']]
            svf_xml3 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\R_仕様書_3.xml', '4'], ['<end>']]

        else:
            Base_Dir = r'\\Ydomnserv\common\部門間フォルダ\FacilityData\test'
            Base_SVF = r'\\ssvfserv\system\SVF\PDF\業務管理システム\工事情報管理ツール\TEST\工事基本情報.csv'
            # Base_SVF = r'\\ssvfserv\system\SVF\PDF\業務管理システム\工事情報管理ツール\TEST\tst.csv'
            SVF_Name = ' Specification_TEST '
            # 帳票タグ
            svf_xml1 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\\TEST\R_仕様書_1.xml', '4'], ['<end>']]
            svf_xml2 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\\TEST\R_仕様書_2.xml', '4'],
                        ['VrComout=ALNK 2'], ['<end>']]
            svf_xml3 = [['<start>'], [r'VrSetForm=D:\system\SVF\FORM\業務管理システム\工事情報管理ツール\\TEST\R_仕様書_3.xml', '4'], ['<end>']]

        l = [['サブタイトル', '予算ID', 'REV_NO', '予算NO', '工事ID', '工事件名', '適用法規',
              # '納入/工事場所', '納期', '納入/工事開始希望日', '納入/工事終了希望日', '見積提出先', '見積提出期日',
              '納入/工事場所', '納入/工事開始希望日', '見積提出先', '見積提出期日',
              '当社支給機材', '14担当者', '仕様詳細', '宛先名', '原課名',
              '工場名', '機器番号', '機器名称', '書類名', '提出期限', '部数'],
             [sub_title, budget_id, rev_no, budget_no, work_id, work_name, law_name,
              # delivery_location, work_delivery_date, work_start_date, work_end_date, Estimate_Submission_Destination, estimate_date,
              delivery_location, delivery_date_str, Estimate_Submission_Destination, estimate_date,
              supplies_name, person_in_charge, inspection_period, '石原産業株式会社 四日市工場', department_name,
              delivery_location, equip_no, equip_name, document_name, submission_deadline, number_of_copies]]

        # with open(Base_SVF, 'w', newline="", encoding='shift_jis') as f:
        # csvファイルをcp932(MicrosoftのShift_JISに変換する)
        with open(Base_SVF, 'w', newline="", encoding='cp932') as f:
            # print(f, file=f) .txt出力
            writer = csv.writer(f)
            writer.writerows(svf_xml1)
            writer.writerows(l)
            writer.writerows(svf_xml2)
            writer.writerows(l)
            writer.writerows(svf_xml3)
            writer.writerows(l)

        import subprocess
        import pathlib

        if current_tab != 'execution_specification':
            target_folder = "specification_data"
        else:
            target_folder = "preview_specification_data"
        # プレビュー用にFoldを本仕様書ページに書き換え
            Fold = 'prospecificationunit'

        # 仕様書ファイル名作成
        # TodaysDate = datetime.datetime.today().strftime("%Y%m%d")
        # FolderName = Base_Dir + "\\" + target + "\\" + str(budget_id) + "\\" + str(work_id) + "\\specification_data\\"
        FolderName = Base_Dir + "\\" + target + "\\" + str(budget_id) + "\\" + str(work_id) + "\\" + target_folder + "\\"

        if target == "work":
            PDFName = "Yosan_Shiyousho_" + str(work_id) + ".pdf"
        else:
            if current_tab != 'execution_specification':
                PDFName = "Hon_Shiyousho_" + str(work_id) + ".pdf"
            else:
                PDFName = "Preview_Shiyousho.pdf"

        FullPath = FolderName + PDFName

        # SVF_Name = ' Specification '

        # フォルダが存在しない場合、フォルダを作成する
        if not pathlib.Path(FolderName).exists():
            os.makedirs(FolderName)

        # 指定ファイルが存在する場合、削除
        if pathlib.Path(FullPath).exists():
            subprocess.run('del ' + FullPath, shell=True)

        # UCXSingle実行
        subprocess.run(r"\\ydomnserv\COMMON\部門間フォルダ\FacilityData\TOOL\UCXSingle.exe -h ssvfserv -u -g " + FullPath
                  + SVF_Name + Base_SVF, shell=True)

        # ファイルアップロード機能
        Attach_FolderName = "\\" + target + "\\" + str(budget_id) + "\\" + str(work_id) + '\\'
        attachment_documents_data, created = AttachmentDocuments.objects.get_or_create(file_name=PDFName, folder=Attach_FolderName)
        attachment_documents_data.folder = '\\' + target + '\\' + str(budget_id) + '\\' + str(work_id) + '\\'
        attachment_documents_data.div_id_name = Fold
        attachment_documents_data.data = target_folder
        attachment_documents_data.entry_time = now
        attachment_documents_data.entry_user = request.user.username
        attachment_documents_data.lost_flag = 0
        attachment_documents_data.save()

        msg = '出力完了\nファイル一覧から取り出してください'

        data = {
            # 'budget_id': budget_id,
            # 'budget_no': budget_no,

            # 'work_id': work_id,
            # 'work_name': work_name,
            # 'law_name': law_name,
            # 'delivery_location': delivery_location,
            # 'work_start_date': work_start_date,
            # 'work_end_date': work_end_date,
            # 'estimate_date': estimate_date,
            # 'supplies_name': supplies_name,
            # 'work_order_department_id': department_id,
            # 'equip_no': equip_no,
            # 'equip_name': equip_name,
            'msg': msg,
            'div_id_name': Fold,
            # '': ,
            # '': ,
            # '': ,
            # '': ,
            # '': ,
            # '': ,
            # '': ,
        }
        return JsonResponse(data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次作業者変更処理
@login_required
@require_POST
def push_task(request):
    try:
        hours = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=hours)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        target = request.POST['target']
        target_id = request.POST['target_id']
        action_cd = request.POST['action_cd']
        this_step = request.POST['this_step']
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        target_budget_id = request.POST['target_budget_id']
        username = request.user.username
        comment = request.POST['comment']
        next_person_department = request.POST['next_person_department']
        next_person = request.POST['next_person']

        # 例外用にプログレスが無い場合、複数ある場合メッセージ表示
        if not Progress.objects.filter(target=target, target_id=target_id).count() == 1:
            data = {
                'msg': 'プログレスデータ0件、または複数件登録されています。システム管理者にご連絡ください。'
            }
            return JsonResponse(data)

        # 基本プログレスデータがあるはずの処理で進める
        progress_data = Progress.objects.get(target=target, target_id=target_id)
        progress_data.present_division = DepartmentMaster.objects.get(department_cd=next_person_department, lost_flag=0).division_cd
        progress_data.present_department = next_person_department
        progress_data.present_operator = UserAttribute.objects.get(id=next_person, lost_flag=0).username
        progress_data.save()

        Log(
            target=target,
            target_id=target_id,
            action=action_cd,
            step=this_step,
            operator_division=this_division,
            operator_department=this_department,
            operator=username,
            operation_datetime=now,
            comment=comment,
            budget_id=target_budget_id,
        ).save()

        data = {
            'msg': '次作業者を変更しました'
        }
        return JsonResponse(data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


@login_required
@require_POST
def job_return(request):
    from fms.views.budget_views import set_budget_status
    try:
        DIFF_JST_FROM_UTC = 9

        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        target = request.POST["target"]
        target_id = int(request.POST["target_id"])
        target_budget_id = int(request.POST["target_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        comment = request.POST["comment"]

        progress_target = target
        # 異常報告のprogressは複数作成されるので、ユニークIDで取得しtargetを再設定する
        if target == 'phenomenon':
            target_budget_id = None
            this_progress_id = int(request.POST["this_progress_id"])

            if this_progress_id != 0:
                progress_data = Progress.objects.get(id=this_progress_id)
                progress_target = progress_data.target

            # 差戻マークの判定用に、target情報を残す
            comment = f'{comment}\ntarget:{progress_target}:'

        # 共通関数「common_def_views.py」の「get_return_person」を呼び出し、
        # 「最終処理step」、「最終処理者」、「最終処理部署」、「最終処理部門」を取得
        return_person_data = get_return_person(target, target_id, this_step, operator, progress_target)

        # 取得した「最終処理step」、「最終処理者」、「最終処理部署」、「最終処理部門」を格納
        last_operation_step = return_person_data['last_operation_step']
        last_operator = return_person_data['last_operator']
        last_operator_department = return_person_data['last_operator_department']
        last_operator_division = return_person_data['last_operator_division']

        if last_operator == '':
            msg = "差戻できません、ログデータを確認してください！"
            ary = {
                'msg': msg
            }
            return JsonResponse(ary)

        # 単年度計画案作成1～単年度予算No付与までのステップ区間は複数の予算IDを同時にステップ移行させる
        # 注意:単年度予算No付与ステップにいる予算が差戻になる場合は、同時にステップ移動
        if 133005001 <= this_step <= 133006031:
            risk_send_back(target_budget_id, this_step, operator, return_person_data, comment)
        else:
            # 対象とするProgressを検索し、該当ステップのレコードが無い場合は警告（多重操作防止のため）
            progress_count = Progress.objects.filter(target=progress_target, target_id=target_id, present_step=this_step).count()

            if progress_count != 1:
                msg = "進捗状況が一致しないため差戻できません、多重操作が行われていないか確認してください！"
                ary = {
                    'msg': msg
                }
                return JsonResponse(ary)

            # 進捗状況に対して「target」と「target_id」と「present_step」で該当するものを取得
            progress_data = Progress.objects.get(target=progress_target, target_id=target_id, present_step=this_step)

            # 各項目を設定
            progress_data.present_step = last_operation_step
            progress_data.present_operator = last_operator
            progress_data.last_operation_step = this_step
            progress_data.present_department = last_operator_department
            progress_data.present_division = last_operator_division
            progress_data.last_operator = operator
            progress_data.last_operation_datetime = now
            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            step_notice(progress_data)

            # ログデータに新規登録
            Log(target=target, target_id=target_id, action="return", operator=operator, operation_datetime=now,
                step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
                budget_id=target_budget_id).save()

            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

        msg = "差戻完了！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次作業者変更処理
@login_required
@require_POST
def hold_step(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        target = request.POST['target']
        target_id = request.POST['target_id']
        action_cd = request.POST['action_cd']
        this_step = request.POST['this_step']
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        target_budget_id = request.POST['target_budget_id']
        username = request.user.username
        comment = request.POST['comment']

        Log(
            target=target,
            target_id=target_id,
            action=action_cd,
            step=this_step,
            operator_division=this_division,
            operator_department=this_department,
            operator=username,
            operation_datetime=now,
            comment=comment,
            budget_id=target_budget_id,
        ).save()

        data = {
            'msg': '保留処理を実行しました'
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事情報を表示する基礎画面を表示
@login_required
@require_POST
def detail_template(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target = request.POST['target']
        level5_step_id = int(request.POST['level5_step_id'])

        # budget
        target_budget_id = int(request.POST['budget_id'])

        # 共通
        new_step = int(request.POST['new_step'])    # コピー機能タブからの詳細表示の際は表示用のダミーstepが代入される
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        select_tab = int(request.POST['select_tab'])
        copy_check = int(request.POST['copy_check'])

        # 以下で取得する変数を事前定義、数値は0、文字は空欄
        last_operation_step = 0
        last_operator = ""
        last_operator_department = ""
        last_operator_division = ""
        present_operator = ""
        present_step_id = 0
        ph_nc_progress_id = 0

        if target == 'budget':
            target_unique_budget_id = int(request.POST['budget_unique_id'])
            present_operator = request.POST['present_operator']
            # 新規登録(target_budget_id=0)を判定
            if target_budget_id == 0:
                # 新規登録時処理
                # 新規登録の場合、Lv5の工程IDの「+1」が最初の工程、その工程を指定
                target_step_id = level5_step_id + 1
            else:
                # 更新時処理
                if not is_edit_budget_step(level5_step_id):
                    # 対象データの現在の工程IDを取得
                    progress_data = Progress.objects.get(target='budget', target_id=target_budget_id)
                    # 上の行に変えて下の行を追加検討中・・・2021/01/18 ueda
                    target_step_id = progress_data.present_step
                else:
                    # 予算基本情報修正ステップのみ特殊処理 Progressの情報を使用しない
                    target_step_id = level5_step_id

                target_unique_budget_id = int(request.POST['budget_unique_id'])
                budget_data = Budget.objects.get(id=target_unique_budget_id, lost_flag=0)
                target_budget_id = budget_data.budget_id

            # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
            this_step = target_step_id

            # 更新処理かを判定(対象のIDが「0」でないとき=更新処理）　※IDは予算IDではなく、レコードのID(主キー)
            if target_unique_budget_id != 0:
                # 更新処理
                # 対象の予算レコード取得
                budget_data = Budget.objects.get(id=target_unique_budget_id, lost_flag=0)
                # 予算データののRevNO取得
                # budget_rev_no = budget_data.rev_no
                # 予算テーブルの部署データ取得
                budget_department = budget_data.budget_main_department
                # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
                department_data = DepartmentMaster.objects.get(department_name=budget_department, lost_flag=0)
                # 予算テーブルの部署のコードを取得
                this_department = department_data.department_cd
                # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division

            # 対象のIDが「0」のとき(=新規登録処理)の処理
            else:
                # 新規登録処理
                # budget_department = user_department_cd
                # 予算データのRevNOに「0」を代入
                # budget_rev_no = 0
                # ユーザー部署名を取得
                this_department = user_department_cd
                department_data = DepartmentMaster.objects.get(department_cd=this_department)
                # 部署にユーザー部署名を代入
                budget_department = department_data.department_name
                # 前作業の情報を初期値に設定(数値項目=0、文字項目は空欄)
                last_operation_step = 0
                last_operator = ""
                last_operator_department = ""
                last_operator_division = ""

            # 予算から開くときは、工事主キーID=0
            target_unique_work_id = 0
            target_work_id = 0
            rev_no = 0
            selected_required_function_id = ""
            target_phenomenon_unique_id = 0
            target_phenomenon_id = 0

        elif target == 'work':
            target_unique_work_id = int(request.POST['id'])
            target_work_id = int(request.POST['work_id'])
            present_operator = request.POST['present_operator']
            # 新規登録(target_work_id=0)を判定
            # 新規登録時処理
            if target_unique_work_id == 0:
                # 新規登録の場合、予算の工程を取得
                progress_data = Progress.objects.get(target='budget', target_id=target_budget_id)
                target_step_id = progress_data.present_step
                target_unique_work_id = 0
                # target_work_rev_no = 0
                rev_no = 0
                selected_required_function_id = ""

            # 更新時処理
            else:
                # 対象データの現在の工程IDを取得
                progress_data = Progress.objects.get(target='work', target_id=target_work_id)
                target_step_id = progress_data.present_step
                # target_unique_work_id = target_id
                work_data = Work.objects.get(id=target_unique_work_id)
                rev_no = work_data.work_rev_no
                # work_data.work_required_functionが「Null」のときの処理
                if work_data.work_required_function is None:
                    selected_required_function_id = 0
                # work_required_functionが空欄でないときの処理
                else:
                    work_required_function = work_data.work_required_function
                    sub_no = work_data.sub_no
                    function_data = FunctionMaster.objects.get(function_name=work_required_function, lost_flag=0)
                    function_cd = function_data.function_cd
                    budget_required_function_data = BudgetRequiredFunction.objects.get(budget_id=target_budget_id, required_function=function_cd, sub_no=sub_no, lost_flag=0)
                    selected_required_function_id = budget_required_function_data.id

            # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
            this_step = target_step_id

            # 対象の予算レコード取得
            budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
            # 対象の予算レコードのidを取得
            target_unique_budget_id = budget_data.id

            # 対象の予算レコードの予算idを取得
            target_budget_id = budget_data.budget_id
            # 予算テーブルの部署データ取得
            budget_department = budget_data.budget_main_department
            # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
            department_data = DepartmentMaster.objects.get(department_name=budget_department, lost_flag=0)
            # 予算テーブルの部署のコードを取得
            this_department = department_data.department_cd

            # 対象のIDが「0」でないとき(=更新処理)の処理　※IDは工事IDではなく、レコードのID(主キー)
            if target_unique_work_id != 0:
                # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="work", target_id=target_work_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="work", target_id=target_work_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="work", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division

            else:
                # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division
            target_phenomenon_unique_id = 0
            target_phenomenon_id = 0

        elif target == 'phenomenon':
            target_phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
            target_phenomenon_id = int(request.POST['phenomenon_id'])
            target_budget_id = int(request.POST['phenomenon_id'])
            target_work_id = int(request.POST['phenomenon_id'])
            ph_nc_progress_id = int(request.POST['progress_id'])

            # 新規登録(target_phenomenon_unique_id=0)を判定
            # 新規登録時処理
            if target_phenomenon_unique_id == 0:
                target_step_id = level5_step_id + 1
                target_phenomenon_unique_id = 0
                # target_work_rev_no = 0
                sub_no = ""
                selected_required_function_id = ""
                # ユーザー部署名を取得
                this_department = user_department_cd
                department_data = DepartmentMaster.objects.get(department_cd=this_department)
                # 部署にユーザー部署名を代入
                budget_department = department_data.department_name
            # 更新時処理
            else:
                if Progress.objects.filter(target='phenomenon', target_id=target_phenomenon_id).count() == 1:
                    # 対象データの現在の工程IDを取得
                    progress_data = Progress.objects.get(target='phenomenon', target_id=target_phenomenon_id)
                    # target_step_id = progress_data.present_step
                    target_step_id = int(request.POST['step_id'])
                    # target_unique_work_id = target_id
                    # phenomenon_data = Phenomenon.objects.get(id=target_phenomenon_unique_id, lost_flag=0)
                    measure_data_num = Measure.objects.filter(phenomenon_id=target_phenomenon_id, lost_flag=0).count()
                    if measure_data_num > 0:
                        measure_data = Measure.objects.get(phenomenon_id=target_phenomenon_id, lost_flag=0)
                        # sub_no = phenomenon_data.sub_no
                        # 対応方針テーブルの部署データ取得
                        if measure_data.work_order_charge_department_id is not None:
                            department = measure_data.work_order_charge_department_id
                        else:
                            department = user_department_cd
                    else:
                        department = user_department_cd
                    # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
                    department_data = DepartmentMaster.objects.get(department_cd=department)
                    # 予算テーブルの部署のコードを取得
                    this_department = department_data.department_cd
                    department_data = DepartmentMaster.objects.get(department_cd=this_department)
                    # 部署にユーザー部署名を代入
                    budget_department = department_data.department_name
                else:
                    # 対象データの現在の工程IDを取得
                    progress_data = Progress.objects.filter(target='phenomenon', target_id=target_phenomenon_id).first()
                    # target_step_id = progress_data.present_step
                    target_step_id = int(request.POST['step_id'])
                    # target_unique_work_id = target_id
                    # phenomenon_data = Phenomenon.objects.get(id=target_phenomenon_unique_id, lost_flag=0)
                    measure_data_num = Measure.objects.filter(phenomenon_id=target_phenomenon_id, lost_flag=0).count()
                    if measure_data_num > 0:
                        measure_data = Measure.objects.get(phenomenon_id=target_phenomenon_id, lost_flag=0)
                        # sub_no = phenomenon_data.sub_no
                        # 対応方針テーブルの部署データ取得
                        if measure_data.work_order_charge_department_id is not None:
                            department = measure_data.work_order_charge_department_id
                        else:
                            department = user_department_cd
                    else:
                        department = user_department_cd
                    # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
                    department_data = DepartmentMaster.objects.get(department_cd=department)
                    # 予算テーブルの部署のコードを取得
                    this_department = department_data.department_cd
                    department_data = DepartmentMaster.objects.get(department_cd=this_department)
                    # 部署にユーザー部署名を代入
                    budget_department = department_data.department_name

            # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
            this_step = target_step_id

            # 対象のIDが「0」でないとき(=更新処理)の処理
            if target_phenomenon_unique_id != 0:
                # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division

            else:
                # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="phenomenon", target_id=target_phenomenon_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division

            target_unique_work_id = 0
            target_unique_budget_id = 0
            # target_work_id = 0
            rev_no = 0
            selected_required_function_id = ""

        elif target == 'stop_work' or target == 'before_stop_work':
            target_work_id = int(request.POST['work_id'])
            present_operator = request.POST['present_operator']
            present_step_id = int(request.POST['present_step_id'])
            target_phenomenon_unique_id = 0
            target_phenomenon_id = 0
            # target_step_id

            # 予算データのidを取得
            budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
            org_unique_budget_id = budget_data.id

            # 新規登録課を確認
            progress_data_num = Progress.objects.filter(target='stop_work', target_id=target_work_id).count()

            if progress_data_num == 0:
                progress_data = Progress.objects.get(target='work', target_id=target_work_id)
                # 中止前step確保
                this_step = progress_data.present_step

                # 中止用のstep
                target_step_id = new_step

            else:
                # 更新時処理
                # 対象データの現在の工程IDを取得
                progress_data = Progress.objects.get(target='stop_work', target_id=target_work_id)
                this_step = progress_data.present_step
                target_step_id = progress_data.present_step

            work_data = Work.objects.get(work_id=target_work_id, lost_flag=0)
            target_unique_work_id = work_data.id
            rev_no = work_data.work_rev_no
            # 要求機能が「Null」のときの処理
            if work_data.work_required_function is None:
                selected_required_function_id = 0
            # req_funcが空欄でないときの処理
            else:
                work_required_function = work_data.work_required_function
                sub_no = work_data.sub_no
                function_data = FunctionMaster.objects.get(function_name=work_required_function, lost_flag=0)
                function_cd = function_data.function_cd
                budget_required_function_data = BudgetRequiredFunction.objects.get(budget_id=target_budget_id,
                                                                                   required_function=function_cd,
                                                                                   sub_no=sub_no, lost_flag=0)
                selected_required_function_id = budget_required_function_data.id

            budget_data_num = Budget.objects.filter(budget_id=target_budget_id, lost_flag=0).count()
            # 存在する
            if budget_data_num > 0:
                budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
                # 対象の予算レコードのidを取得
                target_unique_budget_id = budget_data.id

                # 予算テーブルの部署データ取得
                budget_department = budget_data.budget_main_department
            else:
                target_unique_budget_id = ""
                # 予算データの部署データ取得
                budget_department = budget_data.budget_main_department

            this_department = budget_department.department_cd
            budget_department = budget_department.department_name
            department_data = DepartmentMaster.objects.get(department_cd=this_department)
            this_division = department_data.division_cd

            # 対象の予算に関するlogデータ数を取得・・・
            # 取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
            log_data_num = Log.objects.filter(target="stop_work", target_id=target_work_id, step__lte=this_step).exclude(
                action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
            # logデータがあった(過去に対象の予算に操作がされていた)場合
            if log_data_num > 0:
                # 最終処理のlogレコード取得・・・
                # 取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data = Log.objects.filter(target="stop_work", target_id=target_work_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                    '-operation_datetime').all()[0:1]
            else:
                # 最終処理のlogレコード取得・・・
                # 取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                log_data = Log.objects.filter(target="stop_work", target_id=target_budget_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

            # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　
            # ※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
            for log_data in log_data:
                last_operation_step = log_data.step
                last_operator = log_data.operator
                last_operator_department = log_data.operator_department
                last_operator_division = log_data.operator_division

        # 部門情報を取得 ・・・通常処理
        department_data = DepartmentMaster.objects.get(department_cd=this_department)
        this_division = department_data.division_cd
        # 部門情報を取得 ・・・リレーション対応
        department_data = DepartmentMaster.objects.get(department_name=budget_department)

        # 進捗工程名取得
        # step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        next_step_data = StepRelation.objects.filter(step_id=target_step_id, lost_flag=0).order_by('display_order')[0]
        next_step = next_step_data.next_step

        step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)
        # 対処部署分類を取得（依頼部署か特定部署か）
        charge_department_class = convert_charge_department(step_data.charge_department_class, user_department_cd)

        # 対処部署分類が依頼部署の場合、次作業部門、次作業部署に自部門、自部署を代入
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        elif charge_department_class == 'ph_nc':
            progress_unique_id = int(request.POST['progress_id'])
            ph_nc_progress_data = Progress.objects.get(id=progress_unique_id)
            ph_nc_department_cd = ph_nc_progress_data.target.replace('ph_nc_', '')
            next_department = ph_nc_department_cd
            department_data = DepartmentMaster.objects.get(department_cd=ph_nc_department_cd)
            next_division = department_data.division_cd
        # 対処部署分類が特定部署の場合、次作業部署に特定部署を代入
        else:
            next_department = charge_department_class
            department_data = DepartmentMaster.objects.get(department_cd=charge_department_class)
            next_division = department_data.division_cd

        # コピー対象詳細表示ページはステップを変換
        if level5_step_id == 133009902:
            target_step_id = 133009902
        elif level5_step_id == 920000000:
            target_step_id = 133009903

        # 対象のstepで表示するページ情報一覧を取得
        page_lists = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0).order_by('page')
        # 対象のstepで表示するページ数を取得
        page_lists_num = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0).count()
        # 対象のstepでデフォルトで表示するページを取得 # TODO:デフォルトページ番号確認
        default_page = page_lists.get(default_page=1)
        default_tab = default_page.page


        # アクションボタンを表示するタブを取得
        action_pb_page_lists_data_num = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0, action_pb_flag=1).count()
        if action_pb_page_lists_data_num > 0:
            page_lists_data = StepDisplayItem.objects.get(step=target_step_id, lost_flag=0, action_pb_flag=1)
            pb_div_id_name = page_lists_data.div_id_name
        else:
            # アクションボタンは表示しない
            pb_div_id_name = ''

        # アクションボタンの表示タブを指定
        action_sub = "_" + pb_div_id_name

        # タブ数にページ数を設定
        tab_num = page_lists_num

        # step名と使用するtemplateを取得
        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        step_name = step_data.step_name
        template_class = step_data.template_class

        # 該当stepでの対象を指定
        if template_class == "work_base" and target != 'stop_work' and target != 'before_stop_work':
            target = "work"
        elif template_class == "budget_base":
            target = "budget"
        elif template_class == "phenomenon_base":
            target = "phenomenon"

        # 禁止文字リスト取得
        ng_character_list = get_ng_character_list()

        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_id': target_unique_work_id,
            'target_budget_id': target_budget_id,
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
            'target_unique_work_id': target_unique_work_id,
            'target_unique_budget_id': target_unique_budget_id,
            'target_work_id': target_work_id,
            'tab_num': tab_num,
            'target_work_rev_no': rev_no,
            'selected_required_function_id': selected_required_function_id,
            'target': target,
            'default_tab': default_tab,
            'pb_div_id_name': pb_div_id_name,
            'page_lists': page_lists,
            'select_tab': select_tab,
            'target_phenomenon_unique_id': target_phenomenon_unique_id,
            'target_phenomenon_id': target_phenomenon_id,
            'action_sub': action_sub,
            'copy_check': copy_check,
            'present_operator': present_operator,
            'ng_character_list': ng_character_list,
            'ph_nc_progress_id': ph_nc_progress_id,
            # 'function_list': function_list,
            # 'function_amount': function_amount,
        }

        return render(request, 'fms/parts/common/detail_template.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# ''→None変換
def blank_to_None(value):
    return None if value is '' else value


# None→''変換
def None_to_blank(value):
    return '' if value is None else value


# 年月日→'-'変換
def date_to_hyphen(value):
    value_str = value.replace('年', '-')
    value_str = value_str.replace('月', '-')
    return value_str.replace('日', '')


# 'true''false'→True False 変換
def str_to_boolean(value):
    value_str = None_to_blank(value)
    ret_value = True
    if value_str == 'false':
        ret_value = False
    return ret_value


# 金額データに桁区切りを追加
def add_comma_value(value):
    ret_value = None_to_blank(value)
    if ret_value != "":
        ret_value = "{:,}".format(value)

    return ret_value


# 桁区切りの金額を数値に変換(空文字チェック付き)
def comma_to_value(value):
    ret_value = blank_to_None(value)
    if ret_value is not None:
        ret_value = ret_value.replace(',', '')
    return ret_value

