# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# modelesをインポート
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Progress, Log
from fms.models import Phenomenon, MaintenanceEquipment, Measure, Inspection, Order, EquipmentHistoryReport
from .phenomenon_views import get_maintenance_equipment_list
from .common_views import action_num_count
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation, MasterCauseCode, MasterResultCode
from plantia.models import MasterPhenomenonCode
from plantia.models import MasterExeCls, MasterConditionCode, MasterPositionCode, MasterTreatmentCode, ServiceSpecmanList, ServiceSpecmanListValue, ServiceUser
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 履歴情報を表示
@login_required
@require_POST
def target_equipment_history_report_data_info(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
        equipment_history_report_data_num = EquipmentHistoryReport.objects.filter(phenomenon_id2=phenomenon_data.phenomenon_id).count()
        equipment_history_report_data = ''
        this_step = request.POST['this_step']
        user_department_cd = request.POST['user_department_cd']

        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'

        open_new_tab_flag = int(request.POST['open_new_tab_flag'])

        if equipment_history_report_data_num > 0:
            equipment_history_report_data = EquipmentHistoryReport.objects.get(phenomenon_id2=phenomenon_data.phenomenon_id,
                                                                               lost_flag=0)

        # 管理区分サロゲートKEY取得
        mgt_class = MasterMgtCls.objects.get(m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0)
        # 工場名
        facility = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)

        equipmenthistoryreport = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0)
        equipment_no_list = list(equipmenthistoryreport.values('t_fclty_ldgr_skey'))
        equipment_no = [d.get('t_fclty_ldgr_skey') for d in equipment_no_list]
        equipment_no = FcltyLdgr.objects.filter(t_fclty_ldgr_skey__in=equipment_no, deleted_flg=0)

        if open_new_tab_flag == 0:
            action_num = action_num_count(t_username, user_department_cd, this_step, target, phenomenon_data.phenomenon_id)

            # データ編集機能要否判定
            report_origin_g_edit_action_num = 0
            report_origin_g_edit_action_num = report_origin_g_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='report_origin_g').count()

            edit_flag = 0

            if report_origin_g_edit_action_num > 0 and action_num > 0:
                edit_flag = 1
        else:
            report_origin_g_edit_action_num = 0
            action_num = 0
            edit_flag = 0

        data = {
            # 'this_step': this_step,
            'phenomenon_data': phenomenon_data,
            'equipment_history_report_data': equipment_history_report_data,
            't_username': t_username,
            'mgt_class': mgt_class,
            'facility': facility,
            'equipment_no': equipment_no,
            # SelectList
            'equipment_list': '',
            'action_button_id': action_button_id,
        }

        if edit_flag == 1:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_data.phenomenon_id, 0)
            return render(request, 'fms/parts/maintenance/report_origin_g/report_origin_g_edit.html', data)

        else:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_data.phenomenon_id, 0)
            return render(request, 'fms/parts/maintenance/report_origin_g/report_origin_g_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 履歴情報を登録･更新処理
@login_required
@require_POST
def target_equipment_history_report_data_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        next_person = request.POST["next_person"]
        this_division = request.POST["this_division"]
        this_department = request.POST["this_department"]
        user_attribute_id = int(request.POST['user_attribute_id'])
        equipment_history_report_id = request.POST['equipment_history_report_id']
        phenomenon_id = int(request.POST["phenomenon_id"])

        special_note_production = request.POST["special_note_production"]
        items_to_be_sent_production = request.POST["items_to_be_sent_production"]
        stop_time = request.POST['stop_time']

        phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)
        if EquipmentHistoryReport.objects.filter(phenomenon_id2=phenomenon_id, lost_flag=0).count() == 0:
            action_type = "add"
        else:
            action_type = "edit"

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

        equipment_history_report_data, created = EquipmentHistoryReport.objects.get_or_create(phenomenon_id2=phenomenon_id, lost_flag=0)
        equipment_history_report_data.special_note_production = special_note_production
        equipment_history_report_data.items_to_be_sent_production = items_to_be_sent_production
        equipment_history_report_data.update_datetime = now
        equipment_history_report_data.update_operator = operator
        equipment_history_report_data.stop_time = stop_time if stop_time is not '' else None
        msg = "履歴データ登録完了！！"

        # 履歴のレコードを保存
        equipment_history_report_data.save()

        # 履歴の主キー値取得
        equipment_history_report_unique_id = equipment_history_report_data.id

        # ログのコメント作成
        comment = "equipment_history_report_id : " + str(equipment_history_report_unique_id)
        comment = comment + "\ntarget:phenomenon:"

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            action = "temporarily_saved"

        # 今のstepと次のstepが違う場合の処理
        else:
            action = "entry"

        # ログを新規登録
        Log(target='phenomenon', target_id=phenomenon_id, action=action,
            operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division).save()

        # 進捗状況を対象(phenomenon)と案件idとstepで抽出･･･異なるstepのprogressが複数作成されるため
        progress_data = Progress.objects.get(target="phenomenon", target_id=phenomenon_id, present_step=this_step)
        # 各項目を設定
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

        equipment_list = get_maintenance_equipment_list(phenomenon_id, 1)
        ary = {
            'msg': msg,
            'equipment_history_report_unique_id': equipment_history_report_unique_id,
            'equipment_list': equipment_list,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済機器履歴一覧表示処理
@require_POST
def equipment_history_report_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        if request.POST['phenomenon_id'] != "":
            str_phenomenon_id = request.POST['phenomenon_id']
            phenomenon_id = int(request.POST['phenomenon_id'])
        else:
            str_phenomenon_id = "0"
            phenomenon_id = 0
        if request.POST['sub_no'] != "":
            str_sub_no = request.POST['sub_no']
            sub_no = int(request.POST['sub_no'])
        else:
            str_sub_no = "0"
            sub_no = 0

        # 登録済機器履歴のレコード数を取得
        equipment_history_report_lists_num = EquipmentHistoryReport.objects.filter(phenomenon_id=phenomenon_id, sub_no=sub_no, lost_flag=0).count()

        # 登録済機器履歴の一覧を取得
        sql = """ SELECT fms_equipment_history_report.*, fms_materialstatemaster.state_name, c_u.unit as c_unit """
        sql = sql + """ , p_u.unit as p_unit  """
        sql = sql + """ FROM ((fms_equipment_history_report """
        sql = sql + """ LEFT JOIN fms_materialstatemaster ON fms_budgetmaterial.state_id=fms_materialstatemaster.state_id) """
        sql = sql + """ LEFT JOIN fms_concentrationunitmaster c_u ON fms_budgetmaterial.concentration_unit_id=c_u.unit_id )"""
        sql = sql + """ LEFT JOIN fms_pressureunitmaster p_u ON fms_budgetmaterial.pressure_unit_id=p_u.unit_id """
        sql = sql + """ WHERE fms_equipment_history_report.phenomenon_id=""" + str_phenomenon_id + """ AND fms_equipment_history_report.sub_no=""" + str_sub_no + """ AND fms_budgetmaterial.lost_flag=0 """

        equipment_history_report_lists = EquipmentHistoryReport.objects.all().raw(sql)

        data = {
            'equipment_history_report_lists': equipment_history_report_lists,
            'equipment_history_report_lists_num': equipment_history_report_lists_num,
        }

        return render(request, 'fms/parts/maintenance/report_maintenance_g/equipment_history_report_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
