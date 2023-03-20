import os
import shutil
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
from fms.models import BudgetRisks, AttachmentDocuments
from fms.models import ProBudgetUnit, ProSpecificationUnit
from django.db import connections

from fms.views.common_def_views import TemplateType
from .cs_views import cs_progress_record_add_budget
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.common_def_views import get_attachment_file_base_path, get_attachment_folder_name, get_template_file_path
from fms.views.notice_mail_views import step_notice


# リスク評価対象の予算リストを取得
def get_risks_list(business_year, this_step):

    try:
        # # 予算見積合計額の算出
        # if budget_list_data_num > 0:
        #     total_budget_price_value = 0
        #     for list_item in budget_list_data:
        #         total_budget_price_value += list_item.budget_price
        # else:
        #     total_budget_price_value = 0

        # 予算リストを取得（単年度計画案作成1 ～ 単年度計画step終了まで）
        with connections['fmsdb'].cursor() as cursor:
            sql = """ SELECT fms_budget.*, fms_departmentmaster.department_name """
            sql += """ FROM fms_budget """
            sql += """ LEFT OUTER JOIN (SELECT fms_progress.* FROM fms_progress WHERE target='budget') AS 
                                                                                                    filteredtable """
            sql += """ ON fms_budget.budget_id = filteredtable.target_id """
            sql += """LEFT OUTER JOIN fms_departmentmaster ON fms_budget.budget_main_department_id = 
                                                                                fms_departmentmaster.department_cd"""
            sql += """ WHERE fms_budget.lost_flag = 0 """
            sql += """ AND fms_budget.cancel_flag != 1 """
            sql += """ AND filteredtable.present_step >= 133005001 """
            sql += """ AND filteredtable.present_step < 134000000 """
            sql += """ AND filteredtable.present_step =  """ + str(this_step)
            sql += """ AND fms_budget.business_year_id = """ + str(business_year)

            res = cursor.execute(sql)

            budget_list_data = res.fetchall()
            budget_list_data_num = len(budget_list_data)

            target_price = sql

            # カラム名を取得し、辞書化
            fetch_array = []
            for data_cnt in range(len(budget_list_data)):
                columns = [column[0] for column in res.description]
                tmp = {}
                for col_cnt in range(len(columns)):
                    tmp[columns[col_cnt]] = budget_list_data[data_cnt][col_cnt]
                fetch_array.append(tmp)

        with connections['fmsdb'].cursor() as cursor:
            sql = """SELECT SUM(budget_price) as sum_value FROM ( """ + target_price + """ ) as target_table """

            res = cursor.execute(sql)
            result_sum = res.fetchall()

            if result_sum[0][0]:
                total_budget_price_value = result_sum[0][0]
            else:
                total_budget_price_value = 0

        msg = ""

    except Exception:
        msg = "ERROR!!"
        budget_list_data = ""
        budget_list_data_num = 0
        total_budget_price_value = 0

    ans = [budget_list_data, budget_list_data_num, total_budget_price_value, fetch_array, msg]

    return ans

