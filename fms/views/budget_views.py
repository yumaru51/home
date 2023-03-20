import shutil

import math
import datetime
import openpyxl
import subprocess
import pathlib
import os
import json
import traceback

# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
from django.db.models import Sum
# formsをインポート
from fms.forms import BudgetEditFormLeft, BudgetEditFormCenter, BudgetEditFormRight


# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction
from fms.models import MPlanBasisMaster, ConstructionPolicyOverview, BudgetConditionRelation
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction
from fms.models import EvaluationCriteriaMaster, EvaluationPointMaster, EvaluationDecisionMaster
from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import BudgetLaw, BudgetEquipment, BudgetRegulation
from fms.models import WorkManagementClassMaster, RegulationMaster
from fms.models import RequiredSpecification, AttachmentDocuments, ProBudgetUnit, ProSpecificationUnit
from fms.models import PlanningChargePerson

from django.db import connection
from gcsystem.models import ItemGroupMaster
from fms.views.common_def_views import convert_charge_department, get_next_target, is_mplan_budget_step, \
    get_budget_name_text
from fms.views.common_def_views import get_template_file_base_path, get_attachment_folder_name
from fms.views.common_views import None_to_blank, blank_to_None, date_to_hyphen
from fms.views.common_def_views import output_log_exception, get_department_person_option_list
from fms.views.common_def_views import is_edit_budget_step
from fms.views.required_spec_views import get_required_specification_rev_no, get_required_specification_no
from fms.views.risks_views import send_data_work, send_data_budget
from fms.views.cs_views import cs_progress_record_append
from django.utils.timezone import make_aware
from fms.views.notice_mail_views import step_notice


