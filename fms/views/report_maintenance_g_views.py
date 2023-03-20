# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# modelesをインポート
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Progress, Log
from fms.models import Phenomenon, MaintenanceEquipment, Measure, Inspection, Order, EquipmentHistoryReport
from .phenomenon_views import get_maintenance_equipment_list
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation, MasterCauseCode, MasterResultCode
from plantia.models import MasterPhenomenonCode, MntceLdgr
from plantia.models import MasterExeCls, MasterConditionCode, MasterPositionCode, MasterTreatmentCode, \
    ServiceSpecmanList, ServiceSpecmanListValue, ServiceUser
from common.common_def import date_to_many_type
from django.utils.timezone import make_aware
from fms.views.common_views import blank_to_None, action_num_count
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
        construction_representative = ''
        user_department_cd = request.POST['user_department_cd']
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'
        this_step = request.POST['this_step']
        open_new_tab_flag = int(request.POST['open_new_tab_flag'])

        if equipment_history_report_data_num > 0:
            equipment_history_report_data = EquipmentHistoryReport.objects.get(phenomenon_id2=phenomenon_data.phenomenon_id, lost_flag=0)
            if equipment_history_report_data.construction_representative is not None and equipment_history_report_data.construction_representative != '':
                representative_name = str.lower(equipment_history_report_data.construction_representative)
                # IEP小口システムからの取り込み情報から、PLANTIA側DBを参照して工事担当者取得
                representative_user = User.objects.get(username=representative_name)
                representative_user_name = representative_user.last_name + ' ' + representative_user.first_name
                representative_list = ServiceUser.objects.filter(user_nm=representative_user_name, deleted_flg=0)
                if representative_list.count() < 1:
                    # PLANTIA側に一致するユーザーデータが無い場合は警告表示
                    response = "<script>alert('工事担当者データがPLANTIA側と一致しません！\\nPLANTIA側にユーザー[" + representative_user_name +"]を追加してください');</script>"
                    return HttpResponse(response)
                else:
                    construction_representative = representative_list[0]

        phenomenon_class_lists = MasterPhenomenonCode.objects.all()
        cause_class_lists = MasterCauseCode.objects.all()

        # 管理区分サロゲートKEY取得
        mgt_class = MasterMgtCls.objects.get(m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0)
        # 工場名
        facility = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)

        equipmenthistoryreport = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0)
        equipment_no_list = list(equipmenthistoryreport.values('t_fclty_ldgr_skey'))
        equipment_no = [d.get('t_fclty_ldgr_skey') for d in equipment_no_list]
        equipment_no = FcltyLdgr.objects.filter(t_fclty_ldgr_skey__in=equipment_no, deleted_flg=0)

        # 案件区分サロゲートKEY取得
        # exe_cls = MasterExeCls.objects.get(m_exe_cls_skey=exe_cls)
        # 案件区分リスト
        exe_cls_lists = MasterExeCls.objects.filter(m_exe_cls_skey__in=(9, 1, 4))
        # 保全区分リスト
        s_specman_list_skey = ServiceSpecmanList.objects.filter(list_nm='MNTCE_CODE')
        maintenance_classification_lists = ServiceSpecmanListValue.objects.filter(s_specman_list_skey__in=s_specman_list_skey).order_by('seq')

        # 部位リスト
        position_lists = MasterPositionCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)
        # 状況リスト
        condition_lists = MasterConditionCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)
        # 現象リスト
        phenomenon_lists = MasterPhenomenonCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)
        # 原因リスト
        cause_lists = MasterCauseCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)
        # 処置リスト
        treatment_lists = MasterTreatmentCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)
        # 結果リスト
        result_lists = MasterResultCode.objects.filter(m_mgt_cls_skey=mgt_class.m_mgt_cls_skey)

        measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id).count()
        if measure_data_num > 0:
            measure_data = Measure.objects.get(phenomenon_id=phenomenon_data.phenomenon_id)
        else:
            measure_data = ""

        if open_new_tab_flag == 0:
            action_num = action_num_count(t_username, user_department_cd, this_step, target, phenomenon_data.phenomenon_id)

            if action_num > 0:
                equipment_add_button_display_flag = 1
            else:
                equipment_add_button_display_flag = 0

            # データ編集機能要否判定
            report_maintenance_g_edit_action_num = 0
            report_maintenance_g_edit_action_num = report_maintenance_g_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='report_maintenance_g').count()

            edit_flag = 0

            if report_maintenance_g_edit_action_num > 0:
                edit_flag = 1
        else:
            action_num = 0
            report_maintenance_g_edit_action_num = 0
            equipment_add_button_display_flag = 0
            edit_flag = 0

        data = {
            # 'this_step': this_step,
            'phenomenon_data': phenomenon_data,
            'measure_data': measure_data,
            'equipment_history_report_data_num': equipment_history_report_data_num,
            'equipment_history_report_data': equipment_history_report_data,
            'phenomenon_class_lists': phenomenon_class_lists,
            'cause_class_lists': cause_class_lists,
            't_username': t_username,
            'mgt_class': mgt_class,
            'facility': facility,
            'equipment_no': equipment_no,
            'construction_representative': construction_representative,
            # SelectList
            'exe_cls_lists': exe_cls_lists,
            'maintenance_classification_lists': maintenance_classification_lists,
            'position_lists': position_lists,
            'condition_lists': condition_lists,
            'phenomenon_lists': phenomenon_lists,
            'cause_lists': cause_lists,
            'treatment_lists': treatment_lists,
            'result_lists': result_lists,
            'equipment_list': '',
            'equipment_add_button_display_flag': equipment_add_button_display_flag,
            'action_button_id': action_button_id,
        }

        if edit_flag == 1:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_data.phenomenon_id, 1)
            return render(request, 'fms/parts/maintenance/report_maintenance_g/report_maintenance_g_edit.html', data)

        else:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_data.phenomenon_id, 0)
            return render(request, 'fms/parts/maintenance/report_maintenance_g/report_maintenance_g_info.html', data)
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
        time_of_occurrence = request.POST['time_of_occurrence']

        completion_date = request.POST['completion_date']
        cycle_reference_date = request.POST['cycle_reference_date']
        start_date = request.POST['start_date']

        exe_cls_skey = request.POST['exe_cls_skey']
        failure_work_type = request.POST['failure_work_type']
        maintenance_classification = request.POST['maintenance_classification']
        condition_skey = request.POST['condition_skey']
        condition_position_cd_skey = request.POST['condition_position_cd_skey']
        phenomenon_cd_skey = request.POST['phenomenon_cd_skey']
        phenomenon_position_cd_skey = request.POST['phenomenon_position_cd_skey']
        cause_cd_skey = request.POST['cause_cd_skey']
        cause_position_cd_skey = request.POST['cause_position_cd_skey']
        treatment_cd_skey = request.POST['treatment_cd_skey']
        treatment_position_cd_skey = request.POST['treatment_position_cd_skey']
        result_cd_skey = request.POST['result_cd_skey']
        repair_time = request.POST['repair_time']
        report_detail = request.POST['report_detail']
        cause_detail = request.POST['cause_detail']
        countermeasure = request.POST['countermeasure']
        phenomenon_details = request.POST['phenomenon_details']
        special_mention = request.POST['special_mention']
        message = request.POST['message']
        if request.POST["equipment_history_report_id"] is not "":
            equipment_history_report_id = int(request.POST["equipment_history_report_id"])
            sub_no = 0
        else:
            equipment_history_report_id = 0
            sub_no = 0

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

        # 注意!!工事担当者(construction_representative)はIEP小口システムから入力されるので、画面からは保存しない
        equipment_history_report_data, created = EquipmentHistoryReport.objects.get_or_create(phenomenon_id2=phenomenon_id, lost_flag=0)
        equipment_history_report_data.sub_no = sub_no
        equipment_history_report_data.m_site_skey = 2
        equipment_history_report_data.m_mgt_cls_skey = MasterMgtCls.objects.get(m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0).m_mgt_cls_skey
        equipment_history_report_data.m_location_skey = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey).m_location_skey
        equipment_history_report_data.time_of_occurrence = time_of_occurrence
        equipment_history_report_data.completion_date = None if completion_date is '' else completion_date
        equipment_history_report_data.cycle_reference_date = None if cycle_reference_date is '' else cycle_reference_date
        equipment_history_report_data.start_date = None if start_date is '' else start_date
        equipment_history_report_data.m_exe_cls_skey = exe_cls_skey if exe_cls_skey is not '' else None
        equipment_history_report_data.failure_work_type = failure_work_type

        if failure_work_type == '重故障修理':
            equipment_history_report_data.serious_breakdown_case = 1
        else:
            equipment_history_report_data.serious_breakdown_case = None

        equipment_history_report_data.s_specman_list_value_skey = maintenance_classification if maintenance_classification is not '' else None

        if Order.objects.filter(phenomenon_id=phenomenon_id).count() > 0:
            equipment_history_report_data.maintenance_name = Order.objects.get(phenomenon_id=phenomenon_id).order_name + ' ' + Order.objects.get(phenomenon_id=phenomenon_id).order_name_extension_name

        # 検査・診断、小口依頼、対応方針から保全担当者情報取得、user_idではPLANTIAと紐づかないため日本語表記で比較する。計器室などの場合「苗字」「名前」に分かれていないためエラーとなる。
        if Inspection.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            inspection_entry_operator = Inspection.objects.get(phenomenon_id=phenomenon_id, lost_flag=0).entry_operator
            inspection_entry_user = User.objects.get(username=inspection_entry_operator)
            maintenance_person_name = inspection_entry_user.last_name + ' ' + inspection_entry_user.first_name

        elif Order.objects.filter(phenomenon_id=phenomenon_id).count() > 0:
            order_permit_person = Order.objects.get(phenomenon_id=phenomenon_id).order_permit_person
            if order_permit_person is not None and order_permit_person is not '':
                # 小口依頼の原課担当者は全角区切りで保存されているので、半角区切りに変換する
                maintenance_person_name = order_permit_person.replace('　', ' ')
            else:
                # エラー：Orderデータがあるが、order_permit_personがNULL
                output_log_exception(request, traceback.format_exc())
                msg = "保全担当者が設定できません！！！\n小口依頼の原課担当者が設定されていません、確認してください"
                ary = {
                    'msg': msg,
                    'equipment_history_report_unique_id': 0,
                }
                return JsonResponse(ary)

        elif Measure.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count() > 0:
            measure_charge_person = Measure.objects.get(phenomenon_id=phenomenon_id,
                                                        lost_flag=0).work_order_department_charge_person
            if measure_charge_person is not None:
                maintenance_person_name = measure_charge_person.last_name + ' ' + measure_charge_person.first_name
            else:
                # エラー：Measureデータがあるが、work_order_department_charge_personがNULL
                output_log_exception(request, traceback.format_exc())
                msg = "保全担当者が設定できません！！！\n対応方針の原課担当者が設定されていません、確認してください"
                ary = {
                    'msg': msg,
                    'equipment_history_report_unique_id': 0,
                }
                return JsonResponse(ary)
        else:
            # エラー：保全担当者を取得する元データが無い
            output_log_exception(request, traceback.format_exc())
            msg = "保全担当者が設定できません！！！\n検査・診断、小口依頼、対応方針のいずれも保存されていません"
            ary = {
                'msg': msg,
                'equipment_history_report_unique_id': 0,
            }
            return JsonResponse(ary)

        # PLANTIA側から保全担当者のs_user_skeyを取得
        if ServiceUser.objects.filter(user_nm=maintenance_person_name, deleted_flg=0).count() > 0:
            equipment_history_report_data.maintenance_personnel = ServiceUser.objects.get(user_nm=maintenance_person_name, deleted_flg=0).s_user_skey
        else:
            # エラー：PLANTIA側にmaintenance_personnelと一致するデータが無い
            output_log_exception(request, traceback.format_exc())
            msg = "保全担当者が設定できません！！！\nPLANTIA側にユーザー[" + maintenance_person_name + "]を追加してください"
            ary = {
                'msg': msg,
                'equipment_history_report_unique_id': 0,
            }
            return JsonResponse(ary)

        equipment_history_report_data.person_in_charge_of_the_original_section = maintenance_person_name
        equipment_history_report_data.m_condition_cd_skey = condition_skey if condition_skey is not '' else None
        equipment_history_report_data.m_position_cd_skey_condition = condition_position_cd_skey if condition_position_cd_skey is not '' else None
        equipment_history_report_data.m_phenomenon_cd_skey = phenomenon_cd_skey if phenomenon_cd_skey is not '' else None
        equipment_history_report_data.m_position_cd_skey_phenomenon = phenomenon_position_cd_skey if phenomenon_position_cd_skey is not '' else None
        equipment_history_report_data.m_cause_cd_skey = cause_cd_skey if cause_cd_skey is not '' else None
        equipment_history_report_data.m_position_cd_skey_cause = cause_position_cd_skey if cause_position_cd_skey is not '' else None
        equipment_history_report_data.m_treatment_cd_skey = treatment_cd_skey if treatment_cd_skey is not '' else None
        equipment_history_report_data.m_position_cd_skey_treatment = treatment_position_cd_skey if treatment_position_cd_skey is not '' else None
        equipment_history_report_data.m_result_cd_skey = result_cd_skey if result_cd_skey is not '' else None
        equipment_history_report_data.repair_time = repair_time if repair_time is not '' else None
        equipment_history_report_data.report_detail = report_detail
        equipment_history_report_data.cause_detail = cause_detail
        equipment_history_report_data.countermeasure = countermeasure
        equipment_history_report_data.phenomenon_details = phenomenon_details
        equipment_history_report_data.special_note_construction_work = special_mention

        equipment_history_report_data.message = message
        # 「一時保存」ではなく「完了」＝「次ステップに進んだ時」の時フラグ更新
        if this_step == next_step:
            equipment_history_report_data.export_complete_flag = 0
        elif this_step != next_step:
            equipment_history_report_data.export_complete_flag = 1
        if action_type == "add":
            equipment_history_report_data.entry_datetime = now
            equipment_history_report_data.entry_operator = operator
            msg = "履歴データ新規登録完了！！"
        # 更新の場合の処理
        elif action_type == "edit":
            equipment_history_report_data.update_datetime = now
            equipment_history_report_data.update_operator = operator
            msg = "履歴データ更新完了！！"

        # 履歴のレコードを保存
        equipment_history_report_data.save()

        # 履歴の主キー値取得
        equipment_history_report_unique_id = equipment_history_report_data.id

        if request.POST['equipment_no'] is not '':
            maintenance_equipment_data, created = MaintenanceEquipment.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                             t_fclty_ldgr_skey=request.POST['equipment_no'],
                                                                                             lost_flag=0)
            if created:
                maintenance_equipment_data.entry_datetime = now
                maintenance_equipment_data.entry_operator = operator

                maintenance_equipment_data.save()

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

        # 原課復旧確認側のprogressを完了させる(旧データは無い場合があるので、filterでチェック)
        if this_step != next_step:
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