# リスク入力画面
@require_POST
def risks_info(request):
    try:
        # JSから継承した変数を取得
        budget_id = int(request.POST['target_budget_id'])
        this_step = int(request.POST['this_step'])

        try:
            # 画面表示に必要なデータの収集
            # 同年度の予算リストを取得
            budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
            # budget_list_data = Budget.objects.filter(business_year=budget_data.business_year, lost_flag=0)
            # budget_list_data_num = len(budget_list_data)
            #
            # # 予算見積合計額の算出
            # if budget_list_data_num > 0:
            #     total_budget_price_value = 0
            #     for list_item in budget_list_data:
            #         total_budget_price_value += list_item.budget_price
            # else:
            #     total_budget_price_value = 0

            # # 予算リストを取得（単年度計画案作成1 ～ 単年度計画step終了まで）
            # with connections['fmsdb'].cursor() as cursor:
            #     sql = """ SELECT fms_budget.*, fms_departmentmaster.department_name """
            #     sql += """ FROM fms_budget """
            #     sql += """ LEFT OUTER JOIN (SELECT fms_progress.* FROM fms_progress WHERE target='budget') AS
            #                                                                                             filteredtable """
            #     sql += """ ON fms_budget.budget_id = filteredtable.target_id """
            #     sql += """LEFT OUTER JOIN fms_departmentmaster ON fms_budget.budget_main_department_id =
            #                                                                         fms_departmentmaster.department_cd"""
            #     sql += """ WHERE fms_budget.lost_flag = 0 """
            #     sql += """ AND filteredtable.present_step >= 133005001 """
            #     sql += """ AND filteredtable.present_step < 134000000 """
            #     sql += """ AND fms_budget.business_year_id = """ + str(budget_data.business_year)
            #
            #     res = cursor.execute(sql)
            #
            #     budget_list_data = res.fetchall()
            #     budget_list_data_num = len(budget_list_data)
            #
            #     target_price = sql
            #
            # with connections['fmsdb'].cursor() as cursor:
            #     sql = """SELECT SUM(budget_price) as sum_value FROM ( """ + target_price + """ ) as target_table """
            #
            #     res = cursor.execute(sql)
            #     result_sum = res.fetchall()
            #
            #     if result_sum[0][0]:
            #         total_budget_price_value = result_sum[0][0]
            #     else:
            #         total_budget_price_value = 0

            # リスク評価対象の予算リストを取得
            ans = get_risks_list(budget_data.business_year, this_step)

            budget_list_data = ans[0]
            budget_list_data_num = ans[1]
            total_budget_price_value = ans[2]
            fetch_array = ans[3]
            msg = ans[4]

            carry_over_flag_list = []
            # 各予算のcarry_over_flagを抽出
            for loop in range(len(budget_list_data)):
                carry_over_flag_list.append(fetch_array[loop]["carry_over_flag"])

            # リスク評価結果データの有無を確認
            if BudgetRisks.objects.filter(business_year=budget_data.business_year.business_year, lost_flag=0).exists():
                budget_risks_data = BudgetRisks.objects.get(business_year=budget_data.business_year.business_year, lost_flag=0)

                risks = budget_risks_data.risks
                note = budget_risks_data.note

            else:
                risks = ""
                note = ""

            if budget_list_data_num > 0:
                for budget_list_item in budget_list_data:
                    if budget_list_item.budget_price is not None:
                        # 3桁区切りの「,」挿入処理
                        budget_list_item.budget_price = "{:,}".format(int(budget_list_item.budget_price))

                total_budget_price_value = "{:,}".format(int(total_budget_price_value))

            # データ編集機能要否判定
            budget_edit_action_num = 0

            budget_edit_action_num = budget_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step,
                                                                                                 target_table='budgetrisks'
                                                                                                 ).count()

            edit_flag = 0

            if budget_edit_action_num > 0:
                edit_flag = 1

        except Exception:
            msg = "ERROR!!"
            note = ""
            risks = ""
            budget_list_data = ""
            budget_list_data_num = 0
            total_budget_price_value = 0
            carry_over_flag_list =[]
            edit_flag = 0

        data = {
            'budget_list_data': budget_list_data,
            'budget_list_data_num': budget_list_data_num,
            'total_budget_price_value': total_budget_price_value,
            'carry_over_flag_list': carry_over_flag_list,
            'risks': risks,
            'note': note,
            'edit_flag': edit_flag,
            'msg': msg,
        }

        return render(request, 'fms/parts/budget/risks/risks_edit.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

@require_POST
def risks_entry(request):
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

        risks_data = request.POST['risks_data']
        note_data = request.POST['note_data']
        # check_state = request.POST['check_state']
        adopted_budget_id = request.POST.getlist('adopted_budget_id[]')
        carry_over_budget_id = request.POST.getlist('carry_over_budget_id[]')

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
        budget_risks_data, created = BudgetRisks.objects.get_or_create(business_year=budget_data.business_year.business_year
                                                                       , lost_flag=0)

        # 新規作成時には全データを埋める
        if created == 1:
            budget_risks_data.business_year = budget_data.business_year.business_year
            budget_risks_data.entry_datetime = now
            budget_risks_data.entry_operator = operator
            budget_risks_data.entry_on_progress_flag = 1
            budget_risks_data.lost_flag = 0

        # 記入内容を保存
        budget_risks_data.risks = risks_data
        budget_risks_data.note = note_data
        budget_risks_data.update_datetime = now
        budget_risks_data.update_operator = operator

        # 次ステップに移行する場合は作成中フラグを落とす
        if next_step != this_step:
            budget_risks_data.entry_on_progress_flag = 0
            action = "entry"
            msg = "リスク検討結果登録完了！！"
        else:
            action = "temporarily_saved"
            msg = "一時保存完了！！"

        # DBに書き込み
        budget_risks_data.save()

        # リスク評価対象の予算リストを取得
        ans = get_risks_list(budget_data.business_year, this_step)

        budget_list_data = ans[0]
        budget_list_data_num = ans[1]
        total_budget_price_value = ans[2]
        fetch_array = ans[3]
        # msg = ans[4]

        # 次ステップが修正ステップの場合、詳細画面を開いた予算だけステップ移動させる
        if next_step == 133005002 or next_step == 133005022 or next_step == 133006002 or next_step == 133006032:
            # ログデータを新規登録
            Log(target='budget', target_id=target_budget_id, action=action, operator=operator, operation_datetime=now,
                step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
                budget_id=target_budget_id).save()

            # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
            progress_data = Progress.objects.get(target="budget", target_id=target_budget_id)
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

        else:
            # 抽出された予算のリストを次ステップへ
            for list_data in budget_list_data:
                # ログデータを新規登録
                Log(target='budget', target_id=list_data.budget_id, action=action, operator=operator, operation_datetime=now,
                    step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
                    budget_id=list_data.budget_id).save()

                # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
                progress_data, created = Progress.objects.get_or_create(target="budget", target_id=list_data.budget_id)
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

                # 年度見送り予算判定
                budget_data = Budget.objects.get(id=list_data.id, lost_flag=0)

                if str(list_data.id) in carry_over_budget_id:
                    budget_data.carry_over_flag = 1
                elif str(list_data.id) in adopted_budget_id:
                    budget_data.carry_over_flag = 0
                else:
                    connections

                budget_data.update_datetime = now
                budget_data.update_operator = operator

                budget_data.save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 次の進捗工程(step)に進む処理
def risks_go_next_step(data):
    from fms.views.budget_views import set_budget_status

    # 引数からデータ取り出し
    target = data['target']
    target_id = data['target_id']
    target_budget_id = data['target_budget_id']
    action = data['action']
    operator = data['operator']
    now = data['now']
    this_step = data['this_step']
    this_department = data['this_department']
    this_division = data['this_division']
    comment = data['comment']
    next_step = data['next_step']
    next_person = data['next_person']
    next_department = data['next_department']

    budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)

    # リスク評価対象の予算リストを取得
    ans = get_risks_list(budget_data.business_year, this_step)

    budget_list_data = ans[0]
    budget_list_data_num = ans[1]
    total_budget_price_value = ans[2]
    fetch_array = ans[3]
    msg = ans[4]

    # 追加処理が発生する特定のstepを読み込み
    budget_planing_end_progress_data = StepMaster.objects.get(step_name="単年度計画案承認2", lost_flag=0)
    end_budget_progress_data = StepMaster.objects.get(step_name="単年度予算No付与", lost_flag=0)

    # 抽出された予算のリストを次ステップへ
    for list_data in budget_list_data:

        # ログデータを新規登録
        Log(target='budget', target_id=list_data.budget_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=list_data.budget_id).save()

        # 進捗状況を対象(budget)と予算idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="budget", target_id=list_data.budget_id)

        # stepが"単年度計画案承認2"の場合
        if this_step == budget_planing_end_progress_data.step_id:

            # 見送りフラグがONの場合、次年度に見送り
            if list_data.carry_over_flag == 1:
                new_budget_data = Budget.objects.get(budget_id=list_data.budget_id, lost_flag=0)
                new_budget_data.business_year_id += 1
                new_budget_data.entry_datetime = now
                new_budget_data.entry_operator = operator

                new_budget_data.save()

                # 進捗を「単年度計画案作成1」に戻す
                back_progress_data = StepMaster.objects.get(step_name="単年度計画案作成1", lost_flag=0)
                back_log = Log.objects.filter(target='budget', target_id=list_data.budget_id,
                                                   step=back_progress_data.step_id).all().order_by('-id')[0]

                progress_data.present_step = back_progress_data.step_id
                progress_data.present_operator = back_log.operator
                progress_data.present_department = back_log.operator_department
                progress_data.present_division = back_log.operator_division
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

                progress_data.save()
                # 予算の状態変更(関数内で判定)
                set_budget_status(progress_data)

                # 進捗通知機能
                if this_step != next_step:
                    step_notice(progress_data)

                continue

            # 見送りフラグがOFFの場合...は通常の「まとめてstep移行」と同様
            # 追加で届出CSのSTEP開始と工事実行へのデータ移行を実施
            else:
                # 届出チェック進捗レコード作成
                cs_progress_record_add_budget(list_data.budget_id, operator, this_step)

                # 工事実行へのデータ移行
                send_data_budget(list_data.budget_id)
                send_data_work(list_data.budget_id, list_data.application_class_id)


        # stepが"単年度予算No付与"の場合
        elif this_step == end_budget_progress_data.step_id:

            # 単年度予算工程完了に移行
            progress_data.present_step = next_step
            progress_data.present_operator = ""
            progress_data.present_department = ""
            progress_data.present_division = ""
            progress_data.last_operation_step = this_step
            progress_data.last_operator = operator
            progress_data.last_operation_datetime = now
            progress_data.save()
            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

            continue

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

        # 進捗通知機能
        if this_step != next_step:
            step_notice(progress_data)


