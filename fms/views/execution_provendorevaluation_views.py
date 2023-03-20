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
from fms.models import ProBudgetUnit, ProSpecificationUnit, ProEstimates, ProVendorEvaluation
from fms.models import ProInspectionResults, ProConstructionPrep, ProConstructionQualityResults
from .execution_views import execution_work_common_data
from .cs_views import get_cs_complete_relation

from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 業者評価テーブル詳細画面
@login_required
@require_POST
def execution_provendorevaluation_data_info(request):
    try:
        # now = datetime.date.today()
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

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

        provendorevaluation_data_num = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 対象のデータがある場合
        if provendorevaluation_data_num > 0:
            provendorevaluation_data = ProVendorEvaluation.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)

            # 各項目の値を取得
            rev_no = provendorevaluation_data.rev_no if provendorevaluation_data.rev_no is not None else ""
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = provendorevaluation_data.sub_id if provendorevaluation_data.sub_id is not None else ""

            estimate_assessment_evaluation_sum = provendorevaluation_data.estimate_assessment_evaluation_sum if provendorevaluation_data.estimate_assessment_evaluation_sum is not None else ""
            candidate_vendor_comment1 = provendorevaluation_data.candidate_vendor_comment1 if provendorevaluation_data.candidate_vendor_comment1 is not None else ""
            candidate_vendor_comment2 = provendorevaluation_data.candidate_vendor_comment2 if provendorevaluation_data.candidate_vendor_comment2 is not None else ""
            candidate_vendor_comment3 = provendorevaluation_data.candidate_vendor_comment3 if provendorevaluation_data.candidate_vendor_comment3 is not None else ""
            candidate_vendor_comment4 = provendorevaluation_data.candidate_vendor_comment4 if provendorevaluation_data.candidate_vendor_comment4 is not None else ""
            candidate_vendor_comment5 = provendorevaluation_data.candidate_vendor_comment5 if provendorevaluation_data.candidate_vendor_comment5 is not None else ""
            eva_final_price = provendorevaluation_data.eva_final_price if provendorevaluation_data.eva_final_price is not None else ""
        else:
            provendorevaluation_data = ''

            rev_no = 0
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = base_data['sub_id']

            estimate_assessment_evaluation_sum = ''
            candidate_vendor_comment1 = ''
            candidate_vendor_comment2 = ''
            candidate_vendor_comment3 = ''
            candidate_vendor_comment4 = ''
            candidate_vendor_comment5 = ''
            eva_final_price = ''

        # 無効となった(=1つ前のrev_noの)対象のデータのレコード数を取得
        old_provendorevaluation_data_num = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).count()
        # 無効となった(=1つ前のrev_noの)対象のデータのレコードがある場合
        if old_provendorevaluation_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象のデータを取得
            old_provendorevaluation_data = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_provendorevaluation_data = ""

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「ProVendorEvaluation」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='provendorevaluation').count()
        edit_flag = 0

        if work_edit_action_num > 0 and level5_step != 212001000:
            edit_flag = 1

        if copy_check == 0:
            # タブ毎のボタン表示対応
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_vendorevaluation', lost_flag=0)
            this_page = stepdisplayitem_data.page
            action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
        else:
            this_page = 9
            action_button_id = ''

        cs_complete_flag = get_cs_complete_relation(budget_id)

        data = {
            'work_common_data': base_data,
            'provendorevaluation_data_num': provendorevaluation_data_num,
            'provendorevaluation_data': provendorevaluation_data,
            'old_provendorevaluation_data_num': old_provendorevaluation_data_num,
            'old_provendorevaluation_data': old_provendorevaluation_data,
            't_username': t_username,
            # 20201211y-kawauchi タブ毎のボタン表示対応
            'this_page': this_page,
            'action_button_id': action_button_id,

            'budget_id': budget_id,
            'rev_no': rev_no,
            'budget_no': budget_no,
            'budget_name': budget_name,
            'construction_id': construction_id,
            'sub_id': sub_id,

            # 20201205y-kawauchi DB参照
            'estimate_assessment_evaluation_sum': estimate_assessment_evaluation_sum,
            'candidate_vendor_comment1': candidate_vendor_comment1,
            'candidate_vendor_comment2': candidate_vendor_comment2,
            'candidate_vendor_comment3': candidate_vendor_comment3,
            'candidate_vendor_comment4': candidate_vendor_comment4,
            'candidate_vendor_comment5': candidate_vendor_comment5,
            'eva_final_price': eva_final_price,

            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],

            'target_id': request.POST['target_id'],
            'target_step_id': request.POST['target_step_id'],

            'cs_complete_flag': cs_complete_flag,

        }

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_provendorevaluation/execution_provendorevaluation_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_provendorevaluation/execution_provendorevaluation_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事納入情報テーブル登録･更新
@login_required
@require_POST
def execution_provendorevaluation_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # # JST = timezone(timedelta(hours=+9), 'JST')
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

        # 工事納入情報テーブルを予算ID, 工事IDの存在チェック
        provendorevaluation_data_num = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 更新
        if provendorevaluation_data_num > 0:
            # 工事納入情報テーブルを予算ID, 工事IDで読込
            provendorevaluation_data = ProVendorEvaluation.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)
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
            provendorevaluation_data, created = ProVendorEvaluation.objects.get_or_create(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0)
            # 登録の日時、登録者を登録
            provendorevaluation_data.entry_datetime = now
            provendorevaluation_data.entry_operator = operator
            # 工事納入情報テーブルを保存
            provendorevaluation_data.save()
            # 登録日時、登録者で工事納入情報テーブルを抽出
            provendorevaluation_data = ProVendorEvaluation.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
            # 主キーを取得
            provendorevaluation_unique_id = provendorevaluation_data.id
            # 主キーで工事納入情報テーブルを抽出
            provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id, lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            provendorevaluation_data.rev_no = 0
            provendorevaluation_data.entry_on_progress_flag = 1
            provendorevaluation_data.lost_flag = 0
            # 工事納入情報テーブルを保存
            provendorevaluation_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                provendorevaluation_data = ProVendorEvaluation.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = provendorevaluation_data.rev_no
                # 該当のレコードを無効
                provendorevaluation_data.lost_flag = 1
                # 予算のレコードを保存
                provendorevaluation_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProVendorEvaluation(budget_id=budget_id, construction_id=construction_id, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                provendorevaluation_data = ProVendorEvaluation.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                provendorevaluation_unique_id = provendorevaluation_data.id
                # 主キーで予算レコードを抽出
                provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                provendorevaluation_data.rev_no = latest_rev_no + 1
                provendorevaluation_data.entry_on_progress_flag = 1
                provendorevaluation_data.lost_flag = 0
                # 予算のレコードを保存
                provendorevaluation_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                provendorevaluation_data = ProVendorEvaluation.objects.get(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                provendorevaluation_unique_id = provendorevaluation_data.id

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

        # 主キーで予算レコードを抽出
        provendorevaluation_data = ProVendorEvaluation.objects.get(id=provendorevaluation_unique_id, lost_flag=0)

        # 各項目の値を設定
        provendorevaluation_data.sub_id = sub_id if sub_id is not '' else None
        # provendorevaluation_data.estimate_assessment_evaluation_sum = request.POST["estimate_assessment_evaluation_sum"] if request.POST["estimate_assessment_evaluation_sum"] is not '' else None
        # provendorevaluation_data.candidate_vendor_comment1 = request.POST["candidate_vendor_comment1"] if request.POST["candidate_vendor_comment1"] is not '' else None
        # provendorevaluation_data.candidate_vendor_comment2 = request.POST["candidate_vendor_comment2"] if request.POST["candidate_vendor_comment2"] is not '' else None
        # provendorevaluation_data.candidate_vendor_comment3 = request.POST["candidate_vendor_comment3"] if request.POST["candidate_vendor_comment3"] is not '' else None
        # provendorevaluation_data.candidate_vendor_comment4 = request.POST["candidate_vendor_comment4"] if request.POST["candidate_vendor_comment4"] is not '' else None
        # provendorevaluation_data.candidate_vendor_comment5 = request.POST["candidate_vendor_comment5"] if request.POST["candidate_vendor_comment5"] is not '' else None
        provendorevaluation_data.eva_final_price = request.POST["eva_final_price"] if request.POST["eva_final_price"] is not '' else None

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            provendorevaluation_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            provendorevaluation_data.entry_on_progress_flag = 1

        # rev_no取得
        provendorevaluation_rev_no = provendorevaluation_data.rev_no

        # 工事納入情報テーブルのレコードを保存
        provendorevaluation_data.save()

        # ログデータを新規登録
        #Log(target='provendorevaluation', target_id=construction_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()
        # ログより差戻を可能とするためtarget='prospecificationunit'とする
        Log(target='prospecificationunit', target_id=construction_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        # 進捗状況を対象(prospecificationunit)と工事idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="prospecificationunit", target_id=construction_id)
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

