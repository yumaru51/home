import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import SubmissionDocumentMaster, SubmissionDocument
from fms.models import Budget, Progress, Log, BudgetMaterial, BudgetRequiredFunction, AmountUnitMaster
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, Estimate, Discount, DataEntryStepMaster
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# マスタの提出書類一覧から選択された時の処理
# @login_required
@require_POST
def select_document(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        document_master_id = int(request.POST["document_master_id"])

        # 提出書類マスタから該当のレコード取得
        document_master_data = SubmissionDocumentMaster.objects.get(id=document_master_id, lost_flag=0)
        # 各項目の値を取得
        document_name = document_master_data.document_name
        default_submission_deadline = document_master_data.default_submission_deadline
        default_number_of_copies = document_master_data.default_number_of_copies
        display_order = document_master_data.display_order
        # document_id を「0」に設定･･･まだ未登録のため
        document_id = 0

        data = {
            'document_name': document_name,
            'default_submission_deadline': default_submission_deadline,
            'default_number_of_copies': default_number_of_copies,
            'display_order': display_order,
            'document_id': document_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済提出書類一覧から選択された時の処理
@require_POST
def document_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        document_id = int(request.POST["document_id"])

        # 登録済提出書類データから該当のレコード取得
        document_data = SubmissionDocument.objects.get(id=document_id, lost_flag=0)
        # 各項目の値を取得
        document_name = document_data.document_name
        submission_deadline = document_data.submission_deadline
        number_of_copies = document_data.number_of_copies
        display_order = document_data.display_order
        document_id = document_data.id

        data = {
            'document_name': document_name,
            'submission_deadline': submission_deadline,
            'number_of_copies': number_of_copies,
            'display_order': display_order,
            'document_id': document_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 提出書類内容表示処理
@require_POST
def document_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        level5_step_id = int(request.POST["level5_step_id"])
        present_step = int(request.POST["this_step"])
        open_new_tab_flag = int(request.POST["open_new_tab_flag"])
        div_id_name =  request.POST["div_id_name"]

        # 提出書類マスタデータを取得
        document_master_lists = SubmissionDocumentMaster.objects.filter(lost_flag=0).order_by('display_order')

        data = {
            'work_id': work_id,
            'document_master_lists': document_master_lists,
            'div_id_name': div_id_name,
        }

        # データ編集機能要否判定
        document_edit_action_num = 0
        # 対象stepで「document」がデータ更新対象か確認
        document_edit_action_num = document_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                                 target_table='document',
                                                                                                 lost_flag=0).count()
        if level5_step_id == 920000000 or level5_step_id == 212001000:
            document_edit_action_num = 0

        edit_flag = 0
        if document_edit_action_num > 0 and open_new_tab_flag == 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/work/document/document_edit.html', data)

        else:
            return render(request, 'fms/parts/work/document/document_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の提出書類一覧の表示処理
@require_POST
def get_document_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        work_id = int(request.POST["work_id"])
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])
        present_step = int(request.POST["this_step"])
        target = request.POST["target"]

        if target == 'phenomenon':
            entry_class = "故障対応"
        else:
            # 現在のstepからデータ登録タイミングを判定
            if present_step < 200000000:
                entry_class = "計画"
            else:
                entry_class = "実行"

        # 登録済の提出書類の数をカウント
        document_lists_num = SubmissionDocument.objects.filter(work_id=work_id, lost_flag=0,
                                                               entry_class=entry_class).count()

        # 登録済の提出書類がある場合の処理
        if document_lists_num > 0:
            # 登録済の提出書類一覧を取得
            document_lists = SubmissionDocument.objects.filter(work_id=work_id, lost_flag=0,
                                                               entry_class=entry_class).all().order_by('display_order')

        else:
            document_lists = ""

        data = {
            'document_lists_num': document_lists_num,
            'document_lists': document_lists,
            'select_pb_disp_flag': select_pb_disp_flag
        }

        return render(request, 'fms/parts/work/document/document_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 提出書類を登録･更新処理
@login_required
@require_POST
def document_entry(request):
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
        # document_id = int(request.POST["document_id"])  # 2021/02/12 使用してない変数なので、コメントアウト ueda
        document_name = request.POST["document_name"]
        submission_deadline = request.POST["submission_deadline"]
        number_of_copies = int(request.POST["number_of_copies"])
        if request.POST["display_order"] is not "":
            display_order = int(request.POST["display_order"])
        else:
            display_order = 99

        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        target = request.POST["target"]

        if target == 'phenomenon':
            entry_class = "故障対応"
        else:
            # 現在のstepからデータ登録タイミングを判定
            if this_step < 200000000:
                entry_class = "計画"
            else:
                entry_class = "実行"

        # 「work_id」、「rev_no」、「提出書類名」で登録済の提出書類を抽出･･･あれば読み込み、なければ新規登録
        document_data, created = SubmissionDocument.objects.get_or_create(work_id=work_id, rev_no=rev_no,
                                                                          document_name=document_name, entry_class=entry_class, lost_flag=0)
        # 各項目を格納
        document_data.work_id = work_id
        document_data.submission_deadline = submission_deadline
        document_data.number_of_copies = number_of_copies
        document_data.display_order = display_order
        document_data.entry_class = entry_class
        document_data.lost_flag = 0
        document_data.entry_on_progress_flag = 1
        # 新規追加の場合の処理
        if action_type == "add":
            document_data.entry_datetime = now
            document_data.entry_operator = operator
            msg = "提出書類データ新規登録完了！！"
        # 更新の場合の処理
        else:
            document_data.update_datetime = now
            document_data.update_operator = operator
            msg = "提出書類データ更新完了！！"
        # 提出書類のレコードを保存
        document_data.save()
        # 提出書類の主キー値取得
        document_id = document_data.id

        # ログのコメント作成
        comment = "work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、書類名 : " + document_name + ""

        # ログを新規登録
        Log(target='submissiondocument', target_id=document_id, action=action_type, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 提出書類を削除処理
@login_required
@require_POST
def document_delete(request):
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
        document_id = int(request.POST["document_id"])
        document_name = request.POST["document_name"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 対象のレコードを抽出
        document_data = SubmissionDocument.objects.get(id=document_id, lost_flag=0)
        # 項目に値格納･･･無効FLを「1」に
        document_data.lost_flag = 1
        # 提出書類のレコードを保存
        document_data.save()

        msg = "提出書類データ削除完了！！"

        # ログのコメント作成
        action_type = "delete"
        comment = "work_id : " + str(work_id) + "、書類名 : " + document_name + ""

        # ログを新規登録
        Log(target='submissiondocument', target_id=document_id, action=action_type, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