# 工事実行側 調達予算へのデータ移行処理
def send_data_budget(budget_id):
    try:
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
        budget_department = budget_data.budget_main_department

        # --調達予算情報テーブル class ProBudgetUnit(models.Model):
        if ProBudgetUnit.objects.filter(budget_id=budget_id, lost_flag=0).count() == 0:
            with connections['fmsdb'].cursor() as cursor:
                sql = """ INSERT INTO [fms].[dbo].[fms_probudgetunit] """
                sql += """ ( """
                sql += """ [budget_id] """
                sql += """ ,[rev_no] """
                sql += """ ,[budget_name] """
                sql += """ ,[req_func] """
                sql += """ ,[department] """
                sql += """ ,[division] """
                sql += """ ,[jurisdiction_area] """
                sql += """ ,[area_person_in_charge] """
                sql += """ ,[original_sec_person_in_charge] """
                sql += """ ,[sche_gov_inspection_date] """
                sql += """ ,[entry_datetime] """
                sql += """ ,[entry_operator] """
                sql += """ ,[update_datetime] """
                sql += """ ,[update_operator] """
                sql += """ ,[budget_no] """
                sql += """ ,[construction_detail] """
                sql += """ ,[entry_on_progress_flag] """
                sql += """ ,[cancel_flag] """
                sql += """ ,[lost_flag] """
                sql += """ ) """
                sql += """ SELECT  """
                sql += """        [budget_id] """
                sql += """        ,0 """
                sql += """        ,[budget_name] """
                sql += """        ,NULL """
                sql += """        ,[budget_main_department_id] """
                sql += """        ,[division_cd] """
                sql += """        ,B.[jurisdiction_area] """
                sql += """        ,B.[area_manager_id] """
                sql += """        ,[budget_department_charge_person_id] """
                sql += """        ,NULL """
                sql += """        ,[entry_datetime] """
                sql += """        ,[entry_operator] """
                sql += """        ,[update_datetime] """
                sql += """        ,[update_operator] """
                sql += """        ,[budget_no] """
                sql += """        ,NULL """
                sql += """        ,1 """
                sql += """        ,0 """
                sql += """        ,0 """
                sql += """	  FROM [fms].[dbo].[fms_budget] A """
                sql += """	  LEFT OUTER JOIN [fms].[dbo].[fms_departmentmaster] as B  """
                sql += """	  ON A.[budget_main_department_id] = B.[department_cd] """
                sql += """     WHERE A.budget_id= """ + str(budget_id)
                sql += """     AND A.lost_flag= 0 """

                res = cursor.execute(sql)

            # 予算関連の添付ファイルコピー処理
            send_data_sub_file('budget', 'probudgetunit', budget_id, 0, 'budget_detail')

            if Progress.objects.filter(target='probudgetunit', target_id=budget_id).count() == 0:
                with connections['fmsdb'].cursor() as cursor:
                    # --進捗状況 class Progress(models.Model):
                    sql = """ INSERT INTO [fms].[dbo].[fms_progress] """
                    sql += """ ( """
                    sql += """     [target] """
                    sql += """     ,[target_id] """
                    sql += """     ,[present_step] """
                    sql += """     ,[present_department] """
                    sql += """     ,[present_division] """
                    sql += """     ,[present_operator] """
                    sql += """     ,[last_operation_step] """
                    sql += """     ,[last_operator] """
                    sql += """     ,[last_operation_datetime] """
                    sql += """ ) """
                    sql += """ VALUES """
                    sql += """ ( """
                    sql += """  'probudgetunit' """
                    sql += """ ,'""" + str(budget_id) + """'"""

                    # 予算額追加の場合エリア管理者決定ステップは飛ばして仕様書発行中に設定
                    if budget_data.application_class_id == 3 or budget_data.application_class_id == 5:
                        sql += """ ,'211001011' """
                    else:
                        sql += """ ,'211001001' """

                    sql += """       ,'CWG' """
                    sql += """       ,'KOUMU' """

                    if budget_department.area_manager_id is not None:
                        sql += """ , '""" + budget_department.area_manager_id + """'"""
                    else:
                        sql += """ , NULL """

                    sql += """ , NULL """
                    sql += """ , NULL """
                    sql += """ , NULL """
                    sql += """ )   """

                    res = cursor.execute(sql)

    except Exception:
        output_log_error(traceback.format_exc())
        raise


