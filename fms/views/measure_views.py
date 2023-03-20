# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation
# modelesをインポート
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Progress, Log
from fms.models import Order, Phenomenon, Measure, NotificationCheck, Inspection
from fms.models import EquipmentHistoryReport, MaintenanceEquipment
from common.common_def import date_to_many_type
from django.utils.timezone import make_aware
from plantia.models import FcltyLdgr
from .phenomenon_views import get_maintenance_equipment_list
from .common_views import action_num_count
from fms.views.common_def_views import output_log_exception, get_department_person_option_list, get_department_option_list
from fms.views.notice_mail_views import step_notice


# IEP送信メール内容取得
def measure_get_mail_data(phenomenon_id):
    subject_str = ''
    msg_body = ''
    phenomenon_id_str = ''
    department_name = ''
    cost_center = ''
    instruction_no = ''
    project_title = ''
    delivery_date_start = ''
    delivery_date_end = ''
    person_full_name = ''
    measure_order_detail = ''
    account_cd = ''
    str_response_request_date = ''
    eqpt_id_str = ''

    if phenomenon_id != 0:
        phenomenon_id_str = str(phenomenon_id)
        phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id)
        project_title = phenomenon_data.project_title
        subject_str = phenomenon_data.project_title + 'に対する工事依頼の件'
        # department_name = phenomenon_data.department.department_name

        equipment_no = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0)
        first_loop = True
        for equipment_no_item in equipment_no:
            if FcltyLdgr.objects.filter(t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).count() != 0:
                if first_loop:
                    eqpt_id_str = eqpt_id_str + '機器番号　　　　　： ' + FcltyLdgr.objects.get(
                        t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).eqpt_id + '\n'
                    first_loop = False
                else:
                    eqpt_id_str = eqpt_id_str + '　　　　　　　　　　 ' + FcltyLdgr.objects.get(
                        t_fclty_ldgr_skey=equipment_no_item.t_fclty_ldgr_skey).eqpt_id + '\n'

        measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id).count()
        if measure_data_num != 0:
            measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)

            if measure_data.cost_center is not None and measure_data.cost_center is not "":
                cost_center = measure_data.cost_center

            if measure_data.instruction_no is not None and measure_data.instruction_no is not "":
                instruction_no = measure_data.instruction_no

            if measure_data.desired_delivery_date_start is not None and str(
                    measure_data.desired_delivery_date_start) is not "":
                delivery_date_start = date_to_many_type(measure_data.desired_delivery_date_start).str_type_date_jp

            if measure_data.desired_delivery_date_end is not None and str(
                    measure_data.desired_delivery_date_end) is not "":
                delivery_date_end = date_to_many_type(measure_data.desired_delivery_date_end).str_type_date_jp

            if measure_data.work_order_charge_department is not None and measure_data.work_order_charge_department is not "":
                department_name = measure_data.work_order_charge_department.department_name

            if measure_data.work_order_department_charge_person is not None and measure_data.work_order_department_charge_person is not "":
                person_full_name = measure_data.work_order_department_charge_person.last_name + '　' + measure_data.work_order_department_charge_person.first_name

            if measure_data.measure_order_detail is not None and measure_data.measure_order_detail is not "":
                measure_order_detail = measure_data.measure_order_detail

            if measure_data.account_cd is not None and measure_data.account_cd is not "":
                account_cd = measure_data.account_cd

            if measure_data.response_request_date is not None and measure_data.response_request_date is not "":
                str_response_request_date = date_to_many_type(measure_data.response_request_date).str_type_date_jp

    msg_body = msg_body + '管理ＮＯ　　　　　： ' + phenomenon_id_str + '\n'
    msg_body = msg_body + '部署　　　　　　　： ' + department_name + '\n'
    msg_body = msg_body + '原価センタ　　　　： ' + cost_center + '\n'
    msg_body = msg_body + '指図書ＮＯ　　　　： ' + instruction_no + '\n'
    msg_body = msg_body + eqpt_id_str
    msg_body = msg_body + '案件名　　　　　　： ' + project_title + '\n'
    msg_body = msg_body + '希望開始日　　　　： ' + delivery_date_start + '\n'
    msg_body = msg_body + '希望完工日　　　　： ' + delivery_date_end + '\n'
    msg_body = msg_body + '原課担当者　　　　： ' + person_full_name + '\n'
    msg_body = msg_body + '工事／依頼内容　　： ' + measure_order_detail + '\n'
    msg_body = msg_body + '勘定コード　　　　： ' + account_cd + '\n'
    msg_body = msg_body + '依頼日　　　　　　： ' + str_response_request_date + '\n'

    return subject_str, msg_body


