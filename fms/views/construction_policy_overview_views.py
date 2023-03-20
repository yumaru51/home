import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Log, ConstructionPolicyOverview
from fms.models import DisplayRequiredItemForFunction, FunctionMaster
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 工事方針概要情報表示処理
@login_required
@require_POST
def policy_overview_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])
        present_step = int(request.POST["this_step"])

        # 各表示項目の値を設定
        rs_no = ""
        if ConstructionPolicyOverview.objects.filter(budget_id=budget_id, lost_flag=0).count() > 0:
            policy = ""
        else:
            policy = "・工事内容区分（仕様書毎に記載）\n　購入品(機械)：\n　購入品(計装)：\n　機械工事：\n　土建工事：\n　計装工事：\n　電気工事：\n\n・備考　\n\n・届出（該当法令、事前・事後届け出について）\n　■不要\n　□要"
        overview = ""
        construction_policy_id = 0

        # データ編集機能要否判定
        policy_overview_edit_action_num = 0
        # 対象stepで「required_specification」がデータ更新対象か確認
        policy_overview_edit_action_num = policy_overview_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='policy_overview').count()

        edit_flag = 0
        if policy_overview_edit_action_num > 0:
            edit_flag = 1

        data = {
            'rs_no': rs_no,
            'policy': policy,
            'overview': overview,
            'construction_policy_id': construction_policy_id,
            'div_id_name': request.POST['div_id_name'],
            'edit_flag': edit_flag,
        }

        return render(request, 'fms/parts/budget/construction_policy_overview/construction_policy_overview_edit.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise



# 工事方針概要登録･更新処理
@login_required
@require_POST
def policy_overview_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        action_type = request.POST["action_type"]
        budget_id = int(request.POST["budget_id"])
        this_budget_id = budget_id
        budget_rev_no = int(request.POST["budget_rev_no"])
        construction_policy_id = int(request.POST["construction_policy_id"])
        rs_no = request.POST["rs_no"]
        no_str = request.POST["no"]
        # 取得したnoの空欄処理(空欄時は「1」を設定)
        if no_str is not "":
            no = int(no_str)
        else:
            no = 1
        policy = request.POST["policy"]
        overview = request.POST["overview"]

        # 新規登録時の処理
        if action_type == "add":
            action = "entry"

            # 「budget_id」、で登録済のレコード数を取得（削除されたNoと重複しないように、lost_flag=1のNoも含めて最大値を取得する）
            policy_overview_data_num = ConstructionPolicyOverview.objects.filter(budget_id=budget_id).count()
            # 登録済のレコードがある場合
            if policy_overview_data_num > 0:
                # 「budget_id」で登録済のデータ(最新の1件)を取得し、最終のnoを取得
                policy_overview_data = ConstructionPolicyOverview.objects.filter(budget_id=budget_id).order_by('-no')[0]
                latest_no = policy_overview_data.no
            # 登録済のレコードがない場合
            else:
                # 最終のsub_noに「0」を設定
                latest_no = 0

            # 今回のnoを設定(最終のno+1)
            this_no = latest_no + 1

            # 「budget_id」、「no」、「登録日時」、「登録者」でレコードを新規登録
            policy_overview_data, created = ConstructionPolicyOverview.objects.get_or_create(
                budget_id=budget_id, no=this_no, entry_datetime=now, entry_operator=operator)

            # 各項目の値を格納
            policy_overview_data.required_spec_no = rs_no
            policy_overview_data.policy = policy
            policy_overview_data.budget_rev_no = 0
            policy_overview_data.entry_on_progress_flag = 1
            policy_overview_data.lost_flag = 0
            policy_overview_data.overview = overview
            # 工事方針概要のレコードを保存
            policy_overview_data.save()
            # construction_policy_id = policy_overview_data.id
            msg = "工事方針･概要を登録しました！！"

        # 更新時の処理
        elif action_type == "update":
            action = "update"
            this_no = no

            # 該当NOのレコードを取得
            policy_overview_data = ConstructionPolicyOverview.objects.get(budget_id=budget_id, lost_flag=0, no=this_no)

            if policy_overview_data.entry_on_progress_flag == 0:
                # 旧リビジョンデータを保存
                policy_overview_data.lost_flag = 1
                policy_overview_data.save()

                # 新リビジョンのデータを保存(idをNoneにすることで、新規レコードを保存)
                policy_overview_data.id = None
                policy_overview_data.budget_rev_no = policy_overview_data.budget_rev_no + 1
                policy_overview_data.lost_flag = 0
                policy_overview_data.entry_datetime = now
                policy_overview_data.entry_operator = operator
                policy_overview_data.update_datetime = None
                policy_overview_data.update_operator = None
            else:
                policy_overview_data.update_datetime = now
                policy_overview_data.update_operator = operator

            policy_overview_data.entry_on_progress_flag = 1
            policy_overview_data.required_spec_no = rs_no
            policy_overview_data.policy = policy
            policy_overview_data.overview = overview
            policy_overview_data.save()
            # construction_policy_id = policy_overview_data.id
            msg = "工事方針･概要を更新しました！！"

        # コメント作成
        comment = "工事方針･概要NO：" + str(this_no)

        # ログを新規登録
        Log(target='construction_policy_overview', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        ary = {
            # 'construction_policy_id': construction_policy_id,
            'no': this_no,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 要求仕様削除処理
@login_required
@require_POST
def policy_overview_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        construction_policy_id = int(request.POST["construction_policy_id"])

        # 主キーの値で工事方針概要のレコードを抽出
        policy_overview_data = ConstructionPolicyOverview.objects.get(id=construction_policy_id)
        # レコードの無効化(lost_flag = 1)
        policy_overview_data.lost_flag = 1
        # 各項目の値取得･･･ログのため
        budget_id = policy_overview_data.budget_id
        this_no = policy_overview_data.no
        this_budget_id = policy_overview_data.budget_id
        action = "delete"

        # 工事方針概要のレコードを保存
        policy_overview_data.save()

        # コメント作成
        comment = "工事方針･概要NO：" + str(this_no)

        # ログを新規登録
        Log(target='construction_policy_overview', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        msg = "削除しました！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の工事方針概要の表示処理
@require_POST
def policy_overview_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id_str = request.POST['target_id']
        target_id = int(target_id_str)
        present_step = int(request.POST["this_step"])

        # 対象予算idに対する登録済工事方針概要のレコード数取得
        policy_overview_lists_num = ConstructionPolicyOverview.objects.filter(budget_id=target_id, lost_flag=0).count()

        # 対象予算idに対する登録済工事方針概要のデータ取得
        policy_overview_lists = ConstructionPolicyOverview.objects.filter(budget_id=target_id, lost_flag=0).order_by('no')

        # データ編集機能要否判定
        policy_overview_edit_action_num = 0
        # 対象stepで「required_specification」がデータ更新対象か確認
        policy_overview_edit_action_num = policy_overview_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='construction_policy_overview').count()

        select_pb_disp_flag = 1
        if policy_overview_edit_action_num > 0:
            select_pb_disp_flag = 1

        data = {
            'policy_overview_lists': policy_overview_lists,
            'policy_overview_lists_num': policy_overview_lists_num,
            'select_pb_disp_flag': select_pb_disp_flag
        }

        return render(request, 'fms/parts/budget/construction_policy_overview/construction_policy_overview_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済工事方針概要選択時処理
@require_POST
def policy_overview_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        construction_policy_id = int(request.POST['construction_policy_id'])

        # 主キーでレコードを抽出
        policy_overview_data = ConstructionPolicyOverview.objects.get(id=construction_policy_id)
        # 各項目の値を取得
        no = policy_overview_data.no
        required_spec_no = policy_overview_data.required_spec_no
        policy = policy_overview_data.policy
        overview = policy_overview_data.overview

        ary = {
            'construction_policy_id': construction_policy_id,
            'no': no,
            'required_spec_no': required_spec_no,
            'policy': policy,
            'overview': overview
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事方針概要編集中フラグリセット処理
def policy_overview_reset_progress_flag(budget_id):
    try:
        policy_overview_data_list = ConstructionPolicyOverview.objects.filter(budget_id=budget_id, lost_flag=0).all()
        for policy_overview_data in policy_overview_data_list:
            policy_overview_data.entry_on_progress_flag = 0
            policy_overview_data.save()

    except Exception:
        output_log_error(traceback.format_exc())
        raise