# 工事実行へのデータ移行処理
def send_data_work(budget_id, application_class_id):
    try:
        # WorkをもとにProSpecificationUnitを作成
        work_list = Work.objects.filter(work_budget_id=budget_id, lost_flag=0).exclude(cancel_flag=1)

        for target_work_data in work_list:

            work_data = Work.objects.filter(work_id=target_work_data.work_id, lost_flag=0).exclude(cancel_flag=1).all().order_by('-work_rev_no')[0]

            # progressのないwork、仕様書見積完了していないworkは実行側に移行しない
            progress_list = Progress.objects.filter(target='work', target_id=work_data.work_id)
            if progress_list.count() != 1:
                continue
            if progress_list[0].present_step < 133009904:
                continue

            # --調達仕様書情報テーブル class ProSpecificationUnit(models.Model):
            if ProSpecificationUnit.objects.filter(budget_id=budget_id,
                                                   construction_id=work_data.work_id, lost_flag=0).count() == 0:
                with connections['fmsdb'].cursor() as cursor:
                    sql = """ INSERT INTO [fms].[dbo].[fms_prospecificationunit] """
                    sql += """ ( """
                    sql += """ [budget_id] """
                    sql += """ ,[rev_no] """
                    sql += """ ,[budget_name] """
                    sql += """ ,[construction_id] """
                    sql += """ ,[sub_id] """
                    sql += """ ,[work_name]	"""
                    sql += """ ,[work_charge_process] """
                    sql += """ ,[req_func]	"""
                    sql += """ ,[department]	"""
                    sql += """ ,[division]	"""
                    sql += """ ,[format_kbn]	"""
                    sql += """ ,[goods_construct_kbn]	"""
                    sql += """ ,[specification_person_in_charge]	"""
                    sql += """ ,[delivery_location]	"""
                    sql += """ ,[desired_construct_period_from]	"""
                    sql += """ ,[desired_construct_period_to]	"""
                    sql += """ ,[desired_delivery_date]	"""
                    sql += """ ,[estimate_submission_date]	"""
                    sql += """ ,[order_limited_date]	"""
                    sql += """ ,[scheduled_inspection_date_from]	"""
                    sql += """ ,[scheduled_inspection_date_to]	"""
                    sql += """ ,[specification_data]	"""
                    sql += """ ,[construction_outline]	"""
                    sql += """ ,[contents_detail1]	"""
                    sql += """ ,[contents_detail2]	"""
                    sql += """ ,[contents_detail3]	"""
                    sql += """ ,[contents_detail4]	"""
                    sql += """ ,[contents_detail5]	"""
                    sql += """ ,[management_class_cd]	"""
                    sql += """ ,[entry_datetime]	"""
                    sql += """ ,[entry_operator]	"""
                    sql += """ ,[update_datetime]	"""
                    sql += """ ,[update_operator]	"""
                    sql += """ ,[budget_no]	"""
                    sql += """ ,[entry_on_progress_flag]	"""
                    sql += """ ,[lost_flag]	"""
                    sql += """ ,[cancel_flag]	"""
                    sql += """	)	"""
                    sql += """	SELECT 	"""
                    sql += """	      [budget_id]	"""
                    sql += """	      ,0	"""
                    sql += """	      ,B.[budget_name]	"""
                    sql += """	      ,[work_id]	"""
                    sql += """	      ,[sub_no]	"""
                    sql += """	      ,[work_name]	"""
                    sql += """	      ,[work_charge_process_id]	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,[work_order_department_id]	"""
                    sql += """	      ,[division_cd]	"""
                    sql += """	      ,[fixed_form]	"""
                    sql += """	      ,[work_class_id]	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,[delivery_location]	"""
                    sql += """	      ,[work_start_date]	"""
                    sql += """	      ,[work_end_date]	"""
                    sql += """	      ,[work_delivery_date]	"""
                    sql += """	      ,[work_estimate_limited_date]	"""
                    sql += """        ,[order_limited_date] """
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,A.[management_class_cd] """
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,NULL	"""
                    sql += """	      ,B.[budget_no]	"""
                    sql += """	      ,1	"""
                    sql += """	      ,0	"""
                    sql += """	      ,0	"""
                    sql += """	  FROM [fms].[dbo].[fms_work] A	"""
                    sql += """	  LEFT OUTER JOIN [fms].[dbo].[fms_budget] as B """
                    sql += """	  ON A.work_budget_id = B.budget_id """
                    sql += """	  AND B.lost_flag = 0 """
                    sql += """	 LEFT OUTER JOIN [fms].[dbo].[fms_departmentmaster] as D  """
                    sql += """	  ON A.work_order_department_id = D.department_cd """
                    sql += """	 WHERE B.budget_id= """ + str(budget_id)
                    sql += """	   AND A.work_id= """ + str(work_data.work_id)
                    sql += """	   AND A.[work_rev_no] = (SELECT max(C.work_rev_no)	"""
                    sql += """	                            FROM [fms].[dbo].[fms_work] C	"""
                    sql += """	                           WHERE C.work_id = """ + str(work_data.work_id) + """)"""

                    res = cursor.execute(sql)

                # 仕様詳細のコピー処理
                send_data_sub(budget_id, work_data.work_id)

                # その他工事関連のデータコピー処理
                send_data_sub_work(work_data.work_id)

                # 工事関連の添付ファイルコピー処理
                send_data_sub_file('work', 'prospecificationunit', budget_id, work_data.work_id, 'prospecificationunit')

                if Progress.objects.filter(target='prospecificationunit', target_id=work_data.work_id).count() == 0:
                    with connections['fmsdb'].cursor() as cursor:
                        # --進捗状況 class Progress(models.Model):
                        sql = """ INSERT INTO [fms].[dbo].[fms_progress] """
                        sql += """ ( """
                        sql += """     [target] """
                        sql += """     ,[target_id] """
                        sql += """     ,[present_step] """
                        sql += """     ,[present_department] """
                        sql += """     ,[present_division] """
                        sql += """     ,[present_operator] """
                        sql += """     ,[last_operation_step] """
                        sql += """     ,[last_operator] """
                        sql += """     ,[last_operation_datetime] """
                        sql += """ ) """
                        sql += """ VALUES """
                        sql += """ ( """
                        sql += """  'prospecificationunit' """
                        sql += """ ,'""" + str(work_data.work_id) + """'"""
                        sql += """ ,'211002011' """

                        execution_charge_person = work_data.work_execution_charge_person
                        if execution_charge_person is not None:
                            execution_charge_person_data = \
                                UserAttribute.objects.filter(username=execution_charge_person.username,
                                                              lost_flag=0).all().order_by('display_order')[0]
                            sql += """ ,'""" + execution_charge_person_data.department + """'"""
                            sql += """ ,'""" + execution_charge_person_data.division + """'"""
                            sql += """ , '""" + execution_charge_person.username + """'"""
                        else:
                            # 実行担当者未入力時は、工務G固定で設定
                            sql += """       ,'CWG' """
                            sql += """       ,'KOUMU' """
                            sql += """	      ,NULL	"""

                        sql += """ , NULL """
                        sql += """ , NULL """
                        sql += """ , NULL """
                        sql += """ )   """

                        res = cursor.execute(sql)

    except Exception:
        output_log_error(traceback.format_exc())
        raise


