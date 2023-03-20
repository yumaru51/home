import math
import os
import shutil
import traceback
from socket import gethostname
# datetimeをインポート
import datetime
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.db import connections
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum
from django.utils.timezone import make_aware

# formsをインポート
from fms.forms import BudgetEditFormLeft, BudgetEditFormCenter, BudgetEditFormRight
# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import WorkClassMaster, RegulationMaster, BudgetCarryForward
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import FreeSpecDetail, SubmissionDocument, Estimate, Supplies, WorkLaw
from fms.models import WorkSpecMEX, PlanningChargePerson
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work
from fms.models import ProBudgetUnit, ProSpecificationUnit, ProEstimates, ProVendorEvaluation, ProIndividualContractDoc
from fms.models import ProInspectionResults, ProDelivery, ProConstructionPrep, ProConstructionQualityResults
from fms.models import WorkManagementClassMaster
from fms.views.common_views import blank_to_None, None_to_blank, date_to_hyphen, str_to_boolean, add_comma_value
from fms.views.notice_mail_views import step_notice
from fms.models import AttachmentDocuments
from fms.views.cs_views import get_cs_complete_count
from fms.views.budget_carry_forward_views import get_budget_carry_forward, check_budget_order_complete
from fms.views.common_def_views import get_next_target, convert_charge_department, \
    get_filter_planning_charge_person_list, is_mplan_budget_step, get_budget_name_text
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.common_def_views import get_department_person_list, get_department_person_option_list
from fms.views.common_def_views import get_ng_character_list


# 工事共通情報を詳細画面で表示
@login_required
@require_POST
def execution_work_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['budget_id'])
        construction_id = int(request.POST['construction_id'])
        present_step = int(request.POST['this_step'])
        level5_step_id = int(request.POST['level5_step_id'])
        copy_check = int(request.POST['copy_check'])
        target = request.POST['target']

        # ProSpecificationUnitの読込(そのままrenderに引き渡すこと)
        base_data = execution_work_common_data(budget_id, construction_id)

        if copy_check == 0:
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_specification', lost_flag=0)
            this_page = stepdisplayitem_data.page
            # action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
            action_button_id = target + str(this_page) + '_action_button'
        else:
            this_page = 5
            action_button_id = ''

        order_complete_flag = check_budget_order_complete(request, budget_id)

        data = {
            'work_common_data': base_data,
            't_username': t_username,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'order_complete_flag': order_complete_flag,
        }

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「work」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='prospecificationunit').count()
        edit_flag = 0
        if level5_step_id == 920000000:
            work_edit_action_num = 0

        if work_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_detail/execution_work_edit.html', data)

        else:
            return render(request, 'fms/parts/execution/execution_detail/execution_work_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# ProSpecificationUnitの読込(execution_work_info_base.htmlの表示に使用するので、戻り値をそのままrenderに引き渡すこと)
def execution_work_common_data(budget_id, construction_id):
    prospecificationunit_data = ""
    rev_no = 0
    budget_no = ""
    budget_name = ""
    work_name = ""
    sub_id = ""
    department = ""
    division = ""
    format_kbn = ""
    goods_construct_kbn = ""
    work_charge_process = ""
    specification_person_in_charge = ""
    procurement_person_in_charge = ""
    management_class_cd = ""
    delivery_location = ""
    desired_construct_period_from = ""
    desired_construct_period_to = ""
    desired_delivery_date = ""
    estimate_submission_date = ""
    estimated_deadline_date = ""
    order_limited_date = ""
    fixed_delivery_location = ""
    fixed_delivery_date_from = ""
    fixed_delivery_date_to = ""
    fixed_delivery_date = ""
    scheduled_inspection_date_from = ""
    scheduled_inspection_date_to = ""
    scheduled_acceptance_date_from = ""
    scheduled_acceptance_date_to = ""
    preparation_delivery_date = ""
    specification_data = ""
    construction_outline = ""
    contents_detail1 = ""
    contents_detail2 = ""
    contents_detail3 = ""
    contents_detail4 = ""
    contents_detail5 = ""
    # 20210114 y-kawauchi 「候補業者」「備考」追加
    candidate_vendor1 = ""
    candidate_vendor2 = ""
    candidate_vendor3 = ""
    candidate_vendor4 = ""
    candidate_vendor5 = ""
    memo = ""

    probable_price = ""

    # 予算データを主キーでレコード抽出
    budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
    relation_budget_id = budget_data.relation_budget_id
    budget_no = None_to_blank(budget_data.budget_no)
    budget_name = None_to_blank(budget_data.budget_name)
    work_charge_process_name = budget_data.facility_process.process_name
    work_charge_process = budget_data.facility_process.process_cd

    # 対象のデータがある場合
    if construction_id > 0:
        prospecificationunit_data = ProSpecificationUnit.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                                     lost_flag=0)
        # 各項目の値を取得
        rev_no = None_to_blank(prospecificationunit_data.rev_no)
        work_name = None_to_blank(prospecificationunit_data.work_name)
        sub_id = None_to_blank(prospecificationunit_data.sub_id)
        format_kbn = None_to_blank(prospecificationunit_data.format_kbn)
        goods_construct_kbn = None_to_blank(prospecificationunit_data.goods_construct_kbn)
        specification_person_in_charge = None_to_blank(prospecificationunit_data.specification_person_in_charge)
        procurement_person_in_charge = None_to_blank(prospecificationunit_data.procurement_person_in_charge)
        management_class_cd = None_to_blank(prospecificationunit_data.management_class_cd)
        delivery_location = None_to_blank(prospecificationunit_data.delivery_location)
        desired_construct_period_from = None_to_blank(prospecificationunit_data.desired_construct_period_from)
        desired_construct_period_to = None_to_blank(prospecificationunit_data.desired_construct_period_to)
        desired_delivery_date = None_to_blank(prospecificationunit_data.desired_delivery_date)
        estimate_submission_date = None_to_blank(prospecificationunit_data.estimate_submission_date)
        order_limited_date = None_to_blank(prospecificationunit_data.order_limited_date)
        scheduled_inspection_date_from = None_to_blank(prospecificationunit_data.scheduled_inspection_date_from)
        scheduled_inspection_date_to = None_to_blank(prospecificationunit_data.scheduled_inspection_date_to)
        scheduled_acceptance_date_from = None_to_blank(prospecificationunit_data.scheduled_acceptance_date_from)
        scheduled_acceptance_date_to = None_to_blank(prospecificationunit_data.scheduled_acceptance_date_to)
        preparation_delivery_date = None_to_blank(prospecificationunit_data.preparation_delivery_date)
        specification_data = None_to_blank(prospecificationunit_data.specification_data)
        construction_outline = None_to_blank(prospecificationunit_data.construction_outline)
        contents_detail1 = None_to_blank(prospecificationunit_data.contents_detail1)
        contents_detail2 = None_to_blank(prospecificationunit_data.contents_detail2)
        contents_detail3 = None_to_blank(prospecificationunit_data.contents_detail3)
        contents_detail4 = None_to_blank(prospecificationunit_data.contents_detail4)
        contents_detail5 = None_to_blank(prospecificationunit_data.contents_detail5)
        candidate_vendor1 = None_to_blank(prospecificationunit_data.candidate_vendor1)
        candidate_vendor2 = None_to_blank(prospecificationunit_data.candidate_vendor2)
        candidate_vendor3 = None_to_blank(prospecificationunit_data.candidate_vendor3)
        candidate_vendor4 = None_to_blank(prospecificationunit_data.candidate_vendor4)
        candidate_vendor5 = None_to_blank(prospecificationunit_data.candidate_vendor5)
        memo = None_to_blank(prospecificationunit_data.memo)
        probable_price = prospecificationunit_data.probable_price
        department = None_to_blank(prospecificationunit_data.department)  # 部署
        if department is '':
            # 過去データ対応のため、部署が未設定ならば予算側の情報を使用する
            department = None_to_blank(budget_data.budget_main_department_id)  # 部署

    # 対象のデータがない場合
    else:
        rev_no = 0
        # 新規データの場合、予算見積額を予想額に表示する
        probable_price = budget_data.budget_price
        department = None_to_blank(budget_data.budget_main_department_id)  # 部署

    # 工事区分(物品/工事)選択の候補の一覧用データ抽出
    work_class_lists = WorkClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')
    goods_construct_kbn_name = ""
    if goods_construct_kbn is not "":
        # 工事区分(物品/工事)
        work_class_data = WorkClassMaster.objects.get(work_class_cd=goods_construct_kbn)
        goods_construct_kbn_name = work_class_data.work_class_name

    # 部門を取得
    if department is not "":
        department_data = DepartmentMaster.objects.get(department_cd=department)
        division = None_to_blank(department_data.division_cd) # 部門

    # 部門選択の候補の一覧用データ抽出
    division_lists = DivisionMaster.objects.filter(lost_flag=0)
    division_name = ""
    if division is not "":
        # 部門
        division_master_data = DivisionMaster.objects.get(division_cd=division)
        division_name = division_master_data.division_name

    # 部署選択の候補の一覧用データ抽出
    department_lists = DepartmentMaster.objects.filter(lost_flag=0)
    department_name = ""
    if department is not "":
        # 部署
        department_master_data = DepartmentMaster.objects.get(department_cd=department)
        department_name = department_master_data.department_name

    # 計画担当者のデータ抽出
    planning_charge_person_name = ""
    if Work.objects.filter(work_id=construction_id, lost_flag=0).count() > 0:
        work_data = Work.objects.filter(work_id=construction_id, lost_flag=0).all().order_by('-id')[0]
        planning_charge_person_id = work_data.work_planning_charge_person_id
        if planning_charge_person_id is not None and planning_charge_person_id != "":
            planning_chargeuser_data = User.objects.get(username=planning_charge_person_id, lost_flag=0)
            planning_charge_person_name = planning_chargeuser_data.last_name + '　' + planning_chargeuser_data.first_name

    # 仕様書担当者選択の候補の一覧用データ抽出
    specification_person_in_charge_list = get_specification_person_in_charge_list()
    specification_person_in_charge_name = ""
    if specification_person_in_charge is not "":
        # 仕様書担当者
        user_data = User.objects.get(username=specification_person_in_charge, lost_flag=0)
        specification_person_in_charge_name = user_data.last_name + '　' + user_data.first_name

    # 調達担当者選択の候補の一覧用データ抽出
    procurement_person_in_charge_list = get_department_person_list('SI')
    procurement_person_in_charge_name = ""
    if procurement_person_in_charge is not "":
        # 調達担当者
        user_data = User.objects.get(username=procurement_person_in_charge, lost_flag=0)
        procurement_person_in_charge_name = user_data.last_name + '　' + user_data.first_name

    # 管理区分選択の候補の一覧用データ抽出
    management_class_list = WorkManagementClassMaster.objects.filter().all()
    management_class_name = ""
    if management_class_cd is not "":
        # 管理区分
        management_class_data = WorkManagementClassMaster.objects.get(management_class_cd=management_class_cd, lost_flag=0)
        management_class_name = management_class_data.management_class_name

    # 無効となった(=1つ前のrev_noの)対象の工事データのレコード数を取得
    old_prospecificationunit_data_num = ProSpecificationUnit.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).count()
    # 無効となった(=1つ前のrev_noの)対象の工事データのレコードがある場合
    if old_prospecificationunit_data_num > 0:
        # 無効となった(=1つ前のrev_noの)対象の工事データを取得
        old_prospecificationunit_data = ProSpecificationUnit.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).all().order_by('-id')[0]
    else:
        old_prospecificationunit_data = ""

    # 決定見積提出期日
    proestimates_data_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                        lost_flag=0).count()
    # 対象のデータがある場合
    if proestimates_data_num > 0:
        proestimates_data = ProEstimates.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                     lost_flag=0)
        estimated_deadline_date = None_to_blank(proestimates_data.estimated_deadline_date)
        fixed_delivery_location = None_to_blank(proestimates_data.fixed_delivery_location)
        fixed_delivery_date_from = None_to_blank(proestimates_data.fixed_delivery_date_from)
        fixed_delivery_date_to = None_to_blank(proestimates_data.fixed_delivery_date_to)
        fixed_delivery_date = None_to_blank(proestimates_data.fixed_delivery_date)

    # 無効となった(=1つ前のrev_noの)対象の調達見積情報テーブルのレコード数を取得
    old_proestimate_data_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                           lost_flag=1).count()
    # 無効となった(=1つ前のrev_noの)対象の調達見積情報テーブルのレコードがある場合
    if old_proestimate_data_num > 0:
        # 無効となった(=1つ前のrev_noの)対象の調達見積情報テーブルを取得
        old_proestimate_data = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                           lost_flag=1).all().order_by('-id')[0]
    else:
        old_proestimate_data = ""

    # 表示側のために桁区切りを追加する
    probable_price = add_comma_value(probable_price)

    data = {
        'prospecificationunit_data': prospecificationunit_data,
        'budget_id': budget_id,
        'relation_budget_id': relation_budget_id,
        'rev_no': rev_no,
        'budget_no': budget_no,
        'budget_name': budget_name,
        'construction_id': construction_id,
        'work_name': work_name,
        'sub_id': sub_id,
        'division': division,
        'division_name': division_name,
        'department': department,
        'department_name': department_name,
        'format_kbn': format_kbn,
        'goods_construct_kbn': goods_construct_kbn,
        'goods_construct_kbn_name': goods_construct_kbn_name,
        'work_charge_process': work_charge_process,
        'work_charge_process_name': work_charge_process_name,
        'specification_person_in_charge': specification_person_in_charge,
        'specification_person_in_charge_name': specification_person_in_charge_name,
        'procurement_person_in_charge': procurement_person_in_charge,
        'procurement_person_in_charge_name': procurement_person_in_charge_name,
        'management_class_cd': management_class_cd,
        'management_class_name': management_class_name,
        'delivery_location': delivery_location,
        'desired_construct_period_from': desired_construct_period_from,
        'desired_construct_period_to': desired_construct_period_to,
        'desired_delivery_date': desired_delivery_date,
        'estimate_submission_date': estimate_submission_date,
        'estimated_deadline_date': estimated_deadline_date,
        'order_limited_date': order_limited_date,
        'fixed_delivery_location': fixed_delivery_location,
        'fixed_delivery_date_from': fixed_delivery_date_from,
        'fixed_delivery_date_to': fixed_delivery_date_to,
        'fixed_delivery_date': fixed_delivery_date,
        'scheduled_inspection_date_from': scheduled_inspection_date_from,
        'scheduled_inspection_date_to': scheduled_inspection_date_to,
        'scheduled_acceptance_date_from': scheduled_acceptance_date_from,
        'scheduled_acceptance_date_to': scheduled_acceptance_date_to,
        'preparation_delivery_date': preparation_delivery_date,
        'specification_data': specification_data,
        'construction_outline': construction_outline,
        'contents_detail1': contents_detail1,
        'contents_detail2': contents_detail2,
        'contents_detail3': contents_detail3,
        'contents_detail4': contents_detail4,
        'contents_detail5': contents_detail5,
        'division_lists': division_lists,
        'department_lists': department_lists,
        'specification_person_in_charge_list': specification_person_in_charge_list,
        'procurement_person_in_charge_list': procurement_person_in_charge_list,
        'management_class_list': management_class_list,
        'work_class_lists': work_class_lists,
        'old_prospecificationunit_data_num': old_prospecificationunit_data_num,
        'old_prospecificationunit_data': old_prospecificationunit_data,
        'old_proestimate_data_num': old_proestimate_data_num,
        'old_proestimate_data': old_proestimate_data,
        'candidate_vendor1': candidate_vendor1,
        'candidate_vendor2': candidate_vendor2,
        'candidate_vendor3': candidate_vendor3,
        'candidate_vendor4': candidate_vendor4,
        'candidate_vendor5': candidate_vendor5,
        'memo': memo,
        'probable_price': probable_price,
        'planning_charge_person_name': planning_charge_person_name,
    }
    return data


