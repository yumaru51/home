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
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import FreeSpecDetail, SubmissionDocument, Estimate, Supplies, WorkLaw
from fms.models import WorkSpecMEX, PlanningChargePerson
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work
from fms.models import ProBudgetUnit, ProSpecificationUnit, ProEstimates, ProVendorEvaluation, ProIndividualContractDoc
from fms.models import ProInspectionResults, ProDelivery, ProConstructionPrep, ProConstructionQualityResults
from fms.models import SupplierMaster
from fms.views.cs_views import get_cs_complete_relation
from .execution_views import execution_work_common_data
from fms.views.common_views import blank_to_None, None_to_blank, date_to_hyphen, comma_to_value
from gcsystem.models import VendorMaster
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 見積情報テーブル詳細画面
@login_required
@require_POST
def execution_proestimates_data_info(request):
    from fms.views.budget_views import get_budget_total_price
    from fms.views.execution_views import get_budget_construction_list
    try:
        DIFF_JST_FROM_UTC = 9
        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['budget_id'])
        construction_id = int(request.POST['construction_id'])
        present_step = int(request.POST['this_step'])
        level5_step = int(request.POST['level5_step_id'])
        copy_check = int(request.POST['copy_check'])

        # ベース部分(ProSpecificationUnit)の読込(そのままrenderに引き渡すこと)
        base_data = execution_work_common_data(budget_id, construction_id)

        proestimates_data_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                            lost_flag=0).count()
        # 対象のデータがある場合
        if proestimates_data_num > 0:
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            proestimates_data = ProEstimates.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                         lost_flag=0)

            # 各項目の値を取得
            rev_no = None_to_blank(proestimates_data.rev_no)
            sub_id = None_to_blank(proestimates_data.sub_id)
            confirmed_vendor = None_to_blank(proestimates_data.confirmed_vendor)
            if proestimates_data.fixed_delivery_date is not None:
                fixed_delivery_date = proestimates_data.fixed_delivery_date
            else:
                fixed_delivery_date = ''
            if proestimates_data.fixed_delivery_date_from is not None:
                fixed_delivery_date_from = proestimates_data.fixed_delivery_date_from
            else:
                fixed_delivery_date_from = ''
            if proestimates_data.fixed_delivery_date_to is not None:
                fixed_delivery_date_to = proestimates_data.fixed_delivery_date_to
            else:
                fixed_delivery_date_to = ''

            candidate_vendor1 = None_to_blank(proestimates_data.candidate_vendor1)
            candidate_vendor2 = None_to_blank(proestimates_data.candidate_vendor2)
            candidate_vendor3 = None_to_blank(proestimates_data.candidate_vendor3)
            candidate_vendor4 = None_to_blank(proestimates_data.candidate_vendor4)
            candidate_vendor5 = None_to_blank(proestimates_data.candidate_vendor5)

        else:
            proestimates_data = ""

            rev_no = 0
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = base_data['sub_id']
            confirmed_vendor = ""

            # データがない場合はProSpecificationUnitの希望工期などをデフォルト表示する
            if base_data['prospecificationunit_data'] != "":
                fixed_delivery_date_from = None_to_blank(
                    base_data['prospecificationunit_data'].desired_construct_period_from)
                fixed_delivery_date_to = None_to_blank(
                    base_data['prospecificationunit_data'].desired_construct_period_to)
                fixed_delivery_date = None_to_blank(base_data['prospecificationunit_data'].desired_delivery_date)
            else:
                fixed_delivery_date_from = ""
                fixed_delivery_date_to = ""
                fixed_delivery_date = ""

            candidate_vendor1 = base_data['candidate_vendor1']
            candidate_vendor2 = base_data['candidate_vendor2']
            candidate_vendor3 = base_data['candidate_vendor3']
            candidate_vendor4 = base_data['candidate_vendor4']
            candidate_vendor5 = base_data['candidate_vendor5']

        # 無効となった(=1つ前のrev_noの)対象のデータのレコード数を取得
        old_proestimates_data_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                lost_flag=1).count()
        # 無効となった(=1つ前のrev_noの)対象のデータのレコードがある場合
        if old_proestimates_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象のデータを取得
            old_proestimates_data = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                lost_flag=1).all().order_by('-id')[0]
        else:
            old_proestimates_data = ""

        # 業者評価画面を統合するため、ProVendorEvaluationを取得
        provendorevaluation_list = ProVendorEvaluation.objects.filter(budget_id=budget_id,
                                                                      construction_id=construction_id,
                                                                      lost_flag=0).all().order_by('-id')
        if provendorevaluation_list.count() > 0:
            provendorevaluation_data_num = 1
            provendorevaluation_data = provendorevaluation_list.first()
        else:
            provendorevaluation_data_num = 0
            provendorevaluation_data = ""

        old_provendorevaluation_list = ProVendorEvaluation.objects.filter(budget_id=budget_id,
                                                                          construction_id=construction_id,
                                                                          lost_flag=1).all().order_by('-id')
        if old_provendorevaluation_list.count() > 0:
            old_provendorevaluation_data_num = 1
            old_provendorevaluation_data = old_provendorevaluation_list.first()
        else:
            old_provendorevaluation_data_num = 0
            old_provendorevaluation_data = ""

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「proestimates」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                         target_table='proestimates').count()
        edit_flag = 0

        if work_edit_action_num > 0 and level5_step != 920000000 and level5_step != 212001000:
            edit_flag = 1

        if copy_check == 0:
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_estimates',
                                                               lost_flag=0)
            this_page = stepdisplayitem_data.page
            action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
        else:
            this_page = 8
            action_button_id = ''

        decision_flag = 1
        # 確定業者が入力済の場合のみ業者名と比較
        if confirmed_vendor is not None and confirmed_vendor != "":
            if confirmed_vendor == candidate_vendor1:
                decision_flag = 1
            elif confirmed_vendor == candidate_vendor2:
                decision_flag = 2
            elif confirmed_vendor == candidate_vendor3:
                decision_flag = 3
            elif confirmed_vendor == candidate_vendor4:
                decision_flag = 4
            elif confirmed_vendor == candidate_vendor5:
                decision_flag = 5

        # 工程ごとの機能分岐 機能のステップ変更に対応するため、それぞれ別のフラグとする
        # 届出CS完了チェック
        cs_complete_flag = 0
        check_cs_complete_flag = 0
        if present_step == 241002031:
            cs_complete_flag = get_cs_complete_relation(budget_id)
            check_cs_complete_flag = 1

        # 最終金額評価編集可能
        edit_eva_final_price_flag = 0
        if present_step == 241002031:
            edit_eva_final_price_flag = 1

        # 業者決定チェック
        check_vendor_flag = 0
        if present_step == 241002031:
            check_vendor_flag = 1

        # 予算額上限オーバーチェック
        check_budget_price_flag = 0
        balance_budget_price_prospect = 0
        balance_budget_price_execution = 0
        if present_step == 241002031:
            # 予算額合計取得(budget_view側関数使用)
            budget_total_price = get_budget_total_price(base_data['relation_budget_id'])
            # 関連工事リスト取得
            construction_lists, budget_prospect_price, budget_execution_price = \
                get_budget_construction_list(base_data['relation_budget_id'], construction_id)
            # 残額取得
            balance_budget_price_prospect = budget_total_price - budget_prospect_price
            balance_budget_price_execution = budget_total_price - budget_execution_price
            check_budget_price_flag = 1

        # renderに引き渡すdata作成
        data = {
            'work_common_data': base_data,
            'delivery_location': base_data['delivery_location'],
            'desired_construct_period_from': base_data['desired_construct_period_from'],
            'desired_construct_period_to': base_data['desired_construct_period_to'],
            'desired_delivery_date': base_data['desired_delivery_date'],
            'goods_construct_kbn': base_data['goods_construct_kbn'],
            'estimate_submission_date': base_data['estimate_submission_date'],
            'estimated_deadline_date': base_data['estimated_deadline_date'],
            'fixed_delivery_location': base_data['fixed_delivery_location'],
            'fixed_delivery_date_from': fixed_delivery_date_from,
            'fixed_delivery_date_to': fixed_delivery_date_to,
            'fixed_delivery_date': fixed_delivery_date,

            'proestimates_data_num': proestimates_data_num,
            'proestimates_data': proestimates_data,

            'budget_id': budget_id,
            'rev_no': rev_no,
            'budget_no': budget_no,
            'budget_name': budget_name,
            'construction_id': construction_id,
            'sub_id': sub_id,

            'candidate_vendor1': candidate_vendor1,
            'candidate_vendor2': candidate_vendor2,
            'candidate_vendor3': candidate_vendor3,
            'candidate_vendor4': candidate_vendor4,
            'candidate_vendor5': candidate_vendor5,
            'decision_flag': decision_flag,

            'old_proestimates_data_num': old_proestimates_data_num,
            'old_proestimates_data': old_proestimates_data,
            't_username': t_username,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'check_cs_complete_flag': check_cs_complete_flag,
            'edit_eva_final_price_flag': edit_eva_final_price_flag,
            'check_vendor_flag': check_vendor_flag,
            'check_budget_price_flag': check_budget_price_flag,

            'balance_budget_price_prospect': balance_budget_price_prospect,
            'balance_budget_price_execution': balance_budget_price_execution,

            'provendorevaluation_data_num': provendorevaluation_data_num,
            'provendorevaluation_data': provendorevaluation_data,
            'old_provendorevaluation_data_num': old_provendorevaluation_data_num,
            'old_provendorevaluation_data': old_provendorevaluation_data,

            'cs_complete_flag': cs_complete_flag,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_proestimates/execution_proestimates_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_proestimates/execution_proestimates_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 見積情報テーブル登録･更新
@login_required
@require_POST
def execution_proestimates_entry(request):
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

        budget_id = int(request.POST['budget_id'])
        rev_no = request.POST['rev_no']
        construction_id = int(request.POST['construction_id'])
        sub_id = request.POST['sub_id']

        estimated_deadline_date = request.POST['estimated_deadline_date']
        estimated_deadline_date = date_to_hyphen(estimated_deadline_date)
        fixed_delivery_location = request.POST['fixed_delivery_location']
        fixed_delivery_date_from = request.POST['fixed_delivery_date_from']
        if fixed_delivery_date_from != '':
            fixed_delivery_date_from = date_to_hyphen(fixed_delivery_date_from)
        fixed_delivery_date_to = request.POST['fixed_delivery_date_to']
        if fixed_delivery_date_to != '':
            fixed_delivery_date_to = date_to_hyphen(fixed_delivery_date_to)
        fixed_delivery_date = request.POST['fixed_delivery_date']
        if fixed_delivery_date != '':
            fixed_delivery_date = date_to_hyphen(fixed_delivery_date)

        candidate_vendor1 = request.POST['candidate_vendor1']
        quotation_req_date1 = request.POST['quotation_req_date1']
        estimated_reply_date1 = request.POST['estimated_reply_date1']
        last_estimated_amount1 = comma_to_value(request.POST['last_estimated_amount1'])
        estimated_amount_af_nego1 = comma_to_value(request.POST['estimated_amount_af_nego1'])
        eva_delivery_date1 = request.POST['eva_delivery_date1']
        eva_estimated_valuation_amount1 = request.POST['eva_estimated_valuation_amount1']
        eva_estimated_assessment_price1 = comma_to_value(request.POST['eva_estimated_assessment_price1'])
        eva_final_price1 = request.POST['eva_final_price1']
        eva_other1 = request.POST['eva_other1']
        quotation_req_date1 = date_to_hyphen(quotation_req_date1)
        estimated_reply_date1 = date_to_hyphen(estimated_reply_date1)

        candidate_vendor2 = request.POST['candidate_vendor2']
        quotation_req_date2 = request.POST['quotation_req_date2']
        estimated_reply_date2 = request.POST['estimated_reply_date2']
        last_estimated_amount2 = comma_to_value(request.POST['last_estimated_amount2'])
        estimated_amount_af_nego2 = comma_to_value(request.POST['estimated_amount_af_nego2'])
        eva_delivery_date2 = request.POST['eva_delivery_date2']
        eva_estimated_valuation_amount2 = request.POST['eva_estimated_valuation_amount2']
        eva_estimated_assessment_price2 = comma_to_value(request.POST['eva_estimated_assessment_price2'])
        eva_final_price2 = request.POST['eva_final_price2']
        eva_other2 = request.POST['eva_other2']
        quotation_req_date2 = date_to_hyphen(quotation_req_date2)
        estimated_reply_date2 = date_to_hyphen(estimated_reply_date2)

        candidate_vendor3 = request.POST['candidate_vendor3']
        quotation_req_date3 = request.POST['quotation_req_date3']
        estimated_reply_date3 = request.POST['estimated_reply_date3']
        last_estimated_amount3 = comma_to_value(request.POST['last_estimated_amount3'])
        estimated_amount_af_nego3 = comma_to_value(request.POST['estimated_amount_af_nego3'])
        eva_delivery_date3 = request.POST['eva_delivery_date3']
        eva_estimated_valuation_amount3 = request.POST['eva_estimated_valuation_amount3']
        eva_estimated_assessment_price3 = comma_to_value(request.POST['eva_estimated_assessment_price3'])
        eva_final_price3 = request.POST['eva_final_price3']
        eva_other3 = request.POST['eva_other3']
        quotation_req_date3 = date_to_hyphen(quotation_req_date3)
        estimated_reply_date3 = date_to_hyphen(estimated_reply_date3)

        candidate_vendor4 = request.POST['candidate_vendor4']
        quotation_req_date4 = request.POST['quotation_req_date4']
        estimated_reply_date4 = request.POST['estimated_reply_date4']
        last_estimated_amount4 = comma_to_value(request.POST['last_estimated_amount4'])
        estimated_amount_af_nego4 = comma_to_value(request.POST['estimated_amount_af_nego4'])
        eva_delivery_date4 = request.POST['eva_delivery_date4']
        eva_estimated_valuation_amount4 = request.POST['eva_estimated_valuation_amount4']
        eva_estimated_assessment_price4 = comma_to_value(request.POST['eva_estimated_assessment_price4'])
        eva_final_price4 = request.POST['eva_final_price4']
        eva_other4 = request.POST['eva_other4']
        quotation_req_date4 = date_to_hyphen(quotation_req_date4)
        estimated_reply_date4 = date_to_hyphen(estimated_reply_date4)

        candidate_vendor5 = request.POST['candidate_vendor5']
        quotation_req_date5 = request.POST['quotation_req_date5']
        estimated_reply_date5 = request.POST['estimated_reply_date5']
        last_estimated_amount5 = comma_to_value(request.POST['last_estimated_amount5'])
        estimated_amount_af_nego5 = comma_to_value(request.POST['estimated_amount_af_nego5'])
        eva_delivery_date5 = request.POST['eva_delivery_date5']
        eva_estimated_valuation_amount5 = request.POST['eva_estimated_valuation_amount5']
        eva_estimated_assessment_price5 = comma_to_value(request.POST['eva_estimated_assessment_price5'])
        eva_final_price5 = request.POST['eva_final_price5']
        eva_other5 = request.POST['eva_other5']
        quotation_req_date5 = date_to_hyphen(quotation_req_date5)
        estimated_reply_date5 = date_to_hyphen(estimated_reply_date5)

        # 見積情報テーブルを予算ID, 工事IDの存在チェック
        proestimates_data_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                            lost_flag=0).count()
        # 更新
        if proestimates_data_num > 0:
            # 見積情報テーブルを予算ID, 工事IDで読込
            proestimates_data = ProEstimates.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                         lost_flag=0)
            new_record = False
        # 新規登録
        else:
            new_record = True

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
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
            proestimates_data, created = ProEstimates.objects.get_or_create(budget_id=budget_id,
                                                                            construction_id=construction_id,
                                                                            entry_on_progress_flag=0, lost_flag=0)
            # 登録の日時、登録者を登録
            proestimates_data.entry_datetime = now
            proestimates_data.entry_operator = operator
            # 工事納入情報テーブルを保存
            proestimates_data.save()
            # 登録日時、登録者で工事納入情報テーブルを抽出
            proestimates_data = ProEstimates.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
            # 主キーを取得
            proestimates_unique_id = proestimates_data.id
            # 主キーで工事納入情報テーブルを抽出
            proestimates_data = ProEstimates.objects.get(id=proestimates_unique_id, lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            proestimates_data.rev_no = 0
            proestimates_data.entry_on_progress_flag = 1
            proestimates_data.lost_flag = 0
            # 工事納入情報テーブルを保存
            proestimates_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                 entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProEstimates.objects.filter(budget_id=budget_id,
                                                                    construction_id=construction_id,
                                                                    entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                proestimates_data = ProEstimates.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                                entry_on_progress_flag=0, lost_flag=0).order_by('-id')[
                    0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = proestimates_data.rev_no
                # 該当のレコードを無効
                proestimates_data.lost_flag = 1
                # 予算のレコードを保存
                proestimates_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProEstimates(budget_id=budget_id, construction_id=construction_id, entry_datetime=now,
                             entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                proestimates_data = ProEstimates.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                proestimates_unique_id = proestimates_data.id
                # 主キーで予算レコードを抽出
                proestimates_data = ProEstimates.objects.get(id=proestimates_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                proestimates_data.rev_no = latest_rev_no + 1
                proestimates_data.entry_on_progress_flag = 1
                proestimates_data.lost_flag = 0
                # 保存
                proestimates_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                proestimates_data = ProEstimates.objects.get(budget_id=budget_id, construction_id=construction_id,
                                                             entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                proestimates_unique_id = proestimates_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"
        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 主キーで見積もりテーブルを抽出
        proestimates_data = ProEstimates.objects.get(id=proestimates_unique_id, lost_flag=0)

        # 各項目の値を設定
        proestimates_data.sub_id = blank_to_None(sub_id)
        proestimates_data.estimated_deadline_date = blank_to_None(estimated_deadline_date)
        proestimates_data.fixed_delivery_location = blank_to_None(fixed_delivery_location)
        proestimates_data.fixed_delivery_date_from = blank_to_None(fixed_delivery_date_from)
        proestimates_data.fixed_delivery_date_to = blank_to_None(fixed_delivery_date_to)
        proestimates_data.fixed_delivery_date = blank_to_None(fixed_delivery_date)

        proestimates_data.candidate_vendor1 = blank_to_None(candidate_vendor1)
        proestimates_data.maker_name1 = blank_to_None(request.POST['maker_name1'])
        proestimates_data.quotation_req_date1 = blank_to_None(quotation_req_date1)
        proestimates_data.estimated_reply_date1 = blank_to_None(estimated_reply_date1)
        proestimates_data.last_estimated_amount1 = blank_to_None(last_estimated_amount1)
        proestimates_data.last_estimated_discount1 = comma_to_value(request.POST['last_estimated_discount1'])
        proestimates_data.estimated_amount_af_nego1 = blank_to_None(estimated_amount_af_nego1)
        proestimates_data.eva_delivery_date1 = blank_to_None(eva_delivery_date1)
        proestimates_data.eva_estimated_valuation_amount1 = blank_to_None(eva_estimated_valuation_amount1)
        proestimates_data.eva_estimated_assessment_price1 = blank_to_None(eva_estimated_assessment_price1)
        proestimates_data.eva_final_price1 = blank_to_None(eva_final_price1)
        proestimates_data.eva_other1 = blank_to_None(eva_other1)

        proestimates_data.candidate_vendor2 = blank_to_None(candidate_vendor2)
        proestimates_data.maker_name2 = blank_to_None(request.POST['maker_name2'])
        proestimates_data.quotation_req_date2 = blank_to_None(quotation_req_date2)
        proestimates_data.estimated_reply_date2 = blank_to_None(estimated_reply_date2)
        proestimates_data.last_estimated_amount2 = blank_to_None(last_estimated_amount2)
        proestimates_data.last_estimated_discount2 = comma_to_value(request.POST['last_estimated_discount2'])
        proestimates_data.estimated_amount_af_nego2 = blank_to_None(estimated_amount_af_nego2)
        proestimates_data.eva_delivery_date2 = blank_to_None(eva_delivery_date2)
        proestimates_data.eva_estimated_valuation_amount2 = blank_to_None(eva_estimated_valuation_amount2)
        proestimates_data.eva_estimated_assessment_price2 = blank_to_None(eva_estimated_assessment_price2)
        proestimates_data.eva_final_price2 = blank_to_None(eva_final_price2)
        proestimates_data.eva_other2 = blank_to_None(eva_other2)

        proestimates_data.candidate_vendor3 = blank_to_None(candidate_vendor3)
        proestimates_data.maker_name3 = blank_to_None(request.POST['maker_name3'])
        proestimates_data.quotation_req_date3 = blank_to_None(quotation_req_date3)
        proestimates_data.estimated_reply_date3 = blank_to_None(estimated_reply_date3)
        proestimates_data.last_estimated_amount3 = blank_to_None(last_estimated_amount3)
        proestimates_data.last_estimated_discount3 = comma_to_value(request.POST['last_estimated_discount3'])
        proestimates_data.estimated_amount_af_nego3 = blank_to_None(estimated_amount_af_nego3)
        proestimates_data.eva_delivery_date3 = blank_to_None(eva_delivery_date3)
        proestimates_data.eva_estimated_valuation_amount3 = blank_to_None(eva_estimated_valuation_amount3)
        proestimates_data.eva_estimated_assessment_price3 = blank_to_None(eva_estimated_assessment_price3)
        proestimates_data.eva_final_price3 = blank_to_None(eva_final_price3)
        proestimates_data.eva_other3 = blank_to_None(eva_other3)

        proestimates_data.candidate_vendor4 = blank_to_None(candidate_vendor4)
        proestimates_data.maker_name4 = blank_to_None(request.POST['maker_name4'])
        proestimates_data.quotation_req_date4 = blank_to_None(quotation_req_date4)
        proestimates_data.estimated_reply_date4 = blank_to_None(estimated_reply_date4)
        proestimates_data.last_estimated_amount4 = blank_to_None(last_estimated_amount4)
        proestimates_data.last_estimated_discount4 = comma_to_value(request.POST['last_estimated_discount4'])
        proestimates_data.estimated_amount_af_nego4 = blank_to_None(estimated_amount_af_nego4)
        proestimates_data.eva_delivery_date4 = blank_to_None(eva_delivery_date4)
        proestimates_data.eva_estimated_valuation_amount4 = blank_to_None(eva_estimated_valuation_amount4)
        proestimates_data.eva_estimated_assessment_price4 = blank_to_None(eva_estimated_assessment_price4)
        proestimates_data.eva_final_price4 = blank_to_None(eva_final_price4)
        proestimates_data.eva_other4 = blank_to_None(eva_other4)

        proestimates_data.candidate_vendor5 = blank_to_None(candidate_vendor5)
        proestimates_data.maker_name5 = blank_to_None(request.POST['maker_name5'])
        proestimates_data.quotation_req_date5 = blank_to_None(quotation_req_date5)
        proestimates_data.estimated_reply_date5 = blank_to_None(estimated_reply_date5)
        proestimates_data.last_estimated_amount5 = blank_to_None(last_estimated_amount5)
        proestimates_data.last_estimated_discount5 = comma_to_value(request.POST['last_estimated_discount5'])
        proestimates_data.estimated_amount_af_nego5 = blank_to_None(estimated_amount_af_nego5)
        proestimates_data.eva_delivery_date5 = blank_to_None(eva_delivery_date5)
        proestimates_data.eva_estimated_valuation_amount5 = blank_to_None(eva_estimated_valuation_amount5)
        proestimates_data.eva_estimated_assessment_price5 = blank_to_None(eva_estimated_assessment_price5)
        proestimates_data.eva_final_price5 = blank_to_None(eva_final_price5)
        proestimates_data.eva_other5 = blank_to_None(eva_other5)

        decision_check_val = request.POST['decision_check']

        if decision_check_val == '1':
            proestimates_data.confirmed_vendor = blank_to_None(candidate_vendor1)
            proestimates_data.confirmed_last_estimated_amount = blank_to_None(last_estimated_amount1)
            proestimates_data.confirmed_estimated_amount_af_nego = blank_to_None(estimated_amount_af_nego1)
        elif decision_check_val == '2':
            proestimates_data.confirmed_vendor = blank_to_None(candidate_vendor2)
            proestimates_data.confirmed_last_estimated_amount = blank_to_None(last_estimated_amount2)
            proestimates_data.confirmed_estimated_amount_af_nego = blank_to_None(estimated_amount_af_nego2)
        elif decision_check_val == '3':
            proestimates_data.confirmed_vendor = blank_to_None(candidate_vendor3)
            proestimates_data.confirmed_last_estimated_amount = blank_to_None(last_estimated_amount3)
            proestimates_data.confirmed_estimated_amount_af_nego = blank_to_None(estimated_amount_af_nego3)
        elif decision_check_val == '4':
            proestimates_data.confirmed_vendor = blank_to_None(candidate_vendor4)
            proestimates_data.confirmed_last_estimated_amount = blank_to_None(last_estimated_amount4)
            proestimates_data.confirmed_estimated_amount_af_nego = blank_to_None(estimated_amount_af_nego4)
        elif decision_check_val == '5':
            proestimates_data.confirmed_vendor = blank_to_None(candidate_vendor5)
            proestimates_data.confirmed_last_estimated_amount = blank_to_None(last_estimated_amount5)
            proestimates_data.confirmed_estimated_amount_af_nego = blank_to_None(estimated_amount_af_nego5)
        else:
            proestimates_data.confirmed_vendor = None
            proestimates_data.confirmed_last_estimated_amount = None
            proestimates_data.confirmed_estimated_amount_af_nego = None

        proestimates_data.update_datetime = now
        proestimates_data.update_operator = operator

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            proestimates_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            proestimates_data.entry_on_progress_flag = 1

        # rev_no取得
        proestimates_rev_no = proestimates_data.rev_no

        # 見積情報テーブルのレコードを保存
        proestimates_data.save()

        # 調達仕様書情報テーブル処理
        prospecificationunit_data = ProSpecificationUnit.objects.get(budget_id=budget_id,
                                                                     construction_id=construction_id,
                                                                     lost_flag=0)
        prospecificationunit_data.special_vendor_si_comment = blank_to_None(request.POST['special_vendor_si_comment'])
        prospecificationunit_data.save()

        # 工事納入情報テーブル処理
        edit_eva_final_price_flag = request.POST['edit_eva_final_price_flag']
        eva_final_price = request.POST['eva_final_price']
        if edit_eva_final_price_flag == '1':

            # 工事納入情報テーブルを予算ID, 工事IDの存在チェック
            provendorevaluation_data_list = ProVendorEvaluation.objects.filter(budget_id=budget_id,
                                                                               construction_id=construction_id,
                                                                               lost_flag=0).order_by('-id')
            if provendorevaluation_data_list.count() > 0:
                # 工事納入情報テーブルを予算ID, 工事IDで読込
                provendorevaluation_data = provendorevaluation_data_list.first()
                new_record = False
            else:
                new_record = True

            # 新規登録時の処理
            if new_record == True:
                provendorevaluation_data, created = ProVendorEvaluation.objects.get_or_create(budget_id=budget_id,
                                                                                              construction_id=construction_id,
                                                                                              entry_on_progress_flag=0,
                                                                                              lost_flag=0)
                provendorevaluation_data.entry_datetime = now
                provendorevaluation_data.entry_operator = operator
                provendorevaluation_data.save()
                provendorevaluation_data = ProVendorEvaluation.objects.get(entry_datetime=now, entry_operator=operator,
                                                                           lost_flag=0)
                provendorevaluation_unique_id = provendorevaluation_data.id
                provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id,
                                                                           lost_flag=0)
                provendorevaluation_data.rev_no = 0
                provendorevaluation_data.entry_on_progress_flag = 1
                provendorevaluation_data.lost_flag = 0
                provendorevaluation_data.save()
            # 更新時の処理
            else:
                on_progress_budget_num = ProVendorEvaluation.objects.filter(budget_id=budget_id,
                                                                            construction_id=construction_id,
                                                                            entry_on_progress_flag=1,
                                                                            lost_flag=0).count()
                complete_entry_budget_num = ProVendorEvaluation.objects.filter(budget_id=budget_id,
                                                                               construction_id=construction_id,
                                                                               entry_on_progress_flag=0,
                                                                               lost_flag=0).count()
                if complete_entry_budget_num > 0:
                    provendorevaluation_data = \
                    ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id,
                                                       entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                    latest_rev_no = provendorevaluation_data.rev_no
                    provendorevaluation_data.lost_flag = 1
                    provendorevaluation_data.save()
                else:
                    latest_rev_no = -1

                if on_progress_budget_num == 0:
                    ProVendorEvaluation(budget_id=budget_id, construction_id=construction_id, entry_datetime=now,
                                        entry_operator=operator, lost_flag=0).save()
                    provendorevaluation_data = ProVendorEvaluation.objects.get(entry_datetime=now,
                                                                               entry_operator=operator, lost_flag=0)
                    provendorevaluation_unique_id = provendorevaluation_data.id
                    provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id,
                                                                               lost_flag=0)
                    provendorevaluation_data.rev_no = latest_rev_no + 1
                    provendorevaluation_data.entry_on_progress_flag = 1
                    provendorevaluation_data.lost_flag = 0
                    provendorevaluation_data.save()
                else:
                    provendorevaluation_data = ProVendorEvaluation.objects.get(budget_id=budget_id,
                                                                               construction_id=construction_id,
                                                                               entry_on_progress_flag=1, lost_flag=0)
                    provendorevaluation_unique_id = provendorevaluation_data.id

            provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id, lost_flag=0)
            # 各項目の値を設定
            provendorevaluation_data.sub_id = blank_to_None(sub_id)
            provendorevaluation_data.eva_final_price = blank_to_None(eva_final_price)
            if this_step != next_step:
                provendorevaluation_data.entry_on_progress_flag = 0
            else:
                provendorevaluation_data.entry_on_progress_flag = 1

            # 工事納入情報テーブルのレコードを保存
            provendorevaluation_data.save()

        # ログデータを新規登録 ログより差戻を可能とするためtarget='prospecificationunit'とする
        Log(target='prospecificationunit', target_id=construction_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=this_budget_id).save()

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
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