def risk_send_back(target_budget_id, this_step, operator, return_person_data, comment):
    from fms.views.budget_views import set_budget_status

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

    try:
        budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)
        user_data = UserAttribute.objects.filter(username=operator, lost_flag=0).all().order_by('display_order')[0]

        # リスク評価対象の予算リストを取得
        ans = get_risks_list(budget_data.business_year, this_step)

        budget_list_data = ans[0]
        budget_list_data_num = ans[1]
        total_budget_price_value = ans[2]
        fetch_array = ans[3]
        # msg = ans[4]

        # 抽出された予算のリストを次ステップへ
        for list_data in budget_list_data:
            # ログデータを新規登録
            Log(target='budget', target_id=list_data.budget_id, action='return', operator=operator,
                operation_datetime=now, step=this_step, comment=comment, operator_department=user_data.department,
                operator_division=user_data.division, budget_id=list_data.budget_id).save()

            # 進捗状況を対象(budget)と予算idで抽出
            progress_data = Progress.objects.get(target="budget", target_id=list_data.budget_id)
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
            # 予算の状態変更(関数内で判定)
            set_budget_status(progress_data)

            # 進捗通知機能
            step_notice(progress_data)

    except Exception:
        output_log_error(traceback.format_exc())
        raise


# データ移行サブ処理(仕様詳細のコピー)
def send_data_sub(budget_id, work_id):

    specification_item = ProSpecificationUnit.objects.get(budget_id=budget_id, construction_id=work_id, lost_flag=0)
    spec_detail_list = FreeSpecDetail.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0).all().order_by('sub_no')

    index = 0
    for spec_detail_item in spec_detail_list:
        if index == 0:
            specification_item.contents_detail1 = spec_detail_item.detail
        elif index == 1:
            specification_item.contents_detail2 = spec_detail_item.detail
        elif index == 2:
            specification_item.contents_detail3 = spec_detail_item.detail
        elif index == 3:
            specification_item.contents_detail4 = spec_detail_item.detail
        elif index == 4:
            specification_item.contents_detail5 = spec_detail_item.detail
        else:
            # 5ページ以降は内容詳細に移せないのでスキップする
            continue
        index = index + 1

    specification_item.save()
    return