# 予算情報登録･更新
@login_required
@require_POST
def execution_budget_entry(request):
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
        comment = request.POST["comment"]

        budget_id = int(request.POST["budget_id"])
        rev_no = request.POST['rev_no']
        budget_no = request.POST['budget_no']
        budget_name = request.POST['budget_name']
        division = request.POST["division"]
        department = request.POST["department"]

        jurisdiction_area = request.POST["jurisdiction_area"]
        area_person_in_charge = request.POST["area_person_in_charge"]
        original_sec_person_in_charge = request.POST["original_sec_person_in_charge"]
        sche_gov_inspection_date = request.POST["sche_gov_inspection_date"]

        sche_gov_inspection_date = date_to_hyphen(sche_gov_inspection_date)

        # 調達予算情報テーブルを予算IDの存在チェック
        probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=0).count()
        # 更新
        if probudgetunit_data_num > 0:
            # 調達予算情報テーブルを予算IDので読込
            probudgetunit_data = ProBudgetUnit.objects.get(budget_id=budget_id, lost_flag=0)
            new_record = False
        # 新規登録
        else:
            new_record = True

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id,lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 予算id(変数)に渡された予算idをセット
        this_budget_id = budget_id

        # 新規登録時の処理
        if new_record == True:
            # 設定した予算IDで新規作成
            probudgetunit_data, created = ProBudgetUnit.objects.get_or_create(budget_id=budget_id, entry_on_progress_flag=0)
            # 登録の日時、登録者を登録
            probudgetunit_data.entry_datetime = now
            probudgetunit_data.entry_operator = operator
            # 調達予算情報テーブルを保存
            probudgetunit_data.save()
            # 登録日時、登録者で調達予算情報テーブルを抽出
            probudgetunit_data = ProBudgetUnit.objects.get(entry_datetime=now, entry_operator=operator,lost_flag=0)
            # 主キーを取得
            probudgetunit_unique_id = probudgetunit_data.id
            # 主キーで調達予算情報テーブルを抽出
            probudgetunit_data = ProBudgetUnit.objects.get(id=probudgetunit_unique_id,lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            probudgetunit_data.rev_no = 0
            probudgetunit_data.entry_on_progress_flag = 1
            probudgetunit_data.cancel_flag = 0
            probudgetunit_data.lost_flag = 0
            # 調達予算情報テーブルを保存
            probudgetunit_data.save()
        # 更新時の処理
        else:
            # 該当の予算idで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProBudgetUnit.objects.filter(budget_id=budget_id, entry_on_progress_flag=1).count()
            # 該当の予算idで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProBudgetUnit.objects.filter(budget_id=budget_id, entry_on_progress_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                probudgetunit_data = ProBudgetUnit.objects.filter(budget_id=budget_id, entry_on_progress_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = probudgetunit_data.rev_no
                # 該当のレコードを無効
                probudgetunit_data.lost_flag = 1
                # 予算のレコードを保存
                probudgetunit_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProBudgetUnit(budget_id=budget_id, entry_datetime=now, entry_operator=operator).save()
                # 登録日時、登録者で予算レコードを抽出
                probudgetunit_data = ProBudgetUnit.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーを取得
                probudgetunit_unique_id = probudgetunit_data.id
                # 主キーで予算レコードを抽出
                probudgetunit_data = ProBudgetUnit.objects.get(id=probudgetunit_unique_id)
                # rev_no、作業中FL、無効FLに値を代入
                probudgetunit_data.rev_no = latest_rev_no + 1
                probudgetunit_data.entry_on_progress_flag = 1
                probudgetunit_data.cancel_flag = 0
                probudgetunit_data.lost_flag = 0
                # 予算のレコードを保存
                probudgetunit_data.save()

            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、作業中FL=1で予算レコードを抽出
                probudgetunit_data = ProBudgetUnit.objects.get(budget_id=budget_id, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                probudgetunit_unique_id = probudgetunit_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"

        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step,lost_flag=0)
            step_name = step_data.step_name
            # 次ステップ設定
            # next_step = step_data.next_step
            msg = step_name + "完了"

        # 主キーで調達予算情報テーブルを抽出
        probudgetunit_data = ProBudgetUnit.objects.get(id=probudgetunit_unique_id,lost_flag=0)
        # 各項目の値を設定
        probudgetunit_data.rev_no = blank_to_None(rev_no)
        probudgetunit_data.division = blank_to_None(division)
        probudgetunit_data.department = blank_to_None(department)

        probudgetunit_data.jurisdiction_area = blank_to_None(jurisdiction_area)
        probudgetunit_data.area_person_in_charge = blank_to_None(area_person_in_charge)
        probudgetunit_data.original_sec_person_in_charge = blank_to_None(original_sec_person_in_charge)
        probudgetunit_data.sche_gov_inspection_date = blank_to_None(sche_gov_inspection_date)
        probudgetunit_data.cancel_flag = 0
        probudgetunit_data.update_datetime = now
        probudgetunit_data.update_operator = operator

        # 今のstepと次のstepが同じ場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            probudgetunit_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            probudgetunit_data.entry_on_progress_flag = 1

        # rev_no取得
        probudgetunit_rev_no = probudgetunit_data.rev_no

        # 調達予算情報のレコードを保存
        probudgetunit_data.save()

        # ログデータを新規登録
        Log(target='probudgetunit', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step,comment=comment, operator_department=this_department, operator_division=this_division,budget_id=this_budget_id).save()

        # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="probudgetunit", target_id=this_budget_id)
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

        # 進捗通知機能
        if this_step != next_step:
            step_notice(progress_data)

        ary = {
            'budget_id': this_budget_id,
            'probudgetunit_rev_no': probudgetunit_rev_no,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 調達仕様書情報テーブル登録･更新
@login_required
@require_POST
def execution_work_entry(request):

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
        comment = request.POST["comment"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]

        budget_id = int(request.POST['budget_id'])
        rev_no = request.POST['rev_no']
        budget_no = request.POST['budget_no']
        budget_name = request.POST['budget_name']
        construction_id = int(request.POST['construction_id'])
        sub_id = request.POST['sub_id']
        work_name = request.POST['work_name']
        division = request.POST["division"]
        department = request.POST["department"]

        format_kbn = request.POST['format_kbn']
        goods_construct_kbn = request.POST['goods_construct_kbn']
        work_charge_process = request.POST['work_charge_process']
        specification_person_in_charge = request.POST['specification_person_in_charge']
        procurement_person_in_charge = request.POST['procurement_person_in_charge']
        management_class_cd = request.POST['management_class_cd']
        delivery_location = request.POST['delivery_location']
        desired_construct_period_from = request.POST['desired_construct_period_from']
        desired_construct_period_to = request.POST['desired_construct_period_to']
        desired_delivery_date = request.POST['desired_delivery_date']
        estimate_submission_date = request.POST['estimate_submission_date']
        order_limited_date = request.POST["order_limited_date"]
        scheduled_inspection_date_from = request.POST['scheduled_inspection_date_from']
        scheduled_inspection_date_to = request.POST['scheduled_inspection_date_to']
        scheduled_acceptance_date_from = request.POST['scheduled_acceptance_date_from']
        scheduled_acceptance_date_to = request.POST['scheduled_acceptance_date_to']
        preparation_delivery_date = request.POST['preparation_delivery_date']
        specification_data = request.POST['specification_data']
        construction_outline = request.POST['construction_outline']
        contents_detail1 = request.POST['contents_detail1']
        contents_detail2 = request.POST['contents_detail2']
        contents_detail3 = request.POST['contents_detail3']
        contents_detail4 = request.POST['contents_detail4']
        contents_detail5 = request.POST['contents_detail5']
        candidate_vendor1 = request.POST['candidate_vendor1']
        candidate_vendor2 = request.POST['candidate_vendor2']
        candidate_vendor3 = request.POST['candidate_vendor3']
        candidate_vendor4 = request.POST['candidate_vendor4']
        candidate_vendor5 = request.POST['candidate_vendor5']
        memo = request.POST['memo']

        probable_price = request.POST['probable_price']
        special_vendor_check = str_to_boolean(request.POST['special_vendor_check'])
        special_vendor_comment = request.POST['special_vendor_comment']

        desired_construct_period_from = date_to_hyphen(desired_construct_period_from)
        desired_construct_period_to = date_to_hyphen(desired_construct_period_to)
        desired_delivery_date = date_to_hyphen(desired_delivery_date)
        estimate_submission_date = date_to_hyphen(estimate_submission_date)
        order_limited_date = date_to_hyphen(order_limited_date)
        scheduled_inspection_date_from = date_to_hyphen(scheduled_inspection_date_from)
        scheduled_inspection_date_to = date_to_hyphen(scheduled_inspection_date_to)
        scheduled_acceptance_date_from = date_to_hyphen(scheduled_acceptance_date_from)
        scheduled_acceptance_date_to = date_to_hyphen(scheduled_acceptance_date_to)
        preparation_delivery_date = date_to_hyphen(preparation_delivery_date)

        # 調達仕様書情報テーブルを予算ID, 工事IDの存在チェック
        prospecificationunit_data_num = ProSpecificationUnit.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                          lost_flag=0).count()

        # 更新
        if prospecificationunit_data_num > 0:
            new_record = False
        # 新規登録
        else:
            new_record = True

            # 工事情報のレコード数を取得
            work_num = Work.objects.all().count()

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
            work_data, created = Work.objects.get_or_create(work_id=this_work_id)

            # 各項目の値を格納
            rev_no = 0
            work_data.work_rev_no = rev_no
            work_data.work_budget_id = budget_id
            work_data.entry_datetime = now
            work_data.entry_operator = operator
            work_data.work_name = work_name
            work_data.entry_on_progress_flag = 1
            work_data.lost_flag = 0
            work_id = work_data.work_id
            # 工事情報のレコードを保存
            work_data.save()

            # 工事情報 = 調達仕様書情報テーブル
            construction_id = this_work_id

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 予算id(変数)に渡された予算idをセット
        this_budget_id = budget_id

        # 新規登録時の処理
        if new_record == True:
            # 設定した予算ID, 工事IDで新規作成
            prospecificationunit_data, created = ProSpecificationUnit.objects.get_or_create(budget_id=budget_id,
                                                                          construction_id=construction_id,
                                                                          entry_on_progress_flag=0)
            # 登録の日時、登録者を登録
            prospecificationunit_data.entry_datetime = now
            prospecificationunit_data.entry_operator = operator
            # 調達仕様書情報テーブルを保存
            prospecificationunit_data.save()
            # 登録日時、登録者で調達仕様書情報テーブルを抽出
            prospecificationunit_data = ProSpecificationUnit.objects.get(entry_datetime=now, entry_operator=operator)
            prospecificationunit_unique_id = prospecificationunit_data.id
            # 主キーで調達仕様書情報テーブルを抽出
            prospecificationunit_data = ProSpecificationUnit.objects.get(id=prospecificationunit_unique_id)
            # rev_no、作業中FL、無効FLに値を代入
            rev_no = 0
            prospecificationunit_data.rev_no = rev_no
            prospecificationunit_data.entry_on_progress_flag = 1
            prospecificationunit_data.lost_flag = 0
            prospecificationunit_data.cancel_flag = 0
            # 調達仕様書情報テーブルを保存
            prospecificationunit_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProSpecificationUnit.objects.filter(budget_id=budget_id,
                                                                         construction_id=construction_id,
                                                                         entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProSpecificationUnit.objects.filter(budget_id=budget_id,
                                                                            construction_id=construction_id,
                                                                            entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                prospecificationunit_data = ProSpecificationUnit.objects.filter(budget_id=budget_id,
                                                                                construction_id=construction_id,
                                                                                entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = prospecificationunit_data.rev_no
                # 該当のレコードを無効
                prospecificationunit_data.lost_flag = 1
                # 予算のレコードを保存
                prospecificationunit_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProSpecificationUnit(budget_id=budget_id, construction_id=construction_id, entry_datetime=now,
                            entry_operator=operator).save()
                # 登録日時、登録者で予算レコードを抽出
                prospecificationunit_data = ProSpecificationUnit.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーを取得
                prospecificationunit_unique_id = prospecificationunit_data.id
                # 主キーで予算レコードを抽出
                prospecificationunit_data = ProSpecificationUnit.objects.get(id=prospecificationunit_unique_id)
                # rev_no、作業中FL、無効FLに値を代入
                rev_no = latest_rev_no + 1
                prospecificationunit_data.rev_no = rev_no
                prospecificationunit_data.entry_on_progress_flag = 1
                prospecificationunit_data.lost_flag = 0
                prospecificationunit_data.cancel_flag = 0
                # 予算のレコードを保存
                prospecificationunit_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                prospecificationunit_data = ProSpecificationUnit.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                           entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                prospecificationunit_unique_id = prospecificationunit_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            action = "temporarily_saved"
            msg = "一時保存完了"
        # 今のstepと次のstepが違う場合の処理
        else:
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step,lost_flag=0)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 主キーで調達仕様書情報テーブルを抽出
        prospecificationunit_data = ProSpecificationUnit.objects.get(id=prospecificationunit_unique_id, lost_flag=0)
        construction_id = prospecificationunit_data.construction_id
        rev_no = prospecificationunit_data.rev_no

        # 各項目の値を設定
        prospecificationunit_data.rev_no = blank_to_None(rev_no)
        prospecificationunit_data.sub_id = blank_to_None(sub_id)
        prospecificationunit_data.work_name = blank_to_None(work_name)
        prospecificationunit_data.division = blank_to_None(division)
        prospecificationunit_data.department = blank_to_None(department)

        prospecificationunit_data.format_kbn = blank_to_None(format_kbn)
        prospecificationunit_data.goods_construct_kbn = blank_to_None(goods_construct_kbn)
        prospecificationunit_data.work_charge_process = blank_to_None(work_charge_process)
        prospecificationunit_data.specification_person_in_charge = blank_to_None(specification_person_in_charge)
        prospecificationunit_data.procurement_person_in_charge = blank_to_None(procurement_person_in_charge)
        prospecificationunit_data.management_class_cd = blank_to_None(management_class_cd)
        prospecificationunit_data.delivery_location = blank_to_None(delivery_location)

        prospecificationunit_data.desired_construct_period_from = blank_to_None(desired_construct_period_from)
        prospecificationunit_data.desired_construct_period_to = blank_to_None(desired_construct_period_to)
        prospecificationunit_data.desired_delivery_date = blank_to_None(desired_delivery_date)
        prospecificationunit_data.estimate_submission_date = blank_to_None(estimate_submission_date)
        prospecificationunit_data.order_limited_date = blank_to_None(order_limited_date)
        prospecificationunit_data.scheduled_inspection_date_from = blank_to_None(scheduled_inspection_date_from)
        prospecificationunit_data.scheduled_inspection_date_to = blank_to_None(scheduled_inspection_date_to)
        prospecificationunit_data.scheduled_acceptance_date_from = blank_to_None(scheduled_acceptance_date_from)
        prospecificationunit_data.scheduled_acceptance_date_to = blank_to_None(scheduled_acceptance_date_to)
        prospecificationunit_data.preparation_delivery_date = blank_to_None(preparation_delivery_date)
        prospecificationunit_data.specification_data = blank_to_None(specification_data)
        prospecificationunit_data.construction_outline = blank_to_None(construction_outline)
        prospecificationunit_data.contents_detail1 = blank_to_None(contents_detail1)
        prospecificationunit_data.contents_detail2 = blank_to_None(contents_detail2)
        prospecificationunit_data.contents_detail3 = blank_to_None(contents_detail3)
        prospecificationunit_data.contents_detail4 = blank_to_None(contents_detail4)
        prospecificationunit_data.contents_detail5 = blank_to_None(contents_detail5)
        prospecificationunit_data.candidate_vendor1 = blank_to_None(candidate_vendor1)
        prospecificationunit_data.candidate_vendor2 = blank_to_None(candidate_vendor2)
        prospecificationunit_data.candidate_vendor3 = blank_to_None(candidate_vendor3)
        prospecificationunit_data.candidate_vendor4 = blank_to_None(candidate_vendor4)
        prospecificationunit_data.candidate_vendor5 = blank_to_None(candidate_vendor5)
        prospecificationunit_data.memo = blank_to_None(memo)

        prospecificationunit_data.update_datetime = now
        prospecificationunit_data.update_operator = operator

        if probable_price == '':
            prospecificationunit_data.probable_price = 0
        else:
            prospecificationunit_data.probable_price = probable_price

        prospecificationunit_data.special_vendor_check = special_vendor_check
        prospecificationunit_data.special_vendor_comment = special_vendor_comment

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            prospecificationunit_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            prospecificationunit_data.entry_on_progress_flag = 1

        # rev_no取得
        prospecificationunit_rev_no = prospecificationunit_data.rev_no

        # 調達仕様書情報テーブルのレコードを保存
        prospecificationunit_data.save()

        # ログデータを新規登録
        Log(target='prospecificationunit', target_id=construction_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        # 進捗状況を対象(prospecificationunit)と工事idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="prospecificationunit",
                                                                target_id=construction_id)
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

        # 進捗通知機能
        if this_step != next_step:
            step_notice(progress_data)

        ary = {
            'rev_no': rev_no,
            'construction_id': construction_id,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算情報を詳細画面で表示
@require_POST
def get_execution_budget_lists(request):
    try:
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
        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000

        where_str = ""
        where_parm = []

        ex_select_str = ""
        budget_join_str = ""

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
            if budget_join_str == "":
                budget_join_str = " LEFT JOIN fms_budget ON fms_probudgetunit.budget_id=fms_budget.budget_id "
            ex_select_str = ", fms_budget.business_year_id"
            where_str += " AND fms_budget.business_year_id = %s"
            where_parm.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            if budget_join_str == "":
                budget_join_str = " LEFT JOIN fms_budget ON fms_probudgetunit.budget_id=fms_budget.budget_id "
            ex_select_str = ", fms_budget.budget_class_id"
            where_str += " AND fms_budget.budget_class_id = %s"
            where_parm.append(int(sel_budget_class))
        # 予算ID
        if sel_budget_id != "":
            where_str += " AND fms_probudgetunit.budget_id = %s"
            where_parm.append(int(sel_budget_id))
        # 予算NO
        if sel_budget_no != "":
            if budget_join_str == "":
                budget_join_str = " LEFT JOIN fms_budget ON fms_probudgetunit.budget_id=fms_budget.budget_id "
            where_str += " AND fms_budget.budget_no LIKE %s"
            where_parm.append('%' + sel_budget_no + '%')
        # 予算名
        if sel_budget_name != "":
            if budget_join_str == "":
                budget_join_str = " LEFT JOIN fms_budget ON fms_probudgetunit.budget_id=fms_budget.budget_id "
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
                budget_join_str = " LEFT JOIN fms_budget ON fms_probudgetunit.budget_id=fms_budget.budget_id "
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

        #未処理のみにチェックがある場合、ユーザーを限定する
        if sel_on_work == 'true':
            # この下2行をコメントアウトし、4行を追加・・・2021/01/11 ueda
            # where_str += " AND fms_probudgetunit.update_operator = %s"
            # where_parm.append(username)
            where_str += " AND fms_stepmaster.step_id > %s"
            where_str += " AND fms_stepmaster.step_id < %s"
            where_parm.append(step_st)
            where_parm.append(step_ed)
            # この上2行をコメントアウトし、4行を追加・・・2021/01/11 ueda

        # 予算情報テーブル取得
        sql = """
            SELECT
                  fms_probudgetunit.*
                """ + ex_select_str + """
                , U1.first_name AS U1_first_name
                , U1.last_name AS U1_last_name
                , U2.first_name AS U2_first_name
                , U2.last_name AS U2_last_name
                , U3.first_name AS U3_first_name
                , U3.last_name AS U3_last_name
                , fms_stepmaster.step_name
                , fms_stepmaster.step_id 
                , fms_departmentmaster.department_name
                , fms_divisionmaster.division_name
                , CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_probudgetunit.entry_datetime, GETDATE()) 
                                                            ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END 
                  AS days_stay
                  
                , CASE WHEN log_2.action = 'return' THEN 1
                                                    ELSE 0 END
                  AS return_flag
            FROM fms_probudgetunit
                """ + budget_join_str + """
                LEFT JOIN fms_budgetcondition ON fms_probudgetunit.budget_id=fms_budgetcondition.budget_id
                LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id
                LEFT JOIN fms_progress ON fms_probudgetunit.budget_id=fms_progress.target_id AND fms_progress.target='probudgetunit'
                LEFT JOIN fms_user as U1 ON fms_progress.present_operator=U1.username
                LEFT JOIN fms_user as U2 ON fms_probudgetunit.area_person_in_charge=U2.username
                LEFT JOIN fms_user as U3 ON fms_probudgetunit.original_sec_person_in_charge=U3.username
                LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id
                LEFT JOIN fms_departmentmaster ON fms_probudgetunit.department=fms_departmentmaster.department_cd
                LEFT JOIN fms_divisionmaster ON fms_departmentmaster.division_cd=fms_divisionmaster.division_cd
                LEFT JOIN (SELECT 
                             [target_id] 
                            ,MAX([operation_datetime]) as last_operationtime 
                            FROM [fms].[dbo].[fms_log] 
                            WHERE [target]='probudgetunit' AND [action] != 'temporarily_saved' 
                            group by [target_id]) as log 
                LEFT JOIN(
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
                                    [target] = 'prospecificationunit' AND [action] != 'temporarily_saved'
                                GROUP BY [target_id]
                                ) AS main
                                INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime AND main.target_id=sub.target_id
                            WHERE
                                main.[operation_datetime] = sub.operation_datetime
                ) AS log_2
                ON [fms].[dbo].[fms_probudgetunit].budget_id=log.target_id                      
            WHERE fms_probudgetunit.lost_flag=0
         """
        if where_str != "":
            sql += where_str

        if sel_display_order == "1":
            sql += " ORDER BY fms_probudgetunit.budget_id"
        elif sel_display_order == "2":
            sql += " ORDER BY fms_probudgetunit.budget_no"
        elif sel_display_order == "3":
            sql += " ORDER BY days_stay desc"

        if len(where_parm) == 0:
            execution_budget_lists = ProBudgetUnit.objects.all().raw(sql)
        else:
            execution_budget_lists = ProBudgetUnit.objects.raw(sql, where_parm)
        execution_budget_lists_num = len(list(execution_budget_lists))

        data = {
            'execution_budget_lists': execution_budget_lists,
            'execution_budget_lists_num': execution_budget_lists_num,
        }

        return render(request, 'fms/parts/execution/execution_budget_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算データ一覧
@require_POST
def execution_budget_filter(request):
    from fms.views.common_def_views import get_filter_master, get_next_target, get_area_manager_master
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()
        area_manager_list = get_area_manager_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        start_work_stop_flag = int(request.POST["start_work_stop_flag"])
        if level5_step_id != 213000000 and level5_step_id != 213009000:
            if start_work_stop_flag == 1:
                # 予算中止申請対象は???から???まで
                step_st = 241000000
                step_ed = 252000000
            elif 213001000 <= level5_step_id < 213009000:
                # 予算関連はLevel4で担当部署を分けているので、該当Level4範囲のステップのみ絞込
                step_st = math.floor(level5_step_id / 1000) * 1000
                step_ed = step_st + 1000
            else:
                step_st = math.floor(level5_step_id / 1000000) * 1000000
                step_ed = step_st + 1000000

            step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed,
                                                  step_level=5, lost_flag=0).all().order_by('step_id')
        elif level5_step_id == 213009000:
            # 実行中予算一覧（予算繰越）画面は、probudgetunitのステップを全て指定可能
            step_list = StepMaster.objects.filter(
                Q(target='probudgetunit')).all()
            step_list = step_list.filter(
                Q(step_level=5) & Q(lost_flag=0)).all().order_by('step_id')

        else:
            # 実行中予算一覧（予算完了）画面は、予算関連より前のステップを全て指定可能
            # QオブジェクトのOR条件の優先度が高いため、一度にフィルターできないので3回に分割
            step_list = StepMaster.objects.filter(
                Q(target='probudgetunit')).all()
            step_list = step_list.filter(
                Q(step_level=5) & Q(lost_flag=0)).all()
            step_list = step_list.filter(Q(step_id__range=(133000000, 133009999)) |
                                         Q(step_id__range=(211001000, 211002999))).all().order_by('step_id')

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
            'area_manager_list': area_manager_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'user_department_cd': target_department,
            'user_division_cd': target_division,
            'user': target_person,
        }

        return render(request, 'fms/parts/execution/execution_budget_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算一覧の絞込のパーツ表示
@login_required
@require_POST
def execution_budget_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = int(request.POST['target_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        present_step = int(request.POST['this_step'])
        work_id = int(request.POST['work_id'])

        department = ""
        division = ""
        div_id_name = 'execution_basicinfo'

        base_data = execution_budget_common_data(target_id, request.user.username)

        step_data = StepMaster.objects.get(step_id=present_step)
        step_name = step_data.step_name

        stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name=div_id_name, lost_flag=0)
        this_page = stepdisplayitem_data.page
        action_button_id = 'probudgetunit' + str(this_page) + '_action_button'

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
            # construction_detail
            'sche_gov_inspection_date': base_data['sche_gov_inspection_date'],
            'division_lists': base_data['division_lists'],
            'department_lists': base_data['department_lists'],
            'area_person_in_charge_list': base_data['area_person_in_charge_list'],
            'area_person_in_charge_name': base_data['area_person_in_charge_name'],
            'original_sec_person_in_charge_list': base_data['original_sec_person_in_charge_list'],
            'original_sec_person_in_charge_name': base_data['original_sec_person_in_charge_name'],
            'old_probudgetunit_data_num': base_data['old_probudgetunit_data_num'],
            'old_probudgetunit_data': base_data['old_probudgetunit_data'],
            't_username': t_username,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'div_id_name': div_id_name,
        }

        # データ編集機能要否判定
        budget_edit_action_num = 0
        budget_edit_action_num = budget_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='probudgetunit').count()

        edit_flag = 0
        if budget_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_detail/execution_budget_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_detail/execution_budget_info_base.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# ProBudgetUnitの読込
def execution_budget_common_data(budget_id, username):
    # 予算データを使用
    budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)

    # 新規 データが無いとリストに表示されないため新規はありえない？
    probudgetunit_data = ""
    rev_no = 0  # RevNO
    jurisdiction_area = ""  # 所管エリア
    area_person_in_charge = ""  # エリア管理者
    original_sec_person_in_charge = None_to_blank(budget_data.budget_department_charge_person_id)  # 原課担当者
    sche_gov_inspection_date = ""  # 官庁検査予定日
    username = username  # ユーザーID

    # 調達予算情報テーブル
    probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=0).count()
    # 更新
    if probudgetunit_data_num > 0:
        probudgetunit_data = ProBudgetUnit.objects.get(budget_id=budget_id, lost_flag=0)
        rev_no = None_to_blank(probudgetunit_data.rev_no)  # RevNO
        jurisdiction_area = None_to_blank(probudgetunit_data.jurisdiction_area)  # 所管エリア
        area_person_in_charge = None_to_blank(probudgetunit_data.area_person_in_charge)  # エリア管理者
        original_sec_person_in_charge = None_to_blank(probudgetunit_data.original_sec_person_in_charge)  # 原課担当者
        sche_gov_inspection_date = None_to_blank(probudgetunit_data.sche_gov_inspection_date)  # 官庁検査予定日
        username = original_sec_person_in_charge

    # 予算NO, 予算名
    budget_no = None_to_blank(budget_data.budget_no)  # 予算NO
    budget_name = None_to_blank(budget_data.budget_name)  # 予算名

    # 部門, 部署
    department = None_to_blank(budget_data.budget_main_department_id)  # 部署
    if department is not "":
        department_data = DepartmentMaster.objects.get(department_cd=department)
        division = None_to_blank(department_data.division_cd) # 部門
        # エリア管理者、所管エリアが未設定の場合、部署情報からデフォルト値を使用する
        if jurisdiction_area == '':
            jurisdiction_area = department_data.jurisdiction_area
        if area_person_in_charge == '':
            area_person_in_charge = department_data.area_manager_id

    # 部門選択の候補の一覧用データ抽出
    division_lists = DivisionMaster.objects.filter(lost_flag=0)
    division_name = ""
    if division is not "":
        # 部門
        division_master_data = DivisionMaster.objects.get(division_cd=division, lost_flag=0)
        division_name = division_master_data.division_name

    # 部署選択の候補の一覧用データ抽出
    department_lists = DepartmentMaster.objects.filter(lost_flag=0)
    department_name = ""
    if department is not "":
        # 部署
        department_master_data = DepartmentMaster.objects.get(department_cd=department)
        department_name = department_master_data.department_name

    # エリア管理者選択の候補の一覧用データ抽出　設備部工務Gのみで絞り込み「CWG」
    area_person_in_charge_list, area_person_in_charge_name = \
        get_department_person_option_list('CWG', area_person_in_charge)

    # 原課担当者選択の候補の一覧用データ抽出
    original_sec_person_in_charge_list, original_sec_person_in_charge_name = \
        get_department_person_option_list(department_master_data.department_cd, username)

    # rev_noの古い同じ予算IDのデータの有無を確認
    old_probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=1).count()
    # rev_noの古い同じ予算IDのデータがあれば1つ前のrev_noのレコードを取得(=実際には無効になったレコードのテーブルのidが新しいもの)
    if old_probudgetunit_data_num > 0:
        old_probudgetunit_data = ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=1).all().order_by('-id')[0]
    else:
        old_probudgetunit_data = ""

    data = {
        'probudgetunit_data': probudgetunit_data,
        'budget_id': budget_id,
        'rev_no': rev_no,
        'budget_no': budget_no,
        'budget_name': budget_name,
        'division': division,
        'division_name': division_name,
        'department': department,
        'department_name': department_name,
        'jurisdiction_area': jurisdiction_area,
        'area_person_in_charge': area_person_in_charge,
        'original_sec_person_in_charge': original_sec_person_in_charge,
        # construction_detail
        'sche_gov_inspection_date': sche_gov_inspection_date,
        'division_lists': division_lists,
        'department_lists': department_lists,
        'area_person_in_charge_list': area_person_in_charge_list,
        'area_person_in_charge_name': area_person_in_charge_name,
        'original_sec_person_in_charge_list': original_sec_person_in_charge_list,
        'original_sec_person_in_charge_name': original_sec_person_in_charge_name,
        'old_probudgetunit_data_num': old_probudgetunit_data_num,
        'old_probudgetunit_data': old_probudgetunit_data,
    }

    return data


