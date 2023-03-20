# datetimeをインポート
import datetime
# ログインユーザーを使用するmoduleをインポート
from time import strptime
import traceback
from django.contrib.auth.decorators import login_required
# postからの引数を使用できるmoduleをインポート
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
# modelesをインポート
from jaconv import jaconv

from fms.models import Measure, Order, ErpConstruction, MCFrame, OrderForIEP, Phenomenon, Progress, DataEntryStepMaster, Log, \
    NotificationCheck
from fms.models import EquipmentHistoryReport, MaintenanceEquipment
from fms.models import UserAttribute, User, DepartmentMaster
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation
from common.common_def import date_to_many_type
from .common_views import action_num_count
from django.utils.timezone import make_aware
from fms.views.common_views import None_to_blank, blank_to_None
from fms.views.report_maintenance_g_views import equipment_history_report_data_pre_entry
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception, get_department_person_option_list
from fms.views.notice_mail_views import step_notice


# 小口工事発注IEPメール内容取得
def maintenance_order_get_mail_data(request, phenomenon_id):
    # 変数初期化
    subject_str = ''
    msg_body = ''
    department_name = ''
    order_title = ''
    order_detail = ''
    start_date_str = ''
    end_date_str = ''
    person_full_name = ''
    request_user_name = ''
    cost_center = ''
    instruction_code = ''
    account_code = ''
    eqpt_id_str = ''

    # データ取得
    if phenomenon_id != 0:
        request_user_name = request.user.last_name + '　' + request.user.first_name
        phenomenon_id_str = str(phenomenon_id)
        phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)
        # department_name = phenomenon_data.department.department_name

        order_data_num = Order.objects.filter(phenomenon_id=phenomenon_id).count()
        if order_data_num != 0:
            order_data = Order.objects.get(phenomenon_id=phenomenon_id)

            if order_data.order_name is not None and order_data.order_name is not "":
                order_title = order_data.order_name + order_data.order_name_extension_name

            if order_data.order_detail is not None and order_data.order_detail is not "":
                order_detail = order_data.order_detail

            if order_data.desired_start_date is not None and str(order_data.desired_start_date) is not "":
                start_date_str = date_to_many_type(order_data.desired_start_date).str_type_date_jp

            if order_data.desired_end_date is not None and str(order_data.desired_end_date) is not "":
                end_date_str = date_to_many_type(order_data.desired_end_date).str_type_date_jp

            if order_data.department_id is not None and order_data.department_id is not "":
                department_name = order_data.department.department_name

            if order_data.order_permit_person is not None and order_data.order_permit_person is not "":
                person_full_name = order_data.order_permit_person

            if order_data.contact_request == 232004001:
                order_for_IEP_data = OrderForIEP.objects.get(order_id=phenomenon_id)
                if order_for_IEP_data.cost_center != None and order_for_IEP_data.cost_center != "":
                    cost_center = order_for_IEP_data.cost_center
                else:
                    cost_center = cost_center
                if order_for_IEP_data.account_code != None and order_for_IEP_data.account_code != "":
                    account_code = order_for_IEP_data.account_code
                    account_code = str(int(account_code) - 2)
                else:
                    account_code = account_code
                if order_for_IEP_data.instruction_code != None and order_for_IEP_data.instruction_code != "":
                    instruction_code = order_for_IEP_data.instruction_code
                else:
                    instruction_code = instruction_code
                if order_for_IEP_data.orders_received_person != None and order_for_IEP_data.orders_received_person != "":
                    orders_received_person = order_for_IEP_data.orders_received_person
                if order_for_IEP_data.order_permit_person != None and order_for_IEP_data.order_permit_person != "":
                    order_permit_person = order_for_IEP_data.order_permit_person
                rem_for_plantia_data = order_for_IEP_data.order_rem_2

            elif is_erp_construction(order_data.contact_request):
                erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id, work_class='SW')
                if erp_construction_data.cost_center != None and erp_construction_data.cost_center != "":
                    cost_center = erp_construction_data.cost_center
                else:
                    cost_center = cost_center
                if erp_construction_data.account_code != None and erp_construction_data.account_code != "":
                    account_code = erp_construction_data.account_code
                else:
                    account_code = account_code
                if erp_construction_data.instruction_code != None and erp_construction_data.instruction_code != "":
                    instruction_code = erp_construction_data.instruction_code
                else:
                    instruction_code = instruction_code

            subject_str = '小口依頼-' + order_title + '依頼の件'

        else:
            measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count()
            if measure_data_num > 0:
                measure_data = Measure.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)
                if measure_data.work_order_department_charge_person is not None and measure_data.work_order_department_charge_person is not "":
                    person_full_name = measure_data.work_order_department_charge_person.last_name + '　' + measure_data.work_order_department_charge_person.first_name
                    account_code = measure_data.account_cd
                    cost_center = measure_data.cost_center
                    instruction_code = measure_data.instruction_no

        equipment_no = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0)
        first_loop = True
        for equipment_no_item in equipment_no:
            if FcltyLdgr.objects.filter(t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).count() != 0:
                if first_loop:
                    eqpt_id_str = eqpt_id_str + '機器番号　　　　　： ' + FcltyLdgr.objects.get(
                        t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).eqpt_id + '\n'
                    first_loop = False
                else:
                    eqpt_id_str = eqpt_id_str + '　　　　　　　　　　' + FcltyLdgr.objects.get(
                        t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).eqpt_id + '\n'

        # order_data_num = Order.objects.filter(phenomenon_id=phenomenon_id).count()
        # if order_data_num != 0:
        #     order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        #
        #     if order_data.order_name is not None and order_data.order_name is not "":
        #         order_title = order_data.order_name + order_data.order_name_extension_name
        #
        #     if order_data.order_detail is not None and order_data.order_detail is not "":
        #         order_detail = order_data.order_detail
        #
        #     if order_data.desired_start_date is not None and str(order_data.desired_start_date) is not "":
        #         start_date_str = date_to_many_type(order_data.desired_start_date).str_type_date_jp
        #
        #     if order_data.desired_end_date is not None and str(order_data.desired_end_date) is not "":
        #         end_date_str = date_to_many_type(order_data.desired_end_date).str_type_date_jp
        #
        #     if order_data.department_id is not None and order_data.department_id is not "":
        #         department_name = order_data.department.department_name
        #
        #     subject_str = '小口依頼-' + order_title + '依頼の件'

    # メール本文作成
    msg_body = msg_body + '管理NO： ' + phenomenon_id_str + '\n'
    msg_body = msg_body + '部署： ' + department_name + '\n'
    msg_body = msg_body + '原価センタ： ' + cost_center + '\n'
    msg_body = msg_body + '指図書NO： ' + instruction_code + '\n'
    # 機器番号
    msg_body = msg_body + eqpt_id_str
    msg_body = msg_body + '案件名： ' + order_title + '\n'
    msg_body = msg_body + '希望開始日： ' + start_date_str + '\n'
    msg_body = msg_body + '希望完工日： ' + end_date_str + '\n'
    msg_body = msg_body + '原課担当者： ' + person_full_name + '\n'
    msg_body = msg_body + '保全担当者： ' + request_user_name + '\n'
    msg_body = msg_body + '工事／依頼内容： ' + order_detail + '\n'
    msg_body = msg_body + '勘定コード： ' + account_code + '\n'

    return subject_str, msg_body


