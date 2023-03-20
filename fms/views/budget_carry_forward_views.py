import math
import datetime
import traceback

# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST

# modelesをインポート
from fms.models import DataEntryStepMaster
from fms.models import Budget, Progress, Log
from fms.models import BusinessYearMaster, DepartmentMaster, UserAttribute
from fms.models import BudgetCarryForward, StepDisplayItem
from fms.views.common_def_views import output_log_exception
from fms.views.common_views import date_to_hyphen
from django.utils.timezone import make_aware
from fms.views.notice_mail_views import step_notice


# 該当予算IDが発注完了しているか判定する
@login_required
def check_budget_order_complete(request, budget_id):
    try:
        order_complete_flag = 0

        # 該当予算の予算繰越情報を取得
        carry_forward_list = BudgetCarryForward.objects.filter(budget_id=budget_id, lost_flag=0).order_by('-id')

        # 発注完了状態のものが１つでもあれば、発注完了状態とする(完了している繰越情報を含む)
        for carry_forward_item in carry_forward_list:
            if carry_forward_item.order_complete_flag != 0:
                order_complete_flag = 1
                break

        return order_complete_flag
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 該当予算IDの有効な繰越情報を取得する
@login_required
def get_budget_carry_forward(request, budget_id):
    try:
        carry_forward_data = ''
        present_step = 0
        # 該当予算の予算繰越情報が存在するか確認
        carry_forward_list = BudgetCarryForward.objects.filter(budget_id=budget_id, lost_flag=0).order_by('-id')
        if carry_forward_list.count() < 1:
            return carry_forward_data, present_step

        # 予算繰越が完了していない繰越情報を取得
        for carry_forward_item in carry_forward_list:
            progress_item = Progress.objects.get(target='budget_carry_forward', target_id=carry_forward_item.carry_forward_id)
            if progress_item.present_step != 213012001:
                carry_forward_data = carry_forward_item
                present_step = progress_item.present_step
                break

        return carry_forward_data, present_step
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 該当予算の繰越情報を新規作成する
@login_required
def make_budget_carry_forward(request, budget_id):
    try:
        # ログインユーザー情報取得
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        this_step = int(request.POST["this_step"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]

        # レコードがない時の処理･･･carry_forward_id=1 とする
        if BudgetCarryForward.objects.all().count() == 0:
            this_carry_forward_id = 1
        # レコードがある時の処理･･･最終のidを取得し、id=最終のid+1 とする
        else:
            last_carry_forward_data = BudgetCarryForward.objects.all().order_by('-carry_forward_id')[0]
            last_carry_forward_id = last_carry_forward_data.carry_forward_id
            this_carry_forward_id = last_carry_forward_id + 1

        # 予算情報取得
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)

        # 予算繰越情報生成
        carry_forward_item = BudgetCarryForward.objects.create(carry_forward_id=this_carry_forward_id, budget_id=budget_id, lost_flag=0)
        carry_forward_item.rev_no = 0
        carry_forward_item.entry_on_progress_flag = 0
        carry_forward_item.entry_datetime = now
        carry_forward_item.entry_operator = t_username
        # 予算側からデータ引継ぎ
        carry_forward_item.carry_forward_price = budget_data.budget_price
        carry_forward_item.carry_forward_year_from_id = budget_data.business_year_id
        carry_forward_item.save()
        # Progress生成
        progress_item = Progress.objects.create(target='budget_carry_forward', target_id=carry_forward_item.carry_forward_id)
        progress_item.present_step = 213010001
        progress_item.present_operator = t_username
        user_attr_list = UserAttribute.objects.filter(username=t_username, lost_flag=0).all()
        progress_item.present_department = user_attr_list[0].department
        progress_item.present_division = user_attr_list[0].division
        progress_item.save()

        # ログデータに新規登録
        Log(target='budget_carry_forward', target_id=carry_forward_item.carry_forward_id, action='add',
            operator=t_username, operation_datetime=now, step=this_step,
            comment='予算繰越処理開始', operator_department=this_department, operator_division=this_division,
            budget_id=budget_id).save()

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# リビジョン更新チェック
@require_POST
@login_required
def update_budget_carry_forward_rev(request, carry_forward_id):
    try:
        # ログインユーザー情報取得
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username

        on_progress_num = BudgetCarryForward.objects.filter(carry_forward_id=carry_forward_id,
                                                            entry_on_progress_flag=1, lost_flag=0).count()
        complete_num = BudgetCarryForward.objects.filter(carry_forward_id=carry_forward_id,
                                                         entry_on_progress_flag=0, lost_flag=0).count()
        # 完了FLがONの件数が「0」より多い場合
        if complete_num > 0:
            # 該当のidで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
            last_carry_forward_data = \
                BudgetCarryForward.objects.filter(carry_forward_id=carry_forward_id,
                                                  entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
            # 該当のidで最終のrev_noを取得
            latest_rev_no = last_carry_forward_data.rev_no
            # 該当のレコードを無効
            last_carry_forward_data.lost_flag = 1
            # レコードを保存
            last_carry_forward_data.save()

            # 完了FLがONの件数が「0」の場合
            if on_progress_num == 0:
                # 新リビジョンのデータを保存
                last_carry_forward_data.id = None
                last_carry_forward_data.rev_no = latest_rev_no + 1
                last_carry_forward_data.entry_on_progress_flag = 1
                last_carry_forward_data.lost_flag = 0
                last_carry_forward_data.entry_datetime = now
                last_carry_forward_data.entry_operator = t_username
                last_carry_forward_data.save()
        else:
            last_carry_forward_data = \
                BudgetCarryForward.objects.filter(carry_forward_id=carry_forward_id,
                                                  entry_on_progress_flag=1, lost_flag=0).order_by('-id')[0]

        return last_carry_forward_data
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算繰越処理開始
@login_required
@require_POST
def budget_carry_forward_start(request):
    from fms.views.budget_views import set_condition
    try:
        budget_id = int(request.POST['budget_id'])

        # 該当予算の予算繰越情報が存在するか確認
        carry_forward_item, present_step = get_budget_carry_forward(request, budget_id)
        if carry_forward_item != '':
            msg = 'すでに予算繰越処理中です！！！'
        else:
            # 予算繰越情報生成
            make_budget_carry_forward(request, budget_id)

            # 予算状態設定(関連予算も含めて変更する)
            relation_budget_data = Budget.objects.filter(relation_budget_id=budget_id, lost_flag=0)
            for target_budget_data in relation_budget_data:
                set_condition(target_budget_data.budget_id, 41)

            msg = '予算繰越処理開始'

        ary = {
            'msg': msg,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算繰越処理完了
@login_required
@require_POST
def budget_carry_forward_complete(request, carry_forward_item, input_budget_price_str):
    from fms.views.budget_views import set_condition
    try:
        # ログインユーザー情報取得
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        target_budget_id = int(request.POST['target_budget_id'])

        # 予算状態設定(関連予算も含めて変更する)
        relation_budget_data = Budget.objects.filter(relation_budget_id=target_budget_id, lost_flag=0)
        for target_budget_data in relation_budget_data:
            set_condition(target_budget_data.budget_id, 31)

        # 予算のリビジョンを更新する
        budget_data = Budget.objects.get(budget_id=target_budget_id, lost_flag=0)

        # 旧リビジョンは削除
        latest_rev_no = budget_data.rev_no
        budget_data.entry_on_progress_flag = 0
        budget_data.lost_flag = 1
        budget_data.save()

        # 新リビジョンの予算データを保存する
        budget_data.business_year_id = carry_forward_item.carry_forward_year_to_id
        # 変更予算額が未入力の場合、現予算額のままとする
        if input_budget_price_str is not None:
            budget_data.budget_price = int(input_budget_price_str.replace(',', ''))
        budget_data.rev_no = latest_rev_no + 1
        budget_data.entry_datetime = now
        budget_data.entry_operator = t_username
        budget_data.update_datetime = None
        budget_data.update_operator = None
        budget_data.lost_flag = 0
        budget_data.id = None
        budget_data.save()

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 予算繰越情リスト表示
@login_required
@require_POST
def budget_carry_forward_list(request):
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
        sel_area_manager = request.POST['sel_area_manager']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']
        sel_on_work = request.POST['sel_on_work']
        level5_step_id = int(request.POST['level5_step_id'])
        sel_display_order = request.POST['sel_display_order']
        sel_show_additional_budget = request.POST['sel_show_additional_budget']
        return_url = request.POST['return_url']
        start_work_stop_flag = int(request.POST['start_work_stop_flag'])
        list_kind = request.POST['list_kind']
        msg = ""

        # 予算繰越情報を基準に、予算リストを取得

        # 実行中予算のみが対象なので、パラメーターは2重に持たない
        where_str = ""
        where_parm = []

        # 検索条件
        where_str += " AND fms_budget.plan_class_id = %s \n"
        where_parm.append('S')

        # 予算状態
        if sel_budget_condition != "":
            where_str += " AND fms_budgetconditionmaster.condition_id = %s \n"
            where_parm.append(int(sel_budget_condition))
        # 進捗状況
        if sel_step != "":
            where_str += " AND D.step_id = %s \n"
            where_parm.append(int(sel_step))
        # 年度(繰越情報の繰越元年度で絞り込み)
        if sel_business_year != "":
            where_str += " AND fms_budgetcarryforward.carry_forward_year_from_id = %s \n"
            where_parm.append(int(sel_business_year))
        # 工事区分
        if sel_budget_class != "":
            where_str += " AND fms_budget.budget_class_id = %s \n"
            where_parm.append(int(sel_budget_class))

        # 追加予算表示
        if sel_show_additional_budget == 'false':
            where_str += " AND fms_budget.budget_id = fms_budget.relation_budget_id \n"
        #  予算ID
        if sel_budget_id != "":
            where_str += " AND fms_budget.budget_id = %s \n"
            where_parm.append(int(sel_budget_id))

        # 予算NO
        if sel_budget_no != "":
            where_str += " AND fms_budget.budget_no LIKE %s \n"
            where_parm.append('%' + sel_budget_no + '%')
        # 予算名
        if sel_budget_name != "":
            where_str += " AND fms_budget.budget_name LIKE %s \n"
            where_parm.append('%' + sel_budget_name + '%')
        # 部門
        if sel_division != "":
            where_str += " AND fms_departmentmaster.division_cd = %s \n"
            where_parm.append(sel_division)
        # 部署
        if sel_department != "":
            where_str += " AND fms_departmentmaster.department_cd = %s \n"
            where_parm.append(sel_department)
        # 行程
        if sel_process != "":
            where_str += " AND fms_budget.facility_process_id = %s \n"
            where_parm.append(sel_process)
        # エリア管理者
        if sel_area_manager != "":
            where_str += " AND fms_budget.area_manager_id = %s \n"
            where_parm.append(sel_area_manager)

        # 次作業部門
        if sel_next_division != "":
            where_str += " AND C.present_division = %s \n"
            where_parm.append(sel_next_division)
        # 次作業部署
        if sel_next_department != "":
            where_str += " AND C.present_department = %s \n"
            where_parm.append(sel_next_department)

        # 未処理のみ
        if start_work_stop_flag == 1:
            where_str += " AND fms_budget.budget_no is not NULL \n"
        elif sel_on_work == 'true':
            if level5_step_id == 213000000 or level5_step_id == 213009000:
                step_st = 213010000
                # 予算繰越完了は表示しない
                step_ed = 213012000
            else:
                step_st = math.floor(level5_step_id / 1000) * 1000
                step_ed = step_st + 1000

            where_str += " AND C.present_step > %s \n"
            where_parm.append(step_st)
            where_str += " AND C.present_step < %s \n"
            where_parm.append(step_ed)

        # 次作業者
        if sel_next_parson != "":
            where_str += " AND C.present_operator = %s \n"
            where_parm.append(sel_next_parson)

        # 予算候補リスト取得
        sql = """ SELECT fms_budget.*, fms_user.first_name, fms_user.last_name, fms_user.username, \n"""
        sql = sql + """     fms_stepmaster.step_name, fms_stepmaster.step_id,fms_budgetcarryforward.* \n"""
        sql = sql + """     ,CASE WHEN fms_budget.budget_no IS NULL THEN '' ELSE fms_budget.budget_no END AS bd_no \n"""
        sql = sql + """     ,fms_budgetconditionmaster.condition_name,fms_departmentmaster.department_name \n"""
        sql = sql + """     ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_budget.entry_datetime, GETDATE()) \n"""
        sql = sql + """                                                 ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END \n"""
        sql = sql + """      AS days_stay \n"""
        sql = sql + """     , CASE WHEN log_2.action = 'return' THEN 1 \n"""
        sql = sql + """     ELSE 0 \n"""
        sql = sql + """     END AS return_flag \n"""
        sql = sql + """     ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_name END B_step_name \n"""
        sql = sql + """     ,CASE WHEN B.step_name IS NULL THEN '' ELSE B.step_id END B_step_id \n"""
        sql = sql + """     ,CASE WHEN D.step_name IS NULL THEN '' ELSE D.step_name END D_step_name \n"""
        sql = sql + """     ,CASE WHEN D.step_name IS NULL THEN '' ELSE D.step_id END D_step_id \n"""
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
        sql = sql + """ RIGHT JOIN fms_probudgetunit ON fms_budget.budget_id=fms_probudgetunit.budget_id AND fms_probudgetunit.lost_flag=0 \n"""
        sql = sql + """ LEFT JOIN fms_progress A ON fms_probudgetunit.budget_id=A.target_id AND A.target='probudgetunit' \n"""
        sql = sql + """ LEFT JOIN fms_stepmaster B ON A.present_step=B.step_id \n"""
        sql = sql + """ LEFT JOIN fms_budgetcondition ON fms_budget.budget_id=fms_budgetcondition.budget_id \n"""
        sql = sql + """ LEFT JOIN fms_budgetconditionmaster ON fms_budgetcondition.budget_condition_id=fms_budgetconditionmaster.condition_id \n"""

        sql = sql + """ RIGHT JOIN fms_budgetcarryforward ON fms_budget.budget_id=fms_budgetcarryforward.budget_id AND fms_budgetcarryforward.lost_flag=0 \n"""
        sql = sql + """ LEFT JOIN fms_progress C ON fms_budgetcarryforward.carry_forward_id=C.target_id AND C.target='budget_carry_forward' \n"""
        sql = sql + """ LEFT JOIN fms_stepmaster D ON C.present_step=D.step_id \n"""

        sql = sql + """ LEFT JOIN fms_progress ON fms_budget.budget_id=fms_progress.target_id AND fms_progress.target='budget' \n"""
        sql = sql + """ LEFT JOIN fms_user ON C.present_operator=fms_user.username \n"""

        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id \n"""
        sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_budget.budget_main_department_id=fms_departmentmaster.department_cd \n"""
        sql = sql + """ LEFT JOIN ( SELECT fms_work.work_budget_id \n"""
        sql = sql + """ 				                      from fms_work \n"""
        sql = sql + """ 									 where fms_work.lost_flag = 0 \n"""
        sql = sql + """ 									 group by fms_work.work_budget_id \n"""
        sql = sql + """ 								   ) AS fms_work ON fms_budget.budget_id = fms_work.work_budget_id \n"""
        sql = sql + """ LEFT JOIN ( SELECT  main.*, sub.[action] \n"""
        sql = sql + """             FROM (  SELECT  budget_id \n"""
        sql = sql + """                             ,MAX(operation_datetime) AS operation_datetime \n"""
        sql = sql + """                       FROM  [fms].[dbo].[fms_log] \n"""
        sql = sql + """                      WHERE  ([target] = 'budget_carry_forward') \n"""
        sql = sql + """                        AND  [action] != 'temporarily_saved' \n"""
        sql = sql + """                   GROUP BY [budget_id] """
        sql = sql + """                  ) AS main """
        sql = sql + """             INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime \n"""
        sql = sql + """                                                    AND main.budget_id=sub.budget_id \n"""
        sql = sql + """                                                     AND sub.target='budget_carry_forward' \n"""
        sql = sql + """             WHERE   main.[operation_datetime] = sub.operation_datetime \n"""
        sql = sql + """           ) AS log_2 ON fms_budget.budget_id = log_2.budget_id \n"""
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
        sql = sql + """               and       (work_progress.present_step >= 133004000 or budget_progress.present_step >= 133004000) \n"""
        sql = sql + """            group by work_budget_id \n"""
        sql = sql + """           ) AS complete_work_num on fms_work.work_budget_id = complete_work_num.work_budget_id \n"""
        sql = sql + """ WHERE fms_budget.lost_flag=0 \n"""
        if where_str != "":
            sql += where_str
        sql = sql + """ AND B.step_id != 0 \n"""

        sql += "    ORDER BY "
        if sel_display_order == "1":
            sql += "fms_budget.budget_id"
        elif sel_display_order == "2":
            sql += "fms_budget.budget_no"
        elif sel_display_order == "3":
            sql += "days_stay desc"
        else:
            sql += "fms_budget.facility_process_id"

        if len(where_parm) == 0:
            budget_lists = Budget.objects.all().raw(sql)
        else:
            budget_lists = Budget.objects.raw(sql, where_parm)

        budget_lists_num = len(list(budget_lists))

        data = {
            'msg': msg,
            'budget_lists': budget_lists,
            'budget_lists_num': budget_lists_num,
            'list_kind': list_kind,
        }
        return render(request, return_url, data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算繰越情報を表示する画面の表示
@login_required
@require_POST
def budget_carry_forward_info(request):
    try:
        budget_id = request.POST['budget_id']
        this_step = request.POST['this_step']
        target_carry_forward_id = request.POST['target_carry_forward_id']

        carry_forward_list = BudgetCarryForward.objects.filter(
            budget_id=budget_id, carry_forward_id=target_carry_forward_id, lost_flag=0).order_by('-id')
        if carry_forward_list.count() < 1:
            # 表示対象データ無し
            return

        carry_forward_item = carry_forward_list[0]
        carry_forward_price_str = "{:,}".format(carry_forward_item.carry_forward_price)

        # 予算情報の取得
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)

        # データ編集可能フラグの取得
        edit_flag = DataEntryStepMaster.objects.filter(
            step_id=this_step, target_table='budget_carry_forward', lost_flag=0).count()

        # タブ毎のボタン表示対応
        stepdisplayitem_data = StepDisplayItem.objects.get(step=this_step, div_id_name='budget_carry_forward',
                                                           lost_flag=0)
        this_page = stepdisplayitem_data.page
        action_button_id = 'budget_carry_forward' + str(this_page) + '_action_button'

        data = {
            'carry_forward_data': carry_forward_item,
            'carry_forward_price_str': carry_forward_price_str,
            'budget_data': budget_data,
            'this_page': this_page,
            'action_button_id': action_button_id,
        }

        if edit_flag > 0:
            return render(request, 'fms/parts/budget/budget_carry_forward/budget_carry_forward_edit.html', data)
        else:
            return render(request, 'fms/parts/budget/budget_carry_forward/budget_carry_forward_info.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算繰越額の登録画面の表示処理
@login_required
@require_POST
def budget_carry_forward_register(request):
    try:
        budget_id = request.POST['budget_id']
        this_step = request.POST['this_step']
        target_carry_forward_id = request.POST['target_carry_forward_id']

        carry_forward_list = BudgetCarryForward.objects.filter(
            budget_id=budget_id, carry_forward_id=target_carry_forward_id, lost_flag=0).order_by('-id')
        if carry_forward_list.count() < 1:
            # 表示対象データ無し
            return

        carry_forward_item = carry_forward_list[0]
        carry_forward_price_str = "{:,}".format(carry_forward_item.carry_forward_price)

        # 予算情報の取得
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)

        # データ編集可能フラグの取得
        edit_flag = DataEntryStepMaster.objects.filter(
            step_id=this_step, target_table='budget_carry_forward_register', lost_flag=0).count()

        # タブ毎のボタン表示対応
        stepdisplayitem_data = StepDisplayItem.objects.get(step=this_step, div_id_name='budget_carry_forward_register',
                                                           lost_flag=0)
        this_page = stepdisplayitem_data.page
        action_button_id = 'budget_carry_forward' + str(this_page) + '_action_button'

        # 年度選択のソースとなるリスト抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1, business_year__gt=carry_forward_item.carry_forward_year_from_id).all()

        data = {
            'carry_forward_data': carry_forward_item,
            'carry_forward_price_str': carry_forward_price_str,
            'budget_data': budget_data,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'business_year_list': business_year_list,
        }

        if edit_flag > 0:
            return render(request, 'fms/parts/budget/budget_carry_forward/budget_carry_forward_register.html', data)
        else:
            return render(request, 'fms/parts/budget/budget_carry_forward/budget_carry_forward_info.html', data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 予算繰越情報の保存処理
@login_required
@require_POST
def budget_carry_forward_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]
        user_attribute_id = int(request.POST['user_attribute_id'])

        target_unique_carry_forward_id = int(request.POST['target_unique_carry_forward_id'])
        target_budget_id = int(request.POST['target_budget_id'])

        carry_forward_reason = request.POST['carry_forward_reason']
        end_date = date_to_hyphen(request.POST['end_date'])
        sel_order_complete_flag = request.POST['sel_order_complete_flag']
        carry_forward_price_str = request.POST['carry_forward_price']
        carry_forward_price_str = carry_forward_price_str.replace(',', '')
        carry_forward_price = int(carry_forward_price_str)

        settlement_no = request.POST.get('settlement_no', None)
        sel_business_year_id = request.POST.get('sel_business_year', None)
        input_budget_price_str = request.POST.get('input_budget_price', None)

        # ユーザー権限に登録されている場合の処理
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_department = user_attribute_data.department
        else:
            next_person = operator
            next_department = this_department

        if target_unique_carry_forward_id == 0:
            # Start処理前にEntry処理が呼ばれている、ありえないので異常
            msg = '繰越情報が特定できません！！！ \n先に繰越開始処理を行ってください'
        else:
            # 該当の予算繰越情報を取得
            carry_forward_item = update_budget_carry_forward_rev(request, target_unique_carry_forward_id)

            carry_forward_item.carry_forward_reason = carry_forward_reason
            carry_forward_item.end_date = end_date
            carry_forward_item.order_complete_flag = sel_order_complete_flag
            carry_forward_item.carry_forward_price = carry_forward_price

            if settlement_no is not None:
                carry_forward_item.settlement_no = settlement_no

            if sel_business_year_id is not None:
                carry_forward_item.carry_forward_year_to_id = sel_business_year_id

            carry_forward_item.update_datetime = now
            carry_forward_item.update_operator = operator
            # progressの更新
            if this_step != next_step:
                msg = "作成完了"
                comment = "作成完了"
                carry_forward_item.entry_on_progress_flag = 0
            else:
                comment = "一時保存"
                msg = "一時保存完了"
                carry_forward_item.entry_on_progress_flag = 1

            carry_forward_item.save()

            # 進捗状況を更新
            progress_data = Progress.objects.get(target='budget_carry_forward', target_id=carry_forward_item.carry_forward_id)

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

            # 予算繰越完了時処理
            if this_step != next_step and next_step == 213012001:
                msg = "予算繰越完了"
                comment = "予算繰越完了"
                budget_carry_forward_complete(request, carry_forward_item, input_budget_price_str)

            if this_step != next_step:
                step_notice(progress_data)

            # ログデータに新規登録
            Log(target='budget_carry_forward', target_id=carry_forward_item.carry_forward_id, action='entry',
                operator=operator, operation_datetime=now, step=this_step,
                comment=comment, operator_department=this_department, operator_division=this_division,
                budget_id=target_budget_id).save()

        ary = {
            'msg': msg,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise




