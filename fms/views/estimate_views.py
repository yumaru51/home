import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, BudgetRequiredFunction, AmountUnitMaster
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, Estimate, Discount
from django.db import connections
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 見積情報表示処理
@login_required
@require_POST
def estimate_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        present_step = int(request.POST["this_step"])
        level5_step_id = int(request.POST["level5_step_id"])

        # 登録済の見積情報数をカウント
        estimate_list_num = Estimate.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0).count()
        adopted_estimate_num = Estimate.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0, adoption_flag=1,
                                                       estimate_price__isnull=False).count()

        # 登録済の見積情報数が「0」でない(=ある)場合の処理
        if estimate_list_num != 0:
            # 登録済の見積情報を取得
            estimate_data = Estimate.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0).all().order_by('id')
            # 登録されているデータ全てに対して処理
            for estimate_data in estimate_data:
                # 対象の見積情報の主キー値取得
                estimate_id = estimate_data.id
                # 対象の見積情報に対する値引情報の数を取得
                discount_data_num = Discount.objects.filter(estimate_id=estimate_id, lost_flag=0).count()
                # 対象の見積情報に対する値引情報の数が「0」でない(=ある)場合の処理
                if discount_data_num != 0:
                    # 値引き合計額を取得
                    discount_sum = Discount.objects.filter(estimate_id=estimate_id, lost_flag=0).aggregate(
                        total=Sum('discount_price'))['total']
                    # 見積額から値引き合計額を差し引き、値引き後額を格納
                    estimate_data.price_after_discount = estimate_data.estimate_price - discount_sum
                # 対象の見積情報に対する値引情報の数が「0」(=ない)の場合の処理
                else:
                    # 値引き後額を「NULL」に
                    estimate_data.price_after_discount = None

                # 値引き回数を格納
                estimate_data.discount_num = discount_data_num
                # 見積情報のレコードを保存
                estimate_data.save()

            # 登録済の見積情報を再取得･･･データ更新しているため
            estimate_list = Estimate.objects.filter(work_id=work_id, entry_class='計画', lost_flag=0).all().order_by('id')

            for estimate_list_item in estimate_list:
                if estimate_list_item.estimate_price is not None:
                    # 3桁区切りの「,」挿入処理
                    estimate_list_item.estimate_price = "{:,}".format(int(estimate_list_item.estimate_price))

                if estimate_list_item.prospect_price is not None:
                    # 3桁区切りの「,」挿入処理
                    estimate_list_item.prospect_price = "{:,}".format(int(estimate_list_item.prospect_price))

        else:
            estimate_list = ""

        data = {
            'estimate_list_num': estimate_list_num,
            'estimate_list': estimate_list,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],
            'adopted_estimate_num': adopted_estimate_num,
        }

        # データ編集機能要否判定
        estimate_edit_action_num = 0
        # 対象stepで「estimate」がデータ更新対象か確認
        estimate_edit_action_num = estimate_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                                 target_table='estimate'
                                                                                                 ).count()
        if level5_step_id == 920000000 or level5_step_id == 212001000:
            estimate_edit_action_num = 0

        edit_flag = 0
        if estimate_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/work/estimate/estimate_edit.html', data)

        else:
            return render(request, 'fms/parts/work/estimate/estimate_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 値引情報表示処理
@login_required
@require_POST
def discount_list_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        estimate_id = int(request.POST["target_estimate_id"])

        # 対象の見積情報の値引情報数を取得
        discount_list_num = Discount.objects.filter(estimate_id=estimate_id, lost_flag=0).count()

        # 値引情報がある場合の処理
        if discount_list_num != 0:
            # 値引情報を取得
            discount_list = Discount.objects.filter(estimate_id=estimate_id, lost_flag=0).all().order_by('discount_no')

        else:
            discount_list = ""

        data = {
            'discount_list_num': discount_list_num,
            'discount_list': discount_list
        }

        return render(request, 'fms/parts/work/estimate/discount_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 見積情報登録･更新処理
@login_required
@require_POST
def estimate_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        action_type = request.POST["action_type"]
        work_id = int(request.POST["work_id"])
        rev_no = int(request.POST["rev_no"])
        estimate_id = int(request.POST["estimate_id"])
        vendor = request.POST["vendor"]
        estimate_price_str = request.POST["estimate_price"]
        if estimate_price_str == "":
            estimate_price = None
        else:
            estimate_price_str = estimate_price_str.replace(',', '')
            estimate_price = int(estimate_price_str)
        prospect_price_str = request.POST["prospect_price"]
        if prospect_price_str == "":
            prospect_price = estimate_price
        else:
            prospect_price_str = prospect_price_str.replace(',', '')
            prospect_price = int(prospect_price_str)
        adoption_flag = int(request.POST["adoption_flag"])
        if adoption_flag == "":
            adoption_flag = 0
        else:
            adoption_flag = int(request.POST["adoption_flag"])
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        start_date_str = request.POST["start_date"]
        start_date_str = start_date_str.replace('年', '-')
        start_date_str = start_date_str.replace('月', '-')
        start_date = start_date_str.replace('日', '')
        end_date_str = request.POST["end_date"]
        end_date_str = end_date_str.replace('年', '-')
        end_date_str = end_date_str.replace('月', '-')
        end_date = end_date_str.replace('日', '')
        estimate_rem = request.POST["estimate_rem"]
        if estimate_rem == "":
            estimate_rem = None
        # management_class = request.POST["management_class"]

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 新規追加の場合の処理
        if action_type == "add":
            # 「work_id」、「rev_no」、「業者名」で登録済の見積情報を抽出･･･あれば読み込み、なければ新規登録←ないはずなので、新規登録になるはず
            estimate_data, created = Estimate.objects.get_or_create(work_id=work_id, rev_no=rev_no, entry_class=entry_class, vendor=vendor)
            # 各項目の値を格納
            estimate_data.estimate_price = estimate_price
            estimate_data.prospect_price = prospect_price
            estimate_data.entry_datetime = now
            estimate_data.entry_operator = operator
            estimate_data.entry_on_progress_flag = 1
            estimate_data.lost_flag = 0
            estimate_data.adoption_flag = adoption_flag
            estimate_data.entry_class = entry_class
            estimate_data.start_date = start_date
            estimate_data.end_date = end_date
            estimate_data.start_date = None if start_date == "" else start_date
            estimate_data.end_date = None if end_date == "" else end_date
            estimate_data.rem = estimate_rem
            # estimate_data.management_class = management_class
            # 見積情報のレコードを保存
            estimate_data.save()
            # 見積情報の主キー値取得
            estimate_id = estimate_data.id

            # # 「estimate_id」で登録済の値引履歴を抽出･･･あれば読み込み、なければ新規登録←ないはずなので、新規登録になるはず
            # discount_data, created = Discount.objects.get_or_create(estimate_id=estimate_id, lost_flag=0)
            #
            # discount_data.discount_no = 1
            # discount_data.discount_price = prospect_price
            # discount_data.lost_flag = 0
            # discount_data.entry_on_progress_flag = 1
            # discount_data.entry_datetime = now
            # discount_data.entry_operator = operator
            # discount_data.update_datetime = ""
            # discount_data.update_operator = ""
            # discount_data.vendor_person = vendor
            #
            # discount_data.save()

            msg = "見積データ新規登録完了！！"
        # 更新の場合の処理
        elif action_type == "edit":
            # 主キーを利用し、見積情報のレコード取得
            estimate_data = Estimate.objects.get(id=estimate_id, lost_flag=0)
            # 各項目の値を格納
            estimate_data.rev_no = rev_no
            estimate_data.vendor = vendor
            estimate_data.estimate_price = estimate_price
            estimate_data.prospect_price = prospect_price
            estimate_data.adoption_flag = adoption_flag
            estimate_data.update_datetime = now
            estimate_data.update_operator = operator
            estimate_data.entry_class = entry_class
            estimate_data.start_date = start_date
            estimate_data.end_date = end_date
            estimate_data.start_date = None if start_date == "" else start_date
            estimate_data.end_date = None if end_date == "" else end_date
            estimate_data.rem = estimate_rem
            # estimate_data.management_class = management_class
            # 見積情報のレコードを保存
            estimate_data.save()
            adoption_flag = 1

            # # 「estimate_id」、「discount_no」、「vendor」で登録済の値引履歴を抽出･･･あれば読み込み、なければ新規登録
            # #　←ないはずなので、新規登録になるはず
            # discount_list = Discount.objects.filter(estimate_id=estimate_id, lost_flag=0).all().order_by('-discount_no')
            # if discount_list.count() > 0:
            #     discount_data, created = Discount.objects.get_or_create(estimate_id=estimate_id,
            #                                                             discount_no=discount_list[0].discount_no+1,
            #                                                             vendor_person=vendor,
            #                                                             lost_flag=0)
            #
            #     discount_data.discount_price = prospect_price
            #     discount_data.lost_flag = 0
            #     discount_data.entry_on_progress_flag = 1
            #     discount_data.entry_datetime = now
            #     discount_data.entry_operator = operator
            #     discount_data.update_datetime = ""
            #     discount_data.update_operator = ""
            #
            #     discount_list[0].entry_on_progress_flag = 0
            #
            #     discount_data.save()
            #     discount_list[0].save()

            msg = "見積データ更新完了！！"

        # 削除の場合の処理
        elif action_type == "delete":
            # 主キーを利用し、見積情報のレコード取得
            estimate_data = Estimate.objects.get(id=estimate_id, lost_flag=0)
            # 各項目の値を格納
            estimate_data.lost_flag = 1
            # 採用フラグを0にする
            estimate_data.adoption_flag = 0
            # 見積情報のレコードを保存
            estimate_data.save()
            msg = "見積データ削除完了！！"

        if adoption_flag == 1:
            price_value_update(this_budget_id, now, operator)

        # コメント作成
        comment = "work_id : " + str(work_id) + "、業者 : " + vendor + ""

        # ログを新規登録
        Log(target='estimate', target_id=estimate_id, action=action_type, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def price_value_update(budget_id, now, operator):
    with connections['fmsdb'].cursor() as cursor:
        sql = """SELECT SUM(prospect_price) as sum_value """
        sql += """,SUM(estimate_price) as sum_estimate_price """
        sql += """FROM (fms_estimate LEFT JOIN fms_work on fms_estimate.work_id = fms_work.work_id and fms_estimate.lost_flag=0 and fms_work.lost_flag=0 and (fms_work.cancel_flag=0 or fms_work.cancel_flag is null)) """
        sql += """where fms_estimate.lost_flag=0 """
        sql += """AND adoption_flag = 1 """
        sql += """AND work_budget_id = """ + str(budget_id)

        res = cursor.execute(sql)
        result_sum = res.fetchall()

        if result_sum[0][0]:
            total_prospect_price_value = result_sum[0].sum_value
            total_estimate_price_value = result_sum[0].sum_estimate_price
        else:
            total_prospect_price_value = 0
            total_estimate_price_value = 0

    budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
    budget_data.application_price = total_estimate_price_value
    budget_data.budget_price = total_prospect_price_value
    budget_data.update_datetime = now
    budget_data.update_operator = operator

    if budget_data.plan_class_id == 'M':
        budget_data.mplan_adjustment_amount = budget_data.budget_price

    budget_data.save()
