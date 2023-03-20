# インポート
import datetime
import json
import traceback
import mimetypes
import openpyxl

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import make_aware
from django.views.decorators.http import require_POST, require_GET

# modelesをインポート
from common.common_def import date_to_many_type
from fms.models import DataEntryStepMaster, Log, Progress, UserAttribute, Order, ErpConstruction, MCFrame, SubmissionDocument
from fms.models import MaintenanceEstimateStatusMaster, MaintenanceEstimate, MaintenanceEstimateVendor
from fms.models import Phenomenon, StepMaster
# 共通部品をインポート
from fms.views.common_def_views import output_log_exception, get_output_file_path, get_template_file_path
from fms.views.common_views import date_to_hyphen,  blank_to_None


# 業者見積を詳細画面で表示
from gcsystem.models import QuantityUnitMaster
from plantia.models import MasterLocation


@login_required
@require_POST
def maintenance_order_estimates_data_info(request):
    try:
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'
        this_step = int(request.POST['this_step'])

        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        phenomenon_id = 0
        order_data = ''
        erp_construction_data = ''
        estimates_data = ''
        storage_space_rem = ''
        estimates_vendor_list = []
        vendor_count = 0
        construction_from = None
        construction_to = None

        # 異常報告IDが指定されていない場合は、何も表示しない
        if phenomenon_unique_id != 0:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id

            # 各情報が保存済かどうか判定
            order_list = Order.objects.filter(phenomenon_id=phenomenon_id).order_by('-id')
            if order_list.count() > 0:
                order_data = order_list.first()
                construction_from = order_data.desired_start_date
                construction_to = order_data.desired_end_date

            erp_construction_list = ErpConstruction.objects.filter(order_id=phenomenon_id).order_by('-id')
            if erp_construction_list.count() > 0:
                erp_construction_data = erp_construction_list.first()
                storage_space_rem = erp_construction_data.storage_space_rem
                if storage_space_rem is None:
                    factory_data = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)
                    factory_name = factory_data.location_nm_1
                    storage_space_rem = order_data.department.department_name + " " + factory_name

            # 小口見積情報が保存済かどうか判定
            estimates_list = MaintenanceEstimate.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id')
            if estimates_list.count() > 0:
                estimates_data = estimates_list.first()
                construction_from = estimates_data.construction_from
                construction_to = estimates_data.construction_to

            # 保存済の場合は、業者別情報を取得
            if estimates_data != '':
                estimates_vendor_list = MaintenanceEstimateVendor.objects.filter(
                    phenomenon_id=phenomenon_id, lost_flag=0).order_by('vendor_no')
                vendor_count = estimates_vendor_list.count()

        status_list = MaintenanceEstimateStatusMaster.objects.filter(lost_flag=0).order_by('display_order')

        data = {
            'action_button_id': action_button_id,
            'div_id_name': div_id_name,
            'phenomenon_unique_id': phenomenon_unique_id,
            'phenomenon_id': phenomenon_id,
            'order_data': order_data,
            'erp_construction_data': erp_construction_data,
            'estimates_data': estimates_data,
            'estimates_vendor_list': estimates_vendor_list,
            'vendor_count': vendor_count,
            'construction_from': construction_from,
            'construction_to': construction_to,
            'storage_space_rem': storage_space_rem,
            'status_list': status_list,
        }

        if DataEntryStepMaster.objects.filter(step_id=this_step, target_table='maintenance_order_estimates',
                                              lost_flag=0).count() > 0:
            template_file = 'fms/parts/maintenance/maintenance_order_estimates/maintenance_order_estimates_edit.html'
        else:
            template_file = 'fms/parts/maintenance/maintenance_order_estimates/maintenance_order_estimates_info.html'

        return render(request, template_file, data)

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 業者見積情報の登録
@login_required
@require_POST
def maintenance_order_estimates_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        this_step = int(request.POST['this_step'])
        next_step = int(request.POST['next_step'])
        user_attribute_id = int(request.POST['user_attribute_id'])
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        action_cd = request.POST['action_cd']
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        decision_check_val = int(request.POST['decision_check_val'])

        # 入力情報は連想配列形式で取得
        input_value_array = json.loads(request.POST['input_value_array'])

        phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
        phenomenon_id = phenomenon_data.phenomenon_id

        # Order、ErpConstructionの見積関連情報の保存
        order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        order_data.order_detail_for_vendor = input_value_array['order_detail_for_vendor']
        order_data.update_datetime = now
        order_data.update_operator = t_username
        order_data.save()

        erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id)
        erp_construction_data.item_text = input_value_array['order_name_for_vendor']
        erp_construction_data.storage_space_rem = input_value_array['delivery_location']
        construction_start_date = date_to_many_type(input_value_array['construction_from'])
        delivery_date = date_to_many_type(input_value_array['delivery_date'])
        erp_construction_data.construction_start_date = construction_start_date.str_type_date_erp
        erp_construction_data.delivery_date = delivery_date.str_type_date_erp
        erp_construction_data.update_datetime = now
        erp_construction_data.update_operator = t_username
        erp_construction_data.save()

        # 新EPR刷新対応
        mcframe_data = MCFrame.objects.get(order_id=phenomenon_id)
        mcframe_data.item_text = input_value_array['order_name_for_vendor']
        mcframe_data.storage_space_rem = input_value_array['delivery_location']
        construction_start_date = date_to_many_type(input_value_array['construction_from'])
        delivery_date = date_to_many_type(input_value_array['delivery_date'])
        mcframe_data.construction_start_date = construction_start_date.str_type_date_erp
        mcframe_data.delivery_date = delivery_date.str_type_date_erp
        mcframe_data.update_datetime = now
        mcframe_data.update_operator = t_username
        mcframe_data.save()
        # 新EPR刷新対応

        # 小口見積情報の保存
        if MaintenanceEstimate.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            estimates_data = MaintenanceEstimate.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by(
                '-id').first()
        else:
            estimates_data, created = MaintenanceEstimate.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                lost_flag=0)
            estimates_data.entry_datetime = now
            estimates_data.entry_operator = t_username

        estimates_data.estimate_deadline = blank_to_None(date_to_hyphen(input_value_array['estimate_deadline']))
        estimates_data.construction_from = blank_to_None(date_to_hyphen(input_value_array['construction_from']))
        estimates_data.construction_to = blank_to_None(date_to_hyphen(input_value_array['construction_to']))
        estimates_data.delivery_date = blank_to_None(date_to_hyphen(input_value_array['delivery_date']))
        estimates_data.delivery_location = blank_to_None(input_value_array['delivery_location'])
        estimates_data.confirmed_vendor_no = decision_check_val
        estimates_data.update_datetime = now
        estimates_data.update_operator = t_username
        estimates_data.save()

        # 業者情報の保存
        if MaintenanceEstimateVendor.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() == 0:
            vendor_data, created = MaintenanceEstimateVendor.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                   vendor_no=1,
                                                                                   lost_flag=0)
            vendor_data.entry_datetime = now
            vendor_data.entry_operator = t_username
            vendor_data.save()

        estimates_vendor_list = MaintenanceEstimateVendor.objects.filter(phenomenon_id=phenomenon_id,
                                                                         lost_flag=0).order_by('vendor_no')
        for vendor_data in estimates_vendor_list:
            no = vendor_data.vendor_no
            vendor_data.status_id = blank_to_None(input_value_array[f'status_{no}'])
            vendor_data.vendor_name = blank_to_None(input_value_array[f'vendor_name_{no}'])
            vendor_data.req_date = blank_to_None(date_to_hyphen(input_value_array[f'req_date_{no}']))
            vendor_data.reply_date = blank_to_None(date_to_hyphen(input_value_array[f'reply_date_{no}']))
            vendor_data.estimate_price = blank_to_None(input_value_array[f'estimate_price_{no}'].replace(',', ''))
            vendor_data.price_after_discount = blank_to_None(
                input_value_array[f'price_after_discount_{no}'].replace(',', ''))
            vendor_data.eva_delivery = blank_to_None(input_value_array[f'eva_delivery_{no}'])
            vendor_data.eva_price = blank_to_None(input_value_array[f'eva_price_{no}'].replace(',', ''))
            vendor_data.eva_estimate = blank_to_None(input_value_array[f'eva_estimate_{no}'])
            vendor_data.eva_last_price = blank_to_None(input_value_array[f'eva_last_price_{no}'])
            vendor_data.eva_other = blank_to_None(input_value_array[f'eva_other_{no}'])
            vendor_data.update_datetime = now
            vendor_data.update_operator = t_username
            vendor_data.save()

        comment = "phenomenon_id : " + str(phenomenon_id)
        if this_step == next_step:
            if action_cd == 'add_vendor':
                # 候補業者追加
                estimates_vendor_list = MaintenanceEstimateVendor.objects.filter(phenomenon_id=phenomenon_id,
                                                                                 lost_flag=0).order_by('-vendor_no')
                new_vendor_no = estimates_vendor_list.first().vendor_no + 1
                vendor_data, created = MaintenanceEstimateVendor.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                       vendor_no=new_vendor_no,
                                                                                       lost_flag=0)
                vendor_data.status_id = 'start'
                vendor_data.entry_datetime = now
                vendor_data.entry_operator = t_username
                vendor_data.save()
                msg = "候補業者追加完了"
                comment = comment + f':候補業者追加 { new_vendor_no } '
            else:
                msg = "一時保存完了"

            action = "temporarily_saved"
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


