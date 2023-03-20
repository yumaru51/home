# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# modelesをインポート
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Progress, Log, StepAction
from fms.models import OrderForIEP, Phenomenon, Measure, NotificationCheck, Inspection
from fms.models import EquipmentHistoryReport, MaintenanceAttachmentFile, MaintenanceEquipment
from common.common_def import date_to_many_type
from .common_views import action_num_count
from .phenomenon_views import get_maintenance_equipment_list
from django.utils.timezone import make_aware

from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 対応を詳細画面で表示
@login_required
@require_POST
def inspection_data_info(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username

        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        if phenomenon_unique_id == 0:
            target_inspection_id = 0
            phenomenon_id = 0
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id, lost_flag=0)
            phenomenon_id = phenomenon_data.phenomenon_id
            inspection_data_num = Inspection.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).count()
            if inspection_data_num == 0:
                target_inspection_id = 0
            else:
                # target_measure_id = int(request.POST['measure_id'])
                inspection_data = Inspection.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)
                target_inspection_id = inspection_data.id
        # target_inspection_id = int(request.POST['inspection_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'

        # 新規登録か判定(予算ID=0なら新規)
        # 新規でないときの処理･･･該当の予算データを読み込み
        if target_inspection_id > 0:
            inspection_data = Inspection.objects.get(id=target_inspection_id, lost_flag=0)
            # ノーデータ(NULL)の部分は、空欄にするための処理を実施
            if inspection_data.inspection_detail is not None:
                inspection_detail = inspection_data.inspection_detail
            else:
                inspection_detail = ""

            if inspection_data.inspection_result is not None and inspection_data.inspection_result is not "":
                inspection_result = inspection_data.inspection_result
            else:
                inspection_result = ""

            if inspection_data.charge_team is not None and str(inspection_data.charge_team) is not "":
                str_charge_team = str(inspection_data.charge_team)
            else:
                str_charge_team = "0"

            if inspection_data.measure is not None and str(inspection_data.measure) is not "":
                str_measure = str(inspection_data.measure)
            else:
                str_measure = ""

            inspection_id = target_inspection_id

            if inspection_data.inspection_result == 0:
                inspection_result_str = '良好'
            elif inspection_data.inspection_result == 1:
                inspection_result_str = '様子見'
            elif inspection_data.inspection_result == 2:
                inspection_result_str = '要修理'
            else:
                inspection_result_str = ''

        # 新規の時の処理･･･基本的にはほぼすべての項目空欄
        else:
            inspection_data = ""
            inspection_detail = ""
            inspection_result = ""
            str_charge_team = ""
            str_measure = ""
            # present_step = new_step
            inspection_id = 0
            inspection_result_str = ''

        if phenomenon_unique_id == 0:
            phenomenon_data = ''
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id, lost_flag=0)

        if phenomenon_data != '':
            # 管理区分サロゲートKEY取得
            mgt_class = MasterMgtCls.objects.get(m_mgt_cls_skey=phenomenon_data.m_mgt_cls_skey, deleted_flg=0)
            # 工場名
            facility = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)

            equipmenthistoryreport = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id,
                                                                         lost_flag=0)
            equipment_no_list = list(equipmenthistoryreport.values('t_fclty_ldgr_skey'))
            equipment_fclty_ldgr_list = [d.get('t_fclty_ldgr_skey') for d in equipment_no_list]
            equipment_no = FcltyLdgr.objects.filter(t_fclty_ldgr_skey__in=equipment_fclty_ldgr_list, deleted_flg=0)

        else:
            # 管理区分サロゲートKEY取得
            mgt_class = ''
            # 工場名
            facility = ''
            equipment_no = ''

        equipment_list = get_maintenance_equipment_list(phenomenon_id, 1)

        # 対応方針修正項目
        measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_id).count()
        if measure_data_num > 0:
            measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)

            # 設定値比較用配列の作成
            if measure_data.m_exe_cls_skey is not None and measure_data.m_exe_cls_skey is not "":
                item_class = measure_data.m_exe_cls_skey
            else:
                item_class = ""
            if item_class == 9:
                item_class_name = "緊急"
            elif item_class == 1:
                item_class_name = "定常"
            elif item_class == 4:
                item_class_name = "自主保全"
            else:
                item_class_name = ""
            # 緊急工事項目
            if measure_data.maintenance_status is not None and str(measure_data.maintenance_status) is not "":
                str_maintenance_status = str(measure_data.maintenance_status)
            else:
                str_maintenance_status = ""
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
            # 対応依頼日
            if measure_data.response_request_date is not None and measure_data.response_request_date is not "":
                date_str = date_to_many_type(measure_data.response_request_date)
                str_response_request_date = date_str.str_type_date_jp
            else:
                str_response_request_date = ""
            # 依頼受付者
            if measure_data.orders_received_person is not None and measure_data.orders_received_person is not "":
                orders_received_person = measure_data.orders_received_person
            else:
                orders_received_person = ""
        else:
            item_class = ""
            item_class_name = ""
            str_maintenance_status = ""
            maintenance_status_str = ""
            str_response_request_date = ""
            orders_received_person = ""

        present_step_data_num = Progress.objects.filter(target_id=phenomenon_id, target='phenomenon').count()

        if present_step_data_num == 1:
            present_step_data = Progress.objects.get(target_id=phenomenon_id, target='phenomenon')
            present_step = present_step_data.present_step
        elif present_step_data_num > 1:
            present_step_data = Progress.objects.filter(target_id=phenomenon_id, target='phenomenon').first()
            present_step = present_step_data.present_step
        else:
            present_step = level5_step_id + 1

        # # 自分の部門CDを取得
        # department_data = DepartmentMaster.objects.get(department_cd=user_department_cd)
        # my_division = department_data.division_cd
        # # 現在のstep、targetに対する操作設定数を取得
        # action_num = StepAction.objects.filter(step_id=present_step, target=target).count()
        #
        # if Progress.objects.filter(target_id=phenomenon_id, target=target).count() == 1:
        #     present_step_data = Progress.objects.get(target_id=phenomenon_id, target=target)
        #     # 現stepの部門情報を取得
        #     this_step_division = present_step_data.present_division
        # else:
        #     this_step_division = ""
        #
        # # 現stepの部門とログインユーザーの部門が違う場合、「action_num = 0」(＝操作ボタンを表示しない)
        # if this_step_division != my_division:
        #     action_num = 0

        action_num = action_num_count(t_username, user_department_cd, present_step, target, phenomenon_id)

        if action_num > 0:
            equipment_add_button_display_flag = 1
        else:
            equipment_add_button_display_flag = 0

        data = {
            'phenomenon_id': phenomenon_id,
            'inspection_data': inspection_data,
            'target_inspection_id': target_inspection_id,
            'inspection_detail': inspection_detail,
            'inspection_result': inspection_result,
            'charge_team': str_charge_team,
            'measure': str_measure,
            'inspection_id': inspection_id,
            'phenomenon_unique_id': phenomenon_unique_id,
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
            'inspection_result_str': inspection_result_str,
            'mgt_class': mgt_class,
            'facility': facility,
            'equipment_no': equipment_no,
            'equipment_add_button_display_flag': equipment_add_button_display_flag,
            'equipment_list': equipment_list,
            'action_button_id': action_button_id,
            'item_class': item_class,
            'item_class_name': item_class_name,
            'maintenance_status': str_maintenance_status,
            'maintenance_status_str': maintenance_status_str,
            'response_request_date': str_response_request_date,
            'orders_received_person': orders_received_person,
        }

        # データ編集機能要否判定
        inspection_edit_action_num = 0

        inspection_edit_action_num = inspection_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='inspection').count()

        edit_flag = 0

        if inspection_edit_action_num > 0 and action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/maintenance/inspection/inspection_edit.html', data)

        else:
            return render(request, 'fms/parts/maintenance/inspection/inspection_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 検査診断情報を登録･更新処理
@login_required
@require_POST
def inspection_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        phenomenon_id = int(request.POST['phenomenon_id'])
        user_attribute_id = int(request.POST["user_attribute_id"])

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        if request.POST["inspection_id"] is not "":
            inspection_id = int(request.POST["inspection_id"])
            phenomenon_id = int(request.POST["phenomenon_id"])
            # sub_no = int(request.POST["sub_no"])
            sub_no = 0
        else:
            if request.POST["phenomenon_id"] is not "":
                phenomenon_id = int(request.POST["phenomenon_id"])
                inspection_data_num = Inspection.objects.filter(phenomenon_id=phenomenon_id).count()
                if inspection_data_num > 0:
                    inspection_data = Inspection.objects.get(phenomenon_id=phenomenon_id)
                    inspection_id = inspection_data.id
                else:
                    inspection_id = 0
            else:
                inspection_id = 0
                phenomenon_id = 0
            sub_no = 0

        inspection_detail = request.POST["inspection_detail"]
        inspection_result = request.POST["inspection_result"]
        if request.POST["charge_team"] != "":
            charge_team = int(request.POST["charge_team"])
        else:
            charge_team = 0
        measure = int(request.POST["measure"])

        if request.POST["equipment_no"] != "":
            equipment_no = request.POST['equipment_no']
        else:
            equipment_no = ''

        item_class = int(request.POST["sel_item_class"])
        if request.POST["maintenance_status"] != "":
            maintenance_status = int(request.POST["maintenance_status"])
        else:
            maintenance_status = ""
        response_request_date_str = request.POST["response_request_date"]
        date_str = date_to_many_type(response_request_date_str)
        response_request_date = date_str.date_type_date
        orders_received_person = request.POST["orders_received_person"]

        # 案件区分関係を変更した場合の処理
        measure_data = Measure.objects.get(phenomenon_id=phenomenon_id, lost_flag=0)

        # 設定値比較用配列の作成
        measure_data_array = []
        measure_data_array += [measure_data.m_exe_cls_skey,
                               measure_data.maintenance_status,
                               str(measure_data.response_request_date),
                               measure_data.orders_received_person,
                               ]

        new_measure_data_array = []
        new_measure_data_array += [item_class,
                                   maintenance_status,
                                   date_str.str_type_date_hyphen,
                                   orders_received_person,
                                   ]

        if measure_data_array != new_measure_data_array:
            measure_data.m_exe_cls_skey = item_class
            if maintenance_status != "":
                measure_data.maintenance_status = maintenance_status
            if response_request_date != "":
                measure_data.response_request_date = response_request_date
            measure_data.orders_received_person = orders_received_person

            measure_data.update_datetime = now
            measure_data.update_operator = operator

            measure_data.save()

        # 新規登録時の処理
        if inspection_id == 0:
            inspection_data_num = Inspection.objects.all().count()
            # 検査診断のレコードがない時の処理･･･予算id=1 とする
            if inspection_data_num == 0:
                this_inspection_id = 1
            # 検査診断のレコードがある時の処理･･･最終の検査診断idを取得し、検査診断id=最終の検査診断id+1 とする
            else:
                last_inspection_data = Inspection.objects.all().order_by('-id')[0]
                last_inspection_id = last_inspection_data.id
                this_inspection_id = last_inspection_data.id + 1
            # 設定した検査診断idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            inspection_data, created = Inspection.objects.get_or_create(id=this_inspection_id)
            # 登録の日時、登録者を登録
            inspection_data.entry_datetime = now
            inspection_data.entry_operator = operator
            # 検査診断のレコードを保存
            inspection_data.save()
            # 登録日時、登録者で検査診断レコードを抽出
            inspection_data = Inspection.objects.get(entry_datetime=now, entry_operator=operator)
            # 主キーを取得
            inspection_unique_id = inspection_data.id
            # 主キーで検査診断レコードを抽出
            inspection_data = Inspection.objects.get(id=inspection_unique_id)
            # 無効FLに値を代入
            inspection_data.lost_flag = 0
            # 検査診断のレコードを保存
            inspection_data.save()
            action_type = "add"

        # 更新時の処理
        else:
            # 検査診断id(変数)に渡された案件idをセット
            this_inspection_id = inspection_id
            # 対象の検査診断レコードを抽出
            inspection_data = Inspection.objects.get(id=this_inspection_id)
            # 主キーを取得
            inspection_unique_id = inspection_data.id
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

        # 主キー検査診断レコードを抽出
        inspection_data = Inspection.objects.get(id=inspection_unique_id)
        inspection_data.phenomenon_id = phenomenon_id
        inspection_data.sub_no = sub_no

        inspection_data.inspection_detail = inspection_detail
        inspection_data.inspection_result = inspection_result
        inspection_data.charge_team = charge_team
        inspection_data.measure = measure

        if action_type == "add":
            inspection_data.entry_datetime = now
            inspection_data.entry_operator = operator
            msg = "検査診断データ新規登録完了！！"
        # 更新の場合の処理
        else:
            inspection_data.update_datetime = now
            inspection_data.update_operator = operator
            msg = "検査診断データ更新完了！！"
        # 検査診断のレコードを保存
        inspection_data.save()

        # 検査診断の主キー値取得
        inspection_unique_id = inspection_data.id

        phenomenon_data = Phenomenon.objects.get(phenomenon_id=inspection_data.phenomenon_id)
        EquipmentHistoryReport.objects.filter(phenomenon_id2=phenomenon_id).update(special_mention=inspection_data.inspection_detail)

        # ログのコメント作成
        comment = "inspection_id : " + str(inspection_unique_id)
        comment = comment + "\ntarget:phenomenon:"

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

        equipment_list = get_maintenance_equipment_list(phenomenon_id, 1)

        ary = {
            'msg': msg,
            'inspection_id': inspection_unique_id,
            'equipment_list': equipment_list,
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