# データ移行サブ処理(工事付属データのコピー)
def send_data_sub_work(work_id):

    # 工事関係法令
    work_law_list = WorkLaw.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0)
    for work_law_item in work_law_list:
        # すでに実行側が作成されていたらコピーしない
        work_law_execution_count = WorkLaw.objects.filter(work_id=work_id, law_name=work_law_item.law_name, entry_class='実行', lost_flag=0).count()
        if work_law_execution_count > 0:
            continue
        work_law_item.id = None
        work_law_item.entry_class = '実行'
        work_law_item.rev_no = 0
        work_law_item.entry_on_progress_flag = 0
        work_law_item.save()

    # 工事支給品
    work_supplies_list = Supplies.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0)
    for work_supplies_item in work_supplies_list:
        # すでに実行側が作成されていたらコピーしない
        supplies_execution_count = Supplies.objects.filter(work_id=work_id, supplies_name=work_supplies_item.supplies_name, entry_class='実行', lost_flag=0).count()
        if supplies_execution_count > 0:
            continue
        work_supplies_item.id = None
        work_supplies_item.entry_class = '実行'
        work_supplies_item.rev_no = 0
        work_supplies_item.entry_on_progress_flag = 0
        work_supplies_item.save()

    # 提出書類
    document_list = SubmissionDocument.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0)
    for document_item in document_list:
        # すでに実行側が作成されていたらコピーしない
        document_execution_count = SubmissionDocument.objects.filter(work_id=work_id, document_name=document_item.document_name, entry_class='実行', lost_flag=0).count()
        if document_execution_count > 0:
            continue
        document_item.id = None
        document_item.entry_class = '実行'
        document_item.rev_no = 0
        document_item.entry_on_progress_flag = 0
        document_item.save()

    return


# データ移行サブ処理(添付ファイルのコピー)
def send_data_sub_file(target_from, target_to, budget_id, work_id, div_id_name_to):

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
        folder_path_to, folder_name_to = get_attachment_folder_name(target_to, budget_id, work_id, copy_file_item.data)
        file_path_to = os.path.join(folder_path_to, copy_file_item.file_name)

        # フォルダの存在チェック　なければフォルダ作成
        if os.path.exists(folder_path_to) is not True:
            os.makedirs(folder_path_to)

        # ファイルの存在チェック(すでにファイルがある場合はコピーしない)
        if os.path.isfile(file_path_to) is not True:
            # ファイルをコピー
            shutil.copy2(file_path_from, file_path_to)

        # すでに実行側が作成されていたらコピーしない
        if AttachmentDocuments.objects.filter(folder=folder_name_to, div_id_name=div_id_name_to, file_name=copy_file_item.file_name, lost_flag=0).count() < 1:
            # 新規レコードを保存
            copy_file_item.id = None
            copy_file_item.folder = folder_name_to
            copy_file_item.div_id_name = div_id_name_to
            copy_file_item.save()

    return