# 対応を詳細画面で表示
@login_required
@require_POST
def measure_data_info(request):
    from .maintenance_views import get_maintenance_option_list
    from .maintenance_views import get_maintenance_cost_center, get_maintenance_account_code, get_maintenance_instruction_no
    try:
        t_username = request.user.username
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        new_step = int(request.POST['new_step'])
        this_step = int(request.POST['this_step'])
        user_department_cd = request.POST['user_department_cd']
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        open_new_tab_flag = int(request.POST['open_new_tab_flag'])
        action_button_id = target + '_' + div_id_name + '_action_button'

        if phenomenon_unique_id == 0:
            target_measure_id = 0
            phenomenon_id = 0
            phenomenon_data = ''
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id

            measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id).count()

            if measure_data_num == 0:
                target_measure_id = 0

            else:
                measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)
                target_measure_id = measure_data.id

        # 更新処理
        if target_measure_id > 0:
            measure_data = Measure.objects.get(id=target_measure_id)
            measure_id = measure_data.id
            instruction_no = measure_data.instruction_no
            cost_center = measure_data.cost_center
            account_cd = measure_data.account_cd

            # ノーデータ(NULL)の部分は、空欄にするための処理を実施
            if measure_data.m_exe_cls_skey is not None and measure_data.m_exe_cls_skey is not "":
                item_class = measure_data.m_exe_cls_skey
            else:
                item_class = ""

            if measure_data.malfunction_class is not None and measure_data.malfunction_class is not "":
                malfunction_class = measure_data.malfunction_class
            else:
                malfunction_class = ""

            if measure_data.desired_delivery_date_start is not None and str(
                    measure_data.desired_delivery_date_start) is not "":
                date_str = date_to_many_type(measure_data.desired_delivery_date_start)
                str_desired_delivery_date_f = date_str.str_type_date_jp
            else:
                str_desired_delivery_date_f = ""

            if measure_data.desired_delivery_date_end is not None and str(measure_data.desired_delivery_date_end) is not "":
                date_str = date_to_many_type(measure_data.desired_delivery_date_end)
                str_desired_delivery_date_t = date_str.str_type_date_jp
            else:
                str_desired_delivery_date_t = ""

            if measure_data.work_order_charge_department is not None and measure_data.work_order_charge_department is not "":
                work_order_charge_department = measure_data.work_order_charge_department.department_cd
            else:
                work_order_charge_department = ""

            if measure_data.work_order_department_charge_person is not None and measure_data.work_order_department_charge_person is not "":
                work_order_department_charge_person = measure_data.work_order_department_charge_person.username
                person = work_order_department_charge_person
            else:
                person = ""

            if measure_data.notification_required_flag is not None and str(
                    measure_data.notification_required_flag) is not "":
                str_notification_required_flag = str(measure_data.notification_required_flag)
            else:
                str_notification_required_flag = ""

            if measure_data.diagnosis_class is not None and str(measure_data.diagnosis_class) is not "":
                str_diagnosis_class = str(measure_data.diagnosis_class)
            else:
                str_diagnosis_class = ""

            if measure_data.maintenance_status is not None and str(measure_data.maintenance_status) is not "":
                str_maintenance_status = str(measure_data.maintenance_status)
            else:
                str_maintenance_status = ""

            if measure_data.response_request_date is not None and measure_data.response_request_date is not "":
                date_str = date_to_many_type(measure_data.response_request_date)
                str_response_request_date = date_str.str_type_date_jp
            else:
                str_response_request_date = ""

            if measure_data.measure_order_detail is not None and measure_data.measure_order_detail is not "":
                measure_order_detail = measure_data.measure_order_detail
            else:
                measure_order_detail = ""

            if measure_data.desired_vendor is not None and measure_data.desired_vendor is not "":
                desired_vendor = measure_data.desired_vendor
            else:
                desired_vendor = 'IEP'

            if measure_data.orders_received_person is not None and measure_data.orders_received_person is not "":
                orders_received_person = measure_data.orders_received_person
            else:
                orders_received_person = ""

            if Progress.objects.filter(target='phenomenon', target_id=phenomenon_id) == 1:
                present_step_data = Progress.objects.get(target_id=phenomenon_id, target='phenomenon')
                present_step = present_step_data.present_step
            else:
                present_step_data = Progress.objects.filter(target_id=phenomenon_id, target='phenomenon').first()
                present_step = present_step_data.present_step

        # 新規処理
        else:
            measure_id = 0
            measure_data = ""
            item_class = ""
            malfunction_class = ""
            str_desired_delivery_date_f = ""
            str_desired_delivery_date_t = ""
            instruction_no = ""
            cost_center = ""
            account_cd = ""
            str_notification_required_flag = "0"
            str_diagnosis_class = "0"
            str_maintenance_status = ""
            str_response_request_date = ""
            measure_order_detail = ""
            present_step = this_step
            # 部署 兼務があるので先頭の部署を取り出す
            work_order_charge_department = UserAttribute.objects.filter(username=request.user.username,
                                                                        lost_flag=0).order_by('display_order').first().department
            # 原課担当者
            person = request.user.username
            # person = ""
            desired_vendor = 'IEP'
            orders_received_person = ""

        if item_class == 9:
            item_class_name = "緊急"
        elif item_class == 1:
            item_class_name = "定常"
        elif item_class == 4:
            item_class_name = "自主保全"
        else:
            item_class_name = ""

        if str_notification_required_flag == "0":
            notification_required_str = "不要"
        elif str_notification_required_flag == "1":
            notification_required_str = "必要"
        else:
            notification_required_str = ""

        if str_diagnosis_class == "1":
            diagnosis_class_str = "機械診断"
        elif str_diagnosis_class == "2":
            diagnosis_class_str = "電気整備"
        elif str_diagnosis_class == "3":
            diagnosis_class_str = "計装整備"
        else:
            diagnosis_class_str = ""

        if str_maintenance_status == "0":
            maintenance_status_str = "緊急対応無"
        elif str_maintenance_status == "1":
            maintenance_status_str = "小口依頼済"
        elif str_maintenance_status == "2":
            maintenance_status_str = "電気整備依頼済"
        elif str_maintenance_status == "3":
            maintenance_status_str = "計装整備依頼済"
        else:
            maintenance_status_str = ""

        if phenomenon_data != '':
            # 管理区分サロゲートKEY取得
            mgt_class = MasterMgtCls.objects.get(m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0)
            # 工場名
            facility = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)

            equipmenthistoryreport = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id,
                                                                         lost_flag=0)
            equipment_no_list = list(equipmenthistoryreport.values('t_fclty_ldgr_skey'))
            equipment_no = [d.get('t_fclty_ldgr_skey') for d in equipment_no_list]
            equipment_no = FcltyLdgr.objects.filter(t_fclty_ldgr_skey__in=equipment_no, deleted_flg=0)

            department_cd = phenomenon_data.department_id

        else:
            # 管理区分サロゲートKEY取得
            mgt_class = ''
            # 工場名
            facility = ''
            equipment_no = ''
            department_cd = ''

        # 原課担当部署リスト（optionリストを取得）
        work_order_charge_department_list = get_department_option_list(work_order_charge_department)

        # 原課担当者リスト（optionリストを取得）
        person_lists = get_department_person_option_list(work_order_charge_department, person)

        # 部署情報から原価センター関連の候補リストを取得（optionリストを取得）
        gc_option_data = get_maintenance_option_list(work_order_charge_department, cost_center, instruction_no, account_cd)
        cost_center_option_list = gc_option_data['cost_center_option_list']
        instruction_no_option_list = gc_option_data['instruction_no_option_list']
        account_code_option_list = gc_option_data['account_code_option_list']

        # 保存済の情報からGCシステム側の情報を取得
        instruction_no_data = get_maintenance_instruction_no(instruction_no)
        cost_center_data = get_maintenance_cost_center(cost_center)
        account_cd_data = get_maintenance_account_code(account_cd)

        # メール送信用文字列取得
        subject_str, msg_body = measure_get_mail_data(phenomenon_id)

        if open_new_tab_flag == 0:
            # データ編集機能要否判定
            measure_edit_action_num = 0
            measure_edit_action_num = measure_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                                   target_table='measure').count()
            if DataEntryStepMaster.objects.filter(step_id=present_step, target_table='phenomenon').count() > 0:
                budget_required_spec_detail_edit_flag = 1
            else:
                budget_required_spec_detail_edit_flag = 0
            edit_flag = 0
            if measure_edit_action_num > 0:
                edit_flag = 1

            action_num = action_num_count(t_username, user_department_cd, present_step, target, phenomenon_id)

            if action_num > 0:
                equipment_add_button_display_flag = 1
            else:
                equipment_add_button_display_flag = 0
        else:
            budget_required_spec_detail_edit_flag = 0
            equipment_add_button_display_flag = 0
            edit_flag = 0
            action_num = 0

        data = {
            'measure_data': measure_data,
            'phenomenon_id': phenomenon_id,
            'target_measure_id': target_measure_id,
            'measure_id': measure_id,
            'item_class': item_class,
            'item_class_name': item_class_name,
            'malfunction_class': malfunction_class,
            'desired_delivery_date_f': str_desired_delivery_date_f,
            'desired_delivery_date_t': str_desired_delivery_date_t,

            'cost_center_option_list': cost_center_option_list,
            'instruction_no_option_list': instruction_no_option_list,
            'account_code_option_list': account_code_option_list,
            'cost_center_data': cost_center_data,
            'instruction_no_data': instruction_no_data,
            'account_cd_data': account_cd_data,

            'notification_required_flag': str_notification_required_flag,
            'diagnosis_class': str_diagnosis_class,
            'maintenance_status': str_maintenance_status,
            'response_request_date': str_response_request_date,
            't_username': t_username,
            'measure_order_detail': measure_order_detail,
            'notification_required_str': notification_required_str,
            'diagnosis_class_str': diagnosis_class_str,
            'maintenance_status_str': maintenance_status_str,
            'msg_body': msg_body,
            'subject_str': subject_str,
            'work_order_charge_department_list': work_order_charge_department_list,
            'work_order_charge_department': work_order_charge_department,
            'person_lists': person_lists,
            'person': person,
            'desired_vendor': desired_vendor,
            'orders_received_person': orders_received_person,
            'present_step': present_step,
            'budget_required_spec_detail_edit_flag': budget_required_spec_detail_edit_flag,
            'equipment_add_button_display_flag': equipment_add_button_display_flag,
            'mgt_class': mgt_class,
            'facility': facility,
            'equipment_no': equipment_no,
            'action_button_id': action_button_id,
            'div_id_name': div_id_name,
        }

        if edit_flag == 1 and action_num > 0:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_id, 1)
            return render(request, 'fms/parts/maintenance/measure/measure_edit.html', data)
        else:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_id, 0)
            return render(request, 'fms/parts/maintenance/measure/measure_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 対応情報を登録･更新処理
@login_required
@require_POST
def measure_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        user_attribute_id = int(request.POST["user_attribute_id"])

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_person = operator
            next_division = this_division
            next_department = this_department

        if request.POST["measure_id"] is not "":
            measure_id = int(request.POST["measure_id"])
            phenomenon_id = int(request.POST["phenomenon_id"])
            # sub_no = int(request.POST["sub_no"])
            sub_no = 0
        else:
            if request.POST["phenomenon_id"] is not "":
                phenomenon_id = int(request.POST["phenomenon_id"])
                measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id).count()
                if measure_data_num > 0:
                    measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)
                    measure_id = measure_data.id
                else:
                    measure_id = 0
            else:
                phenomenon_id = 0
                measure_id = 0
            sub_no = 0

        measure_order_detail = request.POST["measure_order_detail"]
        malfunction_class = request.POST["malfunction_class"]
        item_class = int(request.POST["item_class"])
        desired_delivery_date_f_str = request.POST["desired_delivery_date_f"]
        date_str = date_to_many_type(desired_delivery_date_f_str)
        desired_delivery_date_f = date_str.date_type_date

        desired_delivery_date_t_str = request.POST["desired_delivery_date_t"]
        date_str = date_to_many_type(desired_delivery_date_t_str)
        desired_delivery_date_t = date_str.date_type_date

        response_request_date_str = request.POST["response_request_date"]
        date_str = date_to_many_type(response_request_date_str)
        response_request_date = date_str.date_type_date

        order_department = request.POST["order_department"]
        if order_department == "":
            dprc = None
        else:
            dprc = DepartmentMaster.objects.get(department_cd=order_department)

        work_order_department_charge_person = request.POST["order_person"]
        if work_order_department_charge_person == "":
            wodcprc = None
        else:
            wodcprc = User.objects.get(username=work_order_department_charge_person)
        cost_center = request.POST["cost_center"]
        account_cd = request.POST["account_code"]
        desired_vendor = request.POST["desired_vendor"]
        instruction_no = request.POST["instruction_no"]
        orders_received_person = request.POST["orders_received_person"]

        diagnosis_class = int(request.POST["maintenance_diagnosis"])
        if request.POST["maintenance_status"] != "":
            maintenance_status = int(request.POST["maintenance_status"])
        else:
            maintenance_status = ""

        if request.POST["equipment_no"] != "":
            equipment_no = request.POST['equipment_no']
        else:
            equipment_no = ''

        # 新規登録時の処理
        if measure_id == 0:
            measure_data_num = Measure.objects.all().count()
            # 対応のレコードがない時の処理･･･予算id=1 とする
            if measure_data_num == 0:
                this_measure_id = 1
            # 対応のレコードがある時の処理･･･最終の対応idを取得し、対応id=最終の対応id+1 とする
            else:
                last_measure_data = Measure.objects.all().order_by('-id')[0]
                last_measure_id = last_measure_data.id
                this_measure_id = last_measure_data.id + 1
            # 設定した対応idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            measure_data, created = Measure.objects.get_or_create(id=this_measure_id)
            # 登録の日時、登録者を登録
            measure_data.entry_datetime = now
            measure_data.entry_operator = operator
            # 対応のレコードを保存
            measure_data.save()
            # 登録日時、登録者で対応レコードを抽出
            measure_data = Measure.objects.get(entry_datetime=now, entry_operator=operator)
            # 主キーを取得
            measure_unique_id = measure_data.id
            # 主キーで対応レコードを抽出
            measure_data = Measure.objects.get(id=measure_unique_id)
            # 無効FLに値を代入
            measure_data.lost_flag = 0
            # 対応のレコードを保存
            measure_data.save()
            action_type = "add"

        # 更新時の処理
        else:
            # 対応id(変数)に渡された案件idをセット
            this_measure_id = measure_id
            # 対象の状況レコードを抽出
            measure_data = Measure.objects.get(id=this_measure_id)
            # 主キーを取得
            measure_unique_id = measure_data.id
            action_type = "edit"

        if equipment_no is not '':
            maintenance_equipment_data, created = MaintenanceEquipment.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                             t_fclty_ldgr_skey=equipment_no,
                                                                                             lost_flag=0)
            if created:
                maintenance_equipment_data.entry_datetime = now
                maintenance_equipment_data.entry_operator = operator
                maintenance_equipment_data.rev_no = 0

                maintenance_equipment_data.save()

        # 主キーで対応レコードを抽出
        measure_data = Measure.objects.get(id=measure_unique_id)
        measure_data.phenomenon_id = phenomenon_id
        measure_data.sub_no = sub_no
        measure_data.measure_order_detail = measure_order_detail
        measure_data.m_exe_cls_skey = item_class
        measure_data.malfunction_class = malfunction_class
        measure_data.orders_received_person = orders_received_person

        if desired_delivery_date_f != "":
            measure_data.desired_delivery_date_start = desired_delivery_date_f
        if desired_delivery_date_t != "":
            measure_data.desired_delivery_date_end = desired_delivery_date_t
        measure_data.work_order_charge_department = dprc
        measure_data.work_order_department_charge_person = wodcprc
        measure_data.cost_center = cost_center
        measure_data.account_cd = account_cd
        measure_data.desired_vendor = desired_vendor
        measure_data.instruction_no = instruction_no
        measure_data.diagnosis_class = diagnosis_class
        if maintenance_status != "":
            measure_data.maintenance_status = maintenance_status
        if response_request_date != "":
            measure_data.response_request_date = response_request_date

        if action_type == "add":
            measure_data.entry_datetime = now
            measure_data.entry_operator = operator
            msg = "対応方針データ新規登録完了！！"
        # 更新の場合の処理
        else:
            measure_data.update_datetime = now
            measure_data.update_operator = operator
            msg = "対応方針データ更新完了！！"

        # 対応のレコードを保存
        measure_data.save()

        # 対応の主キー値取得
        measure_unique_id = measure_data.id

        # ログのコメント作成
        comment = "measure_id : " + str(measure_unique_id)
        comment = comment + "\ntarget:phenomenon:"

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            action = "temporarily_saved"

        # 今のstepと次のstepが違う場合の処理
        else:
            action = "entry"

        # ログを新規登録
        Log(target='phenomenon', target_id=phenomenon_id, action=action, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division).save()

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
            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

        elif progress_data_list.count() > 1:
            # 同一ステップのprogressが複数存在＞エラー出力
            raise ValueError("There are multiple progresses with the same step.")

        # メール送信用文字列取得
        subject_str, msg_body = measure_get_mail_data(phenomenon_id)

        equipment_list = get_maintenance_equipment_list(phenomenon_id, 1)

        ary = {
            'msg': msg,
            'measure_id': measure_unique_id,
            'msg_body': msg_body,
            'subject_str': subject_str,
            'equipment_list': equipment_list,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def measure_change_department(request):
    try:
        order_department = request.POST['order_department']
        person_lists = get_department_person_option_list(order_department)
        data = {
            'person_lists': person_lists,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
