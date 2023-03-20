import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import RegulationMaster, SuppliesMaster
from fms.models import Supplies, WorkLaw
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, Estimate, Discount, DataEntryStepMaster, Log
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 工事関連法令･支給品情報表示処理
@require_POST
def work_law_supplies_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        present_step = int(request.POST["this_step"])
        level5_step_id = int(request.POST["level5_step_id"])
        div_id_name = request.POST["div_id_name"]

        # 法令マスタより法律名に絞って関係法令情報(一覧)取得
        law_master_lists = RegulationMaster.objects.filter(regulation_cd__contains="000", lost_flag=0)

        # 支給品マスタより支給品情報(一覧)取得
        supplies_master_lists = SuppliesMaster.objects.filter(lost_flag=0).order_by('display_order')

        data = {
            'work_id': work_id,
            'law_master_lists': law_master_lists,
            'supplies_master_lists': supplies_master_lists,
            'div_id_name': div_id_name,
        }

        # データ編集機能要否判定
        work_law_edit_action_num = 0
        # 対象stepで「work_law」がデータ更新対象か確認
        work_law_edit_action_num = work_law_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='work_law').count()
        # 対象stepで「work_supplies」がデータ更新対象か確認
        work_law_edit_action_num = work_law_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='work_supplies').count()

        edit_flag = 0

        if level5_step_id == 920000000 or level5_step_id == 212001000:
            work_law_edit_action_num = 0

        if work_law_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/work/law_supplies/law_supplies_edit.html', data)

        else:
            return render(request, 'fms/parts/work/law_supplies/law_supplies_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise



# 登録済関連法令表示処理
@require_POST
def get_work_law_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])
        present_step = int(request.POST["this_step"])

        # 現在のstepからデータ登録タイミングを判定
        if present_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 登録済の関連法令のレコード数を取得
        work_law_lists_num = WorkLaw.objects.filter(work_id=work_id, lost_flag=0, entry_class=entry_class).count()

        # 登録済の関連法令のレコードがある場合
        if work_law_lists_num > 0:
            # 登録済の関連法令の情報を取得
            work_law_lists = WorkLaw.objects.filter(work_id=work_id, lost_flag=0, entry_class=entry_class).all()

        else:
            work_law_lists = ""

        data = {
            'work_law_lists_num': work_law_lists_num,
            'work_law_lists': work_law_lists,
            'select_pb_disp_flag': select_pb_disp_flag
        }

        return render(request, 'fms/parts/work/law_supplies/work_law_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済支給品表示処理
@require_POST
def get_work_supplies_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])
        present_step = int(request.POST["this_step"])

        # 現在のstepからデータ登録タイミングを判定
        if present_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 登録済の支給品のレコード数を取得
        work_supplies_lists_num = Supplies.objects.filter(work_id=work_id, lost_flag=0, entry_class=entry_class).count()

        # 登録済の支給品のレコードがある場合
        if work_supplies_lists_num > 0:
            # 登録済の支給品の情報を取得
            work_supplies_lists = Supplies.objects.filter(work_id=work_id, lost_flag=0, entry_class=entry_class).all()

        else:
            work_supplies_lists = ""

        data = {
            'work_supplies_lists_num': work_supplies_lists_num,
            'work_supplies_lists': work_supplies_lists,
            'select_pb_disp_flag': select_pb_disp_flag
        }

        return render(request, 'fms/parts/work/law_supplies/work_supplies_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 法令マスタから選択したときの処理
@require_POST
def select_work_law(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_law_master_id = request.POST["work_law_cd"]

        # 選択した法令cdで対象のレコードを抽出
        regulation_master_data = RegulationMaster.objects.get(regulation_cd=work_law_master_id)
        # 各項目の値を取得
        regulation_name = regulation_master_data.regulation_name
        regulation_cd = regulation_master_data.regulation_cd
        display_order = regulation_master_data.display_order
        work_law_id = 0

        data = {
            'regulation_name': regulation_name,
            'regulation_cd': regulation_cd,
            'display_order': display_order,
            'work_law_id': work_law_id,
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係法令登録･更新処理
@login_required
@require_POST
def work_law_entry(request):
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
        # work_law_id = int(request.POST["work_law_id"]) 2021/02/08 int変換エラー発症&使用していない変数のため、コメントアウト
        work_law_name = request.POST["work_law_name"]
        # display_order = int(request.POST["display_order"])
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 対象の工事id、rev_no、法令名での登録済関係法令レコードを取得･･･あれば読み込み、なければ新規登録
        work_law_data, created = WorkLaw.objects.get_or_create(work_id=work_id, rev_no=rev_no, law_name=work_law_name, entry_class=entry_class)
        # 各項目の値を格納
        work_law_data.work_id = work_id
        work_law_data.rev_no = rev_no
        work_law_data.entry_class = entry_class
        work_law_data.lost_flag = 0
        work_law_data.entry_on_progress_flag = 1
        # 新規登録時の場合の処理
        if action_type == "add":
            work_law_data.entry_datetime = now
            work_law_data.entry_operator = operator
            msg = "適用法規データ新規登録完了！！"
        # 更新時の場合の処理
        else:
            work_law_data.update_datetime = now
            work_law_data.update_operator = operator
            msg = "適用法規データ更新完了！！"
        # 工事関係法令のレコード保存
        work_law_data.save()
        # 主キーの値を取得
        worl_law_id = work_law_data.id

        # コメント作成
        comment = "work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、適用法規名 : " + work_law_name + ""

        # ログを新規登録
        Log(target='worklaw', target_id=worl_law_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係法令削除処理
@login_required
@require_POST
def work_law_delete(request):
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
        rev_no = int(request.POST["rev_no"])
        work_law_id = int(request.POST["work_law_id"])
        work_law_name = request.POST["work_law_name"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 主キーの値で工事関係法令の対象レコードを抽出
        work_law_data = WorkLaw.objects.get(id=work_law_id)
        # 対象レコードを無効化(lost_flag = 1)
        work_law_data.lost_flag = 1
        # 工事関係法令のレコード保存
        work_law_data.save()

        msg = "適用法規データ削除完了！！"
        action_type = "delete"

        # コメント作成
        comment = "work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、適用法規名 : " + work_law_name + ""

        # ログを新規登録
        Log(target='worklaw', target_id=work_law_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 関係法令詳細情報表示処理
@require_POST
def work_law_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_law_id = int(request.POST["work_law_id"])

        # 主キーの値で工事関係法令の対象レコードを抽出
        work_law_data = WorkLaw.objects.get(id=work_law_id)
        # 各項目の値を取得
        work_law_name = work_law_data.law_name
        work_law_id = work_law_data.id

        data = {
            'work_law_name': work_law_name,
            'work_law_id': work_law_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 支給品マスタから選択したときの処理
@require_POST
def select_work_supplies(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_supplies_id = int(request.POST["work_supplies_id"])

        # 主キーの値で工事関係法令の対象レコードを抽出
        supplies_master_data = SuppliesMaster.objects.get(id=work_supplies_id)
        # 各項目の値を取得
        supplies_name = supplies_master_data.supplies_name
        master_supplies_id = supplies_master_data.id
        display_order = supplies_master_data.display_order
        work_supplies_id = 0

        data = {
            'supplies_name': supplies_name,
            'master_supplies_id': master_supplies_id,
            'display_order': display_order,
            'work_supplies_id': work_supplies_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 支給品登録･更新処理
@login_required
@require_POST
def work_supplies_entry(request):
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
        # work_supplies_id = int(request.POST["work_supplies_id"]) 使用していない変数なので、コメントアウト（エラー発生）
        work_supplies_name = request.POST["work_supplies_name"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 対象の工事id、rev_no、支給品名での登録済支給品レコードを取得･･･あれば読み込み、なければ新規登録
        work_supplies_data, created = Supplies.objects.get_or_create(work_id=work_id, entry_class=entry_class, rev_no=rev_no, supplies_name=work_supplies_name)
        # 各項目の値を格納
        work_supplies_data.work_id = work_id
        work_supplies_data.rev_no = rev_no
        work_supplies_data.entry_class = entry_class
        work_supplies_data.lost_flag = 0
        work_supplies_data.entry_on_progress_flag = 1
        # 新規登録時の場合の処理
        if action_type == "add":
            work_supplies_data.entry_datetime = now
            work_supplies_data.entry_operator = operator
            msg = "支給品データ新規登録完了！！"
        # 更新時の場合の処理
        else:
            work_supplies_data.update_datetime = now
            work_supplies_data.update_operator = operator
            msg = "支給品データ更新完了！！"

        # 工事関係支給品のレコード保存
        work_supplies_data.save()
        # 主キーの値を取得
        work_supplies_id = work_supplies_data.id

        # コメント作成
        comment = "work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、支給品名 : " + work_supplies_name + ""

        # ログを新規登録
        Log(target='supplies', target_id=work_supplies_id, action=action_type, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 支給品削除処理
@login_required
@require_POST
def work_supplies_delete(request):
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
        rev_no = int(request.POST["rev_no"])
        work_supplies_id = int(request.POST["work_supplies_id"])
        work_supplies_name = request.POST["work_supplies_name"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 主キーの値で工事関係支給品の対象レコードを抽出
        work_supplies_data = Supplies.objects.get(id=work_supplies_id)
        # 対象レコードを無効化(lost_flag = 1)
        work_supplies_data.lost_flag = 1

        # 工事関係支給品のレコード保存
        work_supplies_data.save()

        msg = "支給品データ削除完了！！"
        action_type = "delete"

        # コメント作成
        comment = "work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、支給品名 : " + work_supplies_name + ""

        # ログを新規登録
        Log(target='supplies', target_id=work_supplies_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 支給品詳細情報表示処理
@require_POST
def work_supplies_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_supplies_id = int(request.POST["work_supplies_id"])

        # 主キーの値で工事関係支給品の対象レコードを抽出
        work_supplies_data = Supplies.objects.get(id=work_supplies_id)
        # 各項目の値を取得
        work_supplies_name = work_supplies_data.supplies_name
        work_supplies_id = work_supplies_data.id

        data = {
            'work_supplies_name': work_supplies_name,
            'work_supplies_id': work_supplies_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


