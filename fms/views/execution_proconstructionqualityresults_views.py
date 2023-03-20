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
from fms.models import ProConstructionQualityResults, ProConstructionPrep, ProConstructionQualityResults
from .execution_views import execution_work_common_data
from common.common_def import date_to_many_type
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 工事品質結果テーブル詳細画面
@login_required
@require_POST
def execution_proconstructionqualityresults_data_info(request):
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
        level5_step_id = int(request.POST['level5_step_id'])
        copy_check = int(request.POST['copy_check'])

        # ベース部分(ProSpecificationUnit)の読込(そのままrenderに引き渡すこと)
        base_data = execution_work_common_data(budget_id, construction_id)

        # 対象のデータがあるかチェック
        proconstructionqualityresults_data_num = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # ある場合各項目値取得
        if proconstructionqualityresults_data_num > 0:
            proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)

            rev_no = proconstructionqualityresults_data.rev_no if proconstructionqualityresults_data.rev_no is not None else ""
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = proconstructionqualityresults_data.sub_id if proconstructionqualityresults_data.sub_id is not None else ""

            quality_inspection_result = proconstructionqualityresults_data.quality_inspection_result if proconstructionqualityresults_data.quality_inspection_result is not None else ""
            production_permit_date = proconstructionqualityresults_data.production_permit_date if proconstructionqualityresults_data.production_permit_date is not None else ""
            memo = proconstructionqualityresults_data.memo if proconstructionqualityresults_data.memo is not None else ""
            date_of_receipt_of_submitted_materials = proconstructionqualityresults_data.date_of_receipt_of_submitted_materials if proconstructionqualityresults_data.date_of_receipt_of_submitted_materials is not None else ""
            submitted_doc_memo = proconstructionqualityresults_data.submitted_doc_memo if proconstructionqualityresults_data.submitted_doc_memo is not None else ""
            check_result = proconstructionqualityresults_data.check_result if proconstructionqualityresults_data.check_result is not None else ""
            acceptance_date = proconstructionqualityresults_data.acceptance_date if proconstructionqualityresults_data.acceptance_date is not None else ""
            receipt = proconstructionqualityresults_data.receipt if proconstructionqualityresults_data.receipt is not None else ""
            receipt_sending_date = proconstructionqualityresults_data.receipt_sending_date if proconstructionqualityresults_data.receipt_sending_date is not None else ""
            construction_completion_date = proconstructionqualityresults_data.construction_completion_date if proconstructionqualityresults_data.construction_completion_date is not None else ""

        # ない場合空値
        else:
            proconstructionqualityresults_data = ''

            rev_no = 0
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = base_data['sub_id']

            quality_inspection_result = ''
            production_permit_date = ''
            memo = ''
            # date_of_receipt_of_submitted_materials = datetime.date.today()
            date_of_receipt_of_submitted_materials = ""
            submitted_doc_memo = ''
            check_result = ''
            acceptance_date = ''
            receipt = ''
            receipt_sending_date = ''
            construction_completion_date = ''

        # 無効となった(=1つ前のrev_noの)対象のデータのレコード数を取得
        old_proconstructionqualityresults_data_num = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).count()
        # 無効となった(=1つ前のrev_noの)対象のデータのレコードがある場合
        if old_proconstructionqualityresults_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象のデータを取得
            old_proconstructionqualityresults_data = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_proconstructionqualityresults_data = ""

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「ProConstructionQualityResults」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='proconstructionqualityresults').count()
        edit_flag = 0

        if work_edit_action_num > 0 and level5_step_id != 212001000:
            edit_flag = 1

        if copy_check ==0:
            # タブ毎のボタン表示対応
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_constructionqualityresults', lost_flag=0)
            this_page = stepdisplayitem_data.page
            action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
        else:
            this_page = 15
            action_button_id = ''

        data = {
            'work_common_data': base_data,
            'proconstructionqualityresults_data_num': proconstructionqualityresults_data_num,
            'proconstructionqualityresults_data': proconstructionqualityresults_data,
            'old_proconstructionqualityresults_data_num': old_proconstructionqualityresults_data_num,
            'old_proconstructionqualityresults_data': old_proconstructionqualityresults_data,
            't_username': t_username,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'budget_no': budget_no,
            'budget_name': budget_name,
            'construction_id': construction_id,
            'sub_id': sub_id,
            # 20201205y-kawauchi DB参照
            'quality_inspection_result': quality_inspection_result,
            'production_permit_date': production_permit_date,
            'memo': memo,
            'date_of_receipt_of_submitted_materials': date_of_receipt_of_submitted_materials,
            'submitted_doc_memo': submitted_doc_memo,
            'check_result': check_result,
            'acceptance_date': acceptance_date,
            'receipt': receipt,
            'receipt_sending_date': receipt_sending_date,
            # 20201215y-kawauchi Fileupload必要情報追加
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'construction_completion_date': construction_completion_date,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_proconstructionqualityresults/execution_proconstructionqualityresults_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_proconstructionqualityresults/execution_proconstructionqualityresults_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事品質結果テーブル登録･更新
@login_required
@require_POST
def execution_proconstructionqualityresults_entry(request):
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

        production_permit_date_date = request.POST['production_permit_date']
        if production_permit_date_date is not "":
            date_str = date_to_many_type(production_permit_date_date)
            production_permit_date_date = date_str.date_type_date
            # production_permit_date_date_str = production_permit_date_date.replace('年', '-')
            # production_permit_date_date_str = production_permit_date_date_str.replace('月', '-')
            # production_permit_date_date = production_permit_date_date_str.replace('日', '')
        date_of_receipt_of_submitted_materials_date = request.POST['date_of_receipt_of_submitted_materials']
        if date_of_receipt_of_submitted_materials_date is not "":
            date_str = date_to_many_type(date_of_receipt_of_submitted_materials_date)
            date_of_receipt_of_submitted_materials_date = date_str.date_type_date
            # date_of_receipt_of_submitted_materials_str = date_of_receipt_of_submitted_materials_date.replace('年', '-')
            # date_of_receipt_of_submitted_materials_str = date_of_receipt_of_submitted_materials_str.replace('月', '-')
            # date_of_receipt_of_submitted_materials_date = date_of_receipt_of_submitted_materials_str.replace('日', '')
        acceptance_date_date = request.POST['acceptance_date']
        if acceptance_date_date is not "":
            date_str = date_to_many_type(acceptance_date_date)
            acceptance_date_date = date_str.date_type_date
            # acceptance_date_date_str = acceptance_date_date.replace('年', '-')
            # acceptance_date_date_str = acceptance_date_date_str.replace('月', '-')
            # acceptance_date_date = acceptance_date_date_str.replace('日', '')
        receipt_sending_date_date = request.POST['receipt_sending_date']
        if receipt_sending_date_date is not "":
            date_str = date_to_many_type(receipt_sending_date_date)
            receipt_sending_date_date = date_str.date_type_date
            # receipt_sending_date_str = receipt_sending_date_date.replace('年', '-')
            # receipt_sending_date_str = receipt_sending_date_str.replace('月', '-')
            # receipt_sending_date_date = receipt_sending_date_str.replace('日', '')

        construction_completion_date = request.POST['construction_completion_date']
        if construction_completion_date is not "":
            date_str = date_to_many_type(construction_completion_date)
            construction_completion_date = date_str.date_type_date

        # 工事納入情報テーブルを予算ID, 工事IDの存在チェック
        proconstructionqualityresults_data_num = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 更新
        if proconstructionqualityresults_data_num > 0:
            # 工事納入情報テーブルを予算ID, 工事IDで読込
            proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)
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
            proconstructionqualityresults_data, created = ProConstructionQualityResults.objects.get_or_create(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0)
            # 登録の日時、登録者を登録
            proconstructionqualityresults_data.entry_datetime = now
            proconstructionqualityresults_data.entry_operator = operator
            # 工事納入情報テーブルを保存
            proconstructionqualityresults_data.save()
            # 登録日時、登録者で工事納入情報テーブルを抽出
            proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
            # 主キーを取得
            proconstructionqualityresults_unique_id = proconstructionqualityresults_data.id
            # 主キーで工事納入情報テーブルを抽出
            proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(id=proconstructionqualityresults_unique_id, lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            proconstructionqualityresults_data.rev_no = 0
            proconstructionqualityresults_data.entry_on_progress_flag = 1
            proconstructionqualityresults_data.lost_flag = 0
            # 工事納入情報テーブルを保存
            proconstructionqualityresults_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                proconstructionqualityresults_data = ProConstructionQualityResults.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = proconstructionqualityresults_data.rev_no
                # 該当のレコードを無効
                proconstructionqualityresults_data.lost_flag = 1
                # 予算のレコードを保存
                proconstructionqualityresults_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProConstructionQualityResults(budget_id=budget_id, construction_id=construction_id, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                proconstructionqualityresults_unique_id = proconstructionqualityresults_data.id
                # 主キーで予算レコードを抽出
                proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(id=proconstructionqualityresults_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                proconstructionqualityresults_data.rev_no = latest_rev_no + 1
                proconstructionqualityresults_data.entry_on_progress_flag = 1
                proconstructionqualityresults_data.lost_flag = 0
                # 予算のレコードを保存
                proconstructionqualityresults_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                proconstructionqualityresults_unique_id = proconstructionqualityresults_data.id

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
        proconstructionqualityresults_data = ProConstructionQualityResults.objects.get(id=proconstructionqualityresults_unique_id, lost_flag=0)

        # 各項目の値を設定
        proconstructionqualityresults_data.sub_id = sub_id if sub_id is not '' else None
        proconstructionqualityresults_data.quality_inspection_result = request.POST["quality_inspection_result"] if request.POST["quality_inspection_result"] is not '' else None
        proconstructionqualityresults_data.production_permit_date = production_permit_date_date if production_permit_date_date is not '' else None
        proconstructionqualityresults_data.memo = request.POST["memo"] if request.POST["memo"] is not '' else None
        proconstructionqualityresults_data.submitted_doc = request.POST["submitted_doc"] if request.POST["submitted_doc"] is not '' else None
        proconstructionqualityresults_data.date_of_receipt_of_submitted_materials = date_of_receipt_of_submitted_materials_date if date_of_receipt_of_submitted_materials_date is not '' else None
        proconstructionqualityresults_data.submitted_doc_memo = request.POST["submitted_doc_memo"] if request.POST["submitted_doc_memo"] is not '' else None
        proconstructionqualityresults_data.check_result = request.POST["check_result"] if request.POST["check_result"] is not '' else None
        proconstructionqualityresults_data.acceptance_date = acceptance_date_date if acceptance_date_date is not '' else None
        proconstructionqualityresults_data.receipt_sending_date = receipt_sending_date_date if receipt_sending_date_date is not '' else None
        proconstructionqualityresults_data.construction_completion_date = construction_completion_date if construction_completion_date is not '' else None

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            proconstructionqualityresults_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            proconstructionqualityresults_data.entry_on_progress_flag = 1

        # rev_no取得
        proconstructionqualityresults_rev_no = proconstructionqualityresults_data.rev_no

        # 工事納入情報テーブルのレコードを保存
        proconstructionqualityresults_data.save()

        # ログデータを新規登録
        #Log(target='proconstructionqualityresults', target_id=construction_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()
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