# 仕様書情報テーブル一覧
@require_POST
def get_execution_work_lists(request):
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
        sel_next_parson = request.POST.get('sel_next_parson')
        sel_on_work = request.POST['sel_on_work']
        level5_step_id_string = request.POST['level5_step_id']
        level5_step_id = int(request.POST['level5_step_id'])
        sel_display_order = request.POST['sel_display_order']
        list_kind = request.POST['list_kind']
        sel_work_id = request.POST['sel_work_id']
        sel_work_name = request.POST['sel_work_name']
        sel_specification_person_in_charge = request.POST['sel_specification_person_in_charge']
        sel_planning_charge_person = request.POST['sel_planning_charge_person']
        sel_area_manager_parson = request.POST['sel_area_manager_parson']

        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000

        where_str = ""
        where_parm = []

        ex_select_str = ""

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
            # ex_select_str += ", fms_budget.business_year_id"
            where_str += " AND fms_budget.business_year_id = %s"
            where_parm.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            # ex_select_str += ", fms_budget.budget_class_id"
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
            ex_select_str += ", fms_budget.facility_process_id"
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
            ex_select_str += ", fms_work.work_name AS planning_work_name"
            where_str += " AND fms_prospecificationunit.work_name LIKE %s"
            where_parm.append('%' + sel_work_name + '%')

        # 仕様担当者
        if sel_specification_person_in_charge != "":
            where_str += " AND fms_prospecificationunit.specification_person_in_charge = %s"
            where_parm.append(sel_specification_person_in_charge)

        # 計画担当者（絞り込み条件が指定されていなくても、リストには表示）
        ex_select_str += ", planningchargepersondata.first_name AS planningchargepersondata_first_name"
        ex_select_str += ", planningchargepersondata.last_name AS planningchargepersondata_last_name"
        planning_charge_person_join_str = 'LEFT JOIN fms_user as planningchargepersondata ON fms_work.work_planning_charge_person_id=planningchargepersondata.username and planningchargepersondata.lost_flag = 0 '
        if sel_planning_charge_person != "":
            # 計画担当者の絞り込み条件を追加
            where_str += " AND fms_work.work_planning_charge_person_id = %s"
            where_parm.append(sel_planning_charge_person)

        # エリア管理者
        if sel_area_manager_parson != "":
            where_str += " AND fms_probudgetunit.area_person_in_charge = %s"
            where_parm.append(sel_area_manager_parson)

        # 未処理のみにチェックがある場合、ユーザーを限定する
        if sel_on_work == 'true':
            where_str += " AND fms_stepmaster.step_id > %s"
            where_str += " AND fms_stepmaster.step_id < %s"
            where_parm.append(step_st)
            where_parm.append(step_ed)

        progress_target = "fms_progress.target='prospecificationunit'"

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
                , fms_budgetclassmaster.budget_class_name as  budget_class
                , fms_processmaster.process_cd as process_cd, fms_processmaster.process_name as process_name
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
                """ + """
                LEFT JOIN fms_budget ON (fms_prospecificationunit.budget_id=fms_budget.budget_id and fms_budget.lost_flag=0)
                LEFT JOIN fms_budgetcondition ON fms_prospecificationunit.budget_id=fms_budgetcondition.budget_id
                LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id
                LEFT JOIN fms_work ON (fms_prospecificationunit.construction_id = fms_work.work_id and fms_work.lost_flag = 0)
                INNER JOIN fms_progress ON fms_prospecificationunit.construction_id=fms_progress.target_id 
                        AND """ + progress_target + """
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
                            group by [target_id]
                ) as log 
                ON [fms].[dbo].[fms_prospecificationunit].construction_id=log.target_id 
                LEFT JOIN(
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
                                    [target] = 'prospecificationunit' AND [action] != 'temporarily_saved'
                                GROUP BY [target_id]
                                ) AS main
                                INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime AND main.target_id=sub.target_id
                            WHERE
                                main.[operation_datetime] = sub.operation_datetime
                ) AS log_2
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
        else:  #sel_display_order == "4":
            sql += " ORDER BY fms_prospecificationunit.construction_id"

        try:
            if len(where_parm) == 0:
                execution_work_lists = ProSpecificationUnit.objects.all().raw(sql)
            else:
                execution_work_lists = ProSpecificationUnit.objects.raw(sql, where_parm)
            execution_work_lists_num = len(list(execution_work_lists))

        except Exception:
            output_log_error(traceback.format_exc())
            msg = "ERROR!!"
            raise

        data = {
            'execution_work_lists': execution_work_lists,
            'execution_work_lists_num': execution_work_lists_num,
            'level5_step_id': level5_step_id,
        }

        if list_kind == 'execution_work':
            return_url = 'fms/parts/execution/execution_work_lists.html'
        elif list_kind == 'copy_work':
            return_url = 'fms/parts/work/work_copy_source/work_copy_source_list.html'
        else:
            return_url = ''

        return render(request, return_url, data)
        # return render(request, 'fms/parts/execution/execution_work_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事一覧の絞込のパーツ表示
