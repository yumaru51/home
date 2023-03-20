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
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import FreeSpecDetail, SubmissionDocument, Estimate, Supplies, WorkLaw
from fms.models import WorkSpecMEX, PlanningChargePerson
from fms.models import FreeSpecDetailTemplate
from django.db import connections

from fms.views.common_def_views import TemplateType
from django.utils.timezone import make_aware
from fms.views.estimate_views import price_value_update
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 工事データ一覧取得
def get_estimate_work_list(target_budget_id):
    msg = ""
    try:
        # 工事レコード抽出
        with connections['fmsdb'].cursor() as cursor:
            sql = """ SELECT fms_estimate.id, fms_estimate.work_id, fms_estimate.vendor, fms_estimate.entry_class, """
            sql += """CASE WHEN fms_estimate.estimate_price IS NULL THEN 0 ELSE fms_estimate.estimate_price END estimate_price, """
            sql += """CASE WHEN fms_estimate.prospect_price IS NULL THEN 0 ELSE fms_estimate.prospect_price END prospect_price, """
            sql += """CASE WHEN fms_estimate.discount_num IS NULL THEN 0 ELSE fms_estimate.discount_num END discount_num, """
            sql += """CASE WHEN fms_estimate.price_after_discount IS NULL THEN 0 ELSE fms_estimate.price_after_discount END price_after_discount, """
            sql += """fms_work.work_budget_id, fms_work.id  as work_unique_id, fms_work.work_id, fms_work.work_name, fms_budget.id  as budget_unique_id, fms_budget.budget_id, """
            sql += """CASE WHEN fms_budget.budget_price IS NULL THEN 0 ELSE fms_budget.budget_price END budget_price """
            sql += """, fms_stepmaster.step_name, fms_stepmaster.step_id, fms_budget.budget_id """
            sql += """FROM fms_budget """
            sql += """LEFT JOIN fms_work on fms_budget.budget_id = fms_work.work_budget_id and (fms_work.cancel_flag=0 or fms_work.cancel_flag is null) """
            sql += """LEFT JOIN fms_estimate on fms_work.work_id = fms_estimate.work_id """
            sql += """LEFT JOIN fms_progress on fms_work.work_id = fms_progress.target_id  and fms_progress.target='work' """
            sql += """LEFT JOIN fms_stepmaster on fms_stepmaster.step_id = fms_progress.present_step """
            sql += """where fms_budget.lost_flag = 0 """
            sql += """AND fms_work.lost_flag = 0 """
            sql += """AND fms_estimate.lost_flag = 0 """
            sql += """AND adoption_flag = 1"""
            sql += """AND work_budget_id = """ + str(target_budget_id)

            res = cursor.execute(sql)

            work_price_lists = res.fetchall()
            work_price_lists_num = len(work_price_lists)

        with connections['fmsdb'].cursor() as cursor:
            sql = """SELECT SUM(prospect_price) as sum_value """
            sql += """FROM (fms_estimate LEFT JOIN fms_work on fms_estimate.work_id = fms_work.work_id and (fms_work.cancel_flag=0 or fms_work.cancel_flag is null)) """
            sql += """where fms_estimate.lost_flag=0 """
            sql += """AND fms_work.lost_flag = 0 """
            sql += """AND adoption_flag = 1 """
            sql += """AND work_budget_id = """ + str(target_budget_id)

            res = cursor.execute(sql)
            result_sum = res.fetchall()

            if result_sum[0][0]:
                total_prospect_price_value = result_sum[0][0]
            else:
                total_prospect_price_value = 0

        # 全工事レコード抽出
        with connections['fmsdb'].cursor() as cursor:
            sql = """ SELECT fms_work.work_id,  """
            sql += """CASE WHEN estimate_data.estimate_price IS NULL THEN '採用未設定' ELSE CONVERT(varchar, FORMAT(estimate_data.estimate_price, '#,###')) END estimate_price, """
            sql += """CASE WHEN estimate_data.prospect_price IS NULL THEN '採用未設定' ELSE CONVERT(varchar, FORMAT(estimate_data.prospect_price, '#,###')) END prospect_price, """
            sql += """CASE WHEN estimate_data.discount_num IS NULL THEN '採用未設定' ELSE CONVERT(varchar, FORMAT(estimate_data.discount_num, '#,###')) END discount_num, """
            sql += """CASE WHEN estimate_data.price_after_discount IS NULL THEN '採用未設定' ELSE CONVERT(varchar, FORMAT(estimate_data.price_after_discount, '#,###')) END price_after_discount, """
            sql += """fms_work.work_budget_id, fms_work.id  as work_unique_id, fms_work.work_id, fms_work.work_name, fms_budget.id  as budget_unique_id, fms_budget.budget_id, """
            sql += """0 as  budget_price """
            sql += """, fms_stepmaster.step_name, fms_stepmaster.step_id, fms_budget.budget_id """
            sql += """, fms_progress.present_operator """
            sql += """FROM fms_budget """
            sql += """LEFT JOIN fms_work on fms_budget.budget_id = fms_work.work_budget_id and (fms_work.cancel_flag=0 or fms_work.cancel_flag is null) """
            sql += """LEFT JOIN fms_progress on fms_work.work_id = fms_progress.target_id  and fms_progress.target='work' """
            sql += """LEFT JOIN fms_stepmaster on fms_stepmaster.step_id = fms_progress.present_step """

            sql += """LEFT JOIN ( """
            sql += """SELECT  fms_estimate.prospect_price,fms_estimate.estimate_price,fms_estimate.price_after_discount,fms_estimate.work_id,fms_estimate.discount_num  """
            sql += """FROM fms_estimate """
            sql += """WHERE fms_estimate.lost_flag = 0 AND  adoption_flag = 1 """
            sql += """) as estimate_data """
            sql += """ON estimate_data.work_id = fms_work.work_id """
            sql += """WHERE fms_budget.lost_flag = 0 """
            sql += """AND fms_work.lost_flag = 0 """
            sql += """AND work_budget_id = """ + str(target_budget_id)

            res = cursor.execute(sql)

            all_work_lists = res.fetchall()
            all_work_lists_num = len(all_work_lists)

    except Exception:
        msg = "ERROR!!"
        work_price_lists = ""
        work_price_lists_num = 0
        total_prospect_price_value = 0

    ans = {
        'msg': msg,
        'work_price_lists': work_price_lists,
        'work_price_lists_num': work_price_lists_num,
        'total_prospect_price_value': total_prospect_price_value,
        'all_work_lists': all_work_lists,
        'all_work_lists_num': all_work_lists_num,
    }

    return ans


