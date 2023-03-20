import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import Budget, MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Log, RequiredSpecification
from fms.models import DisplayRequiredItemForFunction, FunctionMaster
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 要求仕様情報表示処理
@login_required
@require_POST
def required_spec_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])
        present_step = int(request.POST["this_step"])

        # 各表示項目の値を設定
        rs_no = ""
        required_spec = ""
        required_spec_id = 0

        data = {
            'rs_no': rs_no,
            'required_spec': required_spec,
            'required_spec_id': required_spec_id,
            'div_id_name': request.POST['div_id_name'],
        }

        # データ編集機能要否判定
        required_spec_edit_action_num = 0
        # 対象stepで「required_specification」がデータ更新対象か確認
        required_spec_edit_action_num = required_spec_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='required_specification').count()

        edit_flag = 0
        if required_spec_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/budget/required_specification/required_specification_edit.html', data)

        else:
            return render(request, 'fms/parts/budget/required_specification/required_specification_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 要求仕様登録･更新処理
@login_required
@require_POST
def required_spec_entry(request):
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
        required_spec_id = int(request.POST["required_spec_id"])
        no_str = request.POST["no"]
        # 取得したnoの空欄処理(空欄時は「1」を設定)
        if no_str is not "":
            no = int(no_str)
        else:
            no = 1
        required_spec = request.POST["required_spec"]

        # 「budget_id」で登録済のデータ(最新の1件)を取得し、最終のrev_noを取得
        budget_rev_no = get_required_specification_rev_no(budget_id)

        # 新規登録時の処理
        if action_type == "add":
            action = "entry"

            # 「budget_id」で登録済のデータ(最新の1件)を取得し、最終のnoを取得
            this_no = get_required_specification_no(budget_id)

            # 「budget_id」、「no」、「登録日時」、「登録者」でレコードを抽出、あれば取得、なければ新規登録
            # ･･･ないはずなので新規登録
            required_specification_data, created = RequiredSpecification.objects.get_or_create(budget_id=budget_id,
                                                                                               no=this_no,
                                                                                               lost_flag=0)

            # 各項目の値を格納
            required_specification_data.budget_rev_no = budget_rev_no
            required_specification_data.required_spec = required_spec
            required_specification_data.entry_on_progress_flag = 1
            required_specification_data.entry_datetime = now
            required_specification_data.entry_operator = operator
            # 要求仕様のレコードを保存
            required_specification_data.save()
            # noの値を取得
            no = required_specification_data.no

            msg = "要求仕様を登録しました！！"

        # 更新時の処理
        elif action_type == "update":
            action = "update"

            # 作業中の要求仕様のレコード件数を取得
            on_progress_required_specification_num = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                          no=no,
                                                                                          lost_flag=0,
                                                                                          entry_on_progress_flag=1).count()

            # 完了（作業中でない）の要求仕様のレコード件数を取得
            complete_entry_required_specification_num = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                             no=no,
                                                                                             lost_flag=0,
                                                                                             entry_on_progress_flag=0).count()

            # 完了の要求仕様のレコードがある場合の処理
            if complete_entry_required_specification_num > 0:
                # 完了の要求仕様のデータ(最新のもの)を取得
                required_specification_data = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                   no=no,
                                                                                   lost_flag=0,
                                                                                   entry_on_progress_flag=0
                                                                                   ).order_by('-id')[0]
                # レコードの無効化(lost_flag = 1)
                required_specification_data.lost_flag = 1
                # 要求仕様のレコードを保存
                required_specification_data.save()

            # 作業中の要求仕様のレコードがない場合の処理
            if on_progress_required_specification_num == 0:
                if complete_entry_required_specification_num == 0:
                    msg = "登録済みの要求仕様がありません！\n先に要求仕様を登録してください！！"
                    ary = {
                        'required_spec_id': 0,
                        'no': "",
                        'msg': msg
                    }
                    return JsonResponse(ary)
                old_complete_entry_required_specification = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                                 no=no,
                                                                                                 lost_flag=1,
                                                                                                 entry_on_progress_flag=0
                                                                                                 ).order_by('-id')[0]
                old_entry_datetime = old_complete_entry_required_specification.entry_datetime
                old_entry_operator = old_complete_entry_required_specification.entry_operator
                # 「budget_id」、「budget_rev_no」、「no」、「登録日時」、「登録者」、「更新日時」、「更新者」の値で要求機能に新規登録
                RequiredSpecification(budget_id=budget_id,
                                      budget_rev_no=budget_rev_no,
                                      no=no,
                                      entry_datetime=old_entry_datetime,
                                      entry_operator=old_entry_operator,
                                      update_datetime=now,
                                      update_operator=operator
                                      ).save()
                # 「更新日時」、「更新者」で登録したレコードを抽出
                required_specification_data = RequiredSpecification.objects.get(update_datetime=now,
                                                                                update_operator=operator
                                                                                )
                # 主キーの値を取得
                required_specification_unique_id = required_specification_data.id
                # 主キーの値で登録したレコードを抽出
                required_specification_data = RequiredSpecification.objects.get(id=required_specification_unique_id)
                # 各項目の値を格納
                required_specification_data.entry_on_progress_flag = 1
                required_specification_data.lost_flag = 0
                # 要求仕様のレコードを保存
                required_specification_data.save()

            # 作業中の要求仕様のレコードがある場合の処理
            else:
                # 「budget_id」、「budget_rev_no」、「no」、「Lost_flag」、「entry_on_progress_flag」でレコードを抽出
                required_specification_data = RequiredSpecification.objects.get(budget_id=budget_id,
                                                                                no=no,
                                                                                lost_flag=0,
                                                                                entry_on_progress_flag=1)
                # 各項目の値を格納
                required_specification_data.budget_rev_no = budget_rev_no
                required_specification_data.update_datetime = now
                required_specification_data.update_operator = operator
                # 要求仕様のレコードを保存
                required_specification_data.save()

            msg = "要求仕様を更新しました！！"

        # 変数に値を設定
        this_no = no

        # 「budget_id」、「budget_rev_no」、「no」、「lost_flag」でレコードを抽出
        required_specification_data = RequiredSpecification.objects.get(budget_id=budget_id,
                                                                        budget_rev_no=budget_rev_no,
                                                                        no=no,
                                                                        lost_flag=0)
        # 主キーの値を取得
        required_spec_id = required_specification_data.id
        # 各項目の値を格納･･･空欄処理、数値化処理を含む
        required_specification_data.required_spec = required_spec

        # 要求仕様のレコードを保存
        required_specification_data.save()

        # 選択した要求仕様No以外の仕様もrev_no変更
        old_required_specification_list = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                               lost_flag=0
                                                                               ).exclude(no=no).exclude(entry_on_progress_flag=1)

        for old_required_specification_list_item in old_required_specification_list:

            RequiredSpecification(budget_id=budget_id,
                                  budget_rev_no=budget_rev_no,
                                  no=old_required_specification_list_item.no,
                                  required_spec=old_required_specification_list_item.required_spec,
                                  lost_flag=0,
                                  entry_on_progress_flag=1,
                                  entry_datetime=old_required_specification_list_item.entry_datetime,
                                  entry_operator=old_required_specification_list_item.entry_operator,
                                  update_datetime=now,
                                  update_operator=operator
                                  ).save()

            old_required_specification_list_item.lost_flag = 1
            old_required_specification_list_item.update_datetime = now
            old_required_specification_list_item.update_operator = operator

            old_required_specification_list_item.save()

        # コメント作成
        comment = "要求仕様NO：" + str(this_no)

        # ログを新規登録
        Log(target='required_specification', target_id=this_budget_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=budget_id).save()

        ary = {
            'required_spec_id': required_spec_id,
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
def required_spec_delete(request):
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
        required_spec_id = int(request.POST["required_spec_id"])

        # 主キーの値で要求仕様のレコードを抽出
        required_specification_data = RequiredSpecification.objects.get(id=required_spec_id)
        # レコードの無効化(lost_flag = 1)
        required_specification_data.lost_flag = 1
        required_specification_data.update_datetime = now
        required_specification_data.update_operator = operator
        # 各項目の値取得･･･ログのため
        budget_id = required_specification_data.budget_id
        this_no = required_specification_data.no
        this_budget_id = required_specification_data.budget_id
        action = "delete"

        # 要求仕様のレコードを保存
        required_specification_data.save()

        # コメント作成
        comment = "要求仕様NO：" + str(this_no)

        # ログを新規登録
        Log(target='required_specification', target_id=this_budget_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=budget_id).save()

        msg = "削除しました！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の要求仕様の表示処理
@require_POST
def required_spec_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id_str = request.POST['target_id']
        target_id = int(target_id_str)
        present_step = int(request.POST["this_step"])

        # 対象予算idに対する登録済要求機能のレコード数取得
        required_specification_lists_num = RequiredSpecification.objects.filter(budget_id=target_id, lost_flag=0).count()

        # 対象予算idに対する登録済要求機能のデータ取得
        required_specification_lists = RequiredSpecification.objects.filter(budget_id=target_id, lost_flag=0).order_by('no')

        # データ編集機能要否判定
        required_spec_edit_action_num = 0
        # 対象stepで「required_specification」がデータ更新対象か確認
        required_spec_edit_action_num = required_spec_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='required_specification').count()

        select_pb_disp_flag = 0
        if required_spec_edit_action_num > 0:
            select_pb_disp_flag = 1

        data = {
            'required_specification_lists': required_specification_lists,
            'required_specification_lists_num': required_specification_lists_num,
            'select_pb_disp_flag': select_pb_disp_flag
        }

        return render(request, 'fms/parts/budget/required_specification/required_specification_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済要求仕様選択時処理
@require_POST
def required_spec_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        required_spec_id = int(request.POST['required_spec_id'])

        # 主キーでレコードを抽出
        required_specification_data = RequiredSpecification.objects.get(id=required_spec_id)
        # 各項目の値を取得
        no = required_specification_data.no
        required_spec = required_specification_data.required_spec

        ary = {
            'required_spec_id': required_spec_id,
            'no': no,
            'required_spec': required_spec
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def get_required_specification_rev_no(budget_id):
    # 該当の予算idで作業中FLがONのレコード数をカウント
    on_progress_required_specification_num = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                  entry_on_progress_flag=1).count()
    # 該当の予算idで(入力)完了FLがONのレコード数をカウント
    complete_entry_required_specification_num = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                                     entry_on_progress_flag=0).count()
    # 完了FLがONの件数が「0」より多い場合
    if complete_entry_required_specification_num > 0:
        # 該当の予算idで、作業中FLがONのレコードを抽出し、rev_noが最新のレコードを抽出
        required_specification_data = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                           entry_on_progress_flag=0
                                                                           ).order_by('-budget_rev_no')[0]
        # 該当の予算idで最終のrev_noを取得
        budget_rev_no = required_specification_data.budget_rev_no
    else:
        budget_rev_no = -1
    # 該当の予算idで作業中FLがONのレコード数が「0」の場合
    if on_progress_required_specification_num == 0:
        budget_rev_no += 1
    else:
        required_specification_data = RequiredSpecification.objects.filter(budget_id=budget_id,
                                                                           entry_on_progress_flag=1
                                                                           ).order_by('-budget_rev_no')[0]
        budget_rev_no = required_specification_data.budget_rev_no

    return budget_rev_no


def get_required_specification_no(budget_id):
    # 「budget_id」で登録済のレコード数を取得(削除してもNoは詰めないのでlost_flagを条件に含めない)
    required_specification_num = RequiredSpecification.objects.filter(budget_id=budget_id).count()
    # 登録済のレコードがある場合
    if required_specification_num > 0:
        # 「budget_id」で登録済のデータ(最新の1件)を取得し、最終のnoを取得
        required_specification_data = RequiredSpecification.objects.filter(budget_id=budget_id).order_by('-no')[0]
        latest_no = required_specification_data.no
    # 登録済のレコードがない場合
    else:
        # 最終のsub_noに「0」を設定
        latest_no = 0

    # 今回のnoを設定(最終のno+1)
    this_no = latest_no + 1

    return this_no
