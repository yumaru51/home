import math
# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# formsをインポート
from fms.forms import BudgetEditFormLeft, BudgetEditFormCenter, BudgetEditFormRight
# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import WorkClassMaster, RegulationMaster
from fms.models import WorkManagementClassMaster
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import FreeSpecDetail, SubmissionDocument, Estimate, Supplies, BudgetLaw, WorkLaw, BudgetEquipment, WorkEquipment
from fms.models import WorkSpecMEX, PlanningChargePerson
from fms.models import FreeSpecDetailTemplate
from fms.models import ProSpecificationUnit
from fms.models import AttachmentDocuments
from django.db import connections
from fms.views.common_def_views import TemplateType, is_mplan_budget_step, get_budget_name_text
from fms.views.common_def_views import get_next_target, convert_charge_department, get_filter_planning_charge_person_list
from django.utils.timezone import make_aware
from common.common_def import date_to_many_type
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception, get_department_person_list
from fms.views.common_views import None_to_blank
from fms.views.notice_mail_views import step_notice


# 工事情報を表示する基礎画面を表示
@login_required
@require_POST
def work_detail(request):
    try:

        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_unique_work_id = int(request.POST['id'])

        target_work_id = int(request.POST['work_id'])
        target_budget_id = int(request.POST['budget_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])

        # 新規登録(target_work_id=0)を判定
        # 新規登録時処理
        if target_unique_work_id == 0:
            # 新規登録の場合、予算の工程を取得
            progress_data = Progress.objects.get(target='budget', target_id=target_budget_id)
            target_step_id = progress_data.present_step
            # 工事の主キーを仮の値を「0」、rev_noを空欄、選択した要求機能(selected_required_function_id)を空欄に設定
            target_unique_work_id = 0
            rev_no = 0
            selected_required_function_id = ""

        # 更新時処理
        else:
            # 対象データの現在の(工事での)工程IDを取得
            progress_data = Progress.objects.get(target='work', target_id=target_work_id)
            target_step_id = progress_data.present_step
            # 主キーで工事のレコードを抽出
            work_data = Work.objects.get(id=target_unique_work_id)
            # 各項目の値を取得
            rev_no = work_data.work_rev_no
            if work_data.work_required_function is None:
                work_required_function = ""
            else:
                work_required_function = work_data.work_required_function
            sub_no = "" if work_data.sub_no is None else work_data.sub_no
            # 機能マスタから機能CDを取得
            if work_required_function is None:
                function_data = ""
            else:
                function_data = FunctionMaster.objects.get(function_name=work_required_function, lost_flag=0)
            function_cd = function_data.function_cd
            # 要求機能から要求機能の主キーの値を取得
            if sub_no == "":
                budget_required_function_data  = ""
            else:
                budget_required_function_data = BudgetRequiredFunction.objects.get(required_function=function_cd, sub_no=sub_no, lost_flag=0)
            selected_required_function_id = budget_required_function_data.id

        # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
        this_step = target_step_id

        # 以下で取得する変数を事前定義、数値は0、文字は空欄
        last_operation_step = 0
        last_operator = ""
        last_operator_department = ""
        last_operator_division = ""

        # 対象の予算レコード取得
        budget_data = Budget.objects.get(id=target_budget_id, lost_flag=0)
        # 対象の予算レコードのidを取得
        target_unique_budget_id = budget_data.id

        # 対象の予算レコードの予算idを取得
        target_budget_id = budget_data.budget_id
        # 予算テーブルの部署データ取得
        budget_department = budget_data.budget_main_department
        # 部署マスターの対象レコード取得　※リレーションを設定しているときは、マスターのmodelsの定義内容（def __str__(self):）の項目を検索フィールドとする
        department_data = DepartmentMaster.objects.get(department_name=budget_department)
        # 予算テーブルの部署のコードを取得
        this_department = department_data.department_cd

        # 対象のIDが「0」でないとき(=更新処理)の処理　※IDは工事IDではなく、レコードのID(主キー)
        if target_unique_work_id != 0:
            # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
            log_data_num = Log.objects.filter(target="work", target_id=target_work_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
            # logデータがあった(過去に対象の予算に操作がされていた)場合
            if log_data_num > 0:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data = Log.objects.filter(target="work", target_id=target_work_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by('-operation_datetime').all()[0:1]
            else:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                log_data = Log.objects.filter(target="work", target_id=target_budget_id, step__lte=this_step).exclude(action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

            # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
            for log_data in log_data:
                last_operation_step = log_data.step
                last_operator = log_data.operator
                last_operator_department = log_data.operator_department
                last_operator_division = log_data.operator_division

        else:
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

        # 部門情報を取得 ・・・通常処理
        department_data = DepartmentMaster.objects.get(department_cd=this_department)
        this_division = department_data.division_cd
        # 部門情報を取得 ・・・リレーション対応
        department_data = DepartmentMaster.objects.get(department_name=budget_department)
        # 進捗工程名取得
        # print(target_step_id)
        step_data = StepMaster.objects.get(step_id=target_step_id)
        budget_step_name = step_data.step_name
        # 対処部署分類を取得（依頼部署か特定部署か）
        charge_department_class = convert_charge_department(step_data.charge_department_class)

        # function_list = FunctionMaster.objects.filter(lost_flag=0).all()
        # 対処部署分類が依頼部署の場合、次作業部門、次作業部署に自部門、自部署を代入
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        # 対処部署分類が特定部署の場合、次作業部署に特定部署を代入
        else:
            next_division = ""
            next_department = charge_department_class

        # tab_num = 11

        # target = "work"

        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_id': target_unique_work_id,
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
            'target_unique_work_id': target_unique_work_id,
            'target_unique_budget_id': target_unique_budget_id,
            'target_work_id': target_work_id,
            # 'tab_num': tab_num,
            'target_work_rev_no': rev_no,
            'selected_required_function_id': selected_required_function_id
            # 'target': target,
            # 'function_list': function_list,
            # 'function_amount': function_amount,
        }

        return render(request, 'fms/parts/work/work_detail/work_base.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事共通情報を詳細画面で表示
@login_required
@require_POST
def work_common_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # 年度の初期値を設定
        d_today = datetime.date.today()
        d_year = d_today.year
        d_month = d_today.month

        int_d_month = int(d_month)
        int_d_year = int(d_year)

        if int_d_month <= 6:
            default_year = int_d_year + 1
        else:
            default_year = int_d_year + 2

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = int(request.POST['id'])
        present_step = int(request.POST['this_step'])
        level5_step_id = int(request.POST['level5_step_id'])
        budget_unique_id = int(request.POST['budget_unique_id'])
        budget_id = int(request.POST['budget_id'])
        is_mplan_flag = is_mplan_budget_step(level5_step_id)

        # 対象の予算データがある場合の処理
        if budget_unique_id != 0:
            # 予算データを主キーでレコード抽出
            budget_data = Budget.objects.get(id=budget_unique_id)
            # 各項目の値を取得
            budget_department = budget_data.budget_main_department.department_cd if budget_data.budget_main_department.department_cd is not None else ""
            budget_process_data = budget_data.facility_process_id if budget_data.facility_process_id is not None else ""
            if budget_department == "":
                budget_division = ""
            else:
                budget_division = DepartmentMaster.objects.get(department_cd=budget_department).division_cd
            # 20210113 y-kawauchi 予算から取ってくるデータ追加
            budget_order_department_charge_person = budget_data.budget_department_charge_person if budget_data.budget_department_charge_person is not None else ""
            budget_start_date = budget_data.start_date if budget_data.start_date is not None else ""
            budget_end_date = budget_data.end_date if budget_data.end_date is not None else ""
            budget_delivery_date = budget_data.delivery_date if budget_data.delivery_date is not None else ""
        # 対象の予算データがない場合の処理　←ありえる？
        else:
            budget_division = ""
            budget_department = ""
            budget_process_data = ""
            budget_order_department_charge_person = ""
            budget_start_date = ""
            budget_end_date = ""
            budget_delivery_date = ""
            # budget_fixed_form = ""

        budget_process_str = str(budget_process_data)
        if budget_process_str != "":
            str_place = budget_process_str.find(' : ')
            budget_process = budget_process_str[0:str_place]

        # 対象の工事idのデータがある場合
        if target_id > 0:
            work_data = Work.objects.get(id=target_id)

            # 各項目の値を取得
            work_id = work_data.work_id
            rev_no = work_data.work_rev_no
            work_name = work_data.work_name
            required_function = "" if work_data.work_required_function is None else work_data.work_required_function
            required_function_sub_no = "" if work_data.sub_no is None else work_data.sub_no

            if work_data.work_class is None:
                work_class = ""
                work_class_name = ""
            else:
                work_class = work_data.work_class.work_class_cd
                work_class_name = work_data.work_class.work_class_name
            if work_data.work_planning_charge_person is None:
                work_planning_charge_person = ""
                work_planning_charge_person_name = ""
            else:
                work_planning_charge_person = work_data.work_planning_charge_person.username
                work_planning_charge_person_name = work_data.work_planning_charge_person
            if work_data.management_class_cd is not None:
                management_class_cd = work_data.management_class_cd
                management_class_data = WorkManagementClassMaster.objects.get(management_class_cd=management_class_cd, lost_flag=0)
                management_class_name = management_class_data.management_class_name
            else:
                management_class_cd = ''
                management_class_name = ''
            work_execution_charge_person = "" if work_data.work_execution_charge_person is None else work_data.work_execution_charge_person.username
            work_execution_charge_person_name = work_data.work_execution_charge_person

            if work_data.work_order_department_charge_person is None:
                work_order_department_charge_person = ""
                work_order_department_charge_person_name = ""
            else:
                work_order_department_charge_person = work_data.work_order_department_charge_person.username
                work_order_department_charge_person_name = work_data.work_order_department_charge_person

            work_order_department = "" if work_data.work_order_department is None else work_data.work_order_department.department_cd

            # 20210113 y-kawauchi 部門部署設備工程　対応
            work_charge_department = budget_department if budget_department is not "" else ""
            work_charge_department_text = DepartmentMaster.objects.get(department_cd=budget_department).department_name if budget_department is not "" else ""
            work_charge_division = budget_division if budget_division is not "" else ""
            work_charge_division_text = DivisionMaster.objects.get(division_cd=budget_division).division_name if budget_division is not "" else ""
            work_charge_process_cd2 = budget_process_data if budget_process_data is not "" else ""
            work_charge_process_text = ProcessMaster.objects.get(process_cd2=budget_process_data).process_name if budget_process_data is not "" else ""
            work_charge_process_cd = ProcessMaster.objects.get(process_cd2=budget_process_data).process_cd if budget_process_data is not "" else ""

            delivery_location = "" if work_data.delivery_location is None else work_data.delivery_location
            start_date = "" if work_data.work_start_date is None else work_data.work_start_date
            end_date = "" if work_data.work_end_date is None else work_data.work_end_date
            delivery_date = "" if work_data.work_delivery_date is None else work_data.work_delivery_date
            estimate_date = "" if work_data.estimate_date is None else work_data.estimate_date
            estimate_limited_date = "" if work_data.work_estimate_limited_date is None else work_data.work_estimate_limited_date
            make_limited_date = "" if work_data.make_limited_date is None else work_data.make_limited_date
            order_limited_date = "" if work_data.order_limited_date is None else work_data.order_limited_date
            fixed_form = "" if work_data.fixed_form is None else work_data.fixed_form
            estimate_range = "" if work_data.estimate_range is None else work_data.estimate_range
            confidentiality = "" if work_data.confidentiality is None else work_data.confidentiality
            warranty = "" if work_data.warranty is None else work_data.warranty
            acceptance_conditions = "" if work_data.acceptance_conditions is None else work_data.acceptance_conditions
            witness_inspection = "" if work_data.witness_inspection is None else work_data.witness_inspection
            acceptance_inspection = "" if work_data.acceptance_inspection is None else work_data.acceptance_inspection
            test_run = "" if work_data.test_run is None else work_data.test_run
            test_run_pass = "" if work_data.test_run_pass is None else work_data.test_run_pass
            inspection_period = "" if work_data.inspection_period is None else work_data.inspection_period
            if work_data.work_rem is None:
                work_rem = ""
            else:
                work_rem = work_data.work_rem

            # 無効となった(=1つ前のrev_noの)対象の工事データのレコード数を取得
            old_work_data_num = Work.objects.filter(work_id=work_id, lost_flag=1).count()

        # 対象の工事idのデータがない場合
        else:
            # 各項目の値を設定
            work_data = ""
            work_id = ""
            rev_no = 0
            work_name = ""
            required_function = ""
            required_function_sub_no = ""
            work_class = ""
            work_class_name = ""
            management_class_cd = ""
            management_class_name = ""
            work_execution_charge_person_name = ""
            work_execution_charge_person = ""
            work_order_department = ""
            delivery_location = ""
            estimate_date = ""
            estimate_limited_date = ""
            make_limited_date = ""
            order_limited_date = ""
            estimate_range = ""
            confidentiality = ""
            warranty = ""
            acceptance_conditions = ""
            witness_inspection = ""
            acceptance_inspection = ""
            test_run = ""
            test_run_pass = ""
            inspection_period = ""
            work_rem = ""
            old_work_data_num = 0
            fixed_form = ""

            work_charge_department = budget_department if budget_department is not "" else ""
            work_charge_department_text = DepartmentMaster.objects.get(department_cd=budget_department).department_name if budget_department is not "" else ""
            work_charge_division = budget_division if budget_division is not "" else ""
            work_charge_division_text = DivisionMaster.objects.get(division_cd=budget_division).division_name if budget_division is not "" else ""
            work_charge_process_cd2 = budget_process_data if budget_process_data is not "" else ""
            work_charge_process_text = ProcessMaster.objects.get(process_cd2=budget_process_data).process_name if budget_process_data is not "" else ""
            work_charge_process_cd = ProcessMaster.objects.get(process_cd2=budget_process_data).process_cd if budget_process_data is not "" else ""
            work_planning_charge_person = ""
            work_planning_charge_person_name = ""
            work_order_department_charge_person = budget_order_department_charge_person.username
            work_order_department_charge_person_name = budget_order_department_charge_person
            start_date = budget_start_date
            end_date = budget_end_date
            delivery_date = budget_delivery_date

            # テンプレート（秘密保持条件）の取得
            num = FreeSpecDetailTemplate.objects.filter(template_id=TemplateType.CONFIDENTIALITY.value, lost_flag=0).count()
            if num == 1:
                confidentiality = (FreeSpecDetailTemplate.objects.get(template_id=TemplateType.CONFIDENTIALITY.value, lost_flag=0)).detail
            # テンプレート（瑕疵担保責任）の取得
            num = FreeSpecDetailTemplate.objects.filter(template_id=TemplateType.WARRANTY.value, lost_flag=0).count()
            if num == 1:
                warranty = (FreeSpecDetailTemplate.objects.get(template_id=TemplateType.WARRANTY.value, lost_flag=0)).detail
            # テンプレート（検収条件）の取得
            num = FreeSpecDetailTemplate.objects.filter(template_id=TemplateType.ACCEPTANCE_CONDITIONS.value, lost_flag=0).count()
            if num == 1:
                acceptance_conditions = (FreeSpecDetailTemplate.objects.get(template_id=TemplateType.ACCEPTANCE_CONDITIONS.value, lost_flag=0)).detail
            # テンプレート（試運転の合格基準）の取得
            num = FreeSpecDetailTemplate.objects.filter(template_id=TemplateType.TEST_RUN_PASS.value, lost_flag=0).count()
            if num == 1:
                test_run_pass = (FreeSpecDetailTemplate.objects.get(template_id=TemplateType.TEST_RUN_PASS.value, lost_flag=0)).detail
            # テンプレート（検査の期間）の取得
            num = FreeSpecDetailTemplate.objects.filter(template_id=TemplateType.INSPECTION_PERIOD.value, lost_flag=0).count()
            if num == 1:
                inspection_period = (FreeSpecDetailTemplate.objects.get(template_id=TemplateType.INSPECTION_PERIOD.value, lost_flag=0)).detail


        # 計画担当者選択の候補の一覧用データ抽出
        work_planning_charge_person_lists = PlanningChargePerson.objects.filter(budget_id=budget_id, lost_flag=0).values()
        l = list(work_planning_charge_person_lists)
        charge_person_lists = [d.get('charge_person') for d in l]
        work_planning_charge_person_lists = User.objects.filter(username__in=charge_person_lists)

        # 実行担当者選択の候補の一覧用データ抽出　設備部管理部工務Gで絞り込み「CWG」
        work_execute_charge_person_lists = get_department_person_list('CWG')

        # 原課担当者選択の候補の一覧用データ抽出
        # 20210113 y-kawauchi 「予算基本情報」画面と仕様を合わせる
        sql = """ SELECT fms_user.* , fms_user.last_name +' '+fms_user.first_name as full_name """
        sql = sql + """ FROM fms_user """
        sql = sql + """ LEFT JOIN fms_userattribute ON fms_user.username=fms_userattribute.username """
        sql = sql + """ WHERE fms_userattribute.division='""" + work_charge_division + """' AND fms_user.lost_flag=0"""
        sql = sql + """ GROUP BY fms_user.username,fms_user.first_name,fms_user.last_name,fms_user.display_order,fms_user.lost_flag"""
        work_order_department_charge_person_lists = User.objects.all().raw(sql)

        # 工事区分(物品/工事)選択の候補の一覧用データ抽出
        work_class_lists = WorkClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')

        # 管理区分選択の候補の一覧用データ抽出
        management_class_list = WorkManagementClassMaster.objects.filter().all()

        # 部門選択の候補の一覧用データ抽出
        division_lists = DivisionMaster.objects.filter(lost_flag=0)

        # 部署選択の候補の一覧用データ抽出
        department_lists = DepartmentMaster.objects.filter(lost_flag=0)

        # 工程選択の候補の一覧用データ抽出
        process_lists = ProcessMaster.objects.filter(lost_flag=0)

        # 登録済みの要求機能一覧取得
        required_function_lists = required_function_list(budget_id)

        # 無効となった(=1つ前のrev_noの)対象の工事データのレコードがある場合
        if old_work_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象の工事データを取得
            old_work_data = Work.objects.filter(work_id=work_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_work_data = ""

        data = {
            'work_data': work_data,
            'old_work_data_num': old_work_data_num,
            'old_work_data': old_work_data,
            't_username': t_username,
            'work_id': work_id,
            'rev_no': rev_no,
            # 'target_work_rev_no': rev_no,
            'work_name': work_name,
            'required_function': required_function,
            'required_function_sub_no': required_function_sub_no,
            'work_class': work_class,
            'work_class_name': work_class_name,
            'management_class_cd': management_class_cd,
            'management_class_name': management_class_name,
            'work_planning_charge_person_name': work_planning_charge_person_name,
            'work_planning_charge_person': work_planning_charge_person,
            'work_execution_charge_person_name': work_execution_charge_person_name,
            'work_execution_charge_person': work_execution_charge_person,
            'work_order_department_charge_person_name': work_order_department_charge_person_name,
            'work_order_department_charge_person': work_order_department_charge_person,
            'work_order_department': work_order_department,
            'delivery_location': delivery_location,
            'start_date': start_date,
            'end_date': end_date,
            'delivery_date': delivery_date,
            'estimate_date': estimate_date,
            'estimate_limited_date': estimate_limited_date,
            'make_limited_date': make_limited_date,
            'order_limited_date': order_limited_date,
            'fixed_form': fixed_form,
            'estimate_range': estimate_range,
            #'budget_material': budget_material,
            'confidentiality': confidentiality,
            'warranty': warranty,
            'acceptance_conditions': acceptance_conditions,
            'witness_inspection': witness_inspection,
            'acceptance_inspection': acceptance_inspection,
            'test_run': test_run,
            'test_run_pass': test_run_pass,
            'inspection_period': inspection_period,
            'work_rem': work_rem,
            'work_charge_division': work_charge_division,
            'work_charge_division_text': work_charge_division_text,
            'work_charge_department': work_charge_department,
            'work_charge_department_text': work_charge_department_text,
            'work_charge_process_cd2': work_charge_process_cd2,
            'work_charge_process_cd': work_charge_process_cd,
            'work_charge_process_text': work_charge_process_text,
            'work_planning_charge_person_lists': work_planning_charge_person_lists,
            'work_execute_charge_person_lists': work_execute_charge_person_lists,
            'work_order_department_charge_person_lists': work_order_department_charge_person_lists,
            'work_class_lists': work_class_lists,
            'management_class_list': management_class_list,
            'division_lists': division_lists,
            'department_lists': department_lists,
            'process_lists': process_lists,
            'required_function_lists': required_function_lists,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'level5_step_id': level5_step_id,
            'is_mplan_flag': is_mplan_flag,
        }

        # データ編集機能要否判定
        work_edit_action_num = 0
        edit_flag = 0
        # 対象stepで「work」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                         target_table='work').count()

        if level5_step_id == 920000000:
            work_edit_action_num = 0

        if work_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/work/work_detail/work_common_edit.html', data)

        else:
            return render(request, 'fms/parts/work/work_detail/work_common_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事(初期)基本情報登録
@login_required
@require_POST
def work_default_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・空欄処理、数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])
        work_name = request.POST["work_name"]
        work_planning_charge_person = None if request.POST["work_planning_charge_person"] == "" else request.POST["work_planning_charge_person"]
        if request.POST["work_id"] == "":
            work_id = 0
        else:
            work_id = int(request.POST["work_id"])
        if request.POST["work_rev_no"] == "":
            work_rev_no = 0
        else:
            work_rev_no = int(request.POST["work_rev_no"])

        if request.POST["last_plan_id"] == "":
            last_plan_id = None
        else:
            last_plan_id = int(request.POST["last_plan_id"])

        this_step = int(request.POST["this_step"])

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 工事情報のレコード数を取得
        work_num = Work.objects.all().count()

        # 新規登録場合の処理
        if work_id == 0:
            # 工事情報のレコードがある場合の処理
            if work_num != 0:
                # 最終の工事idを取得
                work_data = Work.objects.all().order_by('-work_id')[0]
                # 今回の工事idを設定(=最終の工事id+1)
                this_work_id = work_data.work_id + 1

            # 工事情報のレコードがない場合の処理
            else:
                # 今回の工事idを「1」に設定
                this_work_id = 1
            # 「工事id」で工事情報のレコード抽出･･･ある場合は読み込み、ない場合は新規登録
            work_data, created =Work.objects.get_or_create(work_id=this_work_id)

            # 計画担当者の値から、ユーザー情報の対象となるレコードを取得･･･リレーション対応
            if work_planning_charge_person is None:
                wpcp = None
            else:
                wpcp = User.objects.get(username=work_planning_charge_person)

            # 各項目の値を格納
            rev_no = 0
            work_data.work_rev_no = rev_no
            work_data.work_budget_id = budget_id
            work_data.last_plan_id = last_plan_id
            work_data.entry_datetime = now
            work_data.entry_operator = operator
            work_data.work_name = work_name
            work_data.work_planning_charge_person = wpcp
            work_data.entry_on_progress_flag = 1
            work_data.lost_flag = 0
            work_id = work_data.work_id
            # 工事情報のレコードを保存
            work_data.save()

        # 更新場合の処理
        else:
            # 対象の工事idで、作業中のレコード数を取得
            on_progress_work_num = Work.objects.filter(work_id=work_id, entry_on_progress_flag=1).count()
            # 対象の工事idで、完了(作業中でない)のレコード数を取得
            complete_entry_work_num = Work.objects.filter(work_id=work_id, entry_on_progress_flag=0).count()

            # 対象の工事idで、完了(作業中でない)のレコードがある場合の処理
            if complete_entry_work_num > 0:
                # 対象の工事id、作業中でないレコードの最新(主キーが大きい)もののレコードを抽出
                work_data = Work.objects.filter(work_id=work_id, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得
                latest_rev_no = work_data.work_rev_no
                # 対象のレコードを無効化(lost_flag = 1)
                work_data.lost_flag = 1
                # 工事情報のレコードを保存
                work_data.save()

            # 対象の工事idで、完了(作業中でない)のレコードがない場合の処理
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 対象の工事idで、作業中のレコードがない場合
            if on_progress_work_num == 0:
                # 「work_id」、「登録日時」、「登録者」で工事情報に新規登録
                Work(work_id=work_id, entry_datetime=now, entry_operator=operator).save()
                # 「登録日時」、「登録者」の値で登録した工事情報のレコード抽出
                work_data = Work.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーの値を取得
                work_unique_id = work_data.id
                # 「主キー」の値で工事情報からレコード抽出
                work_data = Work.objects.get(id=work_unique_id)
                # 各項目の値を格納
                work_data.work_rev_no = latest_rev_no + 1
                rev_no = latest_rev_no + 1
                work_data.entry_on_progress_flag = 1
                work_data.lost_flag = 0
                this_budget_id = work_data.work_budget_id
                # 工事情報のレコード保存
                work_data.save()

                # 提出書類、工事関連法令、工事支給品、見積情報に対するrev_noアップ処理
                # 1つ前のrev_noの提出書類のレコードを抽出･･･複数あれば全て抽出
                document_data = SubmissionDocument.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=latest_rev_no)
                # 抽出されたレコードに対し繰り返し処理
                for document_data in document_data:
                    # 次のrevに引き継ぐデータを取得
                    document_name = document_data.document_name
                    number_of_copies = document_data.number_of_copies
                    submission_deadline = document_data.submission_deadline
                    display_order = document_data.display_order
                    entry_class = document_data.entry_class
                    # レコードの無効化(lost_flag = 1)
                    document_data.lost_flag = 1
                    # 提出書類のレコードを保存
                    document_data.save()

                    # 「work_id」、「rev_no」、「提出書類名」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                    document_data, created = SubmissionDocument.objects.get_or_create(work_id=work_id, entry_class=entry_class, rev_no=rev_no,
                                                                                      document_name=document_name)
                    # 各項目の値(1つ前のrevでの値)を格納
                    document_data.submission_deadline = submission_deadline
                    document_data.number_of_copies = number_of_copies
                    document_data.display_order = display_order
                    document_data.entry_class = entry_class
                    document_data.lost_flag = 0
                    document_data.entry_on_progress_flag = 1
                    document_data.entry_datetime = now
                    document_data.entry_operator = operator
                    # 提出書類のレコードを保存
                    document_data.save()

                # 1つ前のrev_noの工事関連法令のレコードを抽出･･･複数あれば全て抽出
                work_law_data = WorkLaw.objects.filter(work_id=work_id, rev_no=latest_rev_no,
                                                       entry_class=entry_class, lost_flag=0)
                # 抽出されたレコードに対し繰り返し処理
                for work_law_data in work_law_data:
                    # 次のrevに引き継ぐデータを取得
                    law_name = work_law_data.law_name
                    entry_class = work_law_data.entry_class
                    # レコードの無効化(lost_flag = 1)
                    work_law_data.lost_flag = 1
                    # 工事関連法令のレコードを保存
                    work_law_data.save()

                    # 「work_id」、「rev_no」、「法令名」で工事関連法令のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                    work_law_data, created = WorkLaw.objects.get_or_create(work_id=work_id, rev_no=rev_no,
                                                                           law_name=law_name, entry_class=entry_class)
                    # 各項目の値(1つ前のrevでの値)を格納
                    work_law_data.entry_class = entry_class
                    work_law_data.lost_flag = 0
                    work_law_data.entry_on_progress_flag = 1
                    work_law_data.entry_datetime = now
                    work_law_data.entry_operator = operator
                    # 工事関連法令のレコードを保存
                    work_law_data.save()

                # 1つ前のrev_noの工事支給品のレコードを抽出･･･複数あれば全て抽出
                work_supplies_data = Supplies.objects.filter(work_id=work_id, rev_no=latest_rev_no, entry_class=entry_class)
                # 抽出されたレコードに対し繰り返し処理
                for work_supplies_data in work_supplies_data:
                    # 次のrevに引き継ぐデータを取得
                    supplies_name = work_supplies_data.supplies_name
                    entry_class = work_supplies_data.entry_class
                    # レコードの無効化(lost_flag = 1)
                    work_supplies_data.lost_flag = 1
                    # 工事支給品のレコードを保存
                    work_supplies_data.save()

                    # 「work_id」、「rev_no」、「支給品名」で工事支給品のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                    work_supplies_data, created = Supplies.objects.get_or_create(work_id=work_id, rev_no=rev_no,
                                                                                 supplies_name=supplies_name,
                                                                                 entry_class=entry_class)
                    # 各項目の値(1つ前のrevでの値)を格納
                    # work_supplies_data.work_id = work_id
                    work_supplies_data.entry_class = entry_class
                    work_supplies_data.lost_flag = 0
                    work_supplies_data.entry_on_progress_flag = 1
                    work_supplies_data.entry_datetime = now
                    work_supplies_data.entry_operator = operator
                    # 工事支給品のレコードを保存
                    work_supplies_data.save()

                # 1つ前のrev_noの見積情報のレコードを抽出･･･複数あれば全て抽出
                estimate_data = Estimate.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=latest_rev_no)
                # 抽出されたレコードに対し繰り返し処理
                for estimate_data in estimate_data:
                    # 次のrevに引き継ぐデータを取得
                    vendor = estimate_data.vendor
                    estimate_price = estimate_data.estimate_price
                    prospect_price = estimate_data.prospect_price
                    entry_class = estimate_data.entry_class
                    estimate_data_entry_datetime = estimate_data.entry_datetime
                    estimate_data_entry_operator = estimate_data.entry_operator
                    estimate_data_adoption_flag = estimate_data.adoption_flag
                    estimate_data_discount_num = estimate_data.discount_num
                    estimate_data_start_date = estimate_data.start_date
                    estimate_data_end_date = estimate_data.end_date
                    estimate_data_rem = estimate_data.rem
                    estimate_data_lost_flag = estimate_data.lost_flag
                    # レコードの無効化(lost_flag = 1)
                    estimate_data.lost_flag = 1
                    # 見積情報のレコードを保存
                    estimate_data.save()

                    # 「work_id」、「rev_no」、「業者名」で見積情報のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                    estimate_data, created = Estimate.objects.get_or_create(work_id=work_id, entry_class=entry_class, rev_no=rev_no, vendor=vendor)
                    # 各項目の値(1つ前のrevでの値)を格納
                    estimate_data.work_id = work_id
                    estimate_data.entry_class = entry_class
                    estimate_data.vendor = vendor
                    estimate_data.estimate_price = estimate_price
                    estimate_data.prospect_price = prospect_price
                    # 削除済の見積はそのままlost_flag=1
                    estimate_data.lost_flag = estimate_data_lost_flag
                    estimate_data.entry_on_progress_flag = 1
                    estimate_data.entry_datetime = estimate_data_entry_datetime
                    estimate_data.entry_operator = estimate_data_entry_operator
                    estimate_data.update_datetime = now
                    estimate_data.update_operator = operator
                    estimate_data.adoption_flag = estimate_data_adoption_flag
                    estimate_data.discount_num = estimate_data_discount_num
                    estimate_data.start_date = estimate_data_start_date
                    estimate_data.end_date = estimate_data_end_date
                    estimate_data.rem = estimate_data_rem
                    # 見積情報のレコードを保存
                    estimate_data.save()

            # 対象の工事idで、作業中のレコードがある場合
            else:
                # 「work_id」と「作業中FL」で工事情報のレコードを取得
                work_data = Work.objects.get(work_id=work_id, entry_on_progress_flag=1)
                # 主キーの値取得
                work_unique_id = work_data.id
                # 予算idの値を取得
                this_budget_id = work_data.work_budget_id
                # rev_noを取得
                rev_no = work_data.work_rev_no

        msg = "初期登録完了！！"

        ary = {
            'work_id': work_id,
            'rev_no': rev_no,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事共通情報登録
@login_required
@require_POST
def work_common_entry(request):
    from .construction_policy_overview_views import policy_overview_reset_progress_flag
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、日付処理、リレーション対応処理を含む
        work_id = int(request.POST["work_id"])
        work_rev_no = int(request.POST["work_rev_no"])
        budget_id = int(request.POST["budget_id"])
        this_budget_id = budget_id
        work_name = request.POST["work_name"]
        # work_planning_charge_person = request.POST["work_planning_charge_person"]
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        # next_person_id = int(request.POST["next_person_id"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        comment = request.POST["comment"]
        work_required_function = None if request.POST["work_required_function"] is "" else request.POST["work_required_function"]
        work_required_function_sub_no = None if request.POST["work_required_function_sub_no"] is "" else request.POST["work_required_function_sub_no"]

        is_mplan_flag = is_mplan_budget_step(this_step)

        work_charge_process = request.POST.get('work_charge_process')
        if work_charge_process == "":
            wcprc = None
        else:
            wcprc = ProcessMaster.objects.get(process_cd2=work_charge_process)
        work_class = request.POST["work_class"]
        if work_class == "":
            wcrc = None
        else:
            wcrc = WorkClassMaster.objects.get(work_class_cd=work_class)
        management_class_cd = request.POST['management_class_cd']
        work_order_department = request.POST["work_charge_department"]
        if work_order_department == "":
            wodrc = None
        else:
            wodrc = DepartmentMaster.objects.get(department_cd=work_order_department)
        work_order_department_charge_person = request.POST["work_order_department_charge_person"]
        if work_order_department_charge_person == "":
            wodcprc = None
        else:
            wodcprc = User.objects.get(username=work_order_department_charge_person)
        work_planning_charge_person = request.POST["work_planning_charge_person"]
        if work_planning_charge_person == "":
            wpcprc = None
        else:
            wpcprc = User.objects.get(username=work_planning_charge_person)
        work_execution_charge_person = request.POST["work_execution_charge_person"]
        if work_execution_charge_person == "":
            wecprc = None
        else:
            wecprc = User.objects.get(username=work_execution_charge_person)
        delivery_location = None if request.POST["delivery_location"] is "" else request.POST["delivery_location"]
        start_date_str = request.POST["start_date"]
        # start_date_str = start_date_str.replace('年', '-')
        # start_date_str = start_date_str.replace('月', '-')
        # start_date = start_date_str.replace('日', '')
        date_str = date_to_many_type(start_date_str)
        start_date = date_str.date_type_date
        end_date_str = request.POST["end_date"]
        # end_date_str = end_date_str.replace('年', '-')
        # end_date_str = end_date_str.replace('月', '-')
        # end_date = end_date_str.replace('日', '')
        date_str = date_to_many_type(end_date_str)
        end_date = date_str.date_type_date
        delivery_date_str = request.POST["delivery_date"]
        # delivery_date_str = delivery_date_str.replace('年', '-')
        # delivery_date_str = delivery_date_str.replace('月', '-')
        # delivery_date = delivery_date_str.replace('日', '')
        date_str = date_to_many_type(delivery_date_str)
        delivery_date = date_str.date_type_date
        estimate_date_str = request.POST["estimate_date"]
        # estimate_date_str = estimate_date_str.replace('年', '-')
        # estimate_date_str = estimate_date_str.replace('月', '-')
        # estimate_date = estimate_date_str.replace('日', '')
        date_str = date_to_many_type(estimate_date_str)
        estimate_date = date_str.date_type_date
        estimate_limited_date_str = request.POST["estimate_limited_date"]
        # estimate_limited_date_str = estimate_limited_date_str.replace('年', '-')
        # estimate_limited_date_str = estimate_limited_date_str.replace('月', '-')
        # estimate_limited_date = estimate_limited_date_str.replace('日', '')
        date_str = date_to_many_type(estimate_limited_date_str)
        estimate_limited_date = date_str.date_type_date
        make_limited_date_str = request.POST["make_limited_date"]
        # make_limited_date_str = make_limited_date_str.replace('年', '-')
        # make_limited_date_str = make_limited_date_str.replace('月', '-')
        # make_limited_date = make_limited_date_str.replace('日', '')
        date_str = date_to_many_type(make_limited_date_str)
        make_limited_date = date_str.date_type_date
        order_limited_date_str = request.POST["order_limited_date"]
        # order_limited_date_str = order_limited_date_str.replace('年', '-')
        # order_limited_date_str = order_limited_date_str.replace('月', '-')
        # order_limited_date = order_limited_date_str.replace('日', '')
        date_str = date_to_many_type(order_limited_date_str)
        order_limited_date = date_str.date_type_date

        fixed_form = None if request.POST["fixed_form"] is "" else request.POST["fixed_form"]
        estimate_range = None if request.POST["estimate_range"] is "" else request.POST["estimate_range"]
        #budget_material = None if request.POST["budget_material"] is "" else int(request.POST["budget_material"])
        confidentiality = None if request.POST["confidentiality"] is "" else request.POST["confidentiality"]
        warranty = None if request.POST["warranty"] is "" else request.POST["warranty"]
        acceptance_conditions = None if request.POST["acceptance_conditions"] is "" else request.POST["acceptance_conditions"]
        witness_inspection = None if request.POST["witness_inspection"] is "" else int(request.POST["witness_inspection"])
        acceptance_inspection = None if request.POST["acceptance_inspection"] is "" else int(request.POST["acceptance_inspection"])
        test_run = None if request.POST["test_run"] is "" else int(request.POST["test_run"])
        test_run_pass = None if request.POST["test_run_pass"] is "" else request.POST["test_run_pass"]
        inspection_period = None if request.POST["inspection_period"] is "" else request.POST["inspection_period"]
        work_rem = None if request.POST["work_rem"] is "" else request.POST["work_rem"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        last_plan_id = None if request.POST["last_plan_id"] is "" else int(request.POST["last_plan_id"])

        # 次の工程(step)に進まない(=一時保存等)場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了！！"
        # 次の工程(step)に進む(=作成完了等)場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step)
            step_name = step_data.step_name
            msg = step_name + "作成完了！！"

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 「work_id」、「rev_no」で工事情報のレコードを抽出
        work_data = Work.objects.get(work_id=work_id, work_rev_no=work_rev_no)
        # 各項目の値を格納
        work_data.work_name = work_name
        work_data.work_budget_id = budget_id
        rev_no = work_data.work_rev_no
        work_data.work_required_function = work_required_function
        work_data.sub_no = work_required_function_sub_no
        work_data.work_charge_process = wcprc
        work_data.work_class = wcrc
        work_data.management_class_cd = management_class_cd or None
        work_data.work_order_department = wodrc
        work_data.work_order_department_charge_person = wodcprc
        work_data.work_planning_charge_person = wpcprc
        work_data.work_execution_charge_person = wecprc
        work_data.delivery_location = delivery_location
        work_data.last_plan_id = last_plan_id

        # 計画区分
        if is_mplan_flag:
            work_data.plan_class_id = 'M'
        else:
            work_data.plan_class_id = 'S'

        if start_date == "":
            work_data.work_start_date = None
        else:
            work_data.work_start_date = start_date
        if end_date == "":
            work_data.work_end_date = None
        else:
            work_data.work_end_date = end_date
        if delivery_date == "":
            work_data.work_delivery_date = None
        else:
            work_data.work_delivery_date = delivery_date
        if estimate_date == "":
            work_data.estimate_date = None
        else:
            work_data.estimate_date = estimate_date
        if estimate_limited_date == "":
            work_data.work_estimate_limited_date = None
        else:
            work_data.work_estimate_limited_date = estimate_limited_date
        if make_limited_date == "":
            work_data.make_limited_date = None
        else:
            work_data.make_limited_date = make_limited_date
        if order_limited_date == "":
            work_data.order_limited_date = None
        else:
            work_data.order_limited_date = order_limited_date
        if fixed_form == "":
            work_data.fixed_form = None
        else:
            work_data.fixed_form = fixed_form
        if estimate_range == "":
            work_data.estimate_range = None
        else:
            work_data.estimate_range = estimate_range
        # if budget_material == "":
        #     work_data.budget_material = None
        # else:
        #     work_data.budget_material = budget_material
        if confidentiality == "":
            work_data.confidentiality = None
        else:
            work_data.confidentiality = confidentiality
        if warranty == "":
            work_data.warranty = None
        else:
            work_data.warranty = warranty
        if acceptance_conditions == "":
            work_data.acceptance_conditions = None
        else:
            work_data.acceptance_conditions = acceptance_conditions
        if witness_inspection == "":
            work_data.witness_inspection = None
        else:
            work_data.witness_inspection = witness_inspection
        if acceptance_inspection == "":
            work_data.acceptance_inspection = None
        else:
            work_data.acceptance_inspection = acceptance_inspection
        if test_run == "":
            work_data.test_run = None
        else:
            work_data.test_run = test_run
        if test_run_pass == "":
            work_data.test_run_pass = None
        else:
            work_data.test_run_pass = test_run_pass
        if inspection_period == "":
            work_data.inspection_period = None
        else:
            work_data.inspection_period = inspection_period
        work_data.work_rem = None if work_rem is "" else work_rem
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 作業中FLに「0」を設定
            work_data.entry_on_progress_flag = 0
        # 次の工程(step)に進まない場合
        else:
            # 作業中FLに「1」を設定
            work_data.entry_on_progress_flag = 1

        work_data.update_datetime = now
        work_data.update_operator = operator

        # 工事関連法令のレコードを保存
        work_data.save()

        # ユーザー属性から次作業者名を取得
        # user_attribute_data = UserAttribute.objects.get(id=next_person_id)
        # next_person = user_attribute_data.username

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 「target="work"」と「work_id」で進捗状況の対象レコードを抽出･･･あれば読み込み、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="work", target_id=work_id)
        # 中止前の作業者を確保
        before_stop_person = progress_data.present_operator
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

        # 関連テーブルの作業中FL(entry_on_progress_flag)を「0」にする
        # 次の工程(step)に進む場合
        if this_step != next_step:
            # 対象の「工事id」、「rev_no」で自由記入仕様のレコードを取得
            free_spec_detail_list = FreeSpecDetail.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for free_spec_detail_list in free_spec_detail_list:
                # 作業中FLに「0」をセット
                free_spec_detail_list.entry_on_progress_flag = 0
                # 自由記入仕様のレコードを保存
                free_spec_detail_list.save()

            # 対象の「工事id」、「rev_no」で提出書類のレコードを取得
            submission_document_list = SubmissionDocument.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for submission_document_list in submission_document_list:
                # 作業中FLに「0」をセット
                submission_document_list.entry_on_progress_flag = 0
                # 提出書類のレコードを保存
                submission_document_list.save()

            # 対象の「工事id」、「rev_no」で見積のレコードを取得
            estimate_list = Estimate.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for estimate_list in estimate_list:
                # 作業中FLに「0」をセット
                estimate_list.entry_on_progress_flag = 0
                # 見積のレコードを保存
                estimate_list.save()

            # 対象の「工事id」、「rev_no」で支給品のレコードを取得
            supplies_list = Supplies.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no,lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for supplies_list in supplies_list:
                # 作業中FLに「0」をセット
                supplies_list.entry_on_progress_flag = 0
                # 支給品のレコードを保存
                supplies_list.save()

            # 対象の「工事id」、「rev_no」で適用法令のレコードを取得
            work_law_list = WorkLaw.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for work_law_list in work_law_list:
                # 作業中FLに「0」をセット
                work_law_list.entry_on_progress_flag = 0
                # 適用法令のレコードを保存
                work_law_list.save()

            # 対象の「工事id」、「rev_no」で熱交換詳細仕様のレコードを取得
            work_spec_m_ex_list = WorkSpecMEX.objects.filter(work_id=work_id, entry_class=entry_class, rev_no=rev_no, lost_flag=0).all()
            # 抽出されたレコードに対し繰り返し処理
            for work_spec_m_ex_list in work_spec_m_ex_list:
                # 作業中FLに「0」をセット
                work_spec_m_ex_list.entry_on_progress_flag = 0
                # 熱交換詳細仕様のレコードを保存
                work_spec_m_ex_list.save()

            # 工事方針概要
            policy_overview_reset_progress_flag(this_budget_id)

        # 進捗通知機能
        if this_step != next_step:
            step_notice(progress_data)

        # ログを新規登録
        Log(target='work', target_id=work_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        # 仕様書予算見積完了チェック
        check_result = check_work_estimates_complete(work_id)

        ary = {
            'before_stop_person': before_stop_person,
            'msg': msg,
            'check_result': check_result
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事データ一覧
@require_POST
def get_work_lists(request):
    try:
        work_lists = ""
        work_lists_num = ""
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
        sel_on_work = request.POST['sel_on_work']
        level5_step_id = int(request.POST['level5_step_id'])
        sel_display_order = request.POST['sel_display_order']
        list_kind = request.POST['list_kind']
        sel_work_id = request.POST['sel_work_id']
        sel_work_name = request.POST['sel_work_name']
        sel_planning_charge_person = request.POST['sel_planning_charge_person']
        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000

        where_str = ""
        where_parm = []
        ex_select_str = ""
        is_mplan_flag = is_mplan_budget_step(level5_step_id)

        # 検索条件
        # 計画区分
        where_str += " AND fms_work.plan_class_id = %s \n"
        if is_mplan_flag:
            where_parm.append('M')
        else:
            where_parm.append('S')

        # 予算状態
        if sel_budget_condition != "":
            where_str += " AND fms_budgetconditionmaster.condition_id = %s \n"
            where_parm.append(int(sel_budget_condition))
        # 進捗状況
        if sel_step != "":
            where_str += " AND fms_stepmaster.step_id = %s"
            where_parm.append(int(sel_step))
        # 年度
        if sel_business_year != "":
            where_str += " AND fms_budget.business_year_id = %s"
            where_parm.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            where_str += " AND fms_budget.budget_class_id = %s"
            where_parm.append(int(sel_budget_class))
        # 予算ID
        if sel_budget_id != "":
            where_str += " AND fms_budget.budget_id = %s"
            where_parm.append(int(sel_budget_id))
        # 予算NO
        if sel_budget_no != "":
            where_str += " AND fms_budget.budget_no = %s"
            where_parm.append(sel_budget_no)
        # 予算名
        if sel_budget_name != "":
            if is_mplan_flag:
                where_str += " AND fms_budget.request_name LIKE %s \n"
            else:
                where_str += " AND fms_budget.budget_name LIKE %s \n"
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
            where_str += " AND fms_work.work_id = %s"
            where_parm.append(sel_work_id)
        # 工事名
        if sel_work_name != "":
            where_str += " AND fms_work.work_name LIKE %s"
            where_parm.append('%' + sel_work_name + '%')

        # 計画担当者
        ex_select_str += ", planningchargepersondata.first_name AS planningchargepersondata_first_name"
        ex_select_str += ", planningchargepersondata.last_name AS planningchargepersondata_last_name"
        # 計画担当者名をリストに表示するためのusernameをJOIN
        planning_charge_person_join_str = 'LEFT JOIN fms_user as planningchargepersondata ON fms_work.work_planning_charge_person_id=planningchargepersondata.username ' \
                                          'and planningchargepersondata.lost_flag = 0 '
        if sel_planning_charge_person != "":
            # 計画担当者名をリストに表示するためのusernameを追加
            where_str += " AND planningchargepersondata.username = %s"
            where_parm.append(sel_planning_charge_person)

        # 未処理のみにチェックがある場合、ユーザーを限定する
        if sel_on_work == 'true':
            # この下2行をコメントアウトし、4行を追加・・・2021/01/11 ueda
            # where_str += " AND fms_work.update_operator = %s"
            # where_parm.append(username)
            where_str += " AND fms_stepmaster.step_id > %s"
            where_parm.append(step_st)
            where_str += " AND fms_stepmaster.step_id < %s"
            where_parm.append(step_ed)

            # この上3行をコメントアウトし、6行を追加・・・2021/01/11 ueda

        # 対象工事レコード抽出
        sql = """ SELECT fms_work.*, fms_user.first_name, fms_user.last_name, fms_stepmaster.step_name, fms_stepmaster.step_id  """
        sql = sql + """ ,fms_budgetconditionmaster.condition_name """
        sql = sql + """ ,fms_departmentmaster.department_name  """
        sql = sql + """ ,fms_budget.budget_name,fms_businessyearmaster.business_year , fms_budget.id  as budget_unique_id"""
        sql = sql + """ ,fms_budget.budget_id as budget_id, fms_budget.budget_no as budget_no"""
        if is_mplan_flag:
            sql = sql + """ ,fms_budget.request_name as request_name"""

        sql = sql + """ ,fms_budgetclassmaster.budget_class_name as  budget_class"""
        sql = sql + """ ,fms_processmaster.process_cd2 as process_cd, fms_processmaster.process_name as process_name """
        sql = sql + """ ,fms_progress.present_operator as  present_operator"""
        sql = sql + """ ,CASE WHEN budget_no IS NULL THEN '' ELSE budget_no END AS bd_no """
        sql = sql + """ ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_work.entry_datetime, GETDATE()) """
        sql = sql + """                                     ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END """
        sql = sql + """ AS days_stay """
        sql = sql + """ , CASE WHEN log_2.action = 'return' THEN 1 """
        sql = sql + """ ELSE 0 """
        sql = sql + """ END AS return_flag """
        sql = sql + ex_select_str
        sql = sql + """ FROM ((((((( fms_work """
        sql = sql + """ LEFT JOIN fms_budget ON fms_work.work_budget_id=fms_budget.budget_id )"""
        sql = sql + """ LEFT JOIN fms_budgetcondition ON fms_budget.budget_id=fms_budgetcondition.budget_id) """
        sql = sql + """ LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id) """

        sql = sql + """ INNER JOIN fms_progress ON fms_work.work_id=fms_progress.target_id AND fms_progress.target='work') """
        sql = sql + """ LEFT JOIN fms_user ON fms_progress.present_operator=fms_user.username) """
        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id) """
        sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd) """
        sql = sql + """ LEFT JOIN fms_businessyearmaster ON fms_budget.business_year_id=fms_businessyearmaster.business_year """
        sql = sql + """ LEFT JOIN fms_budgetclassmaster ON fms_budget.budget_class_id=fms_budgetclassmaster.budget_class_cd """
        sql = sql + """ LEFT JOIN fms_processmaster ON fms_budget.facility_process_id=fms_processmaster.process_cd2 """
        sql = sql + """ LEFT JOIN (SELECT """
        sql = sql + """             [target_id] """
        sql = sql + """             ,MAX([operation_datetime]) as last_operationtime """
        sql = sql + """             FROM [fms].[dbo].[fms_log] """
        sql = sql + """             WHERE [target]='work' """
        sql = sql + """                             AND [action] != 'temporarily_saved' """
        sql = sql + """             group by [target_id]) as log """
        sql = sql + """ ON [fms].[dbo].[fms_work].work_id=log.target_id """

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
                                [target] = 'work' AND [action] != 'temporarily_saved'
                            GROUP BY [target_id]
                            ) AS main
                            INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime AND main.target_id=sub.target_id
                        WHERE
                            main.[operation_datetime] = sub.operation_datetime """
        sql = sql + """ ) AS log_2 """
        sql = sql + """ ON fms_work.work_id = log_2.target_id """
        sql = sql + planning_charge_person_join_str
        sql = sql + """ WHERE fms_work.lost_flag=0 AND fms_budget.lost_flag=0"""
        if where_str != "":
            sql += where_str

        if sel_display_order == "1":
            sql += " ORDER BY fms_budget.budget_id"
        elif sel_display_order == "2":
            sql += " ORDER BY fms_budget.budget_no"
        elif sel_display_order == "3":
            sql += " ORDER BY days_stay desc"
        else:  # sel_display_order == "4":
            sql += " ORDER BY fms_work.work_id"

        if len(where_parm) == 0:
            work_lists = Work.objects.all().raw(sql)
        else:
            work_lists = Work.objects.raw(sql, where_parm)
        work_lists_num = len(list(work_lists))

        budget_name_text = get_budget_name_text(level5_step_id)

        if list_kind == 'work':
            return_url = 'fms/parts/work/work_lists.html'
            data = {
                'work_lists': work_lists,
                'work_lists_num': work_lists_num,
                'is_mplan_flag': is_mplan_flag,
                'budget_name_text': budget_name_text,
            }
        elif list_kind == 'copy_work':
            return_url = 'fms/parts/work/work_copy_source/work_copy_source_list.html'
            data = {
                'execution_work_lists': work_lists,
                'execution_work_lists_num': work_lists_num,
                'level5_step_id': level5_step_id,
                'is_mplan_flag': is_mplan_flag,
                'budget_name_text': budget_name_text,
            }
        else:
            return
        return render(request, return_url, data)

        # return render(request, 'fms/parts/work/work_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事一覧の絞込のパーツ表示
@require_POST
def work_filter(request):
    from fms.views.common_def_views import get_filter_master, get_next_target
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        step_st = math.floor(level5_step_id / 1000000) * 1000000
        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        planning_charge_person_list = get_filter_planning_charge_person_list()

        budget_name_text = get_budget_name_text(level5_step_id)

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
            'target_department': target_department,
            'user_division_cd': target_division,
            'target_person': target_person,
            'planning_charge_person_list': planning_charge_person_list,
            'budget_name_text': budget_name_text,
        }

        return render(request, 'fms/parts/work/work_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def required_function_list(target_id):
    # 対象予算idに対する登録済要求機能のデータ取得
    sql = """ SELECT A.id, A.required_function_id, A.sub_no, B.function_name
              FROM fms_budgetrequiredfunction A
              LEFT JOIN fms_functionmaster B ON A.required_function_id = B.function_cd
              WHERE A.budget_id = %s AND A.lost_flag=0 """
    lists = BudgetRequiredFunction.objects.all().raw(sql, [target_id])
    num = len(list(lists))

    return lists


# テスト用
# バイナリファイルDB書込み
def additional_document_save(request):
    try:
        path = request.POST['path']

        #doc = open(path, 'rb').read()
        # sql = "INSERT INTO sometable (theblobcolumn) VALUES (%s)"
        # cursor.execute(sql, (doc,))

        try:
            with open(path, 'rb') as f:
                doc = f.read()

            with connections['fmsdb'].cursor() as cursor:
                sql = """ INSERT INTO
                            fms_additionaldocuments (file_no, [file])
                            VALUES (%s, %s) """
                cursor.execute(sql, (1, doc))
                msg = path + "\n登録しました！！"
        except Exception:
            msg = e

        result = {
            'msg': msg,
        }

        return JsonResponse(result)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# バイナリファイルDBより取得→ファイル生成
def additional_document_read(request):
    try:
        path = request.POST['path']
        # id = request.POST['id']

        try:
            with connections['fmsdb'].cursor() as cursor:
                sql = """ SELECT [file]
                            FROM fms_additionaldocuments
                            WHERE id = %s """
                cursor.execute(sql, [2])
                for row in cursor:
                    lists = [elem for elem in row]
                num = len(lists)

                with open(path, 'wb') as f:
                    f.write(lists[0])

                msg = path + "\n取得しました！！"
        except Exception:
            msg = e

        result = {
            'msg': msg,
        }

        return JsonResponse(result)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 計画工事データコピー
@require_POST
def plan_work_copy(request):
    try:
        target_work_unique_id = int(request.POST["target_work_unique_id"])
        target = request.POST["target"]
        work_rev_no = request.POST["work_rev_no"]
        copy_target = "work"

        work_data = Work.objects.get(id=target_work_unique_id)
        budget_id = work_data.work_budget_id
        work_id = work_data.work_id
        rev_no = work_data.work_rev_no

        entry_class = '計画'

        if work_data.management_class_cd is not None and work_data.management_class_cd != "":
            management_class_cd = work_data.management_class_cd
        else:
            management_class_cd = ""

        if work_data.work_charge_process is not None and work_data.work_charge_process != "":
            work_charge_process = work_data.work_charge_process.process_cd
            work_charge_process_text = ProcessMaster.objects.get(process_cd2=work_charge_process
                                                                 ).process_name if work_charge_process is not "" else ""
        else:
            work_charge_process = ""
            work_charge_process_text = ""

        if work_data.work_class is not None and work_data.work_class != "":
            work_class = work_data.work_class.work_class_cd
        else:
            work_class = ""

        if work_data.delivery_location is not None and work_data.delivery_location != "":
            delivery_location = work_data.delivery_location
        else:
            delivery_location = ""

        if work_data.fixed_form is not None and work_data.fixed_form != "":
            fixed_form = work_data.fixed_form
        else:
            fixed_form = ""

        if work_data.estimate_range is not None and work_data.estimate_range != "":
            estimate_range = work_data.estimate_range
        else:
            estimate_range = ""

        # 登録済みの法令の数をカウント
        law_list_num = WorkLaw.objects.filter(work_id=work_id, entry_class=entry_class, lost_flag=0).count()

        # 登録済の支給品のレコード数を取得
        work_supplies_lists_num = Supplies.objects.filter(work_id=work_id, entry_class=entry_class, lost_flag=0).count()

        # 登録済の仕様詳細の数をカウント
        free_spec_list_num = FreeSpecDetail.objects.filter(work_id=work_id, entry_class=entry_class, lost_flag=0).count()

        # 登録済の関係機器情報の数をカウント
        equipment_list_num = WorkEquipment.objects.filter(budget_id=budget_id, work_id=work_id, lost_flag=0).count()

        # 登録済の提出書類の数をカウント
        document_lists_num = SubmissionDocument.objects.filter(work_id=work_id, entry_class=entry_class,
                                                               lost_flag=0).count()

        # 格納先path作成　idを汎用的にするため「level4_id」「level5_id」としたい。
        file_folder = '\\' + copy_target + '\\' + str(budget_id) + '\\' + str(work_id) + '\\'
        # 登録済の添付ファイルの数をカウント
        uploadfile_list_num = AttachmentDocuments.objects.filter(folder=file_folder, div_id_name=copy_target,
                                                                 lost_flag=0).count()

        msg = '工事内容をコピーしました。保存されていないので、保存してください！！'

        ary = {
            'msg': msg,
            # 'work_data': work_data,
            'budget_id': budget_id,
            # 'work_name': work_name,
            # 'work_charge_department': work_order_department,
            # 'work_charge_department_name': work_order_department_name,
            # 'work_charge_division': work_charge_division,
            # 'work_charge_division_name': work_charge_division_name,
            'management_class_cd': management_class_cd,
            'work_charge_process': work_charge_process,
            'work_charge_process_text': work_charge_process_text,
            'work_class': work_class,
            'delivery_location': delivery_location,
            'fixed_form': fixed_form,
            'estimate_range': estimate_range,
            'law_list_num': law_list_num,
            'work_supplies_lists_num': work_supplies_lists_num,
            'free_spec_list_num': free_spec_list_num,
            'equipment_list_num': equipment_list_num,
            'document_lists_num': document_lists_num,
            'uploadfile_list_num': uploadfile_list_num,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 仕様詳細コピー処理
@require_POST
def copy_free_spec_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        work_id = int(request.POST["work_id"])
        this_step = int(request.POST["this_step"])
        copy_work_id = int(request.POST['copy_work_id'])
        copy_step_no = int(request.POST['copy_step_no'])
        rev_no = int(request.POST['rev_no'])

        copy_free_spec_detail_detail_data =[]

        # コピー元のstepからデータ登録タイミングを判定
        if copy_step_no < 200000000:
            entry_class = "計画"
            copy_free_spec_detail_list = FreeSpecDetail.objects.filter(work_id=copy_work_id, entry_class=entry_class,
                                                                       lost_flag=0)
            for copy_free_spec_detail_data in copy_free_spec_detail_list:
                # 現在のstepからデータ登録タイミングを判定
                if this_step < 200000000:
                    entry_class = "計画"
                    # 「work_id」、「lost_flag」、「登録区分」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録
                    # (ないはずなので新規登録)
                    free_spec_detail_data, created = FreeSpecDetail.objects.get_or_create(work_id=work_id,
                                                                                          entry_class=entry_class,
                                                                                          sub_no=copy_free_spec_detail_data.sub_no,
                                                                                          lost_flag=0)
                    # 各項目の値(1つ前のrevでの値)を格納
                    # free_spec_detail_data.sub_no = copy_free_spec_detail_data.sub_no
                    free_spec_detail_data.required_function_id = copy_free_spec_detail_data.required_function_id
                    free_spec_detail_data.required_function_sub_no = copy_free_spec_detail_data.required_function_sub_no
                    free_spec_detail_data.detail = None_to_blank(copy_free_spec_detail_data.detail)
                    free_spec_detail_data.entry_on_progress_flag = 1

                    if created == 1:
                        free_spec_detail_data.rev_no = rev_no

                    free_spec_detail_data.entry_datetime = now
                    free_spec_detail_data.entry_operator = operator
                    # 仕様詳細のレコードを保存
                    free_spec_detail_data.save()

                else:
                    if copy_free_spec_detail_data.sub_no < 6:
                        copy_free_spec_detail_detail_data.append(copy_free_spec_detail_data.detail)

        else:
            pro_specification_unit_data_num = ProSpecificationUnit.objects.filter(construction_id=copy_work_id,
                                                                                  lost_flag=0).count()
            if pro_specification_unit_data_num == 1:
                pro_specification_unit_data = ProSpecificationUnit.objects.get(construction_id=copy_work_id, lost_flag=0)

                for detail_num in range(5):
                    if eval('pro_specification_unit_data.contents_detail%d != "" and pro_specification_unit_data.contents_detail%d is not None' %((detail_num + 1), (detail_num + 1))):
                        eval('copy_free_spec_detail_detail_data.append(pro_specification_unit_data.contents_detail%d)' % (detail_num + 1))

                sub_no = 0
                # 「work_id」、「lost_flag」、「登録区分」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録
                # (ないはずなので新規登録)
                for detail_item in copy_free_spec_detail_detail_data:
                    free_spec_detail_data, created = FreeSpecDetail.objects.get_or_create(work_id=work_id,
                                                                                          entry_class="計画",
                                                                                          sub_no=sub_no + 1,
                                                                                          lost_flag=0)
                    # 各項目の値(1つ前のrevでの値)を格納
                    # free_spec_detail_data.sub_no = copy_free_spec_detail_data.sub_no
                    free_spec_detail_data.detail = None_to_blank(detail_item)
                    free_spec_detail_data.entry_on_progress_flag = 1

                    if created == 1:
                        free_spec_detail_data.rev_no = rev_no

                        # last_free_spec_detail_list = FreeSpecDetail.objects.filter(work_id=work_id, entry_class="計画",
                        #                                                            lost_flag=1)
                        # if last_free_spec_detail_list.count() == 0:
                        #     free_spec_detail_data.rev_no = 0
                        # else:
                        #     free_spec_detail_data.rev_no = last_free_spec_detail_list.order_by('-rev_no')[0].rev_no + 1

                        last_free_spec_detail_list = FreeSpecDetail.objects.filter(work_id=work_id, entry_class="計画",
                                                                                   entry_on_progress_flag=0)
                        if last_free_spec_detail_list.count() > 0:
                            for last_free_spec_detail_data in last_free_spec_detail_list:
                                last_free_spec_detail_data.lost_flag = 1
                                last_free_spec_detail_data.update_datetime = now
                                last_free_spec_detail_data.update_operator = operator
                                last_free_spec_detail_data.save()

                        free_spec_detail_data.entry_datetime = now
                        free_spec_detail_data.entry_operator = operator
                    else:
                        free_spec_detail_data.update_datetime = now
                        free_spec_detail_data.update_operator = operator

                    # 仕様詳細のレコードを保存
                    free_spec_detail_data.save()

                    sub_no += 1

        msg = "仕様詳細データコピー完了！！"

        ary = {
            'copy_free_spec_detail_detail_data': copy_free_spec_detail_detail_data,
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係機器情報コピー処理
@require_POST
def copy_equipment_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        work_id = int(request.POST["work_id"])
        this_step = int(request.POST["this_step"])
        copy_work_id = int(request.POST['copy_work_id'])
        copy_step_no = int(request.POST['copy_step_no'])
        rev_no = int(request.POST['rev_no'])

        # コピー元のstepからデータ登録タイミングを判定
        if copy_step_no < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        copy_work_equipment_list = WorkEquipment.objects.filter(work_id=copy_work_id, lost_flag=0)

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        for copy_work_equipment_data in copy_work_equipment_list:
            # 「work_id」、「lost_flag」、「機器No」で機器情報のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
            work_equipment_data, created = WorkEquipment.objects.get_or_create(work_id=work_id,
                                                                               equip_no=copy_work_equipment_data.equip_no,
                                                                               lost_flag=0)
            # 各項目の値(1つ前のrevでの値)を格納
            work_equipment_data.budget_id = copy_work_equipment_data.budget_id
            work_equipment_data.equip_name = copy_work_equipment_data.equip_name
            work_equipment_data.management_class = copy_work_equipment_data.management_class
            work_equipment_data.facility = copy_work_equipment_data.facility
            work_equipment_data.equipment_purchase = copy_work_equipment_data.equipment_purchase
            work_equipment_data.construction = copy_work_equipment_data.construction
            work_equipment_data.equip_family = copy_work_equipment_data.equip_family
            work_equipment_data.equip_type = copy_work_equipment_data.equip_type
            work_equipment_data.entry_on_progress_flag = 1

            if created == 1:
                last_work_equipment_list = WorkEquipment.objects.filter(work_id=work_id,
                                                                        equip_no=copy_work_equipment_data.equip_no,
                                                                        lost_flag=1)
                if this_step < 200000000:
                    work_equipment_data.rev_no = rev_no
                elif last_work_equipment_list.count() == 0:
                    work_equipment_data.rev_no = 0
                else:
                    work_equipment_data.rev_no = last_work_equipment_list.order_by('-rev_no')[0].rev_no + 1

                work_equipment_data.entry_datetime = now
                work_equipment_data.entry_operator = operator
            else:
                work_equipment_data.update_datetime = now
                work_equipment_data.update_operator = operator

            # 機器情報のレコードを保存
            work_equipment_data.save()

        msg = "機器情報データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 全工事の仕様書予算見積完了をチェックする
def check_work_estimates_complete(work_id):
    complete_flag = 0

    # work_idから予算の取得
    target_work_data = Work.objects.filter(work_id=work_id, lost_flag=0).order_by('-id')[0]
    budget_id = target_work_data.work_budget_id

    # 予算の申請区分に応じて処理分岐
    budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
    if budget_data.plan_class_id == 'M':
        step_list = {'詳細仕様検討': 132002011, '仕様書予算見積完了': 132009911}
    elif budget_data.application_class.application_class_cd == 1:
        step_list = {'詳細仕様検討': 133002011, '仕様書予算見積完了': 133009904}
    else:
        step_list = {'詳細仕様検討': 136002011, '仕様書予算見積完了': 133009904}

    budget_count_progress = Progress.objects.filter(target='budget', target_id=budget_data.budget_id,
                                                    present_step=step_list['詳細仕様検討']).count()

    # 全工事数を取得
    work_count_all = Work.objects.filter(work_budget_id=budget_id, lost_flag=0).count()

    # キャンセルされた工事数を取得
    work_count_cancel = Work.objects.filter(work_budget_id=budget_id, lost_flag=0, cancel_flag=1).count()

    # キャンセルされた工事以外のリストを取得
    work_data_list = Work.objects.filter(work_budget_id=budget_id, lost_flag=0).exclude(cancel_flag=1)

    # work_idリスト化
    work_id_list = [work_data.work_id for work_data in work_data_list]
    work_count_estimate_comp = Progress.objects.filter(target='work', target_id__in=work_id_list,
                                                       present_step=step_list['仕様書予算見積完了']).count()

    if (work_count_estimate_comp + work_count_cancel) >= work_count_all and budget_count_progress > 0:
        complete_flag = 1

    if complete_flag == 1:
        msg = "全ての予算見積が完了しました。\n予算の進捗状況を予算見積作成に進めますか？"
    else:
        msg = "仕様書予算見積完了していない工事があります。"

    ary = {
        'msg': msg,
        'budget_id': budget_id,
        'complete_flag': complete_flag,
        'work_count_all': work_count_all,
        'work_count_cancel': work_count_cancel,
        'work_count_estimate_comp': work_count_estimate_comp,
    }
    return ary