# 工事データ一覧表示
@login_required
@require_POST
def estimate_work_lists_display(request):
    try:
        # ログインユーザー情報取得
        t_username = request.user.username

        # JSから継承した変数を取得
        my_division_cd = request.POST['user_division_cd']
        my_department_cd = request.POST['user_department_cd']
        target_estimate_id = int(request.POST['target_estimate_id'])
        target_budget_id = int(request.POST['target_budget_id'])
        new_price = int(request.POST['new_price'])
        this_step = int(request.POST['this_step'])
        target = request.POST['target']

        DIFF_JST_FROM_UTC = 9
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        msg = ""

        # 通常申請と追加予算申請の処理を共通化するために、ステップ番号をリスト化
        if 133000000 < this_step < 134000000:
            step_list = {'詳細仕様検討': 133002011,
                         '予算見積': 133004000,
                         '予算見積作成': 133004001,
                         '予算見積承認': 133004011,
                         '差戻表示上限': 133004002,
                         '個別予算見積作成': 133003001,
                         '仕様書予算見積完了': 133009904,
                         }
        elif 136000000 < this_step < 137000000:
            step_list = {'詳細仕様検討': 136002011,
                         '予算見積': 136004000,
                         '予算見積作成': 136004001,
                         '予算見積承認': 136004011,
                         '差戻表示上限': 136004002,
                         '個別予算見積作成': 136003001,
                         '仕様書予算見積完了': 133009904,
                         }
        elif 132000000 < this_step < 133000000:
            step_list = {'詳細仕様検討': 132002011,
                         '予算見積': 132004000,
                         '予算見積作成': 132004001,
                         '予算見積承認': 132004011,
                         '差戻表示上限': 132004001,
                         '個別予算見積作成': 132003001,
                         '仕様書予算見積完了': 132009911,
                         }
        else:
            # 工事実行側ステップで表示した場合は単年度計画と同じ処理
            step_list = {'詳細仕様検討': 133002011,
                         '予算見積': 133004000,
                         '予算見積作成': 133004001,
                         '予算見積承認': 133004011,
                         '差戻表示上限': 133004002,
                         '個別予算見積作成': 133003001,
                         '仕様書予算見積完了': 133009904,
                         }

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        if target_estimate_id != 0:
            estimate_data = Estimate.objects.get(work_id=target_estimate_id, lost_flag=0, adoption_flag=1)
            estimate_data.prospect_price = new_price
            estimate_data.update_datetime = now
            estimate_data.update_operator = operator

            estimate_data.save()

            price_value_update(target_budget_id, now, operator)

        try:
            ans = get_estimate_work_list(target_budget_id)

            msg = ans.get('msg')

            # 仕様書予算見積完了していない工事のみのリストを表示する場合の処理（復活させる可能性を考慮してコメントアウト)
            # if this_step > step_list['予算見積']:
            #     work_price_lists = ans.get('work_price_lists')
            #     work_price_lists_num = ans.get('work_price_lists_num')
            # else:
            work_price_lists = ans.get('all_work_lists')
            work_price_lists_num = ans.get('all_work_lists_num')
            total_prospect_price_value = ans.get('total_prospect_price_value')

            # データ編集機能要否判定
            edit_flag = 0
            action_button_display_flag = 1
            if DataEntryStepMaster.objects.filter(step_id=this_step, target_table='estimate').count() > 0:
                edit_flag = 1

            # 工事差戻PB表示ステップ上限判定
            if this_step <= step_list['差戻表示上限']:
                return_pb_disp_flag = 1
            else:
                return_pb_disp_flag = 0

            # 新規工事作成完了PB表示flag処理
            work_entry_complete_flag = 0
            if this_step == step_list['詳細仕様検討']:
                # 現在のステップのprogressと、部門、部署が一致している場合は新規工事作成完了PB許可
                present_step_data = Progress.objects.get(target='budget', target_id=target_budget_id)
                if my_division_cd == present_step_data.present_division and my_department_cd == present_step_data.present_department:
                    work_entry_complete_flag = 1

            # 新規仕様書作成可能中flag処理(注意:work_entry_possible_flag=0の場合、見積調整可能)
            if this_step < step_list['予算見積作成'] or 200000000 < this_step:
                work_entry_possible_flag = 1
            else:
                work_entry_possible_flag = 0

            if 211001000 < this_step < 211002021:
                probudget_step_flag = 1
            else:
                probudget_step_flag = 0

        except Exception:
            raise

        sql = """ SELECT fms_work.id, fms_work.work_budget_id, fms_work.work_id, fms_progress.present_step """
        sql = sql + """ FROM fms_work """
        sql = sql + """ LEFT JOIN fms_progress ON fms_work.work_id = fms_progress.target_id AND fms_progress.target = 'work' """
        sql = sql + """ WHERE fms_work.lost_flag = 0 AND fms_work.work_budget_id =""" + str(target_budget_id)
        sql = sql + """ AND ( fms_work.cancel_flag IS NULL OR fms_work.cancel_flag != 1)"""
        sql = sql + f" AND fms_progress.present_step = { str(step_list['仕様書予算見積完了']) } "

        complete_work = Work.objects.raw(sql)
        complete_work_num = len(list(complete_work))

        sql = """ SELECT fms_work.id, fms_work.work_budget_id, fms_work.work_id, fms_progress.present_step """
        sql = sql + """ FROM fms_work """
        sql = sql + """ LEFT JOIN fms_progress ON fms_work.work_id = fms_progress.target_id AND fms_progress.target = 'work' """
        sql = sql + """ WHERE fms_work.lost_flag = 0 AND fms_work.work_budget_id =""" + str(target_budget_id)
        sql = sql + """ AND ( fms_work.cancel_flag IS NULL OR fms_work.cancel_flag != 1) """

        total_work = Work.objects.raw(sql)
        total_work_num = len(list(total_work))

        incomplete_work_num = total_work_num - complete_work_num
        if incomplete_work_num > 0:
            complete_flag = 0
        else:
            complete_flag = 1

        data = {
            'msg': msg,
            'work_price_lists': work_price_lists,
            'work_price_lists_num': work_price_lists_num,
            'total_prospect_price_value': total_prospect_price_value,
            'edit_flag': edit_flag,
            'action_button_display_flag': action_button_display_flag,
            'return_pb_disp_flag': return_pb_disp_flag,
            'work_entry_complete_flag': work_entry_complete_flag,
            'target_budget_id': target_budget_id,
            'work_entry_possible_flag': work_entry_possible_flag,
            'complete_flag': complete_flag,
            'complete_work_num': complete_work_num,
            'total_work_num': total_work_num,
            'probudget_step_flag': probudget_step_flag,
            'div_id_name': request.POST['div_id_name'],
            'return_pb_disable_id': step_list['詳細仕様検討'],
        }

        # データ編集機能要否判定
        estimate_list_edit_action_num = 0
        edit_flag = 0
        estimate_list_edit_action_num = estimate_list_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step,
                                                                                             target_table='estimate_list',
                                                                                             lost_flag=0
                                                                                             ).count()
        if estimate_list_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/work/estimate/budget_work_lists_edit.html', data)
        else:
            return render(request, 'fms/parts/work/estimate/budget_work_lists_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


@require_POST
def budget_estimate_entry(request):
    from fms.views.budget_views import set_budget_status
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSから継承した変数を取得
        next_division = request.POST['next_division']
        next_department = request.POST['next_department']
        next_person = request.POST['next_person']
        user_attribute_id = int(request.POST['user_attribute_id'])
        next_step = int(request.POST['next_step'])
        this_department = request.POST['this_department']
        this_division = request.POST['this_division']
        target_budget_id = int(request.POST['target_budget_id'])
        this_step = int(request.POST['this_step'])
        comment = request.POST['comment']

        budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="budget", target_id=budget_data.budget_id)
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

        # 次ステップに移行する場合は作成中フラグを落とす
        if next_step != this_step:
            Budget.entry_on_progress_flag = 0
            action = "entry"
            msg = "予算見積作成完了！！"
        else:
            action = "temporarily_saved"
            msg = "一時保存完了！！"

        # 進捗通知機能
        if next_step != this_step:
            step_notice(progress_data)

        # ログデータを新規登録
        Log(target='budget', target_id=budget_data.budget_id, action=action, operator=operator,
            operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=target_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def estimate_send_back(target_budget_id, this_step, operator, return_person_data, comment):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        msg = ""

        # 取得した「最終処理step」、「最終処理者」、「最終処理部署」、「最終処理部門」を格納
        last_operation_step = return_person_data['last_operation_step']
        last_operator = return_person_data['last_operator']
        last_operator_department = return_person_data['last_operator_department']
        last_operator_division = return_person_data['last_operator_division']

        budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
        user_data = UserAttribute.objects.filter(username=operator, lost_flag=0).all().order_by('display_order')[0]

        # 見積対象の工事データを抽出
        ans = get_estimate_work_list(target_budget_id)

        msg = ans.get('msg')
        work_price_lists = ans.get('work_price_lists')
        work_price_lists_num = ans.get('work_price_lists_num')
        total_prospect_price_value = ans.get('total_prospect_price_value')

        for target_data in work_price_lists:
            # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
            progress_data, created = Progress.objects.get_or_create(target="work", target_id=target_data.work_id)
            # 各項目を設定
            progress_data.present_step = last_operation_step
            progress_data.present_operator = last_operator
            progress_data.present_department = last_operator_department
            progress_data.present_division = last_operator_division
            progress_data.last_operation_step = this_step
            progress_data.last_operator = operator
            progress_data.last_operation_datetime = now

            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            step_notice(progress_data)

        # ログデータを新規登録
        Log(target='budget', target_id=budget_data.budget_id, action='return', operator=operator,
            operation_datetime=now, step=this_step, comment=comment,
            operator_department=user_data.department, operator_division=user_data.division,
            budget_id=target_budget_id).save()
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 新規仕様書作成完了処理
def budget_new_work_entry_complete(request):
    from fms.views.budget_views import set_budget_status
    try:
        # 現在時刻を取得
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # JSから継承した変数を取得
        budget_id = int(request.POST['budget_id'])

        # 予算の申請区分に応じて処理分岐
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)

        # 有効なWORKがあるか判定
        work_list = Work.objects.filter(work_budget_id=budget_id, lost_flag=0).exclude(cancel_flag=1)
        if work_list.count() < 1:
            msg = '工事データがありません！！'
            result_ok_flag = 0
            ary = {
                'msg': msg,
                'result_ok_flag': result_ok_flag
            }
            return JsonResponse(ary)

        if budget_data.plan_class_id == 'M':
            # 中期計画側処理
            operator = request.user.username
            step_list = {'詳細仕様検討': 132002011,
                         '予算見積作成': 132004001}
        elif budget_data.application_class.application_class_cd == 1:
            # 通常側は予算見積作成ステップの次担当者は操作したユーザー
            operator = request.user.username
            # 通常申請と追加予算申請の処理を共通化するために、ステップ番号をリスト化
            step_list = {'詳細仕様検討': 133002011,
                         '予算見積作成': 133004001}
        else:
            # 追加予算側は予算見積作成ステップの次担当者は予算担当者
            operator = budget_data.budget_person.username
            step_list = {'詳細仕様検討': 136002011,
                         '予算見積作成': 136004001}

        user_attribute_data = UserAttribute.objects.filter(username=operator, lost_flag=0).order_by('display_order')[0]
        division = user_attribute_data.division
        department = user_attribute_data.department

        progress_data_num = Progress.objects.filter(
            target='budget', target_id=budget_id, present_step=step_list['詳細仕様検討']).count()

        if progress_data_num == 0:
            msg = '対象の予算データがありません！！'
            result_ok_flag = 0
        else:
            progress_data = Progress.objects.get(
                target='budget', target_id=budget_id, present_step=step_list['詳細仕様検討'])
            last_operation_step = progress_data.present_step

            progress_data.present_step = step_list['予算見積作成']
            progress_data.present_operator = operator
            progress_data.present_division = division
            progress_data.present_department = department
            progress_data.last_operation_datetime = now
            progress_data.last_operation_step = last_operation_step
            progress_data.last_operator = request.user.username

            progress_data.save()
            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

            msg = '予算を予算見積に進めました！！'
            result_ok_flag = 1

            # 進捗通知機能
            step_notice(progress_data)

        ary = {
            'msg': msg,
            'result_ok_flag': result_ok_flag
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 見積作成画面での差戻処理
@login_required
@require_POST
def work_return(request):
    try:
        # 現在時刻を取得
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSから継承した変数を取得
        work_id = int(request.POST['work_id'])
        budget_id = int(request.POST['budget_id'])
        this_step = int(request.POST['this_step'])

        budget_progress_data = Progress.objects.get(target='budget', target_id=budget_id)
        budget_this_step = budget_progress_data.present_step

        # 通常申請と追加予算申請の処理を共通化するために、ステップ番号をリスト化
        if 133000000 < budget_this_step < 134000000:
            step_list = {'詳細仕様検討': 133002011,
                         '予算見積作成': 133004001}
        elif 136000000 < budget_this_step < 137000000:
            step_list = {'詳細仕様検討': 136002011,
                         '予算見積作成': 136004001}
        elif 132000000 < budget_this_step < 133000000:
            step_list = {'詳細仕様検討': 132002011,
                         '予算見積作成': 132004001}

        log_data = Log.objects.filter(target='work', target_id=work_id, step=step_list['詳細仕様検討'],
                                      action='entry').order_by('-operation_datetime')[0]
        to_operator = log_data.operator
        operator_department = log_data.operator_department
        operator_division = log_data.operator_division

        work_progress_data = Progress.objects.get(target='work', target_id=work_id)
        last_step = work_progress_data.present_step
        last_operator = work_progress_data.present_operator

        work_progress_data.present_step = step_list['詳細仕様検討']
        work_progress_data.present_operator = to_operator
        work_progress_data.present_division = operator_division
        work_progress_data.present_department = operator_department
        work_progress_data.last_operation_datetime = now
        work_progress_data.last_operation_step = last_step
        work_progress_data.last_operator = last_operator

        work_progress_data.save()

        # 進捗通知機能
        step_notice(work_progress_data)

        comment = '工事一覧から差戻'
        # ログを新規登録
        Log(target='work', target_id=work_id, action='return', operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=operator_department,
            operator_division=operator_division, budget_id=budget_id).save()

        msg = "差戻完了！！"
        result_ok_flag = 1
        data = {
            'msg': msg,
            'result_ok_flag': result_ok_flag
        }
        return JsonResponse(data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