# 予算情報を表示する基礎画面を表示
@login_required
@require_POST
def budget_detail(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_budget_id = int(request.POST['budget_unique_id'])
        target_budget_id = int(request.POST['budget_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])

        # 新規登録(target_budget_id=0)を判定
        if target_budget_id == 0:
            # 新規登録時処理
            # 新規登録の場合、Lv5の工程IDの「+1」が最初の工程、その工程を指定
            target_step_id = level5_step_id + 1
        elif not is_edit_budget_step(level5_step_id):
            # 更新時処理
            # 対象データの現在の工程IDを取得
            progress_data = Progress.objects.get(target='budget', target_id=target_budget_id)
            target_step_id = progress_data.present_step
        else:
            # 予算基本情報修正ステップのみ特殊処理  Progressの情報を使用しない
            target_step_id = level5_step_id

        # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
        this_step =target_step_id

        # 以下で取得する変数を事前定義、数値は0、文字は空欄
        last_operation_step = 0
        last_operator = ""
        last_operator_department = ""
        last_operator_division = ""
        # 更新処理かを判定(対象のIDが「0」でないとき=更新処理）　※IDは予算IDではなく、レコードのID(主キー)
        if target_unique_budget_id != 0:
            # 更新処理
            # 対象の予算レコード取得
            budget_data = Budget.objects.get(id=target_unique_budget_id, lost_flag=0)
            # 予算データののRevNO取得
            budget_rev_no = budget_data.rev_no
            # 予算テーブルの部署データ取得
            budget_department = budget_data.budget_main_department
            # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
            department_data = DepartmentMaster.objects.get(department_name=budget_department)
            # 予算テーブルの部署のコードを取得
            this_department = department_data.department_cd
            # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
            log_data_num = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
            # logデータがあった(過去に対象の予算に操作がされていた)場合
            if log_data_num > 0:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by('-operation_datetime').all()[0:1]
            else:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                log_data = Log.objects.filter(target="budget", target_id=target_budget_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

            # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
            for log_data in log_data:
                last_operation_step = log_data.step
                last_operator = log_data.operator
                last_operator_department = log_data.operator_department
                last_operator_division = log_data.operator_division

        # 対象のIDが「0」のとき(=新規登録処理)の処理
        else:
            # 新規登録処理
            budget_department = user_department_cd
            #予算データのRevNOに「0」を代入
            budget_rev_no = 0
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

        # 部門情報を取得 ・・・通常処理
        department_data = DepartmentMaster.objects.get(department_cd=this_department)
        this_division = department_data.division_cd
        # 部門情報を取得 ・・・リレーション対応
        department_data = DepartmentMaster.objects.get(department_name=budget_department)
        # 進捗工程名取得
        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        budget_step_name = step_data.step_name
        # 対処部署分類を取得（依頼部署か特定部署か）
        charge_department_class = convert_charge_department(step_data.charge_department_class)

        # 機能リスト取得
        function_list = FunctionMaster.objects.filter(lost_flag=0).all()
        # 対処部署分類が依頼部署の場合、次作業部門、次作業部署に自部門、自部署を代入
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        # 対処部署分類が特定部署の場合、次作業部署に特定部署を代入
        else:
            next_division = ""
            next_department = charge_department_class

        # 予算から開くときは、工事主キーID=0
        target_unique_work_id = 0

        # タブ数の所得は未搭載　※要検討・・・デバッグ用に仮に8を設定
        tab_num = 11

        target_work_id = 0

        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        template_class = step_data.template_class

        if template_class == "budget_base":
            target = "budget"

        elif template_class == "work_base":
            target = "work"

        # templateに引数を引き渡し
        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_id': target_unique_budget_id,
            'budget_rev_no': budget_rev_no,
            'target_budget_id': target_budget_id,
            'target_step_id': target_step_id,
            't_username': t_username,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'budget_step_name': budget_step_name,
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
            'function_list': function_list,
            'target_unique_work_id': target_unique_work_id,
            # 'function_amount': function_amount,
            'tab_num': tab_num,
            'target_work_id': target_work_id,
            'target_unique_budget_id': target_unique_budget_id,
            'target': target,
        }

        # 使用する「・・・・base.html」を判定
        if template_class == "budget_base":
            # 使用する「budget_base.html」の時の処理
            return render(request, 'fms/parts/budget/budget_detail/budget_base.html', data)

        elif template_class == "work_base":
            # 使用する「work_base.html」の時の処理
            return render(request, 'fms/parts/work/work_detail/work_base.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算情報を詳細画面で表示
@login_required
@require_POST
def budget_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # 本日の年月日を取得し、「年」と「月」に分解後、整数型に変換
        d_today = datetime.date.today()
        d_year = d_today.year
        d_month = d_today.month

        int_d_month = int(d_month)
        int_d_year = int(d_year)

        # 「月」が6月以前なら初期の年を本日の「年」+1、7月以降なら初期の年を本日の「年」+2
        if int_d_month <= 6:
            default_year = int_d_year + 1
        else:
            default_year = int_d_year + 2

        t_username = request.user.username

        # full_name = request.user.get_full_name()

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = int(request.POST['id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        level5_step_id_string = request.POST['level5_step_id']
        target = request.POST['target']
        target_step_id = request.POST['target_step_id']

        # 次のLV14のstep_id・・・2021/01/18 追加検討中　ueda
        # next_level5_step_id = level5_step_id + 1000

        # 新規登録か判定(予算ID=0なら新規)
        # 新規でないときの処理･･･該当の予算データを読み込み
        if target_id > 0:
            budget_data = Budget.objects.get(id=target_id, lost_flag=0)
            # ノーデータ(NULL)の部分は、空欄にするための処理を実施

            if budget_data.budget_no is not None:
                budget_no = budget_data.budget_no
            else:
                budget_no = ""

            if budget_data.relation_budget_id is not None:
                str_relation_budget_id = str(budget_data.relation_budget_id)
            else:
                str_relation_budget_id = ""

            if budget_data.decision_no is not None:
                decision_no = budget_data.decision_no
            else:
                decision_no = ""

            business_year = budget_data.business_year.business_year

            if budget_data.request_name is not None:
                request_name = budget_data.request_name
            else:
                request_name = ""

            if budget_data.budget_name is not None:
                budget_name = budget_data.budget_name
            else:
                budget_name = ""

            start_date = "" if budget_data.start_date is None else budget_data.start_date
            end_date = "" if budget_data.end_date is None else budget_data.end_date
            order_date = "" if budget_data.order_date is None else budget_data.order_date
            delivery_date = "" if budget_data.delivery_date is None else budget_data.delivery_date

            budget_rev_no = budget_data.rev_no
            pre_order_flag = budget_data.pre_order_flag
            asdm_flag = budget_data.asdm_flag
            purpose_class = budget_data.purpose_class.purpose_class_cd

            if budget_data.purpose is not None:
                purpose = budget_data.purpose
            else:
                purpose = ""

            if budget_data.request_detail is not None:
                request_detail = budget_data.request_detail
            else:
                request_detail = ""

            if budget_data.detail is not None:
                detail = budget_data.detail
            else:
                detail = ""

            if budget_data.effect is not None:
                effect = budget_data.effect
            else:
                effect = ""

            if budget_data.influence_for_operation is not None:
                influence_for_operation = budget_data.influence_for_operation
            else:
                influence_for_operation = ""

            if budget_data.influence_for_quality is not None:
                influence_for_quality = budget_data.influence_for_quality
            else:
                influence_for_quality = ""

            if budget_data.remove_assets is not None:
                remove_assets = budget_data.remove_assets
            else:
                remove_assets = ""

            if budget_data.budget_rem is not None:
                rem = budget_data.budget_rem
            else:
                rem = ""

            if budget_data.application_price is not None:
                application_price_raw = budget_data.application_price
                # 3桁区切りの「,」挿入処理
                application_price = "{:,}".format(application_price_raw)
            else:
                application_price = budget_data.application_price

            if budget_data.budget_price is not None:
                budget_price_raw = budget_data.budget_price
                budget_price = "{:,}".format(budget_price_raw)
            else:
                budget_price = budget_data.budget_price

            if budget_data.application_class is not None:
                application_class_name = budget_data.application_class.application_class_name
                application_class = budget_data.application_class.application_class_cd
            else:
                application_class_name = ""
                application_class = ""

            if budget_data.budget_class is not None:
                budget_class_cd = budget_data.budget_class.budget_class_cd
                budget_class_name = budget_data.budget_class.budget_class_name
            else:
                budget_class_cd = ""
                budget_class_name = ""

            if budget_data.period_class is not None:
                period_class_cd = budget_data.period_class.period_class_cd
                period_class_name = budget_data.period_class.period_class_name
            else:
                period_class_cd = ""
                period_class_name = ""

            department_name = budget_data.budget_main_department.department_name
            department = budget_data.budget_main_department.department_cd
            budget_division = budget_data.budget_main_department.division_cd
            budget_id = budget_data.budget_id
            str_budget_id = str(budget_id)
            budget_condition_data = BudgetCondition.objects.get(budget_id=budget_id)
            condition_name = budget_condition_data.budget_condition.condition_name
            budget_condition = budget_condition_data.budget_condition.condition_id
            budget_department_charge_person = budget_data.budget_department_charge_person.username
            budget_department_charge_person_name = budget_data.budget_department_charge_person

            if budget_data.budget_person is not None:
                budget_person_name = budget_data.budget_person
                budget_person = budget_data.budget_person.username
            else:
                budget_person_name = ""
                budget_person = ""

            facility_process = budget_data.facility_process.process_cd
            process_name = budget_data.facility_process.process_name

            if not is_edit_budget_step(level5_step_id):
                # 進捗状況からステップ情報取得
                present_step_data = Progress.objects.get(target_id=budget_id, target='budget')
                present_step = present_step_data.present_step
            else:
                # 予算基本情報修正ステップのみ特殊処理  Progressの情報を使用しない
                present_step = level5_step_id

            step_data = StepMaster.objects.get(step_id=present_step, lost_flag=0)
            step_name = step_data.step_name

            # 主担当部署判定
            charge_department_class = convert_charge_department(step_data.charge_department_class)

            previous_step = step_data.previous_step
            department_data = DepartmentMaster.objects.get(department_cd=department)

            if charge_department_class == 'BD':
                next_division = department_data.division_cd
                next_department = department_data.department_cd
            else:
                next_division = ""
                next_department = charge_department_class

            # 原課担当者
            username = budget_department_charge_person

            # rev_noの古い同じ予算IDのデータの有無を確認
            old_budget_data_num = Budget.objects.filter(budget_id=budget_id, lost_flag=1).count()

            management_class_cd = ''
            if budget_data.management_class_cd is not None:
                management_class_cd = budget_data.management_class_cd
                management_class_data = WorkManagementClassMaster.objects.get(management_class_cd=management_class_cd, lost_flag=0)
                management_class_name = management_class_data.management_class_name
            else:
                management_class_cd = ''
                management_class_name = ''
            process_cd = budget_data.facility_process_id

            no_make_cs_flag = budget_data.no_make_cs_flag

        # 新規の時の処理･･･基本的にはほぼすべての項目空欄
        else:
            budget_data = ""
            str_budget_id = ""
            application_class_name = ""
            budget_class_name = ""
            period_class_name = ""
            department_name = ""
            condition_name = ""
            budget_department_charge_person = ""
            budget_department_charge_person_name = ""
            budget_person = ""
            budget_person_name = ""
            process_name = ""
            step_name = ""
            previous_step = 0
            charge_department_class = "BD"
            application_price = 0
            budget_price = 0
            budget_condition = 11
            budget_no = ""
            str_relation_budget_id = ""
            decision_no = ""
            business_year = default_year
            request_name = ""
            budget_name = ""
            start_date = ""
            end_date = ""
            order_date = ""
            delivery_date = ""
            pre_order_flag = ""
            asdm_flag = ""
            purpose_class = ""
            purpose = ""
            request_detail = ""
            detail = ""
            effect = ""
            influence_for_operation = ""
            influence_for_quality = ""
            remove_assets = ""
            rem = ""
            application_class = ""
            budget_class_cd = ""
            period_class_cd = ""
            facility_process = ""
            budget_rev_no = 0
            present_step = new_step
            next_division = user_division_cd
            next_department = user_department_cd
            old_budget_data_num = 0
            management_class_cd = ""
            management_class_name = ""
            # 部署 兼務があるので先頭の部署を取り出す
            department = UserAttribute.objects.filter(username=request.user.username, lost_flag=0).order_by('display_order').first().department
            # 原課担当者
            username = request.user.username
            process_cd = ""

            no_make_cs_flag = 0

        # 部署リスト
        departmentmaster = DepartmentMaster.objects.filter(lost_flag=0).order_by('display_order')
        departments_list = ''
        for departmentmaster in departmentmaster:
            if departmentmaster.department_cd == department:
                departments_list += '<option value="' + departmentmaster.department_cd + '" selected>' + departmentmaster.department_name + '</option>'
            else:
                departments_list += '<option value="' + departmentmaster.department_cd + '">' + departmentmaster.department_name + '</option>'

        # 原課担当者リスト
        user_list = get_department_person_option_list(department, username)

        # 設備工程
        processmaster = ProcessMaster.objects.filter(department=department, lost_flag=0).order_by('display_order')
        processmaster_list = ''
        for processmaster in processmaster:
            if processmaster.process_cd2 == process_cd:
                processmaster_list += '<option value="' + processmaster.process_cd2 + '" selected>' + processmaster.process_cd + ' : ' + processmaster.process_name + '</option>'
            else:
                processmaster_list += '<option value="' + processmaster.process_cd2 + '">' + processmaster.process_cd + ' : ' + processmaster.process_name + '</option>'
        # 予算状態選択のソースとなるリスト抽出
        budget_condition_list = BudgetConditionMaster.objects.filter(lost_flag=0).all()
        # 年度選択のソースとなるリスト抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1)

        # 申請区分選択のソースとなるリスト抽出
        if level5_step_id_string[0:3] == '136':
            # 追加予算申請ステップでは、通常申請は不可能
            application_class_list = ApplicationClassMaster.objects.filter(lost_flag=0).exclude(application_class_cd=1).order_by('display_order')
            # 追加予算申請側は、注釈に設備管理部表示
            budget_planning_team_name = '設備管理部'
        else:
            # 追加予算申請ステップ以外では、通常申請のみ可能とする
            application_class_list = ApplicationClassMaster.objects.filter(lost_flag=0, application_class_cd=1).all().order_by('display_order')
            # 通常申請側は、注釈に工事企画G表示
            budget_planning_team_name = '工事企画G'

        # 工事区分選択のソースとなるリスト抽出
        budget_class_list = BudgetClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 期区分選択のソースとなるリスト抽出
        period_class_list = PeriodClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 目的区分選択のソースとなるリスト抽出
        purpose_class_list = PurposeClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 管理区分選択の候補の一覧用データ抽出
        management_class_list = WorkManagementClassMaster.objects.filter().all()

        # rev_noの古い同じ予算IDのデータがあれば1つ前のrev_noのレコードを取得(=実際には無効になったレコードのテーブルのidが新しいもの)
        if old_budget_data_num > 0:
            old_budget_data = Budget.objects.filter(budget_id=budget_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_budget_data = ""

        # 定量評価選択用リスト取得
        quantitative_evaluation_dict = get_budget_evaluation_dict()

        # 中期計画策定用データ取得
        mpaln_evaluation_list = EvaluationCriteriaMaster.objects.filter(
            target='budget', criteria_cd='mpaln_evaluation', lost_flag=0).order_by( 'display_order' )

        mplan_basis_list = MPlanBasisMaster.objects.filter(lost_flag=0).order_by('display_order').all()

        data = {
            'budget_data': budget_data,
            'old_budget_data_num': old_budget_data_num,
            'old_budget_data': old_budget_data,
            't_username': t_username,
            'application_class_name': application_class_name,
            'budget_class_name': budget_class_name,
            'period_class_name': period_class_name,
            'department_name': department_name,
            'condition_name': condition_name,
            'budget_department_charge_person': budget_department_charge_person,
            'budget_department_charge_person_name': budget_department_charge_person_name,
            'budget_person': budget_person,
            'budget_person_name': budget_person_name,
            'step_name': step_name,
            'previous_step': previous_step,
            'charge_department_class': charge_department_class,
            'next_division': next_division,
            'next_department': next_department,
            'application_price': application_price,
            'budget_price': budget_price,
            'budget_condition_list': budget_condition_list,
            'business_year_list': business_year_list,
            'application_class_list': application_class_list,
            'budget_class_list': budget_class_list,
            'period_class_list': period_class_list,
            'departments_list': departments_list,
            'processmaster_list': processmaster_list,
            'budget_condition': budget_condition,
            'purpose_class_list': purpose_class_list,
            'budget_id': str_budget_id,
            'budget_no': budget_no,
            'relation_budget_id': str_relation_budget_id,
            'decision_no': decision_no,
            'business_year': business_year,
            'application_class': application_class,
            'budget_class_cd': budget_class_cd,
            'period_class_cd': period_class_cd,
            'facility_process': facility_process,
            'process_name': process_name,
            'request_name': request_name,
            'budget_name': budget_name,
            'start_date': start_date,
            'end_date': end_date,
            'order_date': order_date,
            'delivery_date': delivery_date,
            'pre_order_flag': pre_order_flag,
            'asdm_flag': asdm_flag,
            'purpose_class': purpose_class,
            'purpose': purpose,
            'request_detail': request_detail,
            'detail': detail,
            'effect': effect,
            'influence_for_operation': influence_for_operation,
            'influence_for_quality': influence_for_quality,
            'remove_assets': remove_assets,
            'rem': rem,
            'budget_rev_no': budget_rev_no,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'management_class_list': management_class_list,
            'management_class_cd': management_class_cd,
            'management_class_name': management_class_name,
            'no_make_cs_flag': no_make_cs_flag,
            'user_list': user_list,
            'evaluation_dict': quantitative_evaluation_dict,
            'budget_planning_team_name': budget_planning_team_name,
            'mpaln_evaluation_list': mpaln_evaluation_list,
            'mplan_basis_list': mplan_basis_list,
        }

        # データ編集機能要否判定
        budget_edit_action_num = 0
        edit_flag = 0

        budget_edit_action_num = budget_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                             target_table='budget',
                                                                                             lost_flag=0
                                                                                             ).count()

        if level5_step_id == 133009902:
            budget_edit_action_num = 0

        if target == 'cs':
            budget_edit_action_num = 0

        if budget_edit_action_num > 0:
            edit_flag = 1

        mplan_flag = False
        if budget_data != '' and budget_data.plan_class_id == 'M':
            mplan_flag = True
        if budget_data == '' and level5_step_id_string[0:3] == '132':
            mplan_flag = True

        if edit_flag == 1:
            if mplan_flag:
                return render(request, 'fms/parts/budget/budget_mplan_detail/budget_mplan_edit.html', data)
            else:
                return render(request, 'fms/parts/budget/budget_detail/budget_edit.html', data)
        else:
            if mplan_flag:
                return render(request, 'fms/parts/budget/budget_mplan_detail/budget_mplan_info.html', data)
            else:
                return render(request, 'fms/parts/budget/budget_detail/budget_info.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算定量評価入力用データ取得処理
def get_budget_evaluation_dict():
    import json
    # 重要度リスト取得
    importance_criteria_list = EvaluationCriteriaMaster.objects.filter(
        target='budget', criteria_cd='importance', lost_flag=0).order_by('display_order')

    # 重要度点数リスト生成
    importance_point_list = {}
    for importance_item in importance_criteria_list:
        importance_point_item_list = importance_item.point_set.all().order_by('display_order')
        point_list = []
        for point_item in importance_point_item_list:
            point_list.append([point_item.id, point_item.point_detail, point_item.point])
        importance_point_list[str(importance_item.id)] = point_list

    # 緊急度リスト取得
    urgency_criteria_list = EvaluationCriteriaMaster.objects.filter(
        target='budget', criteria_cd='urgency', lost_flag=0).order_by('display_order')

    # 緊急度点数リスト生成
    urgency_point_list = {}
    for urgency_item in urgency_criteria_list:
        urgency_point_item_list = urgency_item.point_set.all().order_by('display_order')
        point_list = []
        for point_item in urgency_point_item_list:
            point_list.append([point_item.id, point_item.point_detail, point_item.point])
        urgency_point_list[str(urgency_item.id)] = point_list

    # 定量評価判定リスト取得
    decision_list = EvaluationDecisionMaster.objects.filter(
        target='budget', evaluation_cd='importance_urgency', lost_flag=0)
    evaluation_list = {}
    for decision_item in decision_list:
        evaluation_list[str(decision_item.evaluation_point)] = decision_item.decision_rank_detail

    # 配列に格納
    data = [
        importance_criteria_list,
        urgency_criteria_list,
        json.dumps(importance_point_list),
        json.dumps(urgency_point_list),
        json.dumps(evaluation_list)]

    return data


# 予算定量判定取得
def get_budget_evaluation_decision(budget_data):
    ret_decision = ""
    if budget_data is not "" and budget_data.importance_criteria_id is not None:
        evaluation_point = budget_data.importance_point.point * budget_data.urgency_point.point
        decision = EvaluationDecisionMaster.objects.get(
            target='budget', evaluation_cd='importance_urgency', evaluation_point=evaluation_point, lost_flag=0)
        ret_decision = decision
    return ret_decision

# 予算データ一覧
@require_POST
def get_budget_lists(request):
    from .execution_views import get_budget_complete_count
    try:
        # target_id = int(request.POST['budget_id'])
        list_type = int(request.POST['list_type'])
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
        sel_area_manager = request.POST['sel_area_manager']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']
        sel_on_work = request.POST['sel_on_work']
        level5_step_id = int(request.POST['level5_step_id'])
        sel_display_order = request.POST['sel_display_order']
        sel_show_additional_budget = request.POST['sel_show_additional_budget']
        sel_main_charge_person_only = request.POST['sel_main_charge_person_only']
        sel_show_complete_only = request.POST['sel_show_complete_only']
        return_url = request.POST['return_url']
        username = request.user.username
        start_work_stop_flag = int(request.POST['start_work_stop_flag'])
        list_kind = request.POST['list_kind']

        where_str = ""
        where_str1 = ""
        where_str2 = ""
        where_parm1 = []
        where_parm2 = []
        is_mplan_flag = is_mplan_budget_step(level5_step_id)

        # sel_copy_target_plan は予算コピー画面だけpostされる項目、他はNoneとして扱う
        sel_copy_target_plan = request.POST.get('sel_copy_target_plan')

        # 検索条件
        # 計画区分
        where_str += " AND fms_budget.plan_class_id = %s \n"
        if is_mplan_flag:
            if sel_copy_target_plan == 'S':
                where_parm1.append('S')
                where_parm2.append('S')
            else:
                where_parm1.append('M')
                where_parm2.append('M')
        else:
            where_parm1.append('S')
            where_parm2.append('S')

        # 予算状態
        if sel_budget_condition != "":
            where_str += " AND fms_budgetconditionmaster.condition_id = %s \n"
            where_parm1.append(int(sel_budget_condition))
            where_parm2.append(int(sel_budget_condition))
        # 進捗状況
        if sel_step != "":
            if list_type == 1:
                where_str += " AND B.step_id = %s \n"
            else:
                where_str += " AND fms_stepmaster.step_id = %s \n"
            where_parm1.append(int(sel_step))
            where_parm2.append(int(sel_step))
        # 年度
        if sel_business_year != "":
            where_str += " AND fms_budget.business_year_id = %s \n"
            where_parm1.append(int(sel_business_year))
            where_parm2.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            where_str += " AND fms_budget.budget_class_id = %s \n"
            where_parm1.append(int(sel_budget_class))
            where_parm2.append(int(sel_budget_class))

        # 追加予算表示
        if sel_show_additional_budget == 'false':
            where_str += " AND fms_budget.budget_id = fms_budget.relation_budget_id \n"
        #  予算ID
        if sel_budget_id != "":
            where_str += " AND fms_budget.budget_id = %s \n"
            where_parm1.append(int(sel_budget_id))
            where_parm2.append(int(sel_budget_id))

        # 予算NO
        if sel_budget_no != "":
            where_str += " AND fms_budget.budget_no LIKE %s \n"
            where_parm1.append('%' + sel_budget_no + '%')
            where_parm2.append('%' + sel_budget_no + '%')
        # 予算名
        if sel_budget_name != "":
            if is_mplan_flag:
                where_str += " AND fms_budget.request_name LIKE %s \n"
            else:
                where_str += " AND fms_budget.budget_name LIKE %s \n"
            where_parm1.append('%' + sel_budget_name + '%')
            where_parm2.append('%' + sel_budget_name + '%')
        # 部門
        if sel_division != "":
            where_str += " AND fms_departmentmaster.division_cd = %s \n"
            where_parm1.append(sel_division)
            where_parm2.append(sel_division)
        # 部署
        if sel_department != "":
            where_str += " AND fms_departmentmaster.department_cd = %s \n"
            where_parm1.append(sel_department)
            where_parm2.append(sel_department)
        # 行程
        if sel_process != "":
            where_str += " AND fms_budget.facility_process_id = %s \n"
            where_parm1.append(sel_process)
            where_parm2.append(sel_process)
        # エリア管理者
        if sel_area_manager != "" and list_type == 1:
            where_str += " AND fms_probudgetunit.area_person_in_charge = %s \n"
            where_parm1.append(sel_area_manager)
            where_parm2.append(sel_area_manager)

        # list_typeが1の場合、次部門、部署、作業者はprobudgetunit側で絞り込む
        # 次作業部門
        if sel_next_division != "":
            if list_type == 1:
                where_str += " AND A.present_division = %s \n"
            else:
                where_str += " AND fms_progress.present_division = %s \n"
            where_parm1.append(sel_next_division)
            where_parm2.append(sel_next_division)
        # 次作業部署
        if sel_next_department != "":
            if list_type == 1:
                where_str += " AND A.present_department = %s \n"
            else:
                where_str += " AND fms_progress.present_department = %s \n"
            where_parm1.append(sel_next_department)
            where_parm2.append(sel_next_department)

        # 未処理のみ
        if start_work_stop_flag == 1:
            where_str += " AND fms_budget.budget_no is not NULL \n"
        elif sel_on_work == 'true':
            # 予算基本情報修正ステップは、Level3カテゴリ内の全てのステップを表示する
            if is_edit_budget_step(level5_step_id) or level5_step_id == 132000000:
                step_st = math.floor(level5_step_id / 100000) * 100000
                step_ed = step_st + 100000
            elif level5_step_id == 213000000 or level5_step_id == 213009000:
                step_st = 211000000
                step_ed = 211002011
            else:
                step_st = math.floor(level5_step_id / 1000) * 1000
                step_ed = step_st + 1000
            if sel_copy_target_plan == 'S' and level5_step_id == 132001000:
                step_st = step_st + 1000000
                step_ed = step_ed + 1000000

            if list_type == 1:
                where_str += " AND B.step_id > %s \n"
                where_parm1.append(step_st)
                where_parm2.append(step_st)
                where_str += " AND B.step_id < %s \n"
                where_parm1.append(step_ed)
                where_parm2.append(step_ed)
            else:
                where_str += " AND fms_stepmaster.step_id > %s \n"
                where_parm1.append(step_st)
                where_parm2.append(step_st)
                where_str += " AND fms_stepmaster.step_id < %s \n"
                where_parm1.append(step_ed)
                where_parm2.append(step_ed)

        # 次作業者
        if sel_next_parson != "":
            if list_type == 1:
                where_str1 += where_str + " AND A.present_operator = %s \n"
            else:
                where_str1 += where_str + " AND fms_progress.present_operator = %s \n"
            where_str2 = where_str + " AND fms_planningchargeperson.charge_person = %s \n"
            where_parm1.append(sel_next_parson)
            where_parm2.append(sel_next_parson)
        else:
            where_str1 += where_str
            where_str2 += where_str

        if sel_main_charge_person_only == 'true':
            main_charge_person_only_where_str = " AND fms_planningchargeperson.main_charge_flag=1 \n"
            where_str2 += main_charge_person_only_where_str

        # 予算候補リスト取得
        sql = """ SELECT fms_budget.*, fms_user.first_name, fms_user.last_name, fms_user.username, \n"""
        sql = sql + """     fms_stepmaster.step_name, fms_stepmaster.step_id \n"""
        sql = sql + """     ,CASE WHEN fms_budget.budget_no IS NULL THEN '' ELSE fms_budget.budget_no END AS bd_no \n"""
        sql = sql + """     ,fms_budgetconditionmaster.condition_name,fms_departmentmaster.department_name \n"""
        sql = sql + """     ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_budget.entry_datetime, GETDATE()) \n"""
        sql = sql + """                                                 ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END \n"""
        sql = sql + """      AS days_stay \n"""
        sql = sql + """     , CASE WHEN log_2.action = 'return' THEN 1 \n"""
        sql = sql + """     ELSE 0 \n"""
        sql = sql + """     END AS return_flag \n"""

        if list_type == 1:
            sql = sql + """     ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_name END B_step_name \n"""
            sql = sql + """     ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_id END B_step_id \n"""

        sql = sql + """     ,CASE WHEN fms_work.work_budget_id IS NULL THEN '' ELSE '〇' END AS related_work \n"""
        sql = sql + """     ,work_num.data_num \n"""
        sql = sql + """     ,complete_work_num.complete_data_num \n"""
        sql = sql + """     ,CASE WHEN (data_num is not NULL AND data_num != 0) THEN CASE WHEN (complete_data_num is not NULL AND complete_data_num != 0) THEN CONVERT(varchar,complete_data_num) ELSE '0' END + '/' + CONVERT(varchar, data_num) ELSE '' END AS complete_num \n"""
        sql = sql + """ FROM fms_budget \n"""
        sql = sql + """ LEFT JOIN (SELECT   [target_id] \n"""
        sql = sql + """                     ,MAX([operation_datetime]) AS last_operationtime \n"""
        sql = sql + """              FROM [fms].[dbo].[fms_log] \n"""
        sql = sql + """             WHERE [target]='budget' \n"""
        sql = sql + """               AND [action] != 'temporarily_saved' \n"""
        sql = sql + """             group by [target_id] \n"""
        sql = sql + """           ) AS log ON [fms].[dbo].[fms_budget].budget_id=log.target_id \n"""

        if list_type == 1:
            sql = sql + """ RIGHT JOIN fms_probudgetunit ON fms_budget.budget_id=fms_probudgetunit.budget_id AND fms_probudgetunit.lost_flag=0 \n"""
            sql = sql + """ LEFT JOIN fms_progress A ON fms_probudgetunit.budget_id=A.target_id AND A.target='probudgetunit' \n"""
            sql = sql + """ LEFT JOIN fms_stepmaster B ON A.present_step=B.step_id \n"""

        sql = sql + """ LEFT JOIN fms_budgetcondition ON fms_budget.budget_id=fms_budgetcondition.budget_id \n"""
        sql = sql + """ LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id \n"""
        sql = sql + """ LEFT JOIN fms_progress ON fms_budget.budget_id=fms_progress.target_id AND fms_progress.target='budget' \n"""

        if list_type == 1:
            sql = sql + """ LEFT JOIN fms_user ON A.present_operator=fms_user.username \n"""
        else:
            sql = sql + """ LEFT JOIN fms_user ON fms_progress.present_operator=fms_user.username \n"""

        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id \n"""
        sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd \n"""
        sql = sql + """ LEFT JOIN ( SELECT fms_work.work_budget_id \n"""
        sql = sql + """ 				                      from fms_work \n"""
        sql = sql + """ 									 where fms_work.lost_flag = 0 \n"""
        sql = sql + """ 									 group by fms_work.work_budget_id \n"""
        sql = sql + """ 								   ) AS fms_work ON fms_budget.budget_id = fms_work.work_budget_id \n"""
        sql = sql + """ LEFT JOIN ( SELECT  main.*, sub.[action] \n"""
        sql = sql + """             FROM (  SELECT  target_id \n"""
        sql = sql + """                             ,MAX(operation_datetime) AS operation_datetime \n"""
        sql = sql + """                       FROM  [fms].[dbo].[fms_log] \n"""
        sql = sql + """                      WHERE  ([target] = 'budget' OR [target] = 'probudgetunit' ) \n"""
        sql = sql + """                        AND  [action] != 'temporarily_saved' \n"""
        sql = sql + """                   GROUP BY [target_id] """
        sql = sql + """                  ) AS main """
        sql = sql + """             INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime \n"""
        sql = sql + """                                                    AND main.target_id=sub.target_id \n"""
        if list_type == 1:
            sql = sql + """                                                     AND sub.target='probudgetunit' \n"""
        else:
            sql = sql + """                                                     AND sub.target='budget' \n"""

        sql = sql + """             WHERE   main.[operation_datetime] = sub.operation_datetime \n"""
        sql = sql + """           ) AS log_2 ON fms_budget.budget_id = log_2.target_id \n"""
        sql = sql + """ LEFT JOIN (SELECT		COUNT(*) AS data_num \n"""
        sql = sql + """                         ,work_budget_id \n"""
        sql = sql + """              FROM		fms_work \n"""
        sql = sql + """             WHERE		fms_work.lost_flag = 0 \n"""
        if sel_on_work == 'true':
            sql = sql + """             and     (fms_work.cancel_flag = 0 or fms_work.cancel_flag is null) \n"""
        sql = sql + """             group by work_budget_id \n"""
        sql = sql + """           ) AS work_num on fms_work.work_budget_id = work_num.work_budget_id \n"""
        sql = sql + """ LEFT JOIN (SELECT		COUNT(*) AS complete_data_num \n"""
        sql = sql + """                         ,work_budget_id \n"""
        sql = sql + """              FROM		fms_work \n"""
        sql = sql + """            LEFT JOIN    fms_progress AS work_progress on fms_work.work_id = work_progress.target_id \n"""
        sql = sql + """                                                      and work_progress.target = 'work' \n"""
        sql = sql + """            LEFT JOIN    fms_progress AS budget_progress on fms_work.work_budget_id = budget_progress.target_id \n"""
        sql = sql + """                                                        and budget_progress.target = 'budget' \n"""
        sql = sql + """             WHERE		fms_work.lost_flag = 0 \n"""
        if sel_on_work == 'true':
            sql = sql + """             and			(fms_work.cancel_flag = 0 or fms_work.cancel_flag is null) \n"""

        sql = sql + """                 and	( \n"""
        sql = sql + """                   (133004000 <= work_progress.present_step   and work_progress.present_step < 134000000 )  or  \n"""
        sql = sql + """                   (133004000 <= budget_progress.present_step and budget_progress.present_step < 134000000) or  \n"""
        sql = sql + """                   (136004000 <= work_progress.present_step   and work_progress.present_step < 137000000)   or  \n"""
        sql = sql + """                   (136004000 <= budget_progress.present_step and budget_progress.present_step < 137000000) or  \n"""
        sql = sql + """                   (132004000 <= work_progress.present_step   and work_progress.present_step < 133000000)   or  \n"""
        sql = sql + """                   (132004000 <= budget_progress.present_step and budget_progress.present_step < 133000000)     \n"""
        sql = sql + """                     ) \n"""

        sql = sql + """            group by work_budget_id \n"""
        sql = sql + """           ) AS complete_work_num on fms_work.work_budget_id = complete_work_num.work_budget_id \n"""

        sql = sql + """ WHERE fms_budget.lost_flag=0\n"""

        # 予算基本情報修正ステップでは、詳細仕様検討ステップの予算を通常表示する
        if not is_edit_budget_step(level5_step_id) and sel_copy_target_plan is None:
            # step=詳細仕様検討ステップ は担当者毎に一覧を表示するために、上記の抽出から除外
            sql = sql + """ AND fms_progress.present_step <> 133002011\n"""
            sql = sql + """ AND fms_progress.present_step <> 136002011\n"""
            sql = sql + """ AND fms_progress.present_step <> 132002011\n"""

        if where_str1 != "":
            sql += where_str1
        if list_type == 1:
            sql = sql + """ AND B.step_id != 0 \n"""

        # 予算基本情報修正ステップでは、詳細仕様検討ステップの予算を通常表示する
        if not is_edit_budget_step(level5_step_id) and sel_copy_target_plan is None:
            # step=詳細仕様検討ステップ は担当者毎に一覧を表示するために、下記の抽出を「UNION ALL」で結合
            sql = sql + """ \n"""
            sql = sql + """ UNION ALL \n"""
            sql = sql + """     SELECT  fms_budget.*, fms_user.first_name, fms_user.last_name, fms_user.username, \n"""
            sql = sql + """             fms_stepmaster.step_name, fms_stepmaster.step_id  \n"""
            sql = sql + """             ,CASE WHEN fms_budget.budget_no IS NULL THEN '' ELSE fms_budget.budget_no END AS bd_no \n"""
            sql = sql + """             ,fms_budgetconditionmaster.condition_name,fms_departmentmaster.department_name \n"""
            sql = sql + """             ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_budget.entry_datetime, GETDATE()) \n"""
            sql = sql + """                                                         ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) \n"""
            sql = sql + """                                                          END AS days_stay \n"""
            sql = sql + """             , CASE WHEN log_2.action = 'return' THEN 1 \n"""
            sql = sql + """                                                 ELSE 0 \n"""
            sql = sql + """                                                  END AS return_flag \n"""
            if list_type == 1:
                sql = sql + """             ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_name END B_step_name \n"""
                sql = sql + """             ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_id END B_step_id \n"""
            sql = sql + """             ,CASE WHEN fms_work.work_budget_id IS NULL THEN '' ELSE '〇' END AS related_work \n"""
            sql = sql + """             ,work_num.data_num \n"""
            sql = sql + """             ,complete_work_num.complete_data_num \n"""
            sql = sql + """             ,CASE WHEN (data_num is not NULL AND data_num != 0) THEN CASE WHEN (complete_data_num is not NULL AND complete_data_num != 0) THEN CONVERT(varchar,complete_data_num) ELSE '0' END + '/' + CONVERT(varchar, data_num) ELSE '' END AS complete_num \n"""
            sql = sql + """     FROM fms_budget \n"""
            sql = sql + """     LEFT JOIN (SELECT   [target_id] \n"""
            sql = sql + """                         ,MAX([operation_datetime]) AS last_operationtime \n"""
            sql = sql + """                  FROM   [fms].[dbo].[fms_log] \n"""
            sql = sql + """                 WHERE [target]='budget' \n"""
            sql = sql + """                   AND [action] != 'temporarily_saved' \n"""
            sql = sql + """                 group by [target_id] \n"""
            sql = sql + """               ) AS log ON fms_budget.budget_id=log.target_id \n"""
            if list_type == 1:
                sql = sql + """     RIGHT JOIN fms_probudgetunit ON fms_budget.budget_id=fms_probudgetunit.budget_id AND fms_probudgetunit.lost_flag=0 \n"""
                sql = sql + """     LEFT JOIN fms_progress A ON fms_probudgetunit.budget_id=A.target_id AND A.target='probudgetunit' \n"""
                sql = sql + """     LEFT JOIN fms_stepmaster B ON A.present_step=B.step_id \n"""
            sql = sql + """     LEFT JOIN fms_budgetcondition ON fms_budget.budget_id=fms_budgetcondition.budget_id \n"""
            sql = sql + """     LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id \n"""
            sql = sql + """     LEFT JOIN fms_progress ON fms_budget.budget_id=fms_progress.target_id AND fms_progress.target='budget' \n"""

            sql = sql + """     LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id \n"""

            sql = sql + """     LEFT JOIN fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd \n"""
            sql = sql + """     LEFT JOIN fms_planningchargeperson ON fms_budget.budget_id = fms_planningchargeperson.budget_id AND fms_planningchargeperson.lost_flag=0 \n"""  # 2021/03/15修正・・・16日に確認のこと
            sql = sql + """     LEFT JOIN fms_user ON fms_planningchargeperson.charge_person = fms_user.username \n"""
            sql = sql + """     LEFT OUTER JOIN ( SELECT    fms_planningchargeperson.budget_id,fms_planningchargeperson.charge_person, \n"""
            sql = sql + """                                 work_progress.work_planning_charge_person_id,work_progress.work_budget_id \n"""
            sql = sql + """ 				        FROM fms_planningchargeperson \n"""
            sql = sql + """                       LEFT JOIN ( SELECT fms_work.work_planning_charge_person_id,fms_work.work_budget_id \n"""
            sql = sql + """                                     FROM fms_work \n"""
            sql = sql + """                                    WHERE fms_work.lost_flag = 0 \n"""
            sql = sql + """                                 ) AS work_progress ON fms_planningchargeperson.budget_id=work_progress.work_budget_id \n"""
            sql = sql + """                                                   AND fms_planningchargeperson.charge_person=work_progress.work_planning_charge_person_id \n"""
            sql = sql + """                                                   AND fms_planningchargeperson.lost_flag = 0 \n"""
            sql = sql + """ 					  GROUP BY  fms_planningchargeperson.budget_id,fms_planningchargeperson.charge_person,work_progress.work_planning_charge_person_id,work_progress.work_budget_id \n"""
            sql = sql + """ 	                ) AS fms_work ON fms_budget.budget_id = fms_work.work_budget_id \n"""
            sql = sql + """                                  AND fms_planningchargeperson.charge_person=fms_work.charge_person \n"""
            sql = sql + """     LEFT JOIN ( SELECT  main.*, sub.[action] \n"""
            sql = sql + """                   FROM ( SELECT target_id \n"""
            sql = sql + """                                 ,MAX(operation_datetime) AS operation_datetime \n"""
            sql = sql + """                            FROM [fms].[dbo].[fms_log] \n"""
            sql = sql + """                           WHERE ([target] = 'budget' OR [target] = 'probudgetunit' ) \n"""
            sql = sql + """                             AND [action] != 'temporarily_saved' \n"""
            sql = sql + """                          GROUP BY [target_id] \n"""
            sql = sql + """                        ) AS main \n"""
            sql = sql + """                 INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime \n"""
            sql = sql + """                                                        AND main.target_id=sub.target_id \n"""
            if list_type == 1:
                sql = sql + """                                                         AND sub.target='probudgetunit' \n"""
            else:
                sql = sql + """                                                         AND sub.target='budget' \n"""

            sql = sql + """                 WHERE main.[operation_datetime] = sub.operation_datetime \n"""
            sql = sql + """               ) AS log_2 ON fms_budget.budget_id = log_2.target_id \n"""
            sql = sql + """     LEFT JOIN (SELECT		COUNT(*) AS data_num \n"""
            sql = sql + """                             ,work_budget_id \n"""
            sql = sql + """                             ,fms_work.work_planning_charge_person_id \n"""
            sql = sql + """                  FROM		fms_work \n"""
            sql = sql + """                 WHERE		fms_work.lost_flag = 0 \n"""
            if sel_on_work == 'true':
                sql = sql + """                  and		(fms_work.cancel_flag = 0 or fms_work.cancel_flag is null) \n"""
            sql = sql + """                group by work_budget_id,fms_work.work_planning_charge_person_id \n"""
            sql = sql + """               ) AS work_num on fms_work.work_budget_id = work_num.work_budget_id \n"""
            sql = sql + """                            and fms_work.work_planning_charge_person_id = work_num.work_planning_charge_person_id \n"""
            sql = sql + """     LEFT JOIN (SELECT		COUNT(*) AS complete_data_num \n"""
            sql = sql + """                             ,work_budget_id \n"""
            sql = sql + """                             ,fms_work.work_planning_charge_person_id \n"""
            sql = sql + """                  FROM		fms_work \n"""
            sql = sql + """                LEFT JOIN fms_progress AS work_progress on fms_work.work_id = work_progress.target_id \n"""
            sql = sql + """                                                       and work_progress.target = 'work' \n"""
            sql = sql + """                LEFT JOIN fms_progress AS budget_progress on fms_work.work_budget_id = budget_progress.target_id \n"""
            sql = sql + """                                                         and budget_progress.target = 'budget' \n"""
            sql = sql + """                WHERE		fms_work.lost_flag = 0 \n"""
            if sel_on_work == 'true':
                sql = sql + """                 and			(fms_work.cancel_flag = 0 or fms_work.cancel_flag is null) \n"""

            sql = sql + """                 and	( \n"""
            sql = sql + """                   (133004000 <= work_progress.present_step   and work_progress.present_step < 134000000 )  or  \n"""
            sql = sql + """                   (133004000 <= budget_progress.present_step and budget_progress.present_step < 134000000) or  \n"""
            sql = sql + """                   (136004000 <= work_progress.present_step   and work_progress.present_step < 137000000)   or  \n"""
            sql = sql + """                   (136004000 <= budget_progress.present_step and budget_progress.present_step < 137000000) or  \n"""
            sql = sql + """                   (132004000 <= work_progress.present_step   and work_progress.present_step < 133000000)   or  \n"""
            sql = sql + """                   (132004000 <= budget_progress.present_step and budget_progress.present_step < 133000000)     \n"""
            sql = sql + """                     ) \n"""

            sql = sql + """                group by work_budget_id, fms_work.work_planning_charge_person_id, work_progress.present_step,budget_progress.present_step \n"""
            sql = sql + """               ) AS complete_work_num on fms_work.work_budget_id = complete_work_num.work_budget_id \n"""
            sql = sql + """                                     and fms_work.work_planning_charge_person_id = complete_work_num.work_planning_charge_person_id \n"""

            sql = sql + """     WHERE fms_budget.lost_flag = 0 \n"""

            # 「level5_step_id」によってプログレス絞り込みを変更
            if level5_step_id == 132002000:
                sql = sql + """       AND fms_progress.present_step = 132002011\n"""
            elif level5_step_id == 133002000:
                sql = sql + """       AND fms_progress.present_step = 133002011\n"""
            elif level5_step_id == 136002000:
                sql = sql + """       AND fms_progress.present_step = 136002011\n"""
            elif level5_step_id == 133000000:
                sql = sql + """       AND fms_progress.present_step = 133002011\n"""
            else:
                sql = sql + """       AND fms_progress.present_step = 133002011\n"""

            sql = sql + """       AND fms_planningchargeperson.complete_flag=0 \n"""
            sql = sql + """       AND fms_planningchargeperson.lost_flag=0 \n"""

            if where_str2 != "":
                sql += where_str2
            if list_type == 1:
                sql = sql + """     AND B.step_id != 0 \n"""

        # ヒアリング資料出力画面では、工事区分順を優先してソートする
        if level5_step_id == 133000000:
            sql += "    ORDER BY fms_budget.budget_class_id,"
        else:
            sql += "    ORDER BY "

        if sel_display_order == "1":
            sql += "fms_budget.budget_id"
        elif sel_display_order == "2":
            sql += "fms_budget.budget_no"
        elif sel_display_order == "3":
            sql += "days_stay desc"
        else:
            sql += "fms_budget.facility_process_id"

        if len(where_parm1) == 0:
            budget_lists = Budget.objects.all().raw(sql)
        else:
            if not is_edit_budget_step(level5_step_id) and sel_copy_target_plan is None:
                budget_lists = Budget.objects.raw(sql, where_parm1 + where_parm2)
            else:
                budget_lists = Budget.objects.raw(sql, where_parm1)

        budget_lists_num = len(list(budget_lists))

        # 完了可能予算のみ
        if sel_show_complete_only == 'true':
            budget_complete_lists = list()
            for budget_item in budget_lists:
                result = get_budget_complete_count(budget_item.budget_id, budget_item.B_step_id)
                if result[0] == 0 or result[0] == 1:
                    budget_complete_lists.append(budget_item)
            budget_lists = budget_complete_lists
            budget_lists_num = len(list(budget_lists))

        copy_relation_budget_id_flag = 0
        if 136001000 == level5_step_id or 136002000 == level5_step_id or 136004000 == level5_step_id:
            # 追加予算申請側のみ、予算コピータブからの関連予算ID入力を行う
            copy_relation_budget_id_flag = 1

        budget_name_text = get_budget_name_text(level5_step_id)
        data = {
            'budget_lists': budget_lists,
            'budget_lists_num': budget_lists_num,
            'list_kind': list_kind,
            'level5_step_id': level5_step_id,
            'copy_relation_budget_id_flag': copy_relation_budget_id_flag,
            'is_mplan_flag': is_mplan_flag,
            'budget_name_text': budget_name_text,
        }

        # return_urlは呼び出しJS側で指定される
        # budget_filter.html
        # >'fms/parts/budget/budget_lists.html';
        # >'fms/parts/temporary_response/budget_select_lists.html';
        # execution_budget_filter.html
        # >'fms/parts/execution/budget_lists.html'
        # budget_copy_source.html
        # >'fms/parts/work/work_copy_source/work_copy_source_list.html'
        return render(request, return_url, data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算情報登録･更新
@login_required
@require_POST
def budget_entry(request):
    from .construction_policy_overview_views import policy_overview_reset_progress_flag
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
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]

        if request.POST["budget_id"] is not "":
            budget_id = int(request.POST["budget_id"])
        else:
            budget_id = 0

        relation_budget_id_str = request.POST["relation_budget_id"]
        decision_no = request.POST["decision_no"]

        budget_condition_str = request.POST["budget_condition"]
        if budget_condition_str is not "":
            budget_condition = int(budget_condition_str)
            bc = BudgetConditionMaster.objects.get(condition_id=budget_condition, lost_flag=0)
        else:
            bc = BudgetConditionMaster.objects.get(condition_id=11, lost_flag=0)
            budget_condition = 11

        business_year = int(request.POST["business_year"])
        b_y = BusinessYearMaster.objects.get(business_year=business_year, lost_flag=0)

        application_class_str = request.POST["application_class"]
        if application_class_str is not "":
            application_class = int(application_class_str)
        else:
            application_class = 1

        apcl = ApplicationClassMaster.objects.get(application_class_cd=application_class, lost_flag=0)

        budget_class_str = request.POST["budget_class"]
        if budget_class_str is not "":
            budget_class = int(budget_class_str)
            bcls = BudgetClassMaster.objects.get(budget_class_cd=budget_class)
        else:
            bcls = BudgetClassMaster.objects.get(budget_class_cd=3)

        period_class_str = request.POST["period_class"]
        if period_class_str is not "":
            period_class = int(period_class_str)
            pcls = PeriodClassMaster.objects.get(period_class_cd=period_class, lost_flag=0)
        else:
            pcls = PeriodClassMaster.objects.get(period_class_cd=1)

        application_price_str = request.POST["application_price"]
        if application_price_str is not "":
            application_price_str = application_price_str.replace(',', '')
            application_price = int(application_price_str)
        else:
            application_price = 0

        budget_price_str = request.POST["budget_price"]
        if budget_price_str is not "":
            budget_price_str = budget_price_str.replace(',', '')
            budget_price = int(budget_price_str)
        else:
            budget_price = 0

        department = request.POST["department"]
        dpt = DepartmentMaster.objects.get(department_cd=department)
        budget_department_charge_person = request.POST["budget_department_charge_person"]
        budget_department_charge_person_usr = User.objects.get(username=budget_department_charge_person, lost_flag=0)

        budget_person = request.POST["budget_person"]
        if budget_person != "":
            budget_person_usr = User.objects.get(username=budget_person, lost_flag=0)
        else:
            budget_person_usr = None

        process = request.POST["process"]
        prcs = ProcessMaster.objects.get(process_cd2=process, lost_flag=0)
        request_name = request.POST["request_name"]
        budget_name = request.POST["budget_name"]
        start_date_str = request.POST["start_date"]
        start_date_str = start_date_str.replace('年', '-')
        start_date_str = start_date_str.replace('月', '-')
        start_date = start_date_str.replace('日', '')
        end_date_str = request.POST["end_date"]
        end_date_str = end_date_str.replace('年', '-')
        end_date_str = end_date_str.replace('月', '-')
        end_date = end_date_str.replace('日', '')
        order_date_str = request.POST["order_date"]
        order_date_str = order_date_str.replace('年', '-')
        order_date_str = order_date_str.replace('月', '-')
        order_date = order_date_str.replace('日', '')
        delivery_date_str = request.POST["delivery_date"]
        delivery_date_str = delivery_date_str.replace('年', '-')
        delivery_date_str = delivery_date_str.replace('月', '-')
        delivery_date = delivery_date_str.replace('日', '')
        pre_order_flag = request.POST["pre_order_flag"]
        asdm_flag = request.POST["asdm_flag"]
        check_material_flag = request.POST["check_material_flag"]

        purpose_class = request.POST["purpose_class"]
        if purpose_class is not "":
            p_cls = PurposeClassMaster.objects.get(purpose_class_cd=purpose_class, lost_flag=0)
        else:
            p_cls = PurposeClassMaster.objects.get(purpose_class_cd="NON")

        purpose = request.POST["purpose"]
        request_detail = request.POST["request_detail"]
        detail = request.POST["detail"]
        effect = request.POST["effect"]
        influence_for_operation = request.POST["influence_for_operation"]
        influence_for_quality = request.POST["influence_for_quality"]
        remove_assets = request.POST["remove_assets"]
        rem = request.POST["rem"]
        comment = request.POST["comment"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        management_class_cd = request.POST['management_class_cd']
        no_make_cs_flag = int(request.POST['no_make_cs_flag'])

        importance_criteria_id = int(request.POST['importance_eval'])
        importance_point_id = int(request.POST['importance_point'])
        urgency_criteria_id = int(request.POST['urgency_eval'])
        urgency_point_id = int(request.POST['urgency_point'])

        last_plan_id = request.POST['last_plan_id']
        plan_class_id = request.POST['plan_class_id']
        mplan_adjustment_amount = request.POST['mplan_adjustment_amount']


        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 新規登録時の処理
        if budget_id == 0:
            budget_data_num = Budget.objects.all().count()
            # 予算のレコードがない時の処理･･･予算id=1 とする
            if budget_data_num == 0:
                this_budget_id = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                last_budget_data = Budget.objects.all().order_by('-budget_id')[0]
                last_budget_id = last_budget_data.budget_id
                this_budget_id = last_budget_data.budget_id + 1
            # 設定した予算idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            budget_data, created = Budget.objects.get_or_create(budget_id=this_budget_id)
            # 登録の日時、登録者を登録
            budget_data.entry_datetime = now
            budget_data.entry_operator = operator
            # 予算のレコードを保存
            budget_data.save()
            # 登録日時、登録者で予算レコードを抽出
            budget_data = Budget.objects.get(entry_datetime=now, entry_operator=operator)
            # 主キーを取得
            budget_unique_id = budget_data.id
            # 主キーで予算レコードを抽出
            budget_data = Budget.objects.get(id=budget_unique_id)
            # rev_no、作業中FL、中止FL、無効FLに値を代入
            budget_data.rev_no = 0
            budget_data.entry_on_progress_flag = 1
            budget_data.cancel_flag = 0
            budget_data.lost_flag = 0
            # 年度繰り越しフラグを無効
            budget_data.carry_over_flag = 0
            # 単年度計画に設定
            budget_data.plan_class_id = 'S'
            # 予算のレコードを保存
            budget_data.save()

        # 更新時の処理
        else:
            # 予算id(変数)に渡された予算idをセット
            this_budget_id = budget_id
            # 物質情報入力チェック
            if check_material_flag == "有り" and this_step != next_step:
                if BudgetMaterial.objects.filter(budget_id=this_budget_id, lost_flag=0).count() < 1:
                    msg = "物質情報が登録されていません！！\n「物質情報」タブにて取扱物質の情報を登録してください！！"
                    entry_success_flag = 0
                    ary = {
                        'budget_id': this_budget_id,
                        'entry_success_flag': entry_success_flag,
                        'msg': msg,
                    }
                    return JsonResponse(ary)

            # 該当の予算idで作業中FLがONのレコード数をカウント
            on_progress_budget_num = Budget.objects.filter(budget_id=budget_id, entry_on_progress_flag=1).count()
            # 該当の予算idで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = Budget.objects.filter(budget_id=budget_id, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                budget_data = Budget.objects.filter(budget_id=budget_id, entry_on_progress_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = budget_data.rev_no
                # 該当のレコードを無効
                budget_data.lost_flag = 1
                # 年度繰り越しフラグを無効
                budget_data.carry_over_flag = 0
                # 予算のレコードを保存
                budget_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                Budget(budget_id=budget_id, entry_datetime=now, entry_operator=operator).save()
                # 登録日時、登録者で予算レコードを抽出
                budget_data = Budget.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーを取得
                budget_unique_id = budget_data.id
                # 主キーで予算レコードを抽出
                budget_data = Budget.objects.get(id=budget_unique_id)
                # rev_no、作業中FL、無効FLに値を代入
                budget_data.rev_no = latest_rev_no + 1
                budget_data.entry_on_progress_flag = 1
                budget_data.cancel_flag = 0
                budget_data.lost_flag = 0
                # 年度繰り越しフラグを無効
                budget_data.carry_over_flag = 0
                # 予算のレコードを保存
                budget_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                budget_data = Budget.objects.get(budget_id=budget_id, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                budget_unique_id = budget_data.id

        # 関連予算IDを登録
        if (relation_budget_id_str is not "" and not relation_budget_id_str == 'None' and relation_budget_id_str != '0') and (application_class == 3 or application_class == 5):
            relation_budget_id = int(relation_budget_id_str)
        else:
            relation_budget_id = this_budget_id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"
            # 予算基本情報を修正した場合は、entry_on_progress_flagを0にする（リビジョン更新のため）
            if is_edit_budget_step(this_step):
                entry_on_progress_flag_value = 0

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 主キーで予算レコードを抽出
        budget_data = Budget.objects.get(id=budget_unique_id)
        # 各項目の値を設定
        budget_data.relation_budget_id = relation_budget_id
        budget_data.decision_no = decision_no
        budget_data.budget_condition = bc
        budget_data.business_year = b_y
        budget_data.application_class = apcl
        budget_data.budget_class = bcls
        budget_data.period_class = pcls
        budget_data.application_price = application_price
        budget_data.budget_price = budget_price
        budget_data.budget_main_department = dpt
        budget_data.budget_department_charge_person = budget_department_charge_person_usr
        budget_data.budget_person = budget_person_usr
        budget_data.facility_process = prcs
        budget_data.request_name = request_name
        budget_data.budget_name = budget_name
        budget_data.start_date = start_date
        budget_data.end_date = end_date

        if order_date == '':
            budget_data.order_date = None
        else:
            budget_data.order_date = order_date

        if delivery_date == '':
            budget_data.delivery_date = None
        else:
            budget_data.delivery_date = delivery_date

        if pre_order_flag == '':
            budget_data.pre_order_flag = None
        else:
            budget_data.pre_order_flag = pre_order_flag

        budget_data.asdm_flag = asdm_flag
        budget_data.purpose_class = p_cls
        budget_data.purpose = purpose
        budget_data.request_detail = request_detail
        budget_data.detail = detail
        budget_data.effect = effect
        budget_data.influence_for_operation = influence_for_operation
        budget_data.influence_for_quality = influence_for_quality
        budget_data.remove_assets = remove_assets
        budget_data.budget_rem = rem
        budget_data.entry_on_progress_flag = entry_on_progress_flag_value
        budget_data.cancel_flag = 0
        budget_data.update_datetime = now
        budget_data.update_operator = operator
        budget_data.management_class_cd = management_class_cd or None
        budget_data.no_make_cs_flag = no_make_cs_flag
        budget_data.check_material_flag = check_material_flag

        # 定量評価は全て入力か、全て未選択のみ
        if importance_criteria_id != 0:
            budget_data.importance_criteria_id = importance_criteria_id
            budget_data.importance_point_id = importance_point_id
            budget_data.urgency_criteria_id = urgency_criteria_id
            budget_data.urgency_point_id = urgency_point_id
            decision = get_budget_evaluation_decision(budget_data)
            budget_data.decision_rank_detail = decision.decision_rank_detail
        else:
            budget_data.importance_criteria_id = None
            budget_data.importance_point_id = None
            budget_data.urgency_criteria_id = None
            budget_data.urgency_point_id = None
            budget_data.decision_rank_detail = None

        if last_plan_id is not None and last_plan_id != '':
            budget_data.last_plan_id = int(last_plan_id)
        else:
            budget_data.last_plan_id = None

        if mplan_adjustment_amount is not None and mplan_adjustment_amount != '':
            budget_data.mplan_adjustment_amount = int(mplan_adjustment_amount.replace(',', ''))
        else:
            budget_data.mplan_adjustment_amount = None

        budget_data.plan_class_id = 'S'

        # rev_no取得
        budget_rev_no = budget_data.rev_no

        # 年度繰り越しフラグを無効
        budget_data.carry_over_flag = 0

        # 予算のレコードを保存
        budget_data.save()

        # 予算状態データを予算idで抽出･･･あれば抽出、なければ新規登録
        budget_condition_data, created = BudgetCondition.objects.get_or_create(budget_id=this_budget_id)
        # 予算状態を設定
        budget_condition_data.budget_condition = bc
        # 予算状態のレコードを保存
        budget_condition_data.save()

        # ログデータを新規登録
        Log(target='budget', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        # 予算基本情報修正ステップではprogressを更新しない
        if not is_edit_budget_step(this_step):
            # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
            progress_data, created = Progress.objects.get_or_create(target="budget", target_id=this_budget_id)
            # 各項目を設定
            progress_data.present_step = next_step
            progress_data.present_operator = next_person
            progress_data.present_department = next_department
            department_data = DepartmentMaster.objects.get(department_cd=next_department)
            progress_data.present_division = department_data.division_cd

            # 今のstepと次のstepが違う場合の処理･･･追加で項目(最終工程、最終作業者、最終処理日時)に値を設定
            if this_step != next_step:
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()
            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        if this_step != next_step:
            # 取扱物質
            handling_material_list = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=0).all()
            for handling_material_list in handling_material_list:
                handling_material_list.entry_on_progress_flag = 0
                handling_material_list.save()

            # 要求機能?
            budget_required_function_list = BudgetRequiredFunction.objects.filter(budget_id=budget_id, lost_flag=0).all()
            for budget_required_function_list in budget_required_function_list:
                budget_required_function_list.entry_on_progress_flag = 0
                budget_required_function_list.save()

            # 要求機能
            required_specification_list = RequiredSpecification.objects.filter(budget_id=budget_id).all()
            for required_specification_list_item in required_specification_list:
                required_specification_list_item.entry_on_progress_flag = 0
                required_specification_list_item.save()

            # 関係法令
            budget_law_list = BudgetLaw.objects.filter(budget_id=budget_id, lost_flag=0).all()
            for budget_law_list in budget_law_list:
                budget_law_list.entry_on_progress_flag = 0
                budget_law_list.save()

            # 関係機器
            budget_equipment_list = BudgetEquipment.objects.filter(budget_id=budget_id, lost_flag=0).all()
            for budget_equipment_list in budget_equipment_list:
                budget_equipment_list.entry_on_progress_flag = 0
                budget_equipment_list.save()

            # 工事方針概要
            policy_overview_reset_progress_flag(budget_id)

            # 進捗通知機能
            step_notice(progress_data)

        entry_success_flag = 1

        ary = {
            'budget_id': this_budget_id,
            'budget_rev_no': budget_rev_no,
            'msg': msg,
            'target_unique_budget_id': budget_unique_id,
            'entry_success_flag': entry_success_flag,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 中期計画情報登録･更新
@login_required
@require_POST
def budget_mplan_entry(request):
    from .construction_policy_overview_views import policy_overview_reset_progress_flag
    try:
        DIFF_JST_FROM_UTC = 9
        msg = ""
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username

        this_step = int(request.POST['this_step'])
        next_step = int(request.POST['next_step'])
        user_attribute_id = int(request.POST['user_attribute_id'])
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        # 入力情報は連想配列形式で取得
        input_value_array = json.loads(request.POST['input_value_array'])

        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 予算IDの取得（新規登録時は0）
        budget_id_str = blank_to_None(input_value_array['budget_id'])
        if budget_id_str is not None:
            budget_id = int(budget_id_str)
        else:
            budget_id = 0

        # 新規登録時の処理
        if budget_id == 0:
            budget_data_num = Budget.objects.all().count()
            # 予算のレコードがない時の処理･･･予算id=1 とする
            if budget_data_num == 0:
                this_budget_id = 1
            # 予算のレコードがある時の処理･･･最終の予算idを取得し、予算id=最終の予算id+1 とする
            else:
                last_budget_id = Budget.objects.all().order_by('-budget_id').first().budget_id
                this_budget_id = last_budget_id + 1

            budget_data, created = Budget.objects.get_or_create(budget_id=this_budget_id, entry_datetime=now, entry_operator=operator)
            budget_data.save()
            budget_unique_id = budget_data.id
            budget_data.rev_no = 0
            budget_data.entry_on_progress_flag = 1
            budget_data.cancel_flag = 0
            budget_data.lost_flag = 0
            budget_data.carry_over_flag = 0
            # 中期計画に設定
            budget_data.plan_class_id = 'M'
            budget_data.no_make_cs_flag = 1
            budget_data.save()

        # 更新時の処理
        else:
            # 予算id(変数)に渡された予算idをセット
            this_budget_id = budget_id
            # 物質情報入力チェック
            if input_value_array['sel_check_material'] == "有り" and this_step != next_step:
                if BudgetMaterial.objects.filter(budget_id=this_budget_id, lost_flag=0).count() < 1:
                    msg = "物質情報が登録されていません！！\n「物質情報」タブにて取扱物質の情報を登録してください！！"
                    ary = {
                        'budget_id': this_budget_id,
                        'entry_success_flag': 0,
                        'msg': msg,
                    }
                    return JsonResponse(ary)

            # 該当の予算idで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = Budget.objects.filter(budget_id=this_budget_id, entry_on_progress_flag=0).count()

            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 完了FL中最終リビジョン番号を取得する
                budget_data = Budget.objects.filter(budget_id=this_budget_id, entry_on_progress_flag=0).order_by('-id')[0]
                latest_rev_no = budget_data.rev_no
                budget_data.lost_flag = 1
                budget_data.carry_over_flag = 0
                budget_data.save()

            # 完了FLがONの件数が「0」の場合
            else:
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数をカウント
            on_progress_budget_num = Budget.objects.filter(budget_id=this_budget_id, entry_on_progress_flag=1).count()

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                Budget(budget_id=this_budget_id, entry_datetime=now, entry_operator=operator).save()
                budget_data = Budget.objects.get(entry_datetime=now, entry_operator=operator)
                budget_unique_id = budget_data.id
                budget_data = Budget.objects.get(id=budget_unique_id)
                budget_data.rev_no = latest_rev_no + 1
                budget_data.entry_on_progress_flag = 1
                budget_data.cancel_flag = 0
                budget_data.lost_flag = 0
                budget_data.carry_over_flag = 0
                # 中期計画に設定
                budget_data.plan_class_id = 'M'
                budget_data.no_make_cs_flag = 1
                budget_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 最新リビジョンのデータを取得
                budget_data = Budget.objects.filter(budget_id=this_budget_id, entry_on_progress_flag=1, lost_flag=0).order_by('-id')[0]
                budget_unique_id = budget_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"
            # 予算基本情報を修正した場合は、entry_on_progress_flagを0にする（リビジョン更新のため）
            if is_edit_budget_step(this_step):
                entry_on_progress_flag_value = 0

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 主キーで予算レコードを抽出
        budget_data = Budget.objects.get(id=budget_unique_id)
        # 各項目の値を設定
        budget_data.business_year_id = blank_to_None(input_value_array['sel_business_year'])
        budget_data.budget_class_id = blank_to_None(input_value_array['sel_budget_class'])
        budget_data.mplan_desired_amount = blank_to_None(input_value_array['mplan_desired_amount'].replace(',', ''))
        budget_data.mplan_basis_id = blank_to_None(input_value_array['sel_mplan_basis'])
        budget_data.mplan_basis_comment = blank_to_None(input_value_array['mplan_basis_comment'])
        budget_data.mplan_adjustment_amount = blank_to_None(input_value_array['mplan_adjustment_amount'].replace(',', ''))
        budget_data.application_price = blank_to_None(input_value_array['application_price'].replace(',', ''))
        budget_data.budget_price = blank_to_None(input_value_array['budget_price'].replace(',', ''))
        budget_data.budget_main_department_id = blank_to_None(input_value_array['sel_budget_department'])
        budget_data.budget_department_charge_person_id = blank_to_None(input_value_array['sel_budget_department_charge_person'])
        budget_data.budget_person_id = blank_to_None(input_value_array['sel_budget_person'])
        budget_data.facility_process_id = blank_to_None(input_value_array['sel_process'])
        budget_data.request_name = blank_to_None(input_value_array['request_name'])
        budget_data.start_date = blank_to_None(date_to_hyphen(input_value_array['start_date']))
        budget_data.end_date = blank_to_None(date_to_hyphen(input_value_array['end_date']))
        budget_data.delivery_date = blank_to_None(date_to_hyphen(input_value_array['delivery_date']))
        budget_data.asdm_flag = blank_to_None(input_value_array['sel_asdm_flag'])
        budget_data.mpaln_evaluation_id = blank_to_None(input_value_array['sel_mpaln_evaluation'])
        budget_data.purpose = blank_to_None(input_value_array['purpose'])
        budget_data.request_detail = blank_to_None(input_value_array['request_detail'])
        budget_data.mplan_concerns = blank_to_None(input_value_array['mplan_concerns'])
        budget_data.effect = blank_to_None(input_value_array['effect'])
        budget_data.influence_for_operation = blank_to_None(input_value_array['influence_for_operation'])
        budget_data.influence_for_quality = blank_to_None(input_value_array['influence_for_quality'])
        budget_data.remove_assets = blank_to_None(input_value_array['remove_assets'])
        budget_data.budget_rem = blank_to_None(input_value_array['rem'])
        budget_data.entry_on_progress_flag = entry_on_progress_flag_value
        budget_data.cancel_flag = 0
        budget_data.update_datetime = now
        budget_data.update_operator = operator
        budget_data.relation_budget_id = this_budget_id
        budget_data.application_class_id = 1
        budget_data.check_material_flag = input_value_array['sel_check_material']
        purpose_class = blank_to_None(input_value_array['sel_purpose_class'])
        if purpose_class is not None:
            budget_data.purpose_class = PurposeClassMaster.objects.get(purpose_class_cd=purpose_class, lost_flag=0)
        else:
            budget_data.purpose_class = PurposeClassMaster.objects.get(purpose_class_cd="NON")

        # rev_no取得
        budget_rev_no = budget_data.rev_no

        # 予算のレコードを保存
        budget_data.save()

        # 予算状態データを予算idで抽出･･･あれば抽出、なければ新規登録
        budget_condition_data, created = BudgetCondition.objects.get_or_create(budget_id=this_budget_id)
        sel_budget_condition = blank_to_None(input_value_array['sel_budget_condition'])
        if sel_budget_condition is not None:
            budget_condition_data.budget_condition_id = int(sel_budget_condition)
        else:
            budget_condition_data.budget_condition_id = None
        budget_condition_data.save()

        # ログデータを新規登録
        Log(target='budget', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=request.POST['comment'], operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        # 予算基本情報修正ステップではprogressを更新しない
        if not is_edit_budget_step(this_step):
            # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
            progress_data, created = Progress.objects.get_or_create(target="budget", target_id=this_budget_id)
            # 各項目を設定
            progress_data.present_step = next_step
            progress_data.present_operator = next_person
            progress_data.present_department = next_department
            department_data = DepartmentMaster.objects.get(department_cd=next_department)
            progress_data.present_division = department_data.division_cd

            # 今のstepと次のstepが違う場合の処理･･･追加で項目(最終工程、最終作業者、最終処理日時)に値を設定
            if this_step != next_step:
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()
            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        if this_step != next_step:
            # 取扱物質
            handling_material_list = BudgetMaterial.objects.filter(budget_id=this_budget_id, lost_flag=0).all()
            for handling_material_list in handling_material_list:
                handling_material_list.entry_on_progress_flag = 0
                handling_material_list.save()

            # 要求機能?
            budget_required_function_list = BudgetRequiredFunction.objects.filter(budget_id=this_budget_id, lost_flag=0).all()
            for budget_required_function_list in budget_required_function_list:
                budget_required_function_list.entry_on_progress_flag = 0
                budget_required_function_list.save()

            # 要求機能
            required_specification_list = RequiredSpecification.objects.filter(budget_id=this_budget_id).all()
            for required_specification_list_item in required_specification_list:
                required_specification_list_item.entry_on_progress_flag = 0
                required_specification_list_item.save()

            # 関係法令
            budget_law_list = BudgetLaw.objects.filter(budget_id=this_budget_id, lost_flag=0).all()
            for budget_law_list in budget_law_list:
                budget_law_list.entry_on_progress_flag = 0
                budget_law_list.save()

            # 関係機器
            budget_equipment_list = BudgetEquipment.objects.filter(budget_id=this_budget_id, lost_flag=0).all()
            for budget_equipment_list in budget_equipment_list:
                budget_equipment_list.entry_on_progress_flag = 0
                budget_equipment_list.save()

            # 工事方針概要
            policy_overview_reset_progress_flag(this_budget_id)

        ary = {
            'budget_id': this_budget_id,
            'budget_rev_no': budget_rev_no,
            'msg': msg,
            'target_unique_budget_id': budget_unique_id,
            'entry_success_flag': 1,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算一覧の絞込のパーツ表示
@require_POST
def budget_filter(request):
    from fms.views.common_def_views import get_filter_master, get_next_target, get_area_manager_master
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list,\
        = get_filter_master()
        area_manager_list = get_area_manager_master()

        # 進捗工程態選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])

        # 予算繰越処理ステップは、他のステップを表示しない
        if 213010000 <= level5_step_id < 213013000:
            step_st = 213010000
            step_ed = 213013000 - 1
        else:
            step_st = math.floor(level5_step_id / 1000000) * 1000000
            step_ed = step_st + 1000000

        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        # 中期計画の場合は予算状態候補リストの切替(フィールド名は共通化)
        budget_name_text = get_budget_name_text(level5_step_id)

        data = {
            'budget_condition_list': budget_condition_list,
            'step_list': step_list,
            'business_year_list': business_year_list,
            'budget_class_list': budget_class_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'process_list': process_list,
            'area_manager_list': area_manager_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'target_department': target_department,
            'user_division_cd': target_division,
            'target_person': target_person,
            'budget_name_text': budget_name_text,
        }

        return render(request, 'fms/parts/budget/budget_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# form用views
@login_required
def budget_edit(request):
    # budget = get_object_or_404(Budget, id=key)
    # print(key)
    if request.method == 'POST':
        form_left = BudgetEditFormLeft(request.POST)
        form_center = BudgetEditFormCenter(request.POST)
        form_right = BudgetEditFormRight(request.POST)
        if form_left.is_valid():
            budget_edit_data = form_left.save(commit=False)
            budget_edit_data.save()
    else:
        form_left = BudgetEditFormLeft()
        form_center = BudgetEditFormCenter()
        form_right = BudgetEditFormRight()

        data = {
            'form_left': form_left,
            'form_center': form_center,
            'form_right': form_right
        }
        return TemplateResponse(request, 'fms/parts/budget_edit.html', data)


# 予算データコピー
@require_POST
def budget_copy(request):
    try:
        target = request.POST["target"]
        target_budget_unique_id = int(request.POST["target_budget_unique_id"])
        copy_budget_id = int(request.POST["copy_budget_id"])
        work_id = request.POST["work_id"]

        budget_data = Budget.objects.get(id=target_budget_unique_id, lost_flag=0)

        if budget_data.application_class is not None and budget_data.application_class != "":
            application_class = budget_data.application_class.application_class_cd
        else:
            application_class = ""

        if budget_data.budget_class is not None and budget_data.budget_class != "":
            budget_class = budget_data.budget_class.budget_class_cd
        else:
            budget_class = ""

        if budget_data.period_class is not None and budget_data.period_class != "":
            period_class = budget_data.period_class.period_class_cd
        else:
            period_class = ""

        if budget_data.budget_main_department is not None and budget_data.budget_main_department != "":
            budget_main_department_department_cd = budget_data.budget_main_department.department_cd
        else:
            budget_main_department_department_cd = ""

        if budget_data.budget_department_charge_person is not None and budget_data.budget_department_charge_person != "":
            budget_department_charge_person_username = budget_data.budget_department_charge_person.username
        else:
            budget_department_charge_person_username = ""

        if budget_data.budget_person is not None and budget_data.budget_person != "":
            budget_person_username = budget_data.budget_person.username
        else:
            budget_person_username = ""

        if budget_data.facility_process is not None and budget_data.facility_process != "":
            facility_process_process_cd = budget_data.facility_process.process_cd2
        else:
            facility_process_process_cd = ""

        if budget_data.management_class_cd is not None and budget_data.management_class_cd != "":
            management_class_cd = budget_data.management_class_cd
        else:
            management_class_cd = ""

        if budget_data.budget_name is not None and budget_data.budget_name != "":
            budget_name = budget_data.budget_name
        else:
            budget_name = ""

        if budget_data.asdm_flag is not None and budget_data.asdm_flag != "":
            asdm_flag = budget_data.asdm_flag
        else:
            asdm_flag = ""

        if budget_data.purpose_class is not None and budget_data.purpose_class != "":
            purpose_class = budget_data.purpose_class.purpose_class_cd
        else:
            purpose_class = ""

        if budget_data.purpose is not None and budget_data.purpose != "":
            purpose = budget_data.purpose
        else:
            purpose = ""

        if budget_data.detail is not None and budget_data.detail != "":
            detail = budget_data.detail
        else:
            detail = ""

        if budget_data.effect is not None and budget_data.effect != "":
            effect = budget_data.effect
        else:
            effect = ""

        if budget_data.influence_for_operation is not None and budget_data.influence_for_operation != "":
            influence_for_operation = budget_data.influence_for_operation
        else:
            influence_for_operation = ""

        if budget_data.influence_for_quality is not None and budget_data.influence_for_quality != "":
            influence_for_quality = budget_data.influence_for_quality
        else:
            influence_for_quality = ""

        if budget_data.budget_rem is not None and budget_data.budget_rem != "":
            rem = budget_data.budget_rem
        else:
            rem = ""

        # 登録済みの法令の数をカウント
        law_list_num = BudgetLaw.objects.filter(budget_id=budget_data.budget_id, lost_flag=0).count()

        # 登録済の支給品の数をカウント
        equipment_list_num = BudgetEquipment.objects.filter(budget_id=budget_data.budget_id, lost_flag=0).count()

        # 登録済の物質情報の数をカウント
        handling_material_list_num = BudgetMaterial.objects.filter(budget_id=budget_data.budget_id, lost_flag=0).count()

        # 登録済の要求仕様の数をカウント
        required_specification_list_num = RequiredSpecification.objects.filter(budget_id=budget_data.budget_id,
                                                                               lost_flag=0).count()

        # 格納先path作成
        file_folder = '\\' + target + '\\' + str(budget_data.budget_id) + '\\' + str(work_id) + '\\'

        uploadfile_list_num = AttachmentDocuments.objects.filter(folder=file_folder, div_id_name=target,
                                                                 lost_flag=0).count()

        msg = '予算内容をコピーしました。保存されていないので、保存してください！！'

        if budget_data.plan_class is None:
            plan_class_str = 'S'
        else:
            plan_class_str = str(budget_data.plan_class.class_cd)

        ary = {
            'request_name': budget_data.request_name,
            'request_detail': budget_data.request_detail,
            'mplan_basis_id': budget_data.mplan_basis_id,
            'mplan_basis_comment': budget_data.mplan_basis_comment,
            'mplan_concerns': budget_data.mplan_concerns,
            'remove_assets': budget_data.remove_assets,
            'application_class': application_class,
            'budget_class': budget_class,
            'period_class': period_class,
            'budget_main_department_department_cd': budget_main_department_department_cd,
            'budget_department_charge_person_username': budget_department_charge_person_username,
            'budget_person_username': budget_person_username,
            'facility_process_process_cd': facility_process_process_cd,
            'management_class_cd': management_class_cd,
            'budget_name': budget_name,
            'asdm_flag': asdm_flag,
            'purpose_class': purpose_class,
            'purpose': purpose,
            'detail': detail,
            'effect': effect,
            'influence_for_operation': influence_for_operation,
            'influence_for_quality': influence_for_quality,
            'rem': rem,
            'plan_class': plan_class_str,
            'msg': msg,
            'law_list_num': law_list_num,
            'equipment_list_num': equipment_list_num,
            'handling_material_list_num': handling_material_list_num,
            'required_specification_list_num': required_specification_list_num,
            'uploadfile_list_num': uploadfile_list_num,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 物質情報コピー処理
@require_POST
def copy_budget_material_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        copy_budget_id = int(request.POST['copy_budget_id'])

        work_id = request.POST['work_id']
        work_id_api = None if work_id == '' else work_id

        # 登録済取扱物質のレコード数を取得
        handling_material_lists = BudgetMaterial.objects.filter(budget_id=copy_budget_id, work_id=work_id_api, lost_flag=0)

        for handling_material_data in handling_material_lists:
            # 「budget_id」、「rev_no」、「提出書類名」で取扱物質のレコードを抽出･･･あれば読み込み、なければ新規登録
            # (ないはずなので新規登録)
            material_data, created = BudgetMaterial.objects.get_or_create(budget_id=budget_id, lost_flag=0,
                                                                          material_name=handling_material_data.material_name)
            # 各項目の値(1つ前のrevでの値)を格納
            material_data.work_id = handling_material_data.work_id
            material_data.material_cd = handling_material_data.material_cd
            material_data.chemical_formula = handling_material_data.chemical_formula
            material_data.sub_no = handling_material_data.sub_no
            material_data.normal_pressure = handling_material_data.normal_pressure
            material_data.maximum_pressure = handling_material_data.maximum_pressure
            material_data.minimum_pressure = handling_material_data.minimum_pressure
            material_data.normal_temperature = handling_material_data.normal_temperature
            material_data.maximum_temperature = handling_material_data.maximum_temperature
            material_data.minimum_temperature = handling_material_data.minimum_temperature
            material_data.concentration = handling_material_data.concentration
            material_data.ph = handling_material_data.ph
            material_data.viscosity = handling_material_data.viscosity
            material_data.bulk_specific_gravity = handling_material_data.bulk_specific_gravity
            material_data.true_specific_gravity = handling_material_data.true_specific_gravity
            material_data.apparent_specific_gravity = handling_material_data.apparent_specific_gravity
            material_data.particle_size = handling_material_data.particle_size
            material_data.moisture = handling_material_data.moisture
            material_data.others = handling_material_data.others
            material_data.concentration_unit_id = handling_material_data.concentration_unit_id
            material_data.pressure_unit_id = handling_material_data.pressure_unit_id
            material_data.state_id = handling_material_data.state_id
            material_data.entry_on_progress_flag = 1

            if created == 1:
                last_material_lists = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=1,
                                                                    material_name=handling_material_data.material_name)
                if last_material_lists.count() == 0:
                    material_data.rev_no = 0
                else:
                    material_data.rev_no = last_material_lists.order_by('-rev_no')[0].rev_no + 1

                material_data.entry_datetime = now
                material_data.entry_operator = operator
            else:
                material_data.update_datetime = now
                material_data.update_operator = operator

            # 提出書類のレコードを保存
            material_data.save()

        msg = "関係法令データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係法令情報コピー処理
@require_POST
def copy_budget_law_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        this_step = int(request.POST["this_step"])
        copy_budget_id = int(request.POST['copy_budget_id'])

        copy_law_list = BudgetLaw.objects.filter(budget_id=copy_budget_id, lost_flag=0)

        for copy_law_data in copy_law_list:
            # 「budget_id」、「rev_no」、「提出書類名」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
            law_data, created = BudgetLaw.objects.get_or_create(budget_id=budget_id, lost_flag=0,
                                                                law_name=copy_law_data.law_name)
            # 各項目の値(1つ前のrevでの値)を格納
            law_data.entry_on_progress_flag = 1

            if created == 1:
                last_law_list = BudgetLaw.objects.filter(budget_id=budget_id, lost_flag=1, law_name=copy_law_data.law_name)
                if last_law_list.count() == 0:
                    law_data.rev_no = 0
                else:
                    law_data.rev_no = last_law_list.order_by('-rev_no')[0].rev_no + 1

                law_data.entry_datetime = now
                law_data.entry_operator = operator
            else:
                law_data.update_datetime = now
                law_data.update_operator = operator

            # 提出書類のレコードを保存
            law_data.save()

        msg = "関係法令データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係機器情報コピー処理
@require_POST
def copy_budget_equipment_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        this_step = int(request.POST["this_step"])
        copy_budget_id = int(request.POST['copy_budget_id'])

        copy_budget_equipment_list = BudgetEquipment.objects.filter(budget_id=copy_budget_id, lost_flag=0)

        for copy_budget_equipment_data in copy_budget_equipment_list:
            # 「budget_id」、「lost_flag」、「機器No」で機器情報のレコードを抽出･･･あれば読み込み、なければ新規登録
            # (ないはずなので新規登録)
            budget_equipment_data, created = BudgetEquipment.objects.get_or_create(budget_id=budget_id,
                                                                                   equip_no=copy_budget_equipment_data.equip_no,
                                                                                   lost_flag=0)
            # 各項目の値(1つ前のrevでの値)を格納
            budget_equipment_data.equip_name = copy_budget_equipment_data.equip_name
            budget_equipment_data.management_class = copy_budget_equipment_data.management_class
            budget_equipment_data.facility = copy_budget_equipment_data.facility
            budget_equipment_data.equip_family = copy_budget_equipment_data.equip_family
            budget_equipment_data.equip_type = copy_budget_equipment_data.equip_type
            budget_equipment_data.entry_on_progress_flag = 1

            if created == 1:
                last_budget_equipment_list = BudgetEquipment.objects.filter(budget_id=budget_id,
                                                                            equip_no=copy_budget_equipment_data.equip_no,
                                                                            lost_flag=1)
                if last_budget_equipment_list.count() == 0:
                    budget_equipment_data.rev_no = 0
                else:
                    budget_equipment_data.rev_no = last_budget_equipment_list.order_by('-rev_no')[0].rev_no + 1

                budget_equipment_data.entry_datetime = now
                budget_equipment_data.entry_operator = operator
            else:
                budget_equipment_data.update_datetime = now
                budget_equipment_data.update_operator = operator

            # 機器情報のレコードを保存
            budget_equipment_data.save()

        msg = "機器情報データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 要求仕様コピー処理
@require_POST
def copy_required_spec_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        copy_budget_id = int(request.POST['copy_budget_id'])

        budget_rev_no = get_required_specification_rev_no(budget_id)

        # 対象予算idに対する登録済要求機能のデータ取得
        copy_required_specification_lists = RequiredSpecification.objects.filter(budget_id=copy_budget_id,
                                                                                 lost_flag=0).order_by('no')

        for copy_required_specification_data in copy_required_specification_lists:

            # 最新の要求仕様Noを取得
            this_no = get_required_specification_no(budget_id)

            # 「budget_id」、「budget_rev_no」、「lost_flag」でレコードを抽出、あれば取得、なければ新規登録
            # ･･･ないはずなので新規登録
            required_specification_data, created = RequiredSpecification.objects.get_or_create(budget_id=budget_id,
                                                                                               budget_rev_no=budget_rev_no,
                                                                                               no=this_no,
                                                                                               lost_flag=0)

            # 各項目の値を格納
            required_specification_data.required_spec = copy_required_specification_data.required_spec
            required_specification_data.entry_on_progress_flag = 1
            required_specification_data.lost_flag = 0
            # 要求仕様のレコードを保存
            required_specification_data.save()

            if created == 1:
                last_required_specification_lists = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                         budget_rev_no=budget_rev_no,
                                                                                         no=this_no,
                                                                                         lost_flag=1)
                # if last_required_specification_lists.count() == 0:
                #     required_specification_data.rev_no = 0
                # else:
                #     required_specification_data.rev_no = last_required_specification_lists.order_by('-rev_no')[0].rev_no + 1

                required_specification_data.entry_datetime = now
                required_specification_data.entry_operator = operator
            else:
                required_specification_data.update_datetime = now
                required_specification_data.update_operator = operator

            # 要求仕様のレコードを保存
            required_specification_data.save()

        msg = "要求仕様データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# コピー用予算一覧の絞込のパーツ表示
@require_POST
def budget_copy_source(request):
    from fms.views.common_def_views import get_filter_master, get_next_target, get_area_manager_master
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()

        area_manager_list = get_area_manager_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        level5_step_id_string = request.POST['level5_step_id']
        step_st = math.floor(level5_step_id / 1000000) * 1000000
        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        if level5_step_id_string[0:3] == '136':
            on_work_flag = 0
        else:
            on_work_flag = 1

        is_mplan_flag = is_mplan_budget_step(level5_step_id)

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        budget_name_text = get_budget_name_text(level5_step_id)
        if budget_name_text == '依頼名':
            budget_name_text = '依頼名/予算名'

        data = {
            'budget_condition_list': budget_condition_list,
            'step_list': step_list,
            'business_year_list': business_year_list,
            'budget_class_list': budget_class_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'process_list': process_list,
            'area_manager_list': area_manager_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'target_department': target_department,
            'user_division_cd': target_division,
            'target_person': target_person,
            'on_work_flag': on_work_flag,
            'is_mplan_flag': is_mplan_flag,
            'budget_name_text': budget_name_text,
        }

        return render(request, 'fms/parts/budget/budget_copy_source/budget_copy_source.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 部署を選択したときにユーザー・工程選択の一覧を絞込
def budget_change_department(request):
    try:
        department = request.POST['department']
        user_list = get_department_person_option_list(department)

        processmaster = ProcessMaster.objects.filter(department=department, lost_flag=0).order_by('display_order')
        processmaster_list = ''
        for processmaster in processmaster:
            processmaster_list += '<option value="' + processmaster.process_cd2 + '">' + processmaster.process_cd \
                                  + ' : ' + processmaster.process_name + '</option>'

        # エリア管理者を原課部署にあわせて抽出
        budget_department_list = DepartmentMaster.objects.filter(department_cd=department, lost_flag=0)
        charge_person_list = ''
        for budget_department in budget_department_list:
            if budget_department.area_manager is not None:
                charge_person_list += '<option value="' + budget_department.area_manager.username + '">' \
                                      + budget_department.area_manager.last_name + ' ' \
                                      + budget_department.area_manager.first_name + '</option>'

        data = {
            'user_list': user_list,
            'processmaster_list': processmaster_list,
            'charge_person_list': charge_person_list,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算状態個別設定
@require_POST
def set_budget_condition(request):
    try:
        budget_id = int(request.POST["budget_id"])
        condition = int(request.POST["condition"])

        set_condition(budget_id, condition)

        msg = '予算状態変更完了'
        data = {
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算状態一括設定
@require_POST
def set_relation_budget_condition(request):
    try:
        budget_id = int(request.POST["budget_id"])
        condition = int(request.POST["condition"])

        relation_budget_data = Budget.objects.filter(relation_budget_id=budget_id, lost_flag=0)

        for target_budget_data in relation_budget_data:
            set_condition(target_budget_data.budget_id, condition)

        msg = '予算状態変更完了'
        data = {
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算状態設定
def set_condition(budget_id, condition):
    budget_condition_item = BudgetCondition.objects.get(budget_id=budget_id)
    budget_condition_item.budget_condition_id = condition
    budget_condition_item.save()
    return

# 予算担当者画面を表示
@login_required
@require_POST
def budget_charge_person_info(request):
    from fms.views.common_def_views import get_department_person_list
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        present_step = int(request.POST['this_step'])

        # 担当者候補リストの情報を取得　設備部管理部工務Gのみで絞り込み「CWG」
        user_list = get_department_person_list('CWG')

        # データ編集機能要否判定
        budget_charge_person_edit_action_num = DataEntryStepMaster.objects.filter(
            step_id=present_step, target_table='budget_charge_person').count()

        edit_flag = 0
        if budget_charge_person_edit_action_num > 0:
            edit_flag = 1

        data = {
            'user_list': user_list,
            'edit_flag': edit_flag,
        }

        return render(request, 'fms/parts/budget/budget_charge_person/budget_charge_person_edit.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算担当者を登録
@login_required
@require_POST
def budget_charge_person_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['budget_id'])
        budget_charge_person = request.POST['budget_charge_person']
        this_step = int(request.POST['this_step'])
        this_department = request.POST['this_department']
        this_division = request.POST['this_division']

        # 予算担当者を設定
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
        budget_data.budget_person_id = budget_charge_person
        # データを保存
        budget_data.save()

        # コメント作成
        comment = "budget_id : " + str(budget_id) + "、予算担当者 : " + budget_charge_person + ""

        # ログを新規登録
        Log(target='budget', target_id=budget_id, action='entry', operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        msg = '予算担当者登録完了'
        data = {
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算Noリストを登録
def budget_no_registration_list(request, registration_data_list, budget_type):
    try:
        # 予算No登録済の予算がないか登録前にチェック
        for registration_data in registration_data_list:
            budget_data = Budget.objects.get(budget_id=registration_data['budget_id'], lost_flag=0)

            if budget_data.budget_no is not None:
                msg = '予算No登録済の予算が含まれています！！！'
                return msg

            # 対象外の予算タイプが混じっていないかチェック
            if budget_type == 'normal' and budget_data.application_class_id != 1:
                msg = '追加予算が含まれています！！！'
                return msg
            elif budget_type == 'append' and budget_data.application_class_id == 1:
                msg = '通常申請の予算が含まれています！！！'
                return msg

        # 問題がなければ、予算No登録
        for registration_data in registration_data_list:
            budget_no_registration(request, registration_data['budget_id'], registration_data['budget_no'])

        msg = '予算No登録完了'
        return msg

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算Noを登録
def budget_no_registration(request, budget_id, budget_no):
    from fms.models import Work
    try:
        DIFF_JST_FROM_UTC = 9
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        this_division = request.POST['user_division_cd']
        this_department = request.POST['user_department_cd']

        # 予算Noを設定
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
        progress_data = Progress.objects.get(target='budget', target_id=budget_id)
        this_step = progress_data.present_step
        budget_data.budget_no = budget_no

        # データを保存
        budget_data.save()

        # 予算状態を実行中に変更
        budget_condition_item = BudgetCondition.objects.get(budget_id=budget_id)
        budget_condition_item.budget_condition_id = 31
        budget_condition_item.save()

        # コメント作成
        comment = "budget_id : " + str(budget_id) + "、予算No : " + str(budget_no) + ""

        # ログを新規登録
        Log(target='budget', target_id=budget_id, action='entry', operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=budget_id).save()

        # 予算額追加の場合、workの付け替え処理
        if budget_data.application_class_id == 3 or budget_data.application_class_id == 5:
            relation_budget_id = budget_data.relation_budget_id
            work_list = Work.objects.filter(work_budget_id=budget_id, lost_flag=0)
            for target_work_data in work_list:
                target_work_data.work_budget_id = relation_budget_id
                target_work_data.save()

            # 主予算側のProSpecificationUnitを生成する
            budget_data_main = Budget.objects.get(budget_id=relation_budget_id, lost_flag=0)
            send_data_work(relation_budget_id, budget_data_main.application_class_id)
            # 予算額追加側のProBudgetUnitを生成する
            send_data_budget(budget_id)

        # 追加予算の場合、データ移行処理
        elif budget_data.application_class_id != 1:
            # 工事実行へのデータ移行処理
            send_data_budget(budget_id)
            send_data_work(budget_id, budget_data.application_class_id)

        # 届出CS生成（追加予算かつ、届出CS作成フラグONの場合のみ）
        if budget_data.application_class_id != 1 and budget_data.no_make_cs_flag == 0:
            cs_progress_record_append(budget_data, operator, progress_data.last_operation_step)

        # 実行側テーブルへの予算No設定
        set_budget_no_execution(budget_id, budget_no)

        if budget_data.application_class_id == 1:
            # 通常申請は予算見積完了ステップに移行
            next_step = 133009905
        else:
            # 追加:予算承認完了ステップに移行
            next_step = 136006011

        progress_data = Progress.objects.get(target='budget', target_id=budget_id)
        progress_data.last_operation_step = progress_data.present_step
        progress_data.last_operator = operator
        progress_data.last_operation_datetime = now
        progress_data.present_step = next_step
        progress_data.present_operator = 'end'
        progress_data.present_department = 'END'
        progress_data.present_division = 'END'
        progress_data.save()
        # 予算の状態変更(関数内で判定)
        set_budget_status(progress_data)

        # 進捗通知機能
        step_notice(progress_data)

        msg = '予算No登録完了'
        data = {
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 実行側テーブルに予算Noを設定
def set_budget_no_execution(budget_id, budget_no):

    pro_budget_list = ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=0)
    for pro_budget_data in pro_budget_list:
        pro_budget_data.budget_no = budget_no
        pro_budget_data.save()

    pro_spec_unit_list = ProSpecificationUnit.objects.filter(budget_id=budget_id, lost_flag=0)
    for pro_spec_unit_data in pro_spec_unit_list:
        pro_spec_unit_data.budget_no = budget_no
        pro_spec_unit_data.save()

    return


# 関連予算を含む予算額合計取得
def get_budget_total_price(budget_id):
    budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
    relation_budget_id = budget_data.relation_budget_id
    budget_total_price_data = Budget.objects.filter(relation_budget_id=relation_budget_id, lost_flag=0).values(
        'relation_budget_id').aggregate(budget_price_sum=Sum('budget_price'))
    budget_total_price = budget_total_price_data['budget_price_sum']

    return budget_total_price


# 詳細仕様検討中で自分が計画担当の予算数を取得
def get_budget_make_specification(step_id, department_cd, username):
    user_count = 0
    # 予算リストの表示条件(get_budget_lists)
    # 該当予算のProgressが詳細仕様検討で自部署担当である
    # 計画担当者に自分が含まれている
    # 予算状態が申請準備中である

    # progress_list = Progress.objects.filter(target='budget', present_step=step_id, present_department=department_cd)
    # for progress in progress_list:
    #     budget_id = progress.target_id
    #     charge_person_list = PlanningChargePerson.objects.filter(budget_id=budget_id, charge_person=username, lost_flag=0 ).all()
    #     if charge_person_list.count() < 1:
    #         continue
    #     budget_condition_list = BudgetCondition.objects.filter(budget_id=budget_id, budget_condition_id=11)
    #     if budget_condition_list.count() < 1:
    #         continue
    #     user_count = user_count + 1

    # 高速化のためSQLで実行
    sql =       """SELECT fms_progress.* """
    sql = sql + """ FROM fms_progress """
    sql = sql + """ LEFT JOIN fms_planningchargeperson ON fms_planningchargeperson.budget_id=fms_progress.target_id"""
    sql = sql + """ LEFT JOIN fms_budgetcondition ON fms_budgetcondition.budget_id=fms_progress.target_id"""
    sql = sql + """ WHERE fms_progress.target='budget' AND """
    sql = sql + """ fms_progress.target='budget' AND """
    sql = sql + f" fms_progress.present_step='{ step_id }' AND "
    sql = sql + f" fms_progress.present_department='{ department_cd }' AND "
    sql = sql + f" fms_planningchargeperson.charge_person='{ username }' AND "
    sql = sql + f" fms_planningchargeperson.lost_flag=0 AND "
    sql = sql + f" fms_budgetcondition.budget_condition_id=11 "

    progress_list = Progress.objects.all().raw(sql)
    user_count = len(list(progress_list))

    return user_count


# 中期計画予算のステップ変更に応じた処理
def set_budget_status(progress_data):
    if progress_data.target != 'budget':
        return
    target_id = progress_data.target_id
    budget_list = Budget.objects.filter(budget_id=target_id, lost_flag=0).all()
    if budget_list.count() != 1:
        return

    relation_list = BudgetConditionRelation.objects.filter(
        this_step_id=progress_data.last_operation_step, next_step_id=progress_data.present_step, lost_flag=0).all()

    if relation_list.count() > 0:
        set_condition(target_id, relation_list[0].budget_condition_id)

    return


# 予算計画移行処理
def go_next_budget_plan_list(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        msg = ''

        # POST情報取得
        budget_id_list = request.POST.getlist("budget_id_list[]")

        # チェック処理
        for budget_id in budget_id_list:
            budget_list = Budget.objects.filter(budget_id=budget_id, lost_flag=0)
            if len(budget_list) != 1:
                msg = f'指定された予算ID({budget_id})が特定できません'
                break
            budget_data = budget_list[0]
            if budget_data.plan_class_id != 'M':
                msg = f'中期計画以外の予算({budget_id})が選択されています'
                break
        if msg != '':
            data = {'msg': msg}
            return JsonResponse(data)

        # 予算単位で、単年度計画移行処理
        for budget_id in budget_id_list:
            go_next_budget_plan(request, budget_id, now)

        msg = '予算計画移行処理完了'
        data = {
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算計画移行
def go_next_budget_plan(request, budget_id, now):
    print(budget_id)
    operator = request.user.username

    # 中期計画側予算を取得
    old_plan_budget_data = Budget.objects.filter(budget_id=budget_id, lost_flag=0).order_by('-id')[0]

    # 予算IDを取得
    new_budget_id = Budget.objects.all().order_by('-budget_id').first().budget_id + 1

    # 旧データのidをNoneにして、そのままSaveし、新規idを割り当てる
    new_budget_data = old_plan_budget_data
    new_budget_data.id = None
    new_budget_data.budget_id = new_budget_id
    new_budget_data.relation_budget_id = new_budget_id
    new_budget_data.last_plan_id = budget_id
    new_budget_data.plan_class_id = 'S'
    new_budget_data.budget_name = new_budget_data.request_name
    new_budget_data.entry_datetime = now
    new_budget_data.entry_operator = operator
    new_budget_data.update_datetime = now
    new_budget_data.update_operator = operator
    new_budget_data.entry_on_progress_flag = 0
    new_budget_data.rev_no = 0
    new_budget_data.save()

    # 関連データコピー(最新データのみ)
    copy_budget_sub_data(BudgetMaterial, budget_id, new_budget_id, True, True)
    copy_budget_sub_data(BudgetRequiredFunction, budget_id, new_budget_id, True, True)
    copy_budget_sub_data(BudgetLaw, budget_id, new_budget_id, True, True)
    copy_budget_sub_data(BudgetEquipment, budget_id, new_budget_id, True, True)

    copy_budget_sub_data(ConstructionPolicyOverview, budget_id, new_budget_id, False, True)
    copy_budget_sub_data(RequiredSpecification, budget_id, new_budget_id, False, True)
    copy_budget_sub_data(PlanningChargePerson, budget_id, new_budget_id, False, False)
    copy_budget_sub_data(BudgetCondition, budget_id, new_budget_id, False, False, False)
    set_condition(new_budget_id, 11)

    copy_budget_sub_data_file('budget', 'budget', budget_id, new_budget_id, 0)

    # Progressの作成
    progress_data, created = Progress.objects.get_or_create(target="budget", target_id=new_budget_id)
    progress_data.present_step = 133001001
    # 次作業者は原課担当者
    progress_data.present_operator = new_budget_data.budget_department_charge_person.username
    progress_data.present_department = new_budget_data.budget_main_department.department_cd
    department_data = DepartmentMaster.objects.get(department_cd=progress_data.present_department)
    progress_data.present_division = department_data.division_cd

    # 進捗状況のレコードを保存
    progress_data.save()

    return


# データ移行サブ処理(関連レコードのコピー)
def copy_budget_sub_data(model, budget_id, copy_budget_id, set_rev_no, set_progress_flag, have_lost_flag=True):

    if have_lost_flag:
        sub_data_list = model.objects.filter(budget_id=budget_id, lost_flag=0)
    else:
        sub_data_list = model.objects.filter(budget_id=budget_id)

    for sub_data_item in sub_data_list:
        # 新規レコードを保存
        sub_data_item.id = None
        sub_data_item.budget_id = copy_budget_id
        if set_rev_no:
            sub_data_item.rev_no = 0
        if set_progress_flag:
            sub_data_item.entry_on_progress_flag = 0

        sub_data_item.save()
    return


# データ移行サブ処理(添付ファイルのコピー)
def copy_budget_sub_data_file(target_from, target_to, budget_id, copy_budget_id, work_id):

    # 検索用path作成
    file_folder_from = '\\' + target_from + '\\' + str(budget_id) + '\\' + str(work_id) + '\\'
    # 登録済の添付ファイルのリストを取得
    copy_file_list = AttachmentDocuments.objects.filter(folder=file_folder_from, div_id_name=target_from, lost_flag=0)

    # ファイル毎にコピー処理
    for copy_file_item in copy_file_list:
        # フルパスを生成
        folder_path_from, folder_name_from = get_attachment_folder_name(target_from, budget_id, work_id, copy_file_item.data)
        file_path_from = os.path.join(folder_path_from, copy_file_item.file_name)

        # コピー先パスを生成
        folder_path_to, folder_name_to = get_attachment_folder_name(target_to, copy_budget_id, work_id, copy_file_item.data)
        file_path_to = os.path.join(folder_path_to, copy_file_item.file_name)

        # フォルダの存在チェック　なければフォルダ作成
        if os.path.exists(folder_path_to) is not True:
            os.makedirs(folder_path_to)

        # ファイルの存在チェック(すでにファイルがある場合はコピーしない)
        if os.path.isfile(file_path_to) is not True:
            # ファイルをコピー
            shutil.copy2(file_path_from, file_path_to)

        # すでにレコードが作成されていたら複製しない
        if AttachmentDocuments.objects.filter(folder=folder_name_to, div_id_name=copy_file_item.div_id_name, file_name=copy_file_item.file_name, lost_flag=0).count() < 1:
            # 新規レコードを保存
            copy_file_item.id = None
            copy_file_item.folder = folder_name_to
            copy_file_item.div_id_name = copy_file_item.div_id_name
            copy_file_item.save()

    return