# 見積依頼書excel作成
@login_required
@require_GET
def make_request_estimate_maintenance_order(request, phenomenon_id, vendor_no):
    try:
        # 今日の日付を取得
        DIFF_JST_FROM_UTC = 18
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        date_str = date_to_many_type(now)
        today_str = date_str.str_type_date_jp

        target_folder = 'result_request_for_quotation'
        templates_file_name = 'request_for_quotation'
        create_file_name = 'result_request_for_quotation'
        templates_file_ext = '.xlsx'

        # テンプレートファイルオープン
        templates_file_full_name = templates_file_name + templates_file_ext
        templates_file_path = get_template_file_path(target_folder, templates_file_full_name)
        wb_new_file = openpyxl.load_workbook(templates_file_path)

        # 入力用データ取得
        order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id)
        estimate_data = MaintenanceEstimate.objects.get(phenomenon_id=phenomenon_id)
        vendor_data = MaintenanceEstimateVendor.objects.get(phenomenon_id=phenomenon_id, vendor_no=vendor_no)
        start_date = date_to_many_type(estimate_data.construction_from).str_type_date_jp
        end_date = date_to_many_type(estimate_data.construction_to).str_type_date_jp

        ws_new_sheet = wb_new_file['Sheet1']
        ws_new_sheet['O2'].value = today_str  # 見積依頼日
        if vendor_data.vendor_name is not None:
            ws_new_sheet['A8'].value = vendor_data.vendor_name + '　御中'  # 業者名

        ws_new_sheet['G19'].value = erp_construction_data.order_id  # 見積依頼NO
        ws_new_sheet['G21'].value = erp_construction_data.item_text  # 品目名称
        ws_new_sheet['G23'].value = order_data.order_detail_for_vendor  # 工事/依頼内容
        ws_new_sheet['G29'].value = start_date + " ～ " + end_date  # 希望工期
        # ws_new_sheet['G31'].value = estimate_data.delivery_location  # 工事実施場所/担当
        ws_new_sheet['G31'].value = erp_construction_data.storage_space_rem  # 工事実施場所/担当
        ws_new_sheet['O9'].value = request.user.last_name + "　" + request.user.first_name
        ws_new_sheet['O12'].value = request.user.username + "@iskweb.co.jp"

        # 登録済の提出書類一覧を取得
        entry_class = '故障対応'
        document_lists = SubmissionDocument.objects.filter(work_id=phenomenon_id, lost_flag=0, entry_class=entry_class
                                                           ).all().order_by('display_order')
        if len(document_lists) > 0:
            doc_name_input_cell_col = 'C'
            doc_num_input_cell_col = 'L'
            doc_deadline_input_cell_col = 'P'
            input_cell_row = 36
            loop_num = 1
            ws_new_sheet[doc_name_input_cell_col + str(input_cell_row)].value = '提出文書'
            for document_list_item in document_lists:
                # 文書名
                doc_name_input_cell = doc_name_input_cell_col + str(input_cell_row + loop_num)
                ws_new_sheet[doc_name_input_cell].value = str(loop_num) + '．' + document_list_item.document_name
                # 部数
                doc_num_input_cell = doc_num_input_cell_col + str(input_cell_row + loop_num)
                ws_new_sheet[doc_num_input_cell].value = '部数：' + str(document_list_item.number_of_copies)
                # 提出期限
                doc_deadline_input_cell = doc_deadline_input_cell_col + str(input_cell_row + loop_num)
                ws_new_sheet[doc_deadline_input_cell].value = '提出期限：' + document_list_item.submission_deadline

                loop_num += 1

        new_file_name = create_file_name + templates_file_ext
        output_file_path = get_output_file_path(target_folder, new_file_name)

        wb_new_file.save(output_file_path)

        with open(output_file_path, 'rb') as fh:
            response = HttpResponse(fh.read(),
                                    content_type=mimetypes.guess_type(new_file_name)[0] or 'application/octet-stream')
            response['Content-Disposition'] = 'inline; filename=' + new_file_name

        return response
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise



