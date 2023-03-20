import datetime
import traceback
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, BudgetRequiredFunction, AmountUnitMaster, Work
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, WorkSpecMEX, DisplayItemForHeatExchange
from fms.models import ExchangeTypeMaster, FreeSpecDetail, StepMaster, FreeSpecTemplate, FreeSpecDetailTemplate
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 詳細仕様(自由記入)表示処理
@require_POST
def free_function_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_work_id = int(request.POST["work_id"])
        this_step = int(request.POST['this_step'])
        work_id = target_work_id

        # 登録済のworkに対す処理
        if target_work_id != 0:
            # 現在のrev_noでのレコードを取得･･･sub_no順
            free_spec_data_list = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', lost_flag=0).order_by('sub_no')
            free_spec_list_num = free_spec_data_list.count()

            # 2次元配列を宣言･･･4×現在のrev_noでのレコード数
            free_spec_list = [[0 for i in range(4)] for j in range(free_spec_list_num)]

            # ページ番号は独立してカウント
            page_index = 0

            # 現在の情報に対し繰り返し処理
            for free_spec_data in free_spec_data_list:
                detail_change_flag = 0

                # 1つ古いレコードのrev_noを取得
                if free_spec_data.rev_no > 0:
                    old_work_rev_no = free_spec_data.rev_no - 1

                    # 1つ古いrev_noでのレコードがあれば、内容を比較して変更フラグを立てる
                    if FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', sub_no=free_spec_data.sub_no, rev_no=old_work_rev_no).count() > 0:
                        last_free_spec_data = FreeSpecDetail.objects.filter(
                            work_id=target_work_id, entry_class='計画', sub_no=free_spec_data.sub_no, rev_no=old_work_rev_no).all().order_by('-id')[0]
                        if last_free_spec_data.detail != free_spec_data.detail:
                            detail_change_flag = 1

                # 配列に「sub_no」、「詳細内容」、「変更有FL」、「ページ番号」を格納
                free_spec_list[page_index][0] = free_spec_data.sub_no
                free_spec_list[page_index][1] = free_spec_data.detail
                free_spec_list[page_index][2] = detail_change_flag
                free_spec_list[page_index][3] = page_index + 1
                page_index += 1

        # 登録済のworkがない場合の処理
        else:
            free_spec_list_num = 0
            free_spec_list = ""

        # データ編集機能要否判定
        work_spec_edit_action_num = 0
        # 対象stepで「work_spec」がデータ更新対象か確認
        work_spec_edit_action_num = work_spec_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='work_spec').count()

        # テンプレートリストの取得
        free_spec_template_lists = FreeSpecTemplate.objects.filter(lost_flag=0)

        data = {
            'work_id': work_id,
            'free_spec_list_num': free_spec_list_num,
            'free_spec_list': free_spec_list,
            'free_spec_template_lists': free_spec_template_lists
        }

        edit_flag = 0
        if work_spec_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, "fms/parts/work/work_spec/free/work_spec_free_edit.html", data)

        else:
            return render(request, "fms/parts/work/work_spec/free/work_spec_free_info.html", data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 詳細仕様(自由記入)登録･更新処理
@login_required
@require_POST
def free_function_data_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_work_id = int(request.POST["work_id"])
        sub_no = int(request.POST["sub_no"])
        detail = request.POST["detail"]
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        this_budget_id = int(request.POST["budget_id"])
        rev_no = int(request.POST["work_rev_no"])
        detail_len = len(detail)
        delete_flag = 0

        # 対象のwork_idで無効になっていないレコード数を取得
        free_spec_list_num = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', lost_flag=0).count()

        # 対象のwork_idで無効になっていないレコードがある場合
        if free_spec_list_num > 0:
            # 最終のsub_noを取得
            free_spec_data = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', lost_flag=0).order_by('-sub_no')[0]
            latest_sub_no = free_spec_data.sub_no

        # 対象のwork_idで無効になっていないレコードがない場合
        else:
            # 最終のsub_noを「0」に設定
            latest_sub_no = 0

        # 最新のsub_noを設定(=最終のsub_no+1)
        this_sub_no = latest_sub_no + 1

        # 更新処理の場合(新規の場合はsub_noは「0」)
        if sub_no != 0:
            # 作業中FLが「1」のレコード数の取得
            on_progress_work_num = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', sub_no=sub_no,
                                                                 lost_flag=0, entry_on_progress_flag=1).count()
            # 作業中FLが「0」(=完了)のレコード数の取得
            complete_entry_work_num = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', sub_no=sub_no,
                                                                    lost_flag=0, entry_on_progress_flag=0).count()
            # 完了のレコードがある場合
            if complete_entry_work_num > 0:
                # 完了のレコードを主キーが最新のもののレコードを取得
                free_spec_data = FreeSpecDetail.objects.filter(work_id=target_work_id, entry_class='計画', sub_no=sub_no, lost_flag=0,
                                                               entry_on_progress_flag=0).order_by('-id')[0]
                # latest_rev_no = free_spec_data.rev_no
                # 対象のレコードの無効FLを「1」(=無効化)
                free_spec_data.lost_flag = 1
                # 詳細仕様(自由記入)のレコードを保存
                free_spec_data.save()

            # 作業中のレコードがない場合
            if on_progress_work_num == 0:
                # 「work_id」、「sub_no」、「登録日時」、「登録者」を指定して新規レコード追加
                FreeSpecDetail(work_id=target_work_id, entry_class='計画', sub_no=sub_no, entry_datetime=now, entry_operator=operator).save()
                # 「登録日時」、「登録者」で上で新規登録したレコードを抽出
                free_spec_data = FreeSpecDetail.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーの値を取得
                free_spec_unique_id = free_spec_data.id
                # 主キーの値でレコードを取得
                free_spec_data = FreeSpecDetail.objects.get(id=free_spec_unique_id)
                # 各項目の値を格納
                free_spec_data.rev_no = rev_no
                free_spec_data.entry_on_progress_flag = 1
                free_spec_data.lost_flag = 0
                # 詳細仕様(自由記入)のレコードを保存
                free_spec_data.save()
            # 作業中のレコードがある場合
            else:
                # 「work_id」、「sub_no」、「作業中FLが"1"」で上で新規登録したレコードを抽出
                free_spec_data = FreeSpecDetail.objects.get(work_id=target_work_id, entry_class='計画', sub_no=sub_no, lost_flag=0,
                                                            entry_on_progress_flag=1)
                # 主キーの値を取得
                free_spec_unique_id = free_spec_data.id
        # 新規処理の場合(新規の場合はsub_noは「0」)
        else:
            # 「work_id」、「sub_no」、「登録日時」、「登録者」を指定してレコード抽出、あれば読み込み、
            # なければ新規レコード追加･･･ないはずなので追加のはず
            free_spec_data, created = FreeSpecDetail.objects.get_or_create(work_id=target_work_id, entry_class='計画', sub_no=this_sub_no,
                                                                           entry_datetime=now, entry_operator=operator)
            # 詳細仕様(自由記入)のレコードを保存
            free_spec_data.save()
            # 主キーの値を取得
            free_spec_unique_id = free_spec_data.id
            # sub_noの値を取得
            sub_no = free_spec_data.sub_no

        # 一時保存時の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
        # 作成完了時時の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step)
            step_name = step_data.step_name

        # 主キーの値でレコードを取得
        free_spec_data = FreeSpecDetail.objects.get(id=free_spec_unique_id)
        # 各項目の値を格納
        free_spec_data.work_id = target_work_id
        free_spec_data.sub_no = sub_no
        free_spec_data.rev_no = rev_no
        free_spec_data.detail = detail

        # 詳細が空欄の場合は、削除する
        if detail_len < 1:
            free_spec_data.lost_flag = 1
            delete_flag = 1
            msg = "削除完了！！"
            free_spec_data.entry_on_progress_flag = 0
        else:
            free_spec_data.lost_flag = 0
            msg = "更新完了！！"

            # 現在のstepと次のstepが同じかを判定
            if this_step != next_step:
                # 作業中のFLを「0」に
                free_spec_data.entry_on_progress_flag = 0
            else:
                # 作業中のFLを「1」に
                free_spec_data.entry_on_progress_flag = 1

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        free_spec_data.entry_class = entry_class
        # 詳細仕様(自由記入)のレコードを保存
        free_spec_data.save()

        # ログのコメントを作成
        comment = "サブNO : " + str(sub_no)

        # ログを新規登録
        Log(target='work_free_spec', target_id=target_work_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        ary = {
            'target_work_id': target_work_id,
            'delete_flag': delete_flag,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 詳細仕様(自由記入)テンプレート選択時処理
@login_required
@require_POST
def select_free_spec_template(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        template_id = int(request.POST["template_id"])

        # template_idでテンプレートの内容情報を取得
        free_spec_data = FreeSpecDetailTemplate.objects.filter(template_id=template_id, lost_flag=0).order_by('page')

        # 対象のtemplate_idのページ数をレコード数で取得
        page_num = FreeSpecDetailTemplate.objects.filter(template_id=template_id, lost_flag=0).count()

        # 2次元配列を宣言･･･3×現在のrev_noでのレコード数
        detail_lists = [0 for i in range(page_num)]

        i = 0

        for free_spec_data in free_spec_data:
            # 各項目の値を取得
            detail = free_spec_data.detail

            # 配列に「詳細内容」を格納
            detail_lists[i] = detail

            # iを「+1」
            i += 1

        ary = {
            'page_num': page_num,
            'detail_lists': detail_lists
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

