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
from fms.models import DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work
from fms.models import ProBudgetUnit, ProSpecificationUnit, ProEstimates, ProVendorEvaluation
from fms.models import ProConstructionPrep, ProConstructionPrep, ProConstructionQualityResults
from .execution_views import execution_work_common_data
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception, get_department_person_option_list
from fms.views.notice_mail_views import step_notice


# 工事準備テーブル詳細画面
@login_required
@require_POST
def execution_proconstructionprep_data_info(request):
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
        user_department_cd = request.POST['user_department_cd']
        copy_check = int(request.POST['copy_check'])

        # ベース部分(ProSpecificationUnit)の読込(そのままrenderに引き渡すこと)
        base_data = execution_work_common_data(budget_id, construction_id)

        # 対象のデータがあるかチェック
        proconstructionprep_data_num = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # ある場合各項目値取得
        if proconstructionprep_data_num > 0:
            proconstructionprep_data = ProConstructionPrep.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)
            rev_no = proconstructionprep_data.rev_no if proconstructionprep_data.rev_no is not None else ''
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = proconstructionprep_data.sub_id if proconstructionprep_data.sub_id is not None else ''
            delivery_prep_period_from = proconstructionprep_data.delivery_prep_period_from if proconstructionprep_data.delivery_prep_period_from is not None else ''
            delivery_prep_period_to = proconstructionprep_data.delivery_prep_period_to if proconstructionprep_data.delivery_prep_period_to is not None else ''
            prep_contents = proconstructionprep_data.prep_contents if proconstructionprep_data.prep_contents is not None else ''
            prep_result = proconstructionprep_data.prep_result if proconstructionprep_data.prep_result is not None else ''
            implementation_department = proconstructionprep_data.implementation_department if proconstructionprep_data.implementation_department is not None else ''
            implementation_department_name = '' if proconstructionprep_data.implementation_department is None else DepartmentMaster.objects.get(department_cd=implementation_department).department_name
            execution_department_manager = proconstructionprep_data.execution_department_manager if proconstructionprep_data.execution_department_manager is not None else ''
            execution_department_manager_name = '' if proconstructionprep_data.execution_department_manager is None else User.objects.get(username=execution_department_manager).last_name + '　' + User.objects.get(username=execution_department_manager).first_name
            memo = proconstructionprep_data.memo if proconstructionprep_data.memo is not None else ''
            delivery_prep_completion_date = proconstructionprep_data.delivery_prep_completion_date if proconstructionprep_data.delivery_prep_completion_date is not None else ''
            required_procedure = proconstructionprep_data.required_procedure if proconstructionprep_data.required_procedure is not None else ''
        # ない場合空値
        else:
            proconstructionprep_data = ''
            rev_no = 0
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = base_data['sub_id']
            delivery_prep_period_from = ''
            delivery_prep_period_to = ''
            prep_contents = ''
            prep_result = ''
            implementation_department = user_department_cd
            implementation_department_name = ''
            execution_department_manager = t_username
            execution_department_manager_name = ''
            memo = ''
            delivery_prep_completion_date = ''
            required_procedure = ''

        # 実施部署
        departmentmaster = DepartmentMaster.objects.filter(lost_flag=0).order_by('display_order')
        departments_list = ''
        for departmentmaster in departmentmaster:
            if departmentmaster.department_cd == implementation_department:
                departments_list += '<option value="' + departmentmaster.department_cd + '" selected>' + departmentmaster.department_name + '</option>'
            else:
                departments_list += '<option value="' + departmentmaster.department_cd + '">' + departmentmaster.department_name + '</option>'

        # 実施部署責任者
        user_list = get_department_person_option_list(implementation_department, execution_department_manager)

        # 無効となった(=1つ前のrev_noの)対象のデータのレコード数を取得
        old_proconstructionprep_data_num = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).count()
        # 無効となった(=1つ前のrev_noの)対象のデータのレコードがある場合
        if old_proconstructionprep_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象のデータを取得
            old_proconstructionprep_data = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_proconstructionprep_data = ""

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「ProConstructionPrep」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='proconstructionprep').count()
        edit_flag = 0

        if work_edit_action_num > 0:
            edit_flag = 1

        if copy_check == 0:
            # タブ毎のボタン表示対応
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_constructionprep', lost_flag=0)
            this_page = stepdisplayitem_data.page
            action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
        else:
            this_page = 14
            action_button_id = ''

        data = {
            'work_common_data': base_data,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'budget_no': budget_no,
            'budget_name': budget_name,
            'construction_id': construction_id,
            'sub_id': sub_id,
            'proconstructionprep_data_num': proconstructionprep_data_num,
            'proconstructionprep_data': proconstructionprep_data,
            'old_proconstructionprep_data_num': old_proconstructionprep_data_num,
            'old_proconstructionprep_data': old_proconstructionprep_data,
            't_username': t_username,
            'delivery_prep_period_from': delivery_prep_period_from,
            'delivery_prep_period_to': delivery_prep_period_to,
            'prep_contents': prep_contents,
            'prep_result': prep_result,
            'implementation_department': implementation_department,
            'implementation_department_name': implementation_department_name,
            'execution_department_manager': execution_department_manager,
            'execution_department_manager_name': execution_department_manager_name,
            'memo': memo,
            'delivery_prep_completion_date': delivery_prep_completion_date,
            'required_procedure': required_procedure,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'departments_list': departments_list,
            'user_list': user_list,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_proconstructionprep/execution_proconstructionprep_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_proconstructionprep/execution_proconstructionprep_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事納入情報テーブル登録･更新
@login_required
@require_POST
def execution_proconstructionprep_entry(request):
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

        delivery_prep_period_from_date = request.POST['delivery_prep_period_from']
        delivery_prep_period_from_date_str = delivery_prep_period_from_date.replace('年', '-')
        delivery_prep_period_from_date_str = delivery_prep_period_from_date_str.replace('月', '-')
        delivery_prep_period_from_date = delivery_prep_period_from_date_str.replace('日', '')
        delivery_prep_period_to_date = request.POST['delivery_prep_period_to']
        delivery_prep_period_to_str = delivery_prep_period_to_date.replace('年', '-')
        delivery_prep_period_to_str = delivery_prep_period_to_str.replace('月', '-')
        delivery_prep_period_to_date = delivery_prep_period_to_str.replace('日', '')
        delivery_prep_completion_date_date = request.POST['delivery_prep_completion_date']
        delivery_prep_completion_date_str = delivery_prep_completion_date_date.replace('年', '-')
        delivery_prep_completion_date_str = delivery_prep_completion_date_str.replace('月', '-')
        delivery_prep_completion_date_date = delivery_prep_completion_date_str.replace('日', '')

        # 工事納入情報テーブルを予算ID, 工事IDの存在チェック
        proconstructionprep_data_num = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 更新
        if proconstructionprep_data_num > 0:
            # 工事納入情報テーブルを予算ID, 工事IDで読込
            proconstructionprep_data = ProConstructionPrep.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)
            new_record = False
        # 新規登録
        else:
            new_record = True

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

        # 予算id(変数)に渡された予算idをセット
        this_budget_id = budget_id

        # 新規登録時の処理
        if new_record == True:
            # 設定した予算ID, 工事IDで新規作成
            proconstructionprep_data, created = ProConstructionPrep.objects.get_or_create(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0)
            # 登録の日時、登録者を登録
            proconstructionprep_data.entry_datetime = now
            proconstructionprep_data.entry_operator = operator
            # 工事納入情報テーブルを保存
            proconstructionprep_data.save()
            # 登録日時、登録者で工事納入情報テーブルを抽出
            proconstructionprep_data = ProConstructionPrep.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
            # 主キーを取得
            proconstructionprep_unique_id = proconstructionprep_data.id
            # 主キーで工事納入情報テーブルを抽出
            proconstructionprep_data = ProConstructionPrep.objects.get(id=proconstructionprep_unique_id, lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            proconstructionprep_data.rev_no = 0
            proconstructionprep_data.entry_on_progress_flag = 1
            proconstructionprep_data.lost_flag = 0
            # 工事納入情報テーブルを保存
            proconstructionprep_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                proconstructionprep_data = ProConstructionPrep.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = proconstructionprep_data.rev_no
                # 該当のレコードを無効
                proconstructionprep_data.lost_flag = 1
                # 予算のレコードを保存
                proconstructionprep_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProConstructionPrep(budget_id=budget_id, construction_id=construction_id, entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                proconstructionprep_data = ProConstructionPrep.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
                # 主キーを取得
                proconstructionprep_unique_id = proconstructionprep_data.id
                # 主キーで予算レコードを抽出
                proconstructionprep_data = ProConstructionPrep.objects.get(id=proconstructionprep_unique_id, lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                proconstructionprep_data.rev_no = latest_rev_no + 1
                proconstructionprep_data.entry_on_progress_flag = 1
                proconstructionprep_data.lost_flag = 0
                # 予算のレコードを保存
                proconstructionprep_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                proconstructionprep_data = ProConstructionPrep.objects.get(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                proconstructionprep_unique_id = proconstructionprep_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"
        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 主キーで予算レコードを抽出
        proconstructionprep_data = ProConstructionPrep.objects.get(id=proconstructionprep_unique_id, lost_flag=0)

        # 各項目の値を設定
        proconstructionprep_data.sub_id = sub_id if sub_id is not '' else None
        proconstructionprep_data.delivery_prep_period_from = delivery_prep_period_from_date if delivery_prep_period_from_date is not '' else None
        proconstructionprep_data.delivery_prep_period_to = delivery_prep_period_to_date if delivery_prep_period_to_date is not '' else None
        proconstructionprep_data.delivery_prep_completion_date = delivery_prep_completion_date_date if delivery_prep_completion_date_date is not '' else None
        proconstructionprep_data.prep_contents = request.POST["prep_contents"] if request.POST["prep_contents"] is not '' else None
        proconstructionprep_data.prep_result = request.POST["prep_result"] if request.POST["prep_result"] is not '' else None
        proconstructionprep_data.implementation_department = request.POST["implementation_department"] if request.POST["implementation_department"] is not '' else None
        proconstructionprep_data.execution_department_manager = request.POST["execution_department_manager"] if request.POST["execution_department_manager"] is not '' else None
        proconstructionprep_data.memo = request.POST["memo"] if request.POST["memo"] is not '' else None
        proconstructionprep_data.required_procedure = request.POST["required_procedure"] if request.POST["required_procedure"] is not '' else None

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            proconstructionprep_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            proconstructionprep_data.entry_on_progress_flag = 1

        # rev_no取得
        proconstructionprep_rev_no = proconstructionprep_data.rev_no

        # 工事納入情報テーブルのレコードを保存
        proconstructionprep_data.save()

        # ログデータを新規登録
        #Log(target='proconstructionprep', target_id=construction_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()
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