# 履歴情報レコード事前作成 (小口依頼登録時処理)
@login_required
@require_POST
def equipment_history_report_data_pre_entry(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username
        phenomenon_id = int(request.POST["phenomenon_id"])

        # 関連情報取得
        phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id)
        measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)

        # EquipmentHistoryReportデータ新規作成
        equipment_history_report_data, created = EquipmentHistoryReport.objects.get_or_create(
            phenomenon_id2=phenomenon_id, lost_flag=0)

        # EquipmentHistoryReportデータ設定
        equipment_history_report_data.export_complete_flag = 0
        equipment_history_report_data.entry_datetime = now
        equipment_history_report_data.entry_operator = operator
        equipment_history_report_data.is_need_input_plantia = blank_to_None(request.POST['is_need_input_plantia'])

        # 関連情報設定
        equipment_history_report_data.time_of_occurrence = phenomenon_data.discovery_date
        equipment_history_report_data.phenomenon_details = phenomenon_data.condition_detail
        equipment_history_report_data.m_mgt_cls_skey = MasterMgtCls.objects.get(
            m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0).m_mgt_cls_skey
        equipment_history_report_data.m_location_skey = MasterLocation.objects.get(
            m_location_skey=phenomenon_data.m_location_skey).m_location_skey
        equipment_history_report_data.failure_work_type = measure_data.malfunction_class
        equipment_history_report_data.m_exe_cls_skey = measure_data.m_exe_cls_skey

        # EquipmentHistoryReportデータ保存
        equipment_history_report_data.save()

        # 履歴の主キー値取得
        equipment_history_report_id = equipment_history_report_data.id

        msg = '履歴データ新規登録完了！！'
        ary = {
            'msg': msg,
            'equipment_history_report_id': equipment_history_report_id,
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
