# datetimeをインポート
import datetime
import mimetypes
import os
import openpyxl
import traceback
# base_dir 取得のためのモジュールインポート
from config.settings.settings_common import BASE_DIR
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET
from fms.models import Measure, Order, ErpConstruction, MCFrame, OrderForIEP, Phenomenon, Progress, Log, SubmissionDocument
from fms.models import UserAttribute, DepartmentMaster, TaxMaster, SupplierMaster, DataEntryStepMaster
from fms.models import MaintenanceEstimate, MaintenanceEstimateVendor
from fms.models import EquipmentHistoryReport
from gcsystem.models import UserMaster
from gcsystem.models import QuantityUnitMaster
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation
from common.common_def import date_to_many_type
from .common_views import action_num_count
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.common_def_views import get_template_file_path, get_output_file_path
from fms.views.notice_mail_views import step_notice


# 対応を詳細画面で表示
@login_required
@require_POST
def maintenance_order_vendor_data_info(request):
    from .maintenance_views import get_maintenance_option_list
    from .maintenance_views import get_maintenance_cost_center, get_maintenance_account_code, get_maintenance_instruction_no
    try:
        t_username = request.user.username

        # full_name = request.user.get_full_name()

        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        if phenomenon_unique_id == 0:
            target_inspection_id = 0
            # department_name = ''
            factory_name = ''
            order_data_num = 0
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id
            # department_name = phenomenon_data.department.department_name
            factory_data = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)
            factory_name = factory_data.location_nm_1
            order_data_num = Order.objects.filter(phenomenon_id=phenomenon_id).count()
            if order_data_num == 0:
                target_order_id = 0
            else:
                order_data = Order.objects.get(phenomenon_id=phenomenon_id)
                target_order_id = order_data.id
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        target_step_id = int(request.POST['target_step_id'])
        department_cd = ""

        # 復旧完了確認の担当部署を取得
        measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count()
        if measure_data_num == 1:
            measure_data = Measure.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)

            if measure_data.malfunction_class is not None and measure_data.malfunction_class is not "":
                malfunction_class = measure_data.malfunction_class
            else:
                malfunction_class = ""

            # if measure_data.work_order_charge_department is not None \
            #         and measure_data.work_order_charge_department is not "":
            #     measure_work_order_charge_department = measure_data.work_order_charge_department.department_cd
            #     department_name = measure_data.work_order_charge_department.department_name
            # else:
            #     measure_work_order_charge_department = ""
            #     department_name = ''

            if measure_data.work_order_charge_department is not None:
                department_cd = measure_data.work_order_charge_department.department_cd
            else:
                department_cd = ''

        else:
            malfunction_class = ""
            # measure_work_order_charge_department = ""
            # department_name = ''

        if order_data_num > 0:
            order_data = Order.objects.get(phenomenon_id=phenomenon_id)
            order_name_for_vendor = order_data.order_name + order_data.order_name_extension_name
            order_name_extension_name = order_data.order_name_extension_name
            order_detail_for_vendor = order_data.order_detail_for_vendor

            if order_data.order_detail_for_vendor is not None and order_data.order_detail_for_vendor is not '':
                order_detail = order_detail_for_vendor
                print_check = 1
            else:
                order_detail = order_data.order_detail
                print_check = 0

            if order_data.department_id is not None \
                    and order_data.department_id is not "":
                measure_work_order_charge_department = order_data.department_id
                department_name = order_data.department.department_name
                department_cd = order_data.department.department_cd
            else:
                measure_work_order_charge_department = ""
                department_name = ''
        else:
            order_name_for_vendor = ""
            order_name_extension_name = ""
            order_detail = ""
            print_check = 0
            order_data = ""
            measure_work_order_charge_department = ""
            department_name = ''

        # 小口見積情報を取得
        if MaintenanceEstimate.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            estimates_data = MaintenanceEstimate.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id').first()
            estimates_vendor_list = MaintenanceEstimateVendor.objects.filter(phenomenon_id=phenomenon_id,
                                                                             vendor_no=estimates_data.confirmed_vendor_no,
                                                                             lost_flag=0).order_by('vendor_no')
            if estimates_vendor_list.count() == 1:
                estimates_vendor = estimates_vendor_list.first()
            else:
                estimates_vendor = ''
        else:
            estimates_vendor = ''

        erp_construction_data_num = ErpConstruction.objects.filter(order_id=phenomenon_id, work_class='SW').count()

        if erp_construction_data_num > 0:
            erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id, work_class='SW')
            tax_cd = erp_construction_data.consumption_tax_code
            vendor_code = erp_construction_data.vendor_code
            cost_center = erp_construction_data.cost_center
            account_code = erp_construction_data.account_code
            instruction_no = erp_construction_data.instruction_code
            if erp_construction_data.item_text is not None and erp_construction_data.item_text is not "":
                order_name_for_vendor = erp_construction_data.item_text
                order_name_extension_name = ""
            if erp_construction_data.construction_start_date is not None and erp_construction_data.construction_start_date is not "":
                start_date_str = erp_construction_data.construction_start_date
                start_date_year_str = start_date_str[0:4]
                start_date_month_str = start_date_str[4:6]
                start_date_day_str = start_date_str[6:8]
                start_date = start_date_year_str + "年" + start_date_month_str + "月" + start_date_day_str + "日"
            else:
                start_date = ''
            if erp_construction_data.delivery_date is not None and erp_construction_data.delivery_date is not "":
                end_date_str = erp_construction_data.delivery_date
                end_date_year_str = end_date_str[0:4]
                end_date_month_str = end_date_str[4:6]
                end_date_day_str = end_date_str[6:8]
                end_date = end_date_year_str + "年" + end_date_month_str + "月" + end_date_day_str + "日"
            else:
                end_date = ''
            if erp_construction_data.order_date is not None and erp_construction_data.order_date is not "":
                order_date_str = erp_construction_data.order_date
                order_date_year_str = order_date_str[0:4]
                order_date_month_str = order_date_str[4:6]
                order_date_day_str = order_date_str[6:8]
                order_date = order_date_year_str + "年" + order_date_month_str + "月" + order_date_day_str + "日"
            else:
                order_date = ''

            mcframe_data = MCFrame.objects.get(order_id=phenomenon_id, work_class='SW')
            order_no = mcframe_data.order_no if mcframe_data.order_no is not None else ""

            if erp_construction_data.vendor_code is not None and erp_construction_data.vendor_code is not "":
                vendor_data = SupplierMaster.objects.get(supplier_cd=vendor_code)
                vendor_name = vendor_data.supplier_name
                vendor_code = erp_construction_data.vendor_code
            else:
                vendor_code = ''
                # 見積情報から業者名を取得
                if estimates_vendor is not "":
                    vendor_name = estimates_vendor.vendor_name
                else:
                    vendor_name = ''

            if tax_cd is not None and tax_cd is not "":
                consumption_tax_data = TaxMaster.objects.get(tax_cd=tax_cd)
                tax_text = consumption_tax_data.text
            else:
                tax_text = ''

            if erp_construction_data.total_price is not None:
                total_price_raw = erp_construction_data.total_price
                # 3桁区切りの「,」挿入処理
                total_price = "{:,}".format(total_price_raw)
            else:
                if estimates_vendor is not "":
                    total_price = "{:,}".format(estimates_vendor.estimate_price)
                else:
                    total_price = ''

            discount_price = erp_construction_data.discount_price
            if discount_price is not None:
                # 3桁区切りの「,」挿入処理
                discount_price = "{:,}".format(discount_price)
            else:
                if estimates_vendor is not "":
                    discount_price = "{:,}".format(estimates_vendor.estimate_price - estimates_vendor.price_after_discount)
                else:
                    discount_price = ''

            if erp_construction_data.discount_price is not None and erp_construction_data.total_price is not None:
                real_price = erp_construction_data.total_price - erp_construction_data.discount_price
                # 3桁区切りの「,」挿入処理
                real_price = "{:,}".format(real_price)
            else:
                if estimates_vendor is not "":
                    real_price = "{:,}".format(estimates_vendor.price_after_discount)
                else:
                    real_price = ''

            storage_space_rem = erp_construction_data.storage_space_rem
            if storage_space_rem is None:
                storage_space_rem = department_name + " " + factory_name
            if erp_construction_data.erp_errormsg is not None and erp_construction_data.erp_errormsg is not "":
                erp_errormsg = erp_construction_data.erp_errormsg
            else:
                erp_errormsg = ''
        else:
            vendor_name = ''
            erp_construction_data = ''
            tax_text = ''
            storage_space_rem = department_name + " " + factory_name
            start_date = ''
            end_date = ''
            order_date = ''
            order_no = ''
            cost_center = ''
            account_code = ''
            instruction_no = ''
            erp_errormsg = ''
            vendor_code = ''
            total_price = ""
            discount_price = ""
            real_price = ""

        purchase_group_code = "YA2"
        purchase_person = ""
        consumption_tax_code = ""
        vendor_lists = SupplierMaster.objects.filter(lost_flag=0)
        consumption_tax_lists = TaxMaster.objects.filter(lost_flag=0)

        if Progress.objects.filter(target='phenomenon', target_id=phenomenon_id, present_step=target_step_id).count() == 1:
            present_step_data = Progress.objects.get(target_id=phenomenon_id, target='phenomenon', present_step=target_step_id)
            present_step = present_step_data.present_step
            action_num = action_num_count(t_username, user_department_cd, present_step, target, phenomenon_id)

            # データ編集機能要否判定
            maintenance_order_vendor_edit_action_num = 0
            maintenance_order_vendor_edit_action_num = maintenance_order_vendor_edit_action_num + DataEntryStepMaster.objects.filter(
                step_id=present_step, target_table='erp_construction').count()
        else:
            action_num = 0
            maintenance_order_vendor_edit_action_num = 0

        # 部署情報から原価センター関連の候補リストを取得（optionリストを取得）
        gc_option_data = get_maintenance_option_list(department_cd, cost_center, instruction_no, account_code)
        cost_center_option_list = gc_option_data['cost_center_option_list']
        instruction_no_option_list = gc_option_data['instruction_no_option_list']
        account_code_option_list = gc_option_data['account_code_option_list']

        # 保存済の情報からGCシステム側の情報を取得
        instruction_no_data = get_maintenance_instruction_no(instruction_no)
        cost_center_data = get_maintenance_cost_center(cost_center)
        account_cd_data = get_maintenance_account_code(account_code)

        data = {
            'purchase_group_code': purchase_group_code,
            'purchase_person': purchase_person,
            'vendor_code': vendor_code,
            'total_price': total_price,
            'discount_price': discount_price,
            'real_price': real_price,
            'storage_space_rem': storage_space_rem,
            'consumption_tax_code': consumption_tax_code,
            'vendor_lists': vendor_lists,
            'consumption_tax_lists': consumption_tax_lists,
            'order_data': order_data,
            'order_no': order_no,
            'erp_construction_data': erp_construction_data,
            'this_user': t_username,
            'tax_text': tax_text,
            'vendor_name': vendor_name,

            'cost_center_option_list': cost_center_option_list,
            'instruction_no_option_list': instruction_no_option_list,
            'account_code_option_list': account_code_option_list,
            'cost_center_data': cost_center_data,
            'instruction_no_data': instruction_no_data,
            'account_cd_data': account_cd_data,

            'start_date': start_date,
            'end_date': end_date,
            'order_detail': order_detail,
            'order_name_for_vendor': order_name_for_vendor,
            'order_name_extension_name': order_name_extension_name,
            'order_date': order_date,
            'print_check': print_check,
            'erp_errormsg': erp_errormsg,
            'action_button_id': action_button_id,
            'measure_work_order_charge_department': measure_work_order_charge_department,
            'malfunction_class': malfunction_class,
        }

        edit_flag = 0
        if maintenance_order_vendor_edit_action_num > 0 and action_num > 0:
            edit_flag = 1
        if edit_flag == 1:
            return render(request, 'fms/parts/maintenance/maintenance_order_vendor/maintenance_order_vendor_edit.html',
                          data)
        else:
            return render(request, 'fms/parts/maintenance/maintenance_order_vendor/maintenance_order_vendor_info.html',
                          data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 小口工事発注レコード作成
@login_required
@require_POST
def maintenance_order_vendor_entry(request):
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
        vendor_code = request.POST['vendor_code']
        total_price_str = request.POST['total_price']
        discount_price_str = request.POST['discount_price']
        storage_space_rem = request.POST['storage_space_rem']
        consumption_tax_code = request.POST['consumption_tax_code']
        cost_center = request.POST['cost_center']
        account_code = request.POST['account_code']
        instruction_no = request.POST['instruction_no']
        order_name = request.POST['order_name']
        order_detail = request.POST['order_detail']
        step_progress_type = request.POST['action_type']
        start_date_str = request.POST['start_date']
        date_str = date_to_many_type(start_date_str)
        start_date_erp = date_str.str_type_date_erp
        ''' 今この下の処理は、上記関数「date_to_many_type(value)」に変更
        position_year = start_date_str.find('年')
        position_month = start_date_str.find('月')
        position_day = start_date_str.find('日')
    
        start_date_year_str = start_date_str[0:4]
        if position_month == 6:
            start_date_month_str = '0' + start_date_str[5:6]
        else:
            start_date_month_str = start_date_str[5:7]
        if position_day - position_month == 2:
            start_date_day_str = '0' + start_date_str[position_month + 1:position_day]
        else:
            start_date_day_str = start_date_str[position_month + 1:position_day]
        start_date = start_date_year_str + start_date_month_str + start_date_day_str
        '''

        end_date_str = request.POST['end_date']
        date_str = date_to_many_type(end_date_str)
        end_date_erp = date_str.str_type_date_erp
        ''' 今この下の処理は、上記関数「date_to_many_type(value)」に変更
        position_year = end_date_str.find('年')
        position_month = end_date_str.find('月')
        position_day = end_date_str.find('日')
    
        end_date_year_str = end_date_str[0:4]
        if position_month == 6:
            end_date_month_str = '0' + end_date_str[5:6]
        else:
            end_date_month_str = end_date_str[5:7]
        if position_day - position_month == 2:
            end_date_day_str = '0' + end_date_str[position_month + 1:position_day]
        else:
            end_date_day_str = end_date_str[position_month + 1:position_day]
        end_date = end_date_year_str + end_date_month_str + end_date_day_str
        '''

        order_date_str = request.POST['order_date']
        position_year = order_date_str.find('年')
        position_month = order_date_str.find('月')
        position_day = order_date_str.find('日')

        order_date_year_str = order_date_str[0:4]
        if position_month == 6:
            order_date_month_str = '0' + order_date_str[5:6]
        else:
            order_date_month_str = order_date_str[5:7]
        if position_day - position_month == 2:
            order_date_day_str = '0' + order_date_str[position_month + 1:position_day]
        else:
            order_date_day_str = order_date_str[position_month + 1:position_day]
        order_date = order_date_year_str + order_date_month_str + order_date_day_str

        gc_user_data = UserMaster.objects.get(ＮＴユーザー名=t_username)
        purchase_person = gc_user_data.担当別購買グループ

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
            sub_no = 0
        else:
            order_id = 0
            if request.POST["phenomenon_id"] is not "":
                phenomenon_id = int(request.POST["phenomenon_id"])
            else:
                phenomenon_id = 0
            sub_no = 0

        order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        order_data.order_detail_for_vendor = order_detail
        order_data.save()

        erp_construction_data_num = ErpConstruction.objects.filter(order_id=phenomenon_id).count()

        erp_construction_data, created = ErpConstruction.objects.get_or_create(order_id=phenomenon_id)
        erp_construction_data.vendor_code = vendor_code
        erp_construction_data.purchase_person = purchase_person

        total_price_str = total_price_str.replace(',', '')
        total_price = int(total_price_str)
        erp_construction_data.total_price = total_price

        discount_price_str = discount_price_str.replace(',', '')
        discount_price = int(discount_price_str)
        erp_construction_data.discount_price = discount_price
        # if discount_price == 0:
        #     erp_construction_data.discount_price = None
        # else:
        #     erp_construction_data.discount_price = discount_price
        erp_construction_data.storage_space_rem = storage_space_rem.replace("\t", " ")  # タブを消去
        erp_construction_data.consumption_tax_code = consumption_tax_code
        erp_construction_data.cost_center = cost_center
        erp_construction_data.account_code = account_code
        erp_construction_data.instruction_code = instruction_no
        erp_construction_data.construction_start_date = start_date_erp
        erp_construction_data.delivery_date = end_date_erp
        erp_construction_data.item_text = order_name.replace("\t", " ")  # タブを消去
        erp_construction_data.order_detail = order_detail
        erp_construction_data.order_date = order_date
        # 外部業者発注からのstep移行時のみstatusを"0"に
        if step_progress_type == 'comp' and this_step == 232001011 and next_step == 232009901:
            erp_construction_data.status = 10
            erp_construction_data.erp_errormsg = ""
            msg = '案件中止処理完了'
        elif step_progress_type == 'comp' and this_step == 232001011:
            erp_construction_data.status = 0
            erp_construction_data.erp_errormsg = ""
            msg = '調達G発注処理完了'
        else:
            msg = '調達G発注処理一時保存完了'

        if erp_construction_data_num > 0:
            erp_construction_data.update_datetime = now
            erp_construction_data.update_operator = t_username
            action_type = 'edit'

        else:
            erp_construction_data.entry_datetime = now
            erp_construction_data.entry_operator = t_username
            action_type = 'add'

        erp_construction_data.department = this_department
        erp_construction_data.division = this_division
        erp_construction_data.entry_operator = t_username

        erp_construction_data.save()

        # 新ERP刷新対応
        mcframe_data, created = MCFrame.objects.get_or_create(order_id=phenomenon_id)
        mcframe_data.vendor_code = vendor_code
        mcframe_data.purchase_person = purchase_person
        mcframe_data.total_price = total_price
        # mcframe_data.discount_price = discount_price
        if discount_price == 0:
            mcframe_data.discount_price = None
        else:
            mcframe_data.discount_price = discount_price
        mcframe_data.storage_space_rem = storage_space_rem.replace("\t", " ")  # タブを消去
        mcframe_data.consumption_tax_code = consumption_tax_code
        mcframe_data.cost_center = cost_center
        mcframe_data.account_code = account_code
        mcframe_data.instruction_code = instruction_no
        mcframe_data.construction_start_date = start_date_erp
        mcframe_data.delivery_date = end_date_erp
        mcframe_data.item_text = order_name.replace("\t", " ")  # タブを消去
        mcframe_data.order_detail = order_detail
        mcframe_data.order_date = order_date
        mcframe_data.order_no = request.POST["order_no"] if request.POST["order_no"] is not '' else None
        mcframe_data.order_type_classification = 8
        numbering = MCFrame.objects.filter(order_id=phenomenon_id).count()
        mcframe_data.numbering = numbering
        mcframe_data.year = int('20' + instruction_no[2:4])
        # 外部業者発注からのstep移行時のみstatusを"0"に
        if step_progress_type == 'comp' and this_step == 232001011 and next_step == 232009901:
            mcframe_data.status = 10
            mcframe_data.erp_errormsg = ""
            msg = '案件中止処理完了'
        elif step_progress_type == 'comp' and this_step == 232001011:
            mcframe_data.status = 0
            mcframe_data.erp_errormsg = ""
            msg = '調達G発注処理完了'
        else:
            msg = '調達G発注処理一時保存完了'
        if erp_construction_data_num > 0:
            mcframe_data.update_datetime = now
            mcframe_data.update_operator = t_username
            action_type = 'edit'

        else:
            mcframe_data.entry_datetime = now
            mcframe_data.entry_operator = t_username
            action_type = 'add'

        mcframe_data.department = this_department
        mcframe_data.division = this_division
        mcframe_data.entry_operator = t_username

        mcframe_data.save()
        # 新ERP刷新対応

        order_unique_id = erp_construction_data.id

        # ログのコメント作成
        comment = "order_id : " + str(order_unique_id)
        comment = comment + "\ntarget:phenomenon:"

        operator = t_username

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
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
            # 進捗状況のレコードを保存
            progress_data.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

        elif progress_data_list.count() > 1:
            # 同一ステップのprogressが複数存在＞エラー出力
            raise ValueError("There are multiple progresses with the same step.")

        # ERP転送に進む時に、調達検収側のProgressを作成
        if this_step != next_step and next_step == 232001021:
            progress_data2, created = Progress.objects.get_or_create(target="phenomenon", target_id=phenomenon_id,
                                                                     present_step=232008001)
            # 調達Gのメンバーが操作するので、ログインユーザーを調達検収の担当者に割り当てる
            progress_data2.present_operator = t_username
            progress_data2.present_department = 'SI'
            progress_data2.present_division = 'KOUMU'
            progress_data2.last_operation_step = this_step
            progress_data2.last_operator = operator
            progress_data2.last_operation_datetime = now
            progress_data2.save()

        # 工程完了に原課復旧確認stepも完了工程へ移行(旧データは無い場合があるので、filterでチェック)
        if next_step == 232009901:
            restoration_check_stepdata_list = Progress.objects.filter(target="phenomenon",
                                                                      target_id=phenomenon_id, present_step=232004002)
            if restoration_check_stepdata_list.count() > 0:
                for restoration_check_stepdata in restoration_check_stepdata_list:
                    restoration_check_stepdata.present_operator = 'end'
                    restoration_check_stepdata.present_department = 'END'
                    restoration_check_stepdata.present_division = 'END'
                    restoration_check_stepdata.last_operation_step = restoration_check_stepdata.present_step
                    restoration_check_stepdata.last_operator = operator
                    restoration_check_stepdata.last_operation_datetime = now
                    restoration_check_stepdata.present_step = 232004003
                    restoration_check_stepdata.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 見積依頼書excel作成
@login_required
@require_GET
def make_request_for_quotation(request, phenomenon_id):
    try:
        DIFF_JST_FROM_UTC = 18
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        date_str = date_to_many_type(now)
        today_str = date_str.str_type_date_jp
        start_datetime = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        operator = request.user.username

        target_folder = 'result_request_for_quotation'
        templates_file_name = 'request_for_quotation'
        create_file_name = 'result_request_for_quotation'
        templates_file_ext = '.xlsx'

        # 共有フォルダパス取得
        templates_file_full_name = templates_file_name + templates_file_ext
        templates_file_path = get_template_file_path(target_folder, templates_file_full_name)

        wb_new_file = openpyxl.load_workbook(templates_file_path)
        order_data = Order.objects.get(phenomenon_id=phenomenon_id)
        erp_construction_data = ErpConstruction.objects.get(order_id=phenomenon_id)
        ordering_unit = erp_construction_data.ordering_unit

        if erp_construction_data.construction_start_date is not None and erp_construction_data.construction_start_date is not "":
            start_date_str = erp_construction_data.construction_start_date
            start_date_year_str = start_date_str[0:4]
            start_date_month_str = start_date_str[4:6]
            start_date_day_str = start_date_str[6:8]
            start_date = start_date_year_str + "年" + start_date_month_str + "月" + start_date_day_str + "日"
        else:
            start_date = ''

        if erp_construction_data.delivery_date is not None and erp_construction_data.delivery_date is not "":
            end_date_str = erp_construction_data.delivery_date
            end_date_year_str = end_date_str[0:4]
            end_date_month_str = end_date_str[4:6]
            end_date_day_str = end_date_str[6:8]
            end_date = end_date_year_str + "年" + end_date_month_str + "月" + end_date_day_str + "日"
        else:
            end_date = ''

        quantity_unit_data = QuantityUnitMaster.objects.get(数量単位コード=ordering_unit)
        unit = quantity_unit_data.単位テキスト

        ws_new_sheet = wb_new_file['Sheet1']

        ws_new_sheet['O2'].value = today_str  # 見積依頼日
        ws_new_sheet['G19'].value = erp_construction_data.order_id  # 見積依頼NO
        ws_new_sheet['G21'].value = erp_construction_data.item_text  # 品目名称
        ws_new_sheet['G23'].value = order_data.order_detail_for_vendor  # 工事/依頼内容
        # ws_new_sheet['G27'].value = str(erp_construction_data.order_amount) + unit  # 数量
        ws_new_sheet['G29'].value = start_date + " ～ " + end_date  # 希望工期
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
