import datetime
import traceback
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import make_aware
from django.views.decorators.http import require_POST

from fms.models import Phenomenon, DataEntryStepMaster, MaintenanceInspectionAcceptance, StepMaster, Log, UserAttribute, \
    Progress
from fms.views import date_to_hyphen
from fms.views.common_def_views import output_log_exception


# 詳細画面の表示
from fms.views.common_views import blank_to_None


@login_required
@require_POST
def maintenance_inspection_acceptance_info(request):
    try:
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'
        this_step = int(request.POST['this_step'])

        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        phenomenon_id = 0
        inspection_acceptance_data = ''
        progress_end_flag = 0

        if phenomenon_unique_id != 0:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id

        # 検収情報が保存済かどうか判定
        if phenomenon_id != 0 and MaintenanceInspectionAcceptance.objects.filter(
                phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            inspection_acceptance_data = MaintenanceInspectionAcceptance.objects.filter(
                phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id').first()

        # 復旧確認側のProgressが、工程完了しているか確認
        progress_data_list = Progress.objects.filter(target_id=phenomenon_id,
                                                     target='phenomenon', present_step=232009901)
        if progress_data_list.count() > 0:
            progress_end_flag = 1

        data = {
            'action_button_id': action_button_id,
            'div_id_name': div_id_name,
            'phenomenon_unique_id': phenomenon_unique_id,
            'phenomenon_id': phenomenon_id,
            'inspection_acceptance_data': inspection_acceptance_data,
            'progress_end_flag': progress_end_flag,
        }

        if DataEntryStepMaster.objects.filter(step_id=this_step, target_table='maintenance_inspection_acceptance',
                                              lost_flag=0).count() > 0:
            template_file = 'fms/parts/maintenance/maintenance_inspection_acceptance' \
                            '/maintenance_inspection_acceptance_edit.html '
        else:
            template_file = 'fms/parts/maintenance/maintenance_inspection_acceptance' \
                            '/maintenance_inspection_acceptance_info.html '

        return render(request, template_file, data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# レコード保存
@login_required
@require_POST
def maintenance_inspection_acceptance_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        this_step = int(request.POST['this_step'])
        next_step = int(request.POST['next_step'])
        user_attribute_id = int(request.POST['user_attribute_id'])
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])

        # 入力情報は連想配列形式で取得
        input_value_array = json.loads(request.POST['input_value_array'])

        phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
        phenomenon_id = phenomenon_data.phenomenon_id

        # 検収情報の保存
        if MaintenanceInspectionAcceptance.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            inspection_acceptance_data = MaintenanceInspectionAcceptance.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id').first()
        else:
            inspection_acceptance_data, created = MaintenanceInspectionAcceptance.objects.get_or_create(phenomenon_id=phenomenon_id, lost_flag=0)
            inspection_acceptance_data.entry_datetime = now
            inspection_acceptance_data.entry_operator = t_username

        inspection_acceptance_data.documents_receipt_date = blank_to_None(date_to_hyphen(input_value_array['documents_receipt_date']))
        inspection_acceptance_data.documents_rem = blank_to_None(input_value_array['documents_rem'])
        inspection_acceptance_data.documents_check_result = blank_to_None(input_value_array['documents_check_result'])
        inspection_acceptance_data.receipt_send_date = blank_to_None(date_to_hyphen(input_value_array['receipt_send_date']))
        inspection_acceptance_data.update_datetime = now
        inspection_acceptance_data.update_operator = t_username
        inspection_acceptance_data.save()

        comment = "phenomenon_id : " + str(phenomenon_id)
        if this_step == next_step:
            action = "temporarily_saved"
            msg = "一時保存完了"
        else:
            step_data = StepMaster.objects.get(step_id=this_step)
            step_name = step_data.step_name
            msg = step_name + "完了"
            action = "entry"

        # ログを新規登録
        Log(target='phenomenon', target_id=phenomenon_id, action=action, operator=t_username,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division).save()

        # 次ステップに進む場合のみ次作業者のuser_attribute_idが設定されるので、部署、部門を含めて取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_person = t_username
            next_division = this_division
            next_department = this_department

        # 進捗状況を対象(phenomenon)と案件idとstepで抽出･･･異なるstepのprogressが複数作成されるため
        progress_data_list = Progress.objects.filter(target_id=phenomenon_id,
                                                     target='phenomenon', present_step=this_step)
        if progress_data_list.count() == 1:
            progress_data = progress_data_list[0]
            progress_data.present_step = next_step
            progress_data.present_operator = next_person
            progress_data.present_department = next_department
            progress_data.present_division = next_division
            if this_step != next_step:
                progress_data.last_operation_step = this_step
                progress_data.last_operator = t_username
                progress_data.last_operation_datetime = now
            # 進捗状況のレコードを保存
            progress_data.save()
        else:
            # 該当のprogressが取得できない場合
            raise ValueError("There are multiple progresses with the same step.")

        ary = {
            'msg': msg,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