# 対応を詳細画面で表示
@login_required
@require_POST
def maintenance_order_data_info(request):
    from .maintenance_views import get_maintenance_option_list
    from .maintenance_views import get_maintenance_cost_center, get_maintenance_account_code, get_maintenance_instruction_no
    try:
        DIFF_JST_FROM_UTC = 9
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        user_department_cd = request.POST['user_department_cd']
        action_button_id = target + '_' + div_id_name + '_action_button'
        target_step_id = int(request.POST['target_step_id'])

        t_username = request.user.username
        plant_code = ''
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        phenomenon_data = ''
        if phenomenon_unique_id == 0:
            target_inspection_id = 0
            target_order_id = 0
            project_title = ''
            # department_name = ''
            equipment_no = ''
            department_cd = ""
            facility_name = ""
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id
            project_title = phenomenon_data.project_title
            facility_code = phenomenon_data.m_location_skey
            facility_code_master_data = MasterLocation.objects.get(m_location_skey=facility_code)
            facility_name = facility_code_master_data.location_nm_1
            equipment_no = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0)
            plant_code = phenomenon_data.m_location_skey
            # factory_data = MasterLocation.objects.get(location_cd=factory_name)
            # m_location_skey = factory_data.m_location_skey
            order_data_num = Order.objects.filter(phenomenon_id=phenomenon_id).count()
            if order_data_num == 0:
                target_order_id = 0
            else:
                # target_measure_id = int(request.POST['measure_id'])
                order_data = Order.objects.get(phenomenon_id=phenomenon_id)
                target_order_id = order_data.id

        measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count()
        if measure_data_num > 0:
            measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)

            if measure_data.work_order_charge_department is not None and measure_data.work_order_charge_department is not "":
                department_name = measure_data.work_order_charge_department.department_name
                department_cd = measure_data.work_order_charge_department.department_cd
            else:
                department_name = ""
                department_cd = ""

            if measure_data.orders_received_person is not None and measure_data.orders_received_person is not "":
                orders_received_person = measure_data.orders_received_person
            else:
                orders_received_person = ""

            if measure_data.desired_vendor is not None and measure_data.desired_vendor is not "":
                order_vendor = measure_data.desired_vendor
            else:
                order_vendor = ""

            account_code = measure_data.account_cd
            cost_center = measure_data.cost_center
            instruction_code = measure_data.instruction_no
        else:
            orders_received_person = ""
            order_vendor = ""
            account_code = ""
            cost_center = ""
            instruction_code = ""
            department_name = ""
            department_cd = ""

        # 更新処理
        if target_order_id > 0:
            order_data = Order.objects.get(id=target_order_id)
            order_name = order_data.order_name
            order_name_extension = order_data.order_name_extension_name
            department_cd = order_data.department_id
            order_permit_person = order_data.order_permit_person
            expected_price = order_data.expected_price
            if expected_price is not None:
                # 3桁区切りの「,」挿入処理
                expected_price = "{:,}".format(expected_price)
            # desired_start_date = order_data.desired_start_date
            date_str = date_to_many_type(order_data.desired_start_date + datetime.timedelta(hours=DIFF_JST_FROM_UTC))
            desired_start_date = date_str.str_type_date_jp
            # desired_end_date = order_data.desired_end_date
            date_str = date_to_many_type(order_data.desired_end_date + datetime.timedelta(hours=DIFF_JST_FROM_UTC))
            desired_end_date = date_str.str_type_date_jp
            order_detail = None_to_blank(order_data.order_detail)
            rem = None_to_blank(order_data.rem)
            plant_code = order_data.m_location_skey
            contact_request = order_data.contact_request
            order_vendor = order_data.order_vendor
            is_need_input_plantia = None_to_blank(order_data.is_need_input_plantia)

            if plant_code is None:
                plant_name = ''
            else:
                facility_code_master = MasterLocation.objects.get(m_location_skey=plant_code)
                plant_name = facility_code_master.location_nm_1
            if order_data.contact_request == 232004001:
                order_for_IEP_data = OrderForIEP.objects.get(order_id=phenomenon_id)
                department = order_for_IEP_data.department
                if order_for_IEP_data.cost_center != None and order_for_IEP_data.cost_center != "":
                    cost_center_code = order_for_IEP_data.cost_center
                else:
                    cost_center_code = cost_center
                if order_for_IEP_data.account_code != None and order_for_IEP_data.account_code != "":
                    account_code = order_for_IEP_data.account_code
                    account_code = str(int(account_code) - 2)
                else:
                    account_code = account_code
                if order_for_IEP_data.instruction_code != None and order_for_IEP_data.instruction_code != "":
                    instruction_code = order_for_IEP_data.instruction_code
                else:
                    instruction_code = instruction_code
                if order_for_IEP_data.orders_received_person != None and order_for_IEP_data.orders_received_person != "":
                    orders_received_person = order_for_IEP_data.orders_received_person
                if order_for_IEP_data.order_permit_person != None and order_for_IEP_data.order_permit_person != "":
                    order_permit_person = order_for_IEP_data.order_permit_person
                rem_for_plantia_data = order_for_IEP_data.order_rem_2
                if is_need_input_plantia == '':
                    # モデル変更前の過去データ対応のため、rem_for_plantia_dataから選択状態を復元する処理
                    if 'PLANTIA登録：要' in rem_for_plantia_data:
                        is_need_input_plantia = '要'
                    else:
                        is_need_input_plantia = '不要'
            elif is_erp_construction(order_data.contact_request):
                department = department_name + ":" + facility_name
                erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id, work_class='SW')
                if erp_construction_data.cost_center != None and erp_construction_data.cost_center != "":
                    cost_center_code = erp_construction_data.cost_center
                else:
                    cost_center_code = cost_center
                if erp_construction_data.account_code != None and erp_construction_data.account_code != "":
                    account_code = erp_construction_data.account_code
                else:
                    account_code = account_code
                if erp_construction_data.instruction_code != None and erp_construction_data.instruction_code != "":
                    instruction_code = erp_construction_data.instruction_code
                else:
                    instruction_code = instruction_code
                rem_for_plantia_data = ''
                is_need_input_plantia = ''
            else:
                department = ''
                account_code = ''
                cost_center_code = ''
                rem_for_plantia_data = ''
                is_need_input_plantia = ''

            phenomenon_data_num = Phenomenon.objects.filter(phenomenon_id=phenomenon_id).count()
            mcframe_data = MCFrame.objects.get(order_id=phenomenon_id, work_class='SW')
            order_no = mcframe_data.order_no if mcframe_data.order_no is not None else ""

        # 新規処理
        else:
            # phenomenon_id = 0
            phenomenon_data_num = Phenomenon.objects.filter(phenomenon_id=phenomenon_id).count()
            if phenomenon_data_num > 0:
                phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id)
                order_name = phenomenon_data.project_title
                plant_name = phenomenon_data.m_location_skey
            else:
                phenomenon_data = ''
                order_name = ''
                plant_name = ''

            measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id).count()
            if measure_data_num > 0:
                measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)
                date_str = date_to_many_type(measure_data.desired_delivery_date_start)
                desired_start_date = date_str.str_type_date_jp
                date_str = date_to_many_type(measure_data.desired_delivery_date_end)
                desired_end_date = date_str.str_type_date_jp
                cost_center_code = measure_data.cost_center
                account_code = measure_data.account_cd
                instruction_code = measure_data.instruction_no
                order_detail = measure_data.measure_order_detail

                if measure_data.work_order_charge_department is not None and measure_data.work_order_charge_department is not "":
                    department = measure_data.work_order_charge_department.department_cd
                else:
                    department = ""

                if measure_data.work_order_department_charge_person is not None and measure_data.work_order_department_charge_person is not "":
                    order_permit_person = \
                        measure_data.work_order_department_charge_person.last_name + '　' + measure_data.work_order_department_charge_person.first_name
                else:
                    order_permit_person = ""
            else:
                desired_start_date = ''
                desired_end_date = ''
                instruction_code = ''
                cost_center_code = ''
                account_code = ''
                order_detail = ''
                department = ''
                order_permit_person = ""

            order_name_extension = ""
            expected_price = ""
            cost_center_name = ""
            account_code_name = ""
            cost_center_name = ""
            rem = ""
            is_need_input_plantia = ""
            rem_for_plantia_data = ""
            contact_request = ""
            order_data = ''
            order_no = ''

        if Progress.objects.filter(target='phenomenon', target_id=phenomenon_data.phenomenon_id, present_step=target_step_id).count() == 1:
            present_step_data = Progress.objects.get(target_id=phenomenon_id, target='phenomenon', present_step=target_step_id)
            present_step = present_step_data.present_step
            action_num = action_num_count(t_username, user_department_cd, present_step, target, phenomenon_id)

            # データ編集機能要否判定
            maintenance_order_edit_action_num = 0
            maintenance_order_edit_action_num = maintenance_order_edit_action_num + DataEntryStepMaster.objects.filter(
                step_id=present_step, target_table='maintenance_order').count()
        else:
            present_step_data = Progress.objects.filter(target_id=phenomenon_id, target='phenomenon').first()
            present_step = present_step_data.present_step
            action_num = 0
            maintenance_order_edit_action_num = 0

        facility_lists = MasterLocation.objects.filter(parent_m_location_skey__isnull=False, deleted_flg=0)
        departments_list = DepartmentMaster.objects.filter(lost_flag=0)

        # 原課担当者リスト（注意：氏名で選択）
        person_lists = get_department_person_option_list(department_cd, '', order_permit_person)

        # 部署情報から原価センター関連の候補リストを取得（optionリストを取得）
        gc_option_data = get_maintenance_option_list(department_cd, cost_center_code, instruction_code, account_code)
        cost_center_option_list = gc_option_data['cost_center_option_list']
        instruction_no_option_list = gc_option_data['instruction_no_option_list']
        account_code_option_list = gc_option_data['account_code_option_list']

        # 保存済の情報からGCシステム側の情報を取得
        instruction_no_data = get_maintenance_instruction_no(instruction_code)
        cost_center_data = get_maintenance_cost_center(cost_center_code)
        account_cd_data = get_maintenance_account_code(account_code)

        if contact_request == 232004001:
            contact_request_name = 'IEP'
        elif is_erp_construction(contact_request):
            contact_request_name = '外部業者(直発注)'
        else:
            contact_request_name = ''

        # メール送信用文字列取得
        subject_str, msg_body = maintenance_order_get_mail_data(request, phenomenon_id)

        # 原課部署の届出チェック進捗状況
        notification_check_complete_flag = 1
        notification_check_list = NotificationCheck.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0).all()
        if notification_check_list.count() > 0:
            notification_check_progress = Progress.objects.get(target_id=phenomenon_data.phenomenon_id, target='ph_nc')
            if notification_check_progress.present_step != 233009901:
                # (TODO:仮運用のためロックしない>0でロック)
                notification_check_complete_flag = 0

        data = {
            'target_order_id': target_order_id,
            'phenomenon_data': phenomenon_data,
            'phenomenon_data_num': phenomenon_data_num,
            'order_name': order_name,
            'order_name_extension': order_name_extension,
            'expected_price': expected_price,
            'desired_start_date': desired_start_date,
            'desired_end_date': desired_end_date,
            'department_cd': department_cd,
            'department': department,
            'plant_code': plant_code,
            'plant_name': plant_name,
            'order_no': order_no,
            'order_detail': order_detail,
            'rem': rem,
            'rem_for_plantia_data': rem_for_plantia_data,

            'cost_center_option_list': cost_center_option_list,
            'instruction_no_option_list': instruction_no_option_list,
            'account_code_option_list': account_code_option_list,
            'cost_center_data': cost_center_data,
            'instruction_no_data': instruction_no_data,
            'account_cd_data': account_cd_data,

            'facility_lists': facility_lists,
            'departments_list': departments_list,
            'person_lists': person_lists,
            'order_data': order_data,
            'msg_body': msg_body,
            'subject_str': subject_str,
            'order_vendor': order_vendor,
            'orders_received_person': orders_received_person,
            'order_permit_person': order_permit_person,
            'contact_request_name': contact_request_name,
            'present_step': present_step,
            'contact_request': contact_request,
            'is_need_input_plantia': is_need_input_plantia,
            'action_button_id': action_button_id,
            'notification_check_complete_flag': notification_check_complete_flag,
        }

        edit_flag = 0

        if maintenance_order_edit_action_num > 0 and action_num > 0:
            edit_flag = 1
        if edit_flag == 1:
            return render(request, 'fms/parts/maintenance/maintenance_order/maintenance_order_edit.html', data)
        else:
            return render(request, 'fms/parts/maintenance/maintenance_order/maintenance_order_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 小口工事発注レコード作成
@login_required
@require_POST
def maintenance_order_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        t_user_first_name = request.user.first_name
        t_user_last_name = request.user.last_name
        this_step = int(request.POST['this_step'])
        next_step = int(request.POST['next_step'])
        next_person = request.POST['next_person']
        next_division = request.POST['next_division']
        next_department = request.POST['next_department']
        user_attribute_id = int(request.POST['user_attribute_id'])
        this_division = request.POST['this_division']
        this_department = request.POST['this_department']
        contact_request = int(request.POST['contact_request'])
        order_name = request.POST['order_name']
        order_name_extension = request.POST['order_name_extension']
        expected_price_str = request.POST['expected_price']
        expected_price_str = expected_price_str.replace(',', '')
        expected_price = int(expected_price_str)
        department = request.POST['department']
        plant_name = request.POST['plant_name']
        cost_center = request.POST['cost_center']
        account_code = request.POST['account_code']
        instruction_code = request.POST['instruction_code']
        order_detail = request.POST['order_detail']
        order_vendor = request.POST['order_vendor']
        rem = request.POST['rem']
        is_need_input_plantia = request.POST['is_need_input_plantia']

        step_progress_type = request.POST['action_type']
        orders_received_person = request.POST['orders_received_person']
        order_permit_person_id = request.POST['order_permit_person']
        start_date_str = request.POST['start_date']
        date_str = date_to_many_type(start_date_str)
        start_date = date_str.date_type_date
        start_date_erp = date_str.str_type_date_erp
        end_date_str = request.POST['end_date']
        date_str = date_to_many_type(end_date_str)
        end_date = date_str.date_type_date
        end_date_erp = date_str.str_type_date_erp

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_person = t_username
            next_division = this_division
            next_department = this_department

        if request.POST["order_id"] is not "":
            order_id = int(request.POST["order_id"])
            phenomenon_id = int(request.POST["phenomenon_id"])
            # sub_no = int(request.POST["sub_no"])
            sub_no = 0
        else:
            order_id = 0
            if request.POST["phenomenon_id"] is not "":
                phenomenon_id = int(request.POST["phenomenon_id"])
            else:
                phenomenon_id = 0
            sub_no = 0

        # OrderForIEPに部署名を入力するため、名称を取得
        department_data = DepartmentMaster.objects.get(department_cd=department)
        department_name = department_data.department_name

        # 注意：小口依頼のorder_permit_person_userは全角空白区切りで保存、PLANTIA側の氏名と揃えるため
        order_permit_person_user = User.objects.get(username=order_permit_person_id)
        order_permit_person_full_name = order_permit_person_user.last_name + '　' + order_permit_person_user.first_name

        phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id, sub_no=sub_no)
        management_class = phenomenon_data.m_mgt_cls_skey
        management_class_master_data = MasterMgtCls.objects.get(m_mgt_cls_skey=management_class, deleted_flg=0)
        mgt_class_name = management_class_master_data.mgt_cls_nm_1
        facility_code = phenomenon_data.m_location_skey
        facility_code_master_data = MasterLocation.objects.get(m_location_skey=facility_code)
        facility_name = facility_code_master_data.location_nm_1
        equipment_no = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0)
        measure_data = Measure.objects.get(phenomenon_id=phenomenon_id, sub_no=sub_no)

        order_data_num = Order.objects.filter(phenomenon_id=phenomenon_id).count()

        if order_data_num > 0:
            order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        else:
            order_data, created = Order.objects.get_or_create(phenomenon_id=phenomenon_id)

        order_data.order_name = order_name
        order_data.order_name_extension_name = order_name_extension
        order_data.contact_request = contact_request
        order_data.department_id = department
        order_data.order_permit_person = order_permit_person_full_name
        order_data.estimation_price = expected_price
        order_data.order_detail = order_detail
        order_data.expected_price = expected_price
        order_data.desired_start_date = start_date
        order_data.desired_end_date = end_date
        order_data.m_location_skey = plant_name
        order_data.order_vendor = order_vendor
        order_data.rem = blank_to_None(rem)
        if contact_request == 232004001:
            order_data.is_need_input_plantia = blank_to_None(is_need_input_plantia)
        else:
            order_data.is_need_input_plantia = None

        if order_data_num > 0:
            order_data.update_datetime = now
            order_data.update_operator = t_username
        else:
            order_data.entry_datetime = now
            order_data.entry_operator = t_username

        order_data.save()

        # 対応の主キー値取得
        order_unique_id = order_data.id
        order_id = order_data.order_id

        if next_step == 232009901:
            msg = '故障対応中止'

        elif contact_request == 232004001:

            account_code = str(int(account_code) + 2)

            order_for_IEP_data_num = OrderForIEP.objects.filter(order_id=phenomenon_id).count()

            order_for_IEP_data, created = OrderForIEP.objects.get_or_create(order_id=phenomenon_id)
            order_for_IEP_data.department = str(department_name) + ":" + facility_name
            order_for_IEP_data.cost_center = cost_center
            order_for_IEP_data.order_name = order_name + order_name_extension
            order_for_IEP_data.order_person = t_user_last_name + " " + t_user_first_name
            order_for_IEP_data.desired_start_date = start_date
            order_for_IEP_data.desired_construction_end_date = end_date
            order_for_IEP_data.order_date = now
            order_for_IEP_data.account_code = account_code
            order_for_IEP_data.instruction_code = instruction_code
            order_for_IEP_data.construction_details = order_detail
            order_for_IEP_data.order_rem = rem
            order_for_IEP_data.orders_received_person = orders_received_person
            order_for_IEP_data.order_permit_person = order_permit_person_full_name

            # 案件区分
            order_for_IEP_data.item_class = int(measure_data.m_exe_cls_skey)

            # PLANTIA登録要否に応じて、注文備考を生成
            if is_need_input_plantia == '要':
                rem2_str = 'PLANTIA登録：要'
                rem2_str = rem2_str + '　区分：' + mgt_class_name
                rem2_str = rem2_str + '　工場：' + facility_name
                # rem2_str = rem2_str + '　機番：' + equipment_no

                first_loop = True
                for equipment_no_1 in equipment_no:
                    if FcltyLdgr.objects.filter(t_fclty_ldgr_skey=equipment_no_1.t_fclty_ldgr_skey).count() != 0:
                        if first_loop:
                            rem2_str = rem2_str + '　機番：' + FcltyLdgr.objects.get(
                                t_fclty_ldgr_skey=equipment_no_1.t_fclty_ldgr_skey).eqpt_id
                            first_loop = False
                        else:
                            rem2_str = rem2_str + '　　　　　　　　　　　　　' + FcltyLdgr.objects.get(
                                t_fclty_ldgr_skey=equipment_no_1.t_fclty_ldgr_skey).eqpt_id
            else:
                rem2_str = 'PLANTIA登録：不要'
                rem2_str = rem2_str + '　区分：' + mgt_class_name
                rem2_str = rem2_str + '　工場：' + facility_name

            order_for_IEP_data.order_rem_2 = rem2_str

            if step_progress_type == 'comp':
                order_for_IEP_data.status = 0

            if order_for_IEP_data_num > 0:
                order_for_IEP_data.update_datetime = now
                order_for_IEP_data.update_operator = t_username

            else:
                order_for_IEP_data.entry_datetime = now
                order_for_IEP_data.entry_operator = t_username
                order_for_IEP_data.update_datetime = now
                order_for_IEP_data.update_operator = t_username

            order_for_IEP_data.save()

            msg = 'IEP依頼処理完了'

        else:
            erp_construction_data_num = ErpConstruction.objects.filter(order_id=phenomenon_id).count()
            erp_construction_data, created = ErpConstruction.objects.get_or_create(order_id=phenomenon_id)
            erp_construction_data.detail_no = 1
            erp_construction_data.purchase_group_code = 'YA2'
            erp_construction_data.currency_code = 'JPY'
            erp_construction_data.account_class = 'F'
            erp_construction_data.item_code = ''
            order_str = order_name + order_name_extension
            order_name = jaconv.z2h(order_str, kana=True, digit=True, ascii=True)
            erp_construction_data.item_text = order_name
            erp_construction_data.order_amount = 1
            erp_construction_data.ordering_unit = 'SK'
            erp_construction_data.delivery_date = end_date_erp
            erp_construction_data.amount_per_base_unit = 'SK'
            erp_construction_data.base_unit_amount = 1
            erp_construction_data.item_group_code = '9V-108000'
            erp_construction_data.plant_code = 'ISKY'
            erp_construction_data.storage_space_code = ''
            erp_construction_data.purchase_trace_no = ''
            erp_construction_data.order_person = t_username
            erp_construction_data.rem = ''
            erp_construction_data.account_code = account_code
            erp_construction_data.cost_center = cost_center
            erp_construction_data.instruction_code = instruction_code
            erp_construction_data.order_no = phenomenon_id
            erp_construction_data.work_class = 'SW'
            erp_construction_data.relation_no = 'SW' + str(phenomenon_id)
            erp_construction_data.item_detail_text = '案件ID：' + str(phenomenon_id)
            erp_construction_data.construction_start_date = start_date_erp
            if erp_construction_data_num > 0:
                erp_construction_data.update_datetime = now
                erp_construction_data.update_operator = t_username
            else:
                erp_construction_data.entry_datetime = now
                erp_construction_data.entry_operator = t_username
            erp_construction_data.save()

            # 新ERP刷新対応
            mcframe_data, created = MCFrame.objects.get_or_create(order_id=phenomenon_id)
            mcframe_data.detail_no = 1
            mcframe_data.purchase_group_code = 'YA4'
            mcframe_data.currency_code = 'JPY'
            mcframe_data.account_class = 'F'
            mcframe_data.item_text = order_name
            mcframe_data.order_amount = 1
            mcframe_data.ordering_unit = 'SK'
            mcframe_data.delivery_date = end_date_erp
            mcframe_data.amount_per_base_unit = 'SK'
            mcframe_data.base_unit_amount = 1
            if 'S' in instruction_code:
                mcframe_data.item_group_code = '9Y-108000'
                mcframe_data.item_code = '9Y-108000'
            else:
                mcframe_data.item_group_code = '9V-108000'
                mcframe_data.item_code = '9V-108000'
            mcframe_data.plant_code = 'ISKY'
            mcframe_data.storage_space_code = 'YA4'
            mcframe_data.purchase_trace_no = ''
            mcframe_data.order_person = t_username
            mcframe_data.rem = ''
            mcframe_data.account_code = account_code
            mcframe_data.cost_center = cost_center
            mcframe_data.instruction_code = instruction_code
            mcframe_data.work_class = 'SW'
            mcframe_data.relation_no = 'SW' + str(phenomenon_id)
            mcframe_data.item_detail_text = '案件ID：' + str(phenomenon_id)
            mcframe_data.construction_start_date = start_date_erp
            mcframe_data.order_no = request.POST["order_no"] if request.POST["order_no"] is not '' else None
            mcframe_data.order_type_classification = 8
            numbering = MCFrame.objects.filter(order_id=phenomenon_id).count()
            mcframe_data.numbering = numbering
            mcframe_data.year = int('20' + instruction_code[2:4])
            if erp_construction_data_num > 0:
                mcframe_data.update_datetime = now
                mcframe_data.update_operator = t_username
            else:
                mcframe_data.entry_datetime = now
                mcframe_data.entry_operator = t_username
            mcframe_data.save()
            # 新ERP刷新対応

            msg = '調達G依頼処理完了'

        # 対応の主キー値取得

        # ログのコメント作成
        comment = "phenomenon_id : " + str(phenomenon_id)
        comment = comment + "\ntarget:phenomenon:"

        operator = t_username

        # 今のstepと次のstepが同じ場合の処理
        if next_step == 232009901:
            action = "stop"
        elif this_step == next_step:
            action = "temporarily_saved"
        # 今のstepと次のstepが違う場合の処理
        else:
            action = "entry"

        # ログを新規登録
        Log(target='phenomenon', target_id=phenomenon_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division).save()

        # 進捗状況を対象(phenomenon)と案件idとstepで抽出･･･異なるstepのprogressが複数作成されるため
        progress_data_list = Progress.objects.filter(target_id=phenomenon_id,
                                                     target='phenomenon', present_step=this_step)
        # 該当stepのprogressが1つだけの場合は各項目を設定
        if progress_data_list.count() == 1:
            progress_data = progress_data_list[0]
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
            else:
                msg = '一時保存完了'
            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

        elif progress_data_list.count() > 1:
            # 同一ステップのprogressが複数存在＞エラー出力
            raise ValueError("There are multiple progresses with the same step.")

        # 次工程に進む時に、原課復旧確認stepのprogressも作成する
        if this_step != next_step and next_step != 232009901:
            progress_data2, created = Progress.objects.get_or_create(target="phenomenon", target_id=phenomenon_id,
                                                                     present_step=232004002)
            # progress_data2.present_operator = phenomenon_data.user_id
            # progress_data2.present_department = phenomenon_data.department_id
            # progress_data2.present_division = phenomenon_data.department.division_cd
            progress_data2.present_operator = order_permit_person_id
            progress_data2.present_department = department
            progress_data2.present_division = DepartmentMaster.objects.get(department_cd=department,
                                                                           lost_flag=0).division_cd
            progress_data2.last_operation_step = this_step
            progress_data2.last_operator = operator
            progress_data2.last_operation_datetime = now
            progress_data2.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data2)

        if this_step != next_step and next_step != 232009901:
            # 履歴情報レコード事前作成
            equipment_history_report_data_pre_entry(request)

        # メール送信用文字列取得
        subject_str, msg_body = maintenance_order_get_mail_data(request, phenomenon_id)

        ary = {
            'msg': msg,
            'order_id': order_id,
            'msg_body': msg_body,
            'subject_str': subject_str,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 外部業者発注判定
def is_erp_construction(contact_request):
    result = False
    if contact_request == 232001011 or contact_request == 232001003:
        result = True
    return result


# 小口工事発注IEPメール送信
@login_required
@require_POST
def maintenance_iep_mail_send(request):
    a = 0