@require_POST
def execution_work_filter(request):
    from fms.views.common_def_views import get_filter_master, get_next_target, get_area_manager_master
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()
        area_manager_list = get_area_manager_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        start_work_stop_flag = int(request.POST["start_work_stop_flag"])
        if start_work_stop_flag != 1:
            step_st = math.floor(level5_step_id / 1000000) * 1000000
            step_ed = step_st + 1000000
        else:
            # エリア管理者の中止申請対象は発注処理(step = 241000000)に入ってから工事・検査実行(step = 252000000)まで
            step_st = 241000000
            step_ed = 252000000

        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed,
                                              step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        specification_person_in_charge_list = get_specification_person_in_charge_list()
        planning_charge_person_list = get_filter_planning_charge_person_list()

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
            'user_department_cd': target_department,
            'user_division_cd': target_division,
            'user': target_person,
            'specification_person_in_charge_list': specification_person_in_charge_list,
            'planning_charge_person_list': planning_charge_person_list,
        }

        return render(request, 'fms/parts/execution/execution_work_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 実行中予算情報の画面表示
@login_required
@require_POST
def probudgetunit_detail_template(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser

        # JSからのPOST引数を取得
        level5_step_id = int(request.POST['level5_step_id'])
        target_budget_id = int(request.POST['budget_id'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        target_unique_budget_id = int(request.POST['target_unique_budget_id'])
        present_operator = request.POST['present_operator']

        # ProBudgetUnitがあれば優先なければBudgetを表示
        probudgetunit_list = ProBudgetUnit.objects.filter(budget_id=target_budget_id, lost_flag=0)
        if probudgetunit_list.count() > 0:
            target = 'probudgetunit'
            probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)
            budget_department = probudgetunit_data.department
        else:
            target = 'budget'
            budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
            budget_department = budget_data.budget_main_department_id

        progress_data = Progress.objects.get(target=target, target_id=target_budget_id)

        # タイトル固定
        if level5_step_id == 213000000:
            step_name = '全仕様書作成完了確認（予算完了開始）'
        elif level5_step_id == 213009000:
            step_name = '予算繰越開始'
        this_step = level5_step_id
        # TODO:デフォルトページ番号確認
        page_lists = StepDisplayItem.objects.filter(step=213002001, lost_flag=0).order_by('page')
        tab_num = page_lists.count()
        default_page = page_lists.get(default_page=1)
        default_tab = default_page.page

        this_department = budget_department
        department_data = DepartmentMaster.objects.get(department_cd=budget_department)
        this_division = department_data.division_cd

        # 次ステップは全仕様書発行済み確認
        next_step = 213002001
        next_step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)
        charge_department_class = convert_charge_department(next_step_data.charge_department_class)

        next_department = charge_department_class
        department_data = DepartmentMaster.objects.get(department_cd=charge_department_class)
        next_division = department_data.division_cd

        # 禁止文字リスト取得
        ng_character_list = get_ng_character_list()

        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_id': 0,
            'target_budget_id': target_budget_id,
            'target_step_id': progress_data.present_step,
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
            'last_operation_step': 0,
            'last_operator': '',
            'last_operator_department': '',
            'last_operator_division': '',
            'target_unique_work_id': 0,
            'target_unique_budget_id': target_unique_budget_id,
            'target_work_id': 0,
            'tab_num': tab_num,
            'target_work_rev_no': 0,
            'selected_required_function_id': "",
            'target': target,
            'start_work_stop_flag': 0,
            'default_tab': default_tab,
            'page_lists': page_lists,
            'select_tab': 1,
            'org_unique_budget_id': target_unique_budget_id,
            'present_operator': present_operator,
            'copy_check': 0,
            'ng_character_list': ng_character_list,
        }

        return render(request, 'fms/parts/execution/execution_detail_template.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事情報を表示する基礎画面を表示
@login_required
@require_POST
def execution_detail_template(request):
    try:
        # 調達予算情報テーブルの新規登録は、他処理でバッチ処理などで予算データより登録する

        # ログインユーザー情報取得
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        t_user_is_superuser = request.user.is_superuser

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target = request.POST['target']
        level5_step_id = int(request.POST['level5_step_id'])

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_budget_id = int(request.POST['budget_id'])

        # 共通
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        select_tab = int(request.POST['select_tab'])
        copy_check = int(request.POST['copy_check'])
        start_work_stop_flag = int(request.POST['start_work_stop_flag'])

        # 以下で取得する変数を事前定義、数値は0、文字は空欄
        last_operation_step = 0
        last_operator = ""
        last_operator_department = ""
        last_operator_division = ""
        present_operator = ""
        budget_progress_data_num = 0
        target_unique_carry_forward_id = 0

        if target == 'probudgetunit':
            # 単年度予算リストのID
            target_unique_budget_id = int(request.POST['target_unique_budget_id'])
            present_operator = request.POST['present_operator']
            org_unique_budget_id = target_unique_budget_id

            # 中止新規登録かを確認
            progress_data_num = Progress.objects.filter(target=target, target_id=target_budget_id,
                                                        present_step__gt=213004000, present_step__lt=213009000).count()
            if progress_data_num == 0:
                budget_progress_data_num = Progress.objects.filter(target='budget', target_id=target_budget_id).count()

                probudgetunit_progress_data_num = Progress.objects.filter(target='probudgetunit',
                                                                          target_id=target_budget_id).count()

            if progress_data_num == 0 and start_work_stop_flag == 1:
                progress_data = Progress.objects.get(target=target, target_id=target_budget_id)
                # 中止前step確保
                this_step = progress_data.present_step

                # 中止用のstep
                target_step_id = new_step

            else:
                # 更新時処理
                if progress_data_num == 0 and probudgetunit_progress_data_num == 0 and budget_progress_data_num > 0:
                    target = 'budget'
                # 対象データの現在の工程IDを取得
                progress_data = Progress.objects.get(target=target, target_id=target_budget_id)
                target_step_id = progress_data.present_step
                # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
                this_step = target_step_id

            # 調達予算情報テーブルの存在チェック
            probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).count()
            # 既に作成済みで調達予算情報テーブル
            if probudgetunit_data_num > 0:
                probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)

                # 調達予算情報テーブルの部署データ取得
                budget_department = probudgetunit_data.department
                # 対象の調達予算情報に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data_num = Log.objects.filter(target="probudgetunit", target_id=target_budget_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
                # logデータがあった(過去に対象の予算に操作がされていた)場合
                if log_data_num > 0:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                    log_data = Log.objects.filter(target="probudgetunit", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                        '-operation_datetime').all()[0:1]
                else:
                    # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                    log_data = Log.objects.filter(target="probudgetunit", target_id=target_budget_id, step__lte=this_step).exclude(
                        action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

                # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
                for log_data in log_data:
                    last_operation_step = log_data.step
                    last_operator = log_data.operator
                    last_operator_department = log_data.operator_department
                    last_operator_division = log_data.operator_division

                probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)
                # 対象の調達予算レコードのidを取得
                target_unique_budget_id = probudgetunit_data.id

            # ない場合は、予算データより
            else:
                budget_data = Budget.objects.get(id=target_unique_budget_id, lost_flag=0)
                # 部署データ
                budget_department = budget_data.budget_main_department_id

            this_department = budget_department
            department_data = DepartmentMaster.objects.get(department_cd=budget_department)
            this_division = department_data.division_cd

            # 予算から開くときは、工事主キーID=0
            target_unique_work_id = 0
            target_work_id = 0
            rev_no = 0
            selected_required_function_id = ""

        elif target == 'prospecificationunit':
            target_unique_work_id = int(request.POST['id'])
            target_work_id = int(request.POST['work_id'])
            present_operator = request.POST['present_operator']

            # 予算データのidを取得
            budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
            org_unique_budget_id = budget_data.id

            # 中止新規登録かを確認
            progress_data_num = Progress.objects.filter(target='prospecificationunit', target_id=target_work_id,
                                                        present_step__istartswith='21200').count()

            if progress_data_num == 0 and start_work_stop_flag == 1:
                progress_data = Progress.objects.get(target='prospecificationunit', target_id=target_work_id)
                # 中止前step確保
                this_step = progress_data.present_step

                # 中止用のstep
                target_step_id = new_step

            else:
                # 更新時処理
                # 対象データの現在の工程IDを取得
                progress_data = Progress.objects.get(target='prospecificationunit', target_id=target_work_id)
                target_step_id = progress_data.present_step
                # 変数名置き換え(「target_step_id」→「this_step」)・・・不要？
                this_step = target_step_id

            prospecificationunit_data = ProSpecificationUnit.objects.get(id=target_unique_work_id, lost_flag=0)
            rev_no = prospecificationunit_data.rev_no
            # 要求機能が「Null」のときの処理
            if prospecificationunit_data.req_func is None:
                selected_required_function_id = 0
            # req_funcが空欄でないときの処理
            else:
                work_required_function = prospecificationunit_data.req_func
                sub_no = prospecificationunit_data.sub_id
                function_data = FunctionMaster.objects.get(function_name=work_required_function, lost_flag=0)
                function_cd = function_data.function_cd
                budget_required_function_data = BudgetRequiredFunction.objects.get(budget_id=target_budget_id,
                                                                                   required_function=function_cd,
                                                                                   sub_no=sub_no, lost_flag=0)
                selected_required_function_id = budget_required_function_data.id

            probudgetunit_data_num = ProBudgetUnit.objects.filter(budget_id=target_budget_id, lost_flag=0).count()
            # 存在する
            if probudgetunit_data_num > 0:
                probudgetunit_data = ProBudgetUnit.objects.get(budget_id=target_budget_id, lost_flag=0)
                # 対象の調達予算レコードのidを取得
                target_unique_budget_id = probudgetunit_data.id

                # 調整予算テーブルの部署データ取得
                budget_department = probudgetunit_data.department
            else:
                target_unique_budget_id = ""
                # 予算データの部署データ取得
                budget_department = budget_data.budget_main_department_id

            this_department = budget_department
            department_data = DepartmentMaster.objects.get(department_cd=budget_department)
            this_division = department_data.division_cd

            # 対象の予算に関するlogデータ数を取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
            log_data_num = Log.objects.filter(target="prospecificationunit", target_id=target_work_id, step__lte=this_step).exclude(
                action="temporarily_saved").exclude(action="return").exclude(operator=t_username).count()
            # logデータがあった(過去に対象の予算に操作がされていた)場合
            if log_data_num > 0:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」、自分の操作
                log_data = Log.objects.filter(target="prospecificationunit", target_id=target_work_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").exclude(operator=t_username).order_by(
                    '-operation_datetime').all()[0:1]
            else:
                # 最終処理のlogレコード取得・・・取得条件：工程IDが現工程以下の工程　　除外条件：「一時保存」、「差戻」
                log_data = Log.objects.filter(target="prospecificationunit", target_id=target_budget_id, step__lte=this_step).exclude(
                    action="temporarily_saved").exclude(action="return").order_by('-operation_datetime').all()[0:1]

            # logレコードより最終工程(id)、最終作業者、最終作業者部署、最終作業者部署　※対象のlogレコードがなければ実行されない(=事前定義時のデータを使用）
            for log_data in log_data:
                last_operation_step = log_data.step
                last_operator = log_data.operator
                last_operator_department = log_data.operator_department
                last_operator_division = log_data.operator_division

        elif target == 'budget_carry_forward':
            target_unique_budget_id = int(request.POST['target_unique_budget_id'])
            budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
            rev_no = budget_data.rev_no
            org_unique_budget_id = budget_data.id
            budget_department = budget_data.budget_main_department_id
            this_department = budget_department
            department_data = DepartmentMaster.objects.get(department_cd=budget_department)
            this_division = department_data.division_cd

            target_unique_work_id = 0
            target_work_id = 0
            selected_required_function_id = 0

            this_step = int(request.POST['carry_forward_step'])
            target_step_id = this_step
            target_unique_carry_forward_id = int(request.POST['carry_forward_id'])

        # 次ステップ情報取得
        next_step_data = StepRelation.objects.filter(step_id=target_step_id, lost_flag=0).order_by('display_order')[0]
        next_step = next_step_data.next_step

        # ステップ情報取得
        step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)

        # 対処部署分類を取得（依頼部署か特定部署か）
        charge_department_class = convert_charge_department(step_data.charge_department_class, user_department_cd)

        # 対処部署分類が依頼部署の場合、次作業部門、次作業部署に自部門、自部署を代入
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        else:
            next_department = charge_department_class
            department_data = DepartmentMaster.objects.get(department_cd=charge_department_class)
            next_division = department_data.division_cd

        # コピー対象詳細表示ページはステップを変換
        if level5_step_id == 920000000:
            if target == 'probudgetunit':
                target_step_id = 213008099
            elif target == 'prospecificationunit':
                target_step_id = 252001093

        # 対象のstepで表示するページ情報一覧を取得
        page_lists = StepDisplayItem.objects.filter(step=target_step_id, lost_flag=0).order_by('page')
        # 対象のstepで表示するページ数を取得
        page_lists_num = page_lists.count()
        # タブ数にページ数を設定
        tab_num = page_lists_num
        # 対象のstepでデフォルトで表示するページを取得 # TODO:デフォルトページ番号確認
        default_page = page_lists.get(default_page=1)
        default_tab = default_page.page

        # step名を取得
        step_data = StepMaster.objects.get(step_id=target_step_id, lost_flag=0)
        step_name = step_data.step_name

        # 禁止文字リスト取得
        ng_character_list = get_ng_character_list()

        data = {
            'user_first_name': t_user_first_name,
            'user_last_name': t_user_last_name,
            'target_id': target_unique_work_id,
            'target_budget_id': target_budget_id,
            'target_step_id': target_step_id,
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
            'target_unique_carry_forward_id': target_unique_carry_forward_id,
            'tab_num': tab_num,
            'target_work_rev_no': rev_no,
            'selected_required_function_id': selected_required_function_id,
            'target': target,
            'start_work_stop_flag': start_work_stop_flag,
            'default_tab': default_tab,
            'page_lists': page_lists,
            'select_tab': select_tab,
            'org_unique_budget_id': org_unique_budget_id,
            'present_operator': present_operator,
            'copy_check': copy_check,
            'ng_character_list': ng_character_list,
        }

        return render(request, 'fms/parts/execution/execution_detail_template.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 実行工事データコピー
@require_POST
def execution_work_copy(request):
    try:
        target_work_unique_id = int(request.POST["target_work_unique_id"])
        this_step = int(request.POST["this_step"])
        target = request.POST["target"]
        copy_target = "prospecificationunit"

        pro_specification_unit_data = ProSpecificationUnit.objects.get(id=target_work_unique_id, lost_flag=0)
        budget_id = pro_specification_unit_data.budget_id
        rev_no = pro_specification_unit_data.rev_no
        construction_id = pro_specification_unit_data.construction_id
        sub_id = pro_specification_unit_data.sub_id
        req_func = pro_specification_unit_data.req_func
        format_kbn = pro_specification_unit_data.format_kbn
        goods_construct_kbn = pro_specification_unit_data.goods_construct_kbn
        specification_person_in_charge = pro_specification_unit_data.specification_person_in_charge
        delivery_location = pro_specification_unit_data.delivery_location
        desired_construct_period_from = pro_specification_unit_data.desired_construct_period_from
        desired_construct_period_to = pro_specification_unit_data.desired_construct_period_to
        desired_delivery_date = pro_specification_unit_data.desired_delivery_date
        estimate_submission_date = pro_specification_unit_data.estimate_submission_date
        scheduled_inspection_date_from = pro_specification_unit_data.scheduled_inspection_date_from
        scheduled_inspection_date_to = pro_specification_unit_data.scheduled_inspection_date_to
        specification_data = pro_specification_unit_data.specification_data
        construction_outline = pro_specification_unit_data.construction_outline
        contents_detail1 = pro_specification_unit_data.contents_detail1
        contents_detail2 = pro_specification_unit_data.contents_detail2
        contents_detail3 = pro_specification_unit_data.contents_detail3
        contents_detail4 = pro_specification_unit_data.contents_detail4
        contents_detail5 = pro_specification_unit_data.contents_detail5
        procurement_person_in_charge = pro_specification_unit_data.procurement_person_in_charge
        management_class_cd = pro_specification_unit_data.management_class_cd
        scheduled_acceptance_date_from = pro_specification_unit_data.scheduled_acceptance_date_from
        scheduled_acceptance_date_to = pro_specification_unit_data.scheduled_acceptance_date_to
        preparation_delivery_date = pro_specification_unit_data.preparation_delivery_date
        candidate_vendor1 = pro_specification_unit_data.candidate_vendor1
        candidate_vendor2 = pro_specification_unit_data.candidate_vendor2
        candidate_vendor3 = pro_specification_unit_data.candidate_vendor3
        candidate_vendor4 = pro_specification_unit_data.candidate_vendor4
        candidate_vendor5 = pro_specification_unit_data.candidate_vendor5
        memo = pro_specification_unit_data.memo
        lost_flag = pro_specification_unit_data.lost_flag
        entry_on_progress_flag = pro_specification_unit_data.entry_on_progress_flag
        entry_datetime = pro_specification_unit_data.entry_datetime
        entry_operator = pro_specification_unit_data.entry_operator
        update_datetime = pro_specification_unit_data.update_datetime
        update_operator = pro_specification_unit_data.update_operator

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 登録済みの法令の数をカウント
        law_list_num = WorkLaw.objects.filter(work_id=construction_id, lost_flag=0, entry_class=entry_class).count()

        # 登録済の支給品の数をカウント
        supplies_list_num = Supplies.objects.filter(work_id=construction_id, lost_flag=0, entry_class=entry_class).count()

        # 登録済の提出書類の数をカウント
        document_lists_num = SubmissionDocument.objects.filter(work_id=construction_id, lost_flag=0,
                                                               entry_class=entry_class).count()

        # 格納先path作成　idを汎用的にするため「level4_id」「level5_id」としたい。
        file_folder = '\\' + copy_target + '\\' + str(budget_id) + '\\' + str(construction_id) + '\\'
        # 登録済の添付ファイルの数をカウント
        uploadfile_list_num = AttachmentDocuments.objects.filter(folder=file_folder, div_id_name=copy_target, lost_flag=0).count()

        msg = '工事内容をコピーしました。保存されていないので、保存してください！！'

        ary = {
            'msg': msg,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'construction_id': construction_id,
            'sub_id': sub_id,
            # 'work_name': work_name,
            # 'work_charge_process': work_charge_process,
            'req_func': req_func,
            # 'department': department,
            # 'division': division,
            # 'division_name': division_name,
            'format_kbn': format_kbn,
            'goods_construct_kbn': goods_construct_kbn,
            'specification_person_in_charge': specification_person_in_charge,
            'delivery_location': delivery_location,
            'desired_construct_period_from': desired_construct_period_from,
            'desired_construct_period_to': desired_construct_period_to,
            'desired_delivery_date': desired_delivery_date,
            'estimate_submission_date': estimate_submission_date,
            'scheduled_inspection_date_from': scheduled_inspection_date_from,
            'scheduled_inspection_date_to': scheduled_inspection_date_to,
            'specification_data': specification_data,
            'construction_outline': construction_outline,
            'contents_detail1': contents_detail1,
            'contents_detail2': contents_detail2,
            'contents_detail3': contents_detail3,
            'contents_detail4': contents_detail4,
            'contents_detail5': contents_detail5,
            'procurement_person_in_charge': procurement_person_in_charge,
            'management_class_cd': management_class_cd,
            'scheduled_acceptance_date_from': scheduled_acceptance_date_from,
            'scheduled_acceptance_date_to': scheduled_acceptance_date_to,
            'preparation_delivery_date': preparation_delivery_date,
            'candidate_vendor1': candidate_vendor1,
            'candidate_vendor2': candidate_vendor2,
            'candidate_vendor3': candidate_vendor3,
            'candidate_vendor4': candidate_vendor4,
            'candidate_vendor5': candidate_vendor5,
            'memo': memo,
            'lost_flag': lost_flag,
            'entry_on_progress_flag': entry_on_progress_flag,
            'entry_datetime': entry_datetime,
            'entry_operator': entry_operator,
            'update_datetime': update_datetime,
            'update_operator': update_operator,
            'law_list_num': law_list_num,
            'supplies_list_num': supplies_list_num,
            'document_lists_num': document_lists_num,
            'uploadfile_list_num': uploadfile_list_num,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


@require_POST
def copy_law_supplies_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)

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

        copy_law_list = WorkLaw.objects.filter(work_id=copy_work_id, lost_flag=0, entry_class=entry_class)
        copy_supplies_list = Supplies.objects.filter(work_id=copy_work_id, lost_flag=0, entry_class=entry_class)

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        for copy_law_data in copy_law_list:
            # 「work_id」、「rev_no」、「提出書類名」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
            law_data, created = WorkLaw.objects.get_or_create(work_id=work_id, lost_flag=0, entry_class=entry_class,
                                                              law_name=copy_law_data.law_name)
            # 各項目の値(1つ前のrevでの値)を格納
            law_data.entry_on_progress_flag = 1

            if created == 1:
                # last_law_list = WorkLaw.objects.filter(work_id=work_id, entry_class=entry_class, lost_flag=1,
                #                                        law_name=copy_law_data.law_name)
                last_law_list = WorkLaw.objects.filter(work_id=work_id, entry_class=entry_class,
                                                       entry_on_progress_flag=0, law_name=copy_law_data.law_name)
                if this_step < 200000000:
                    law_data.rev_no = rev_no
                elif last_law_list.count() == 0:
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

        for copy_supplies_data in copy_supplies_list:
            # 「work_id」、「rev_no」、「提出書類名」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
            supplies_data, created = Supplies.objects.get_or_create(work_id=work_id, lost_flag=0, entry_class=entry_class,
                                                                    supplies_name=copy_supplies_data.supplies_name)
            # 各項目の値(1つ前のrevでの値)を格納
            supplies_data.entry_on_progress_flag = 1

            if created == 1:
                last_supplies_list = Supplies.objects.filter(work_id=work_id, entry_class=entry_class,
                                                             entry_on_progress_flag=0,
                                                             supplies_name=copy_supplies_data.supplies_name)
                if this_step < 200000000:
                    supplies_data.rev_no = rev_no
                elif last_supplies_list.count() == 0:
                    supplies_data.rev_no = 0
                else:
                    supplies_data.rev_no = last_supplies_list.order_by('-rev_no')[0].rev_no + 1

                supplies_data.entry_datetime = now
                supplies_data.entry_operator = operator
            else:
                supplies_data.update_datetime = now
                supplies_data.update_operator = operator

            # 提出書類のレコードを保存
            supplies_data.save()

        msg = "法令/支給品データコピー完了！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 提出書類のコピー処理
@require_POST
def copy_document_list_entry(request):
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

        copy_document_list = SubmissionDocument.objects.filter(work_id=copy_work_id, lost_flag=0, entry_class=entry_class)

        copy_document_list_num = SubmissionDocument.objects.filter(work_id=copy_work_id, lost_flag=0,
                                                                   entry_class=entry_class).count()

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        if copy_document_list_num > 0:

            for copy_document_data in copy_document_list:
                # 「work_id」、「rev_no」、「提出書類名」で提出書類のレコードを抽出･･･あれば読み込み、なければ新規登録(ないはずなので新規登録)
                document_data, created = SubmissionDocument.objects.get_or_create(work_id=work_id, lost_flag=0,
                                                                                  entry_class=entry_class,
                                                                                  document_name=copy_document_data.document_name)
                # 各項目の値(1つ前のrevでの値)を格納
                document_data.submission_deadline = copy_document_data.submission_deadline
                document_data.number_of_copies = copy_document_data.number_of_copies
                document_data.display_order = copy_document_data.display_order
                document_data.entry_on_progress_flag = 1

                if created == 1:
                    last_document_list = SubmissionDocument.objects.filter(work_id=work_id, entry_class=entry_class,
                                                                           entry_on_progress_flag=0,
                                                                           document_name=copy_document_data.document_name)
                    if this_step < 200000000:
                        document_data.rev_no = rev_no
                    elif last_document_list.count() == 0:
                        document_data.rev_no = 0
                    else:
                        document_data.rev_no = last_document_list.order_by('-rev_no')[0].rev_no + 1

                    document_data.entry_datetime = now
                    document_data.entry_operator = operator
                else:
                    document_data.update_datetime = now
                    document_data.update_operator = operator

                # 提出書類のレコードを保存
                document_data.save()

            msg = "提出書類データコピー完了！！"

        else:
            msg = "提出書類データコピー対象無し！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 添付ファイルのコピー
@require_POST
def copy_uploadfile_list_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        str_date = datetime.datetime.now().strftime('%Y%m%d')
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # コピー先
        budget_id = int(request.POST["budget_id"])
        work_id = int(request.POST["work_id"])
        target = request.POST["target"]

        # コピー元
        copy_budget_id = int(request.POST['copy_budget_id'])
        copy_work_id = int(request.POST['copy_work_id'])
        copy_step_no = int(request.POST['copy_step_no'])

        if copy_step_no < 200000000 and (target == "work" or target == "prospecificationunit"):
            copy_target = "work"
        elif copy_step_no < 200000000 and target == "budget":
            copy_target = "budget"
        elif copy_step_no > 200000000:
            copy_target = "prospecificationunit"
        else:
            copy_target = ""

        # 格納先path作成　idを汎用的にするため「level4_id」「level5_id」としたい。
        copy_file_folder = '\\' + copy_target + '\\' + str(copy_budget_id) + '\\' + str(copy_work_id) + '\\'
        file_folder = '\\' + target + '\\' + str(budget_id) + '\\' + str(work_id) + '\\'

        # 登録済の添付ファイルの数をカウント
        copy_uploadfile_list = AttachmentDocuments.objects.filter(folder=copy_file_folder, div_id_name=copy_target,
                                                                  lost_flag=0)

        copy_uploadfile_list_num = AttachmentDocuments.objects.filter(folder=copy_file_folder, div_id_name=copy_target,
                                                                  lost_flag=0).count()

        # ベースディレクトリ
        if gethostname() == 'YWEBSERV1':  # 本番
            base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\Production'
        elif gethostname() == 'I7161DD6':  # テスト
            base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test'
        else:
            base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test'

        if copy_uploadfile_list_num > 0:

            for copy_uploadfile_data in copy_uploadfile_list:

                copy_upload_file_path = base_dir + copy_file_folder + copy_uploadfile_data.data + '\\'
                upload_file_path = base_dir + file_folder + copy_uploadfile_data.data + '\\'

                # 存在チェック　なければフォルダ作成
                # if os.path.exists(upload_file_path) != True:
                if os.path.exists(upload_file_path) is not True:
                    os.makedirs(upload_file_path)

                source_file_name = copy_uploadfile_data.file_name

                len_source_file_name = len(source_file_name)

                if len_source_file_name > 8:
                    source_file_name_first_8_chara = source_file_name[0:8]

                    if source_file_name_first_8_chara.isdecimal() is True:
                        if source_file_name[8:9] == '_':
                            source_file_name_without_date = source_file_name[9:len_source_file_name]
                        else:
                            source_file_name_without_date = source_file_name[8:len_source_file_name]
                    else:
                        source_file_name_without_date = source_file_name
                else:
                    source_file_name_without_date = source_file_name

                file_name = str_date + "_" + source_file_name_without_date

                # ファイルの有無確認
                copy_path = os.path.join(copy_upload_file_path, copy_uploadfile_data.file_name)
                # path = os.path.join(upload_file_path, copy_uploadfile_data.file_name)
                path = os.path.join(upload_file_path, file_name)

                if os.path.exists(path) is not True:
                    # ファイルをコピー
                    shutil.copy2(copy_path, path)

                # file = request.FILES['file']
                #
                # with open(path, 'wb') as f:
                #     for chunk in file.chunks():
                #         f.write(chunk)

                # 「folder」、「div_id_name」、「lost_flag=0」で添付ファイルのレコードを抽出･･･あれば読み込み、なければ新規登録
                # (ないはずなので新規登録)
                uploadfile_data, created = AttachmentDocuments.objects.get_or_create(folder=file_folder, div_id_name=target,
                                                                                     file_name=file_name)

                # 各項目の値(1つ前のrevでの値)を格納
                # uploadfile_data.file_name = copy_uploadfile_data.file_name
                uploadfile_data.data = copy_uploadfile_data.data
                uploadfile_data.entry_time = now
                uploadfile_data.entry_user = operator
                uploadfile_data.lost_flag = 0

                # 提出書類のレコードを保存
                uploadfile_data.save()

            msg = "添付ファイルコピー完了！！"

        else:
            msg = "添付ファイルコピー対象無し！！"

        ary = {
            'msg': msg,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事一覧の絞込のパーツ表示
@require_POST
def execution_work_copy_source(request):
    from fms.views.common_def_views import get_filter_master, get_next_target
    try:
        # 絞込条件マスタ情報取得
        budget_condition_list, business_year_list, budget_class_list, division_list, departments_list, process_list = \
            get_filter_master()

        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        step_st = math.floor(level5_step_id / 1000000) * 1000000
        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed,
                                              step_level=5, lost_flag=0).all().order_by('step_id')

        is_mplan_flag = is_mplan_budget_step(level5_step_id)

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        specification_person_in_charge_list = get_specification_person_in_charge_list()
        planning_charge_person_list = get_filter_planning_charge_person_list()

        budget_name_text = get_budget_name_text(level5_step_id)

        data = {
            'copy_budget_condition_list': budget_condition_list,
            'copy_step_list': step_list,
            'copy_business_year_list': business_year_list,
            'copy_budget_class_list': budget_class_list,
            'copy_division_list': division_list,
            'copy_departments_list': departments_list,
            'copy_process_list': process_list,
            'copy_user_list': next_person_list,
            'copy_next_departments_list': next_departments_list,
            'copy_user_department_cd': target_department,
            'copy_user_division_cd': target_division,
            'copy_user': target_person,
            'specification_person_in_charge_list': specification_person_in_charge_list,
            'planning_charge_person_list': planning_charge_person_list,
            'is_mplan_flag': is_mplan_flag,
            'budget_name_text': budget_name_text,
        }

        return render(request, 'fms/parts/work/work_copy_source/work_copy_source.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関連予算を含む工事リストの取得（見込み額、実行額計算処理を含む）
def get_budget_construction_list(relation_budget_id, exclude_construction_id=0):

    sql = """SELECT fms_prospecificationunit. * , fms_stepmaster.step_id , fms_stepmaster.step_name , fms_erpconstruction.total_price"""
    sql = sql + """, fms_erpconstruction.discount_price, fms_budget.relation_budget_id """
    # 実行額
    sql = sql + """, CASE WHEN fms_erpconstruction.total_price > 0 THEN  fms_erpconstruction.total_price - fms_erpconstruction.discount_price """
    sql = sql + """       ELSE 0 """
    sql = sql + """       END as execution_price"""
    # 見込額
    sql = sql + """, CASE WHEN fms_proestimates.confirmed_vendor is not Null AND fms_proestimates.confirmed_estimated_amount_af_nego > 0 THEN  fms_proestimates.confirmed_estimated_amount_af_nego """
    sql = sql + """       WHEN fms_proestimates.confirmed_vendor is not Null AND fms_proestimates.confirmed_last_estimated_amount > 0 THEN  fms_proestimates.confirmed_last_estimated_amount """
    sql = sql + """       WHEN min_estimated_data.min_nego_amount > 0 THEN min_estimated_data.min_nego_amount """
    sql = sql + """       WHEN min_estimated_data.min_estimated_amount > 0 THEN min_estimated_data.min_estimated_amount """
    sql = sql + """       ELSE 0 """
    sql = sql + """       END as prospect_price"""
    # 中止完了フラグ
    sql = sql + """, CASE WHEN fms_stepmaster.step_id=212009902 THEN 1 """
    sql = sql + """       ELSE 0 """
    sql = sql + """       END as cancel_complete_flag"""
    # 各テーブル結合
    sql = sql + """ FROM[fms].[dbo].[fms_prospecificationunit] as fms_prospecificationunit"""
    sql = sql + """ LEFT JOIN fms_progress ON fms_prospecificationunit.construction_id = fms_progress.target_id AND fms_progress.target = 'prospecificationunit'"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step = fms_stepmaster.step_id"""
    sql = sql + """ LEFT JOIN fms_erpconstruction ON fms_prospecificationunit.construction_id = fms_erpconstruction.order_id"""
    sql = sql + """ AND(fms_erpconstruction.work_class = 'CW' OR fms_erpconstruction.work_class = 'RW')"""
    sql = sql + """ AND fms_erpconstruction.total_price!<0"""
    sql = sql + """ LEFT JOIN fms_proestimates ON fms_proestimates.construction_id = fms_prospecificationunit.construction_id AND fms_proestimates.lost_flag = 0"""
    # 見積最低額取得のための結合
    sql = sql + """ LEFT JOIN( """
    sql = sql + """ SELECT estimated_data.construction_id, min(estimated_amount) as min_estimated_amount, min(nego_amount) as min_nego_amount"""
    sql = sql + """ FROM("""
    sql = sql + """ SELECT fms_proestimates.construction_id, fms_proestimates.last_estimated_amount1 as estimated_amount, fms_proestimates.estimated_amount_af_nego1 as nego_amount"""
    sql = sql + """ FROM fms_proestimates"""
    sql = sql + """ LEFT JOIN fms_prospecificationunit ON fms_prospecificationunit.construction_id = fms_proestimates.construction_id"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ WHERE fms_proestimates.last_estimated_amount1 is not Null AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)
    sql = sql + """ UNION ALL"""
    sql = sql + """ SELECT fms_proestimates.construction_id, fms_proestimates.last_estimated_amount2 as estimated_amount, fms_proestimates.estimated_amount_af_nego2 as nego_amount"""
    sql = sql + """ FROM fms_proestimates"""
    sql = sql + """ LEFT JOIN fms_prospecificationunit ON fms_prospecificationunit.construction_id = fms_proestimates.construction_id"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ WHERE fms_proestimates.last_estimated_amount2 is not Null AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)
    sql = sql + """ UNION ALL"""
    sql = sql + """ SELECT fms_proestimates.construction_id, fms_proestimates.last_estimated_amount3 as estimated_amount, fms_proestimates.estimated_amount_af_nego3 as nego_amount"""
    sql = sql + """ FROM fms_proestimates"""
    sql = sql + """ LEFT JOIN fms_prospecificationunit ON fms_prospecificationunit.construction_id = fms_proestimates.construction_id"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ WHERE fms_proestimates.last_estimated_amount3 is not Null AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)
    sql = sql + """ UNION ALL"""
    sql = sql + """ SELECT fms_proestimates.construction_id, fms_proestimates.last_estimated_amount4 as estimated_amount, fms_proestimates.estimated_amount_af_nego4 as nego_amount"""
    sql = sql + """ FROM fms_proestimates"""
    sql = sql + """ LEFT JOIN fms_prospecificationunit ON fms_prospecificationunit.construction_id = fms_proestimates.construction_id"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ WHERE fms_proestimates.last_estimated_amount4 is not Null AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)
    sql = sql + """ UNION ALL"""
    sql = sql + """ SELECT fms_proestimates.construction_id, fms_proestimates.last_estimated_amount5 as estimated_amount, fms_proestimates.estimated_amount_af_nego5 as nego_amount"""
    sql = sql + """ FROM fms_proestimates"""
    sql = sql + """ LEFT JOIN fms_prospecificationunit ON fms_prospecificationunit.construction_id = fms_proestimates.construction_id"""
    sql = sql + """ LEFT JOIN fms_budget ON fms_budget.budget_id = fms_prospecificationunit.budget_id"""
    sql = sql + """ WHERE fms_proestimates.last_estimated_amount5 is not Null AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)
    sql = sql + """ ) as estimated_data"""
    sql = sql + """ GROUP BY estimated_data.construction_id"""
    sql = sql + """ ) as min_estimated_data"""
    sql = sql + """ ON min_estimated_data.construction_id = fms_prospecificationunit.construction_id"""

    sql = sql + """ WHERE fms_budget.lost_flag = 0 AND fms_prospecificationunit.lost_flag = 0 AND fms_budget.relation_budget_id ="""
    sql = sql + str(relation_budget_id)

    # 一部工事を除外する場合は条件追加
    if exclude_construction_id != 0:
        sql = sql + """ AND fms_prospecificationunit.construction_id != """ + str(exclude_construction_id)

    sql = sql + """ ORDER BY fms_stepmaster.step_id, fms_prospecificationunit.construction_id"""

    construction_lists = ProSpecificationUnit.objects.raw(sql)

    # 見込み額合計、実行額合計取得
    budget_prospect_price = 0
    budget_execution_price = 0
    for construction_item in construction_lists:
        # 中止完了していた場合は実行額に含めない
        if construction_item.cancel_complete_flag != 1:
            budget_execution_price += construction_item.execution_price

            if construction_item.execution_price > 0:
                budget_prospect_price += construction_item.execution_price
            else:
                budget_prospect_price += construction_item.prospect_price

    return construction_lists, budget_prospect_price, budget_execution_price

# 予算関連情報取得
@require_POST
def budget_information(request):
    from fms.views.budget_views import get_budget_total_price
    try:
        t_username = request.user.username
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['budget_id'])
        present_step = int(request.POST['this_step'])

        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
        relation_budget_id = budget_data.relation_budget_id

        # 関連予算リスト取得
        sql = """SELECT fms_budget.id, fms_budget.budget_id, fms_budget.budget_no, fms_budget.budget_name, fms_budget.application_class_id, fms_budget.budget_price """
        sql = sql + """ FROM fms_budget """
        sql = sql + """ WHERE fms_budget.lost_flag=0 AND fms_budget.relation_budget_id= """ + str(relation_budget_id)
        sql = sql + """ ORDER BY fms_budget.budget_id """
        budget_lists = Budget.objects.raw(sql)

        # 主予算データ取得
        original_budget_data = Budget.objects.filter(relation_budget_id=relation_budget_id,
                                                     lost_flag=0).order_by('budget_id')[0]

        # 予算額合計取得(budget_view側関数使用)
        budget_total_price = get_budget_total_price(original_budget_data.budget_id)

        # 関連工事リスト取得
        construction_lists, budget_prospect_price, budget_execution_price = \
            get_budget_construction_list(relation_budget_id)
        # 残額取得
        balance_budget_price_prospect = budget_total_price - budget_prospect_price
        balance_budget_price_execution = budget_total_price - budget_execution_price

        start_carry_forward_flg = 0

        # 実行中予算詳細画面のみ特殊処理
        if present_step == 213000000:
            this_step = 213002001
        elif present_step == 213009000:
            this_step = 213002001
            # 繰越処理開始ボタン表示フラグ
            start_carry_forward_flg = 1
        else:
            this_step = present_step

        # アクションボタン表示対応
        stepdisplayitem_list = StepDisplayItem.objects.filter(
            step=this_step, div_id_name='budget_information', lost_flag=0)
        if len(stepdisplayitem_list) > 0:
            stepdisplayitem_item = stepdisplayitem_list[0]
            this_page = stepdisplayitem_item.page
            action_button_id = 'probudgetunit' + str(this_page) + '_action_button'
        else:
            this_page = ''
            action_button_id = ''

        # 予算完了工程の一部は次ステップへ移行可能かチェックを行う
        budget_complete_result = get_budget_complete_count(budget_id, present_step)

        data = {
            'budget_id': original_budget_data.budget_id,
            'original_budget_data': original_budget_data,
            'budget_lists': budget_lists,
            'construction_lists': construction_lists,
            'budget_total_price': budget_total_price,
            'budget_prospect_price': budget_prospect_price,
            'budget_execution_price': budget_execution_price,
            'balance_budget_price_prospect': balance_budget_price_prospect,
            'balance_budget_price_execution': balance_budget_price_execution,
            'budget_complete_flag': budget_complete_result[0],
            'prospecunit_count': budget_complete_result[1],
            'prospecunit_complete_count': budget_complete_result[2],
            'cs_count': budget_complete_result[3],
            'cs_complete_count': budget_complete_result[4],
            'prospecunit_complete_label': budget_complete_result[5],
            'this_step': present_step,
            'this_page': this_page,
            'action_button_id': action_button_id,
            't_username': t_username,
            'start_carry_forward_flg': start_carry_forward_flg,
        }

        return render(request, 'fms/parts/execution/budget_information.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 仕様書担当者選択の候補取得
def get_specification_person_in_charge_list():
    return get_department_person_list('CWG')


# 予算完了処理用進捗判定
def get_budget_complete_count(main_budget_id, present_step):
    # 戻り値用リスト
    # result = budget_complete_flag,prospecunit_count,prospecunit_complete_count,cs_count,cs_complete_count
    result = [0] * 6

    # 予算関連のステップに応じて、仕様書側の判定ステップ値を設定
    if present_step == 213000000 \
            or present_step == 211002001 or present_step == 211001011 or present_step == 211001001:
        target_step_id = 241001001
        result[5] = '仕様書状態（作成完了+中止/総数）'
    elif present_step == 213002001:
        # ERP転送中 以降
        target_step_id = 241003002
        result[5] = '仕様書状態（発注完了+中止/総数）'
    elif present_step == 213003001:
        # 完了 以降
        target_step_id = 252001092
        result[5] = '仕様書状態（完了+中止/総数）'
    elif present_step == 0:
        # probudgetunitが無い場合は完了不可能
        result[0] = 2
        return result
    else:
        # 判定不要ステップ
        return result

    result[0] = 1

    # 追加予算も判定
    budget_list = Budget.objects.filter(relation_budget_id=main_budget_id, lost_flag=0)
    for budget_item in budget_list:
        # 関連予算フラグ
        relation_budget_flag = 0
        if budget_item.budget_id != budget_item.relation_budget_id:
            relation_budget_flag = 1

        # 予算状態が[実行中]か判定
        if target_step_id == 241001001:
            budget_condition_item = BudgetCondition.objects.get(budget_id=budget_item.budget_id)
            if budget_condition_item.budget_condition_id != 31:
                result[0] = 2

        # 仕様書完了数取得
        result_spec = get_specification_progress_count(budget_item.budget_id, target_step_id)
        result[1] += result_spec[0]
        result[2] += result_spec[1]

        # CS側完了数取得
        if present_step == 213002001:
            cs_result = get_cs_complete_count(budget_item.budget_id, relation_budget_flag)
            result[3] += cs_result[0]
            result[4] += cs_result[1]

    # 完了可能判定（仕様書が0の場合は完了不可とする）
    if result[2] < result[1] or result[4] < result[3] or result[1] == 0:
        result[0] = 2

    return result


# budget_idに所属するProSpecificationUnitの進捗判定
def get_specification_progress_count(budget_id, step_id):
    complete_count = 0
    specification_list = ProSpecificationUnit.objects.filter(budget_id=budget_id, lost_flag=0)
    total_count = specification_list.count()

    for specification_item in specification_list:
        # ProSpecificationUnitのProgressを取得

        progress_list = Progress.objects.filter(
            target='prospecificationunit',
            target_id=specification_item.construction_id)

        if len(progress_list) > 0:
            progress_item = progress_list[0]
            # ステップ判定　中止は完了可能とみなす
            if step_id <= progress_item.present_step or progress_item.present_step == 212009902:
                complete_count = complete_count + 1

    return total_count, complete_count


# 関連予算側のprobudgetの完了処理
def probudget_complete_progress(request):
    DIFF_JST_FROM_UTC = 9
    now_naive = datetime.datetime.now()
    now = make_aware(now_naive)
    operator = request.user.username
    this_step = int(request.POST["this_step"])
    next_step = int(request.POST["next_step"])
    next_person_id = int(request.POST["next_person_id"])
    next_division = request.POST["next_division"]
    next_department = request.POST["next_department"]
    target_id = int(request.POST["target_id"])
    this_department = request.POST["this_department"]
    this_division = request.POST["this_division"]
    action = request.POST["action"]
    comment = request.POST["comment"]
    target = request.POST["target"]
    target_budget_id = int(request.POST["target_budget_id"])
    # 次作業者データをユーザー属性マスタから取得
    if UserAttribute.objects.filter(id=next_person_id).count() > 0:
        user_attribute_data = UserAttribute.objects.get(id=next_person_id)
        next_person = user_attribute_data.username
    else:
        next_person = None

    # 関連予算リストの取得
    budget_list = Budget.objects.filter(relation_budget_id=target_id, lost_flag=0)

    for budget_data in budget_list:
        if budget_data.budget_id != budget_data.relation_budget_id:
            progress_data = Progress.objects.get(target='probudgetunit', target_id=budget_data.budget_id)
            # 各項目を設定
            progress_data.present_step = next_step
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

