# datetimeをインポート
import datetime
from datetime import timedelta, timezone
# ログインユーザーを使用するmoduleをインポート
import math
import traceback
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
from fms.models import StepMaster, ProcessMaster
from fms.models import Progress, Log
from fms.models import OrderForIEP, Phenomenon, Measure, NotificationCheck, Inspection
from fms.models import EquipmentHistoryReport, MaintenanceAttachmentFile, MaintenanceEquipment
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation, MasterConditionCode
from common.common_def import date_to_many_type
from .common_views import None_to_blank, action_num_count
from django.utils.timezone import make_aware
from django.db import connections
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 状況情報を詳細画面で表示
@login_required
@require_POST
def phenomenon_data_info(request):
    try:
        t_username = request.user.username
        t_user_last_name = request.user.last_name
        t_user_first_name = request.user.first_name
        target_id = int(request.POST['id'])
        new_step = int(request.POST['new_step'])
        user_department_cd = request.POST['user_department_cd']
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'
        open_new_tab_flag = int(request.POST['open_new_tab_flag'])

        # 新規処理
        if target_id == 0:
            phenomenon_data = 0
            phenomenon_id = 0
            condition_list = phenomenon_condition_list(None)
            present_step = new_step
            discovery_user_name = t_username

        # 更新処理
        else:
            phenomenon_data = Phenomenon.objects.get(id=target_id)
            phenomenon_id = phenomenon_data.phenomenon_id or 0
            condition_list = phenomenon_condition_list(phenomenon_data.m_mgt_cls_skey)

            if Progress.objects.filter(target='phenomenon', target_id=phenomenon_id) == 1:
                present_step_data = Progress.objects.get(target_id=phenomenon_id, target='phenomenon')
                present_step = present_step_data.present_step
            else:
                present_step_data = Progress.objects.filter(target_id=phenomenon_id, target='phenomenon').first()
                present_step = present_step_data.present_step

            discovery_user_name = ""

        mgt_cls_lists = MasterMgtCls.objects.all()
        facility_lists = MasterLocation.objects.filter(parent_m_location_skey__isnull=False, deleted_flg=0)
        departments_list = DepartmentMaster.objects.all()
        discoverer_list = User.objects.filter(lost_flag=0)

        action_num = action_num_count(t_username, user_department_cd, present_step, target, phenomenon_id)

        if action_num > 0:
            equipment_add_button_display_flag = 1
        else:
            equipment_add_button_display_flag = 0

        data = {
            't_username': t_username,
            'discovery_user_name': discovery_user_name,
            't_user_last_name': t_user_last_name,
            't_user_first_name': t_user_first_name,
            'phenomenon_data': phenomenon_data,
            'phenomenon_id': phenomenon_id,
            'mgt_cls_lists': mgt_cls_lists,
            'facility_lists': facility_lists,
            'departments_list': departments_list,
            'discoverer_list': discoverer_list,
            'condition_list': condition_list,
            'equipment_list': '',
            'equipment_add_button_display_flag': equipment_add_button_display_flag,
            'action_button_id': action_button_id,
            'div_id_name': div_id_name,
        }

        # データ編集機能要否判定
        phenomenon_edit_action_num = 0
        phenomenon_edit_action_num = phenomenon_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                                     target_table='phenomenon').count()
        edit_flag = 0
        if phenomenon_edit_action_num > 0 and action_num > 0 and open_new_tab_flag != 1:
            edit_flag = 1

        if edit_flag == 1:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_id, 1)
            return render(request, 'fms/parts/maintenance/phenomenon/phenomenon_edit.html', data)

        else:
            data['equipment_list'] = get_maintenance_equipment_list(phenomenon_id, 0)
            return render(request, 'fms/parts/maintenance/phenomenon/phenomenon_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 状況情報を登録･更新処理
@login_required
@require_POST
def phenomenon_entry(request):
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

        if request.POST["phenomenon_id"] is not "":
            phenomenon_id = int(request.POST["phenomenon_id"])
        else:
            phenomenon_id = 0
            sub_no = 0
        project_title = request.POST["project_title"]
        department = this_department
        discoverer = request.POST["discoverer"]
        discovery_date = request.POST["discovery_date"]

        management_class = request.POST["management_class"]
        factory_name = request.POST["factory_name"]
        equipment_no = request.POST["equipment_no"] if request.POST["equipment_no"] is not '' else None
        condition = request.POST["condition"] if request.POST["condition"] is not '' else None
        condition_detail = request.POST["condition_detail"]
        improvement_proposal = request.POST["improvement_proposal"]

        # 新規処理
        if phenomenon_id == 0:
            phenomenon_data_num = Phenomenon.objects.all().count()
            # 状況のレコードがない時の処理･･･案件id=1 とする
            if phenomenon_data_num == 0:
                this_phenomenon_id = 1
            # 状況のレコードがある時の処理･･･最終の案件idを取得し、案件id=最終の案件id+1 とする
            else:
                last_phenomenon_data = Phenomenon.objects.all().order_by('-phenomenon_id')[0]
                last_phenomenon_id = last_phenomenon_data.phenomenon_id
                this_phenomenon_id = last_phenomenon_data.phenomenon_id + 1

            # 設定した案件idでレコードを抽出し、あれば呼出、なければ新規作成･･･ないはずなので、新規作成
            phenomenon_data, created = Phenomenon.objects.get_or_create(phenomenon_id=this_phenomenon_id)
            # 登録の日時、登録者を登録
            phenomenon_data.entry_datetime = now
            phenomenon_data.entry_operator = operator
            # 状況のレコードを保存
            phenomenon_data.save()
            # 登録日時、登録者で状況レコードを抽出
            phenomenon_data = Phenomenon.objects.get(entry_datetime=now, entry_operator=operator)
            # 主キーを取得
            phenomenon_unique_id = phenomenon_data.id
            # 主キーで状況レコードを抽出
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            # sub_no、無効FLに値を代入
            phenomenon_data.sub_no = 0
            phenomenon_data.lost_flag = 0
            # 状況のレコードを保存
            phenomenon_data.save()
            action_type = "add"

        # 更新処理
        else:
            # 案件id(変数)に渡された案件idをセット
            this_phenomenon_id = phenomenon_id
            # 対象の状況レコードを抽出
            # phenomenon_data = Phenomenon.objects.get(phenomenon_id=this_phenomenon_id, sub_no=sub_no)
            phenomenon_data = Phenomenon.objects.get(phenomenon_id=this_phenomenon_id)
            # 主キーを取得
            phenomenon_unique_id = phenomenon_data.id
            action_type = "edit"

            # 多重操作防止処理
            progress_count = Progress.objects.filter(target="phenomenon",
                                                     target_id=phenomenon_id, present_step=this_step).count()
            if progress_count != 1:
                msg = "進捗状況が一致しないため保存できません、多重操作が行われていないか確認してください！"
                ary = {
                    'msg': msg
                }
                return JsonResponse(ary)

        # 主キーで状況レコードを抽出
        phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
        phenomenon_data.project_title = project_title
        phenomenon_data.discovery_date = discovery_date
        dprc = DepartmentMaster.objects.get(department_cd=department)
        phenomenon_data.department = dprc
        phenomenon_data.user = User.objects.get(username=discoverer)
        phenomenon_data.condition_detail = condition_detail
        phenomenon_data.improvement_proposal = improvement_proposal

        phenomenon_data.m_mgt_cls_skey = management_class
        phenomenon_data.m_location_skey = factory_name
        phenomenon_data.m_condition_cd_skey = condition

        if action_type == "add":
            phenomenon_data.entry_datetime = now
            phenomenon_data.entry_operator = operator
            msg = "状況データ新規登録完了！！"
        # 更新の場合の処理
        else:
            phenomenon_data.update_datetime = now
            phenomenon_data.update_operator = operator
            msg = "状況データ更新完了！！"
        # 状況のレコードを保存
        phenomenon_data.save()
        phenomenon_id = phenomenon_data.phenomenon_id
        # 状況の主キー値取得
        phenomenon_unique_id = phenomenon_data.id

        if request.POST['equipment_no'] is not '':
            maintenance_equipment_data, created = MaintenanceEquipment.objects.get_or_create(phenomenon_id=phenomenon_id,
                                                                                             t_fclty_ldgr_skey=request.POST['equipment_no'],
                                                                                             lost_flag=0
                                                                                             )

            if created:
                maintenance_equipment_data.entry_datetime = now
                maintenance_equipment_data.entry_operator = operator

                maintenance_equipment_data.save()

        # ログのコメント作成
        comment = "phenomenon_id : " + str(this_phenomenon_id)
        comment = comment + "\ntarget:phenomenon:"

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            action = "temporarily_saved"

        # 今のstepと次のstepが違う場合の処理
        else:
            action = "entry"

        # ログを新規登録
        Log(target='phenomenon', target_id=this_phenomenon_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division).save()

        if action_type == "add":
            # 進捗状況を対象(phenomenon)と案件idで抽出･･･あれば呼び出し、なければ新規登録
            progress_data, created = Progress.objects.get_or_create(target="phenomenon", target_id=phenomenon_id,
                                                                    present_step=this_step)
        else:
            # 進捗状況を対象(phenomenon)と案件idで抽出
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
                'phenomenon_id': this_phenomenon_id,
                'equipment_list': equipment_list,
            }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 異常報告データ一覧
@require_POST
def get_phenomenon_lists(request):
    try:
        sel_step = request.POST['sel_step']
        sel_phenomenon_id = request.POST['sel_phenomenon_id']
        sel_project_name = request.POST['sel_project_name']
        sel_item_class = request.POST['sel_item_class']
        sel_maintenance_status = request.POST['sel_maintenance_status']
        sel_malfunction_class = request.POST['sel_malfunction_class']
        sel_division = request.POST['sel_division']
        sel_department = request.POST['sel_department']
        sel_process = request.POST['sel_process']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']
        sel_mng_charge_person = request.POST['sel_mng_charge_person']
        sel_on_work = request.POST['sel_on_work']
        level5_step_id = int(request.POST['level5_step_id'])
        return_url = request.POST['return_url']
        sel_display_order = request.POST['sel_display_order']
        sel_desired_delivery_date_filter_start = request.POST['sel_desired_delivery_date_filter_start']
        sel_desired_delivery_date_filter_end = request.POST['sel_desired_delivery_date_filter_end']
        list_type = request.POST['list_type']

        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000

        where_str = ""
        where_parm1 = []

        # 検索条件
        # 進捗状況
        if sel_step != "":
            where_str += " AND fms_stepmaster.step_id = %s \n"
            where_parm1.append(int(sel_step))
        # 案件ID
        if sel_phenomenon_id != "":
            where_str += " AND fms_phenomenon.phenomenon_id = %s \n"
            where_parm1.append(int(sel_phenomenon_id))
        # 案件名
        if sel_project_name != "":
            where_str += " AND fms_phenomenon.project_title LIKE %s \n"
            where_parm1.append('%' + sel_project_name + '%')
        # 案件区分
        if sel_item_class != "":
            where_str += " AND fms_measure.m_exe_cls_skey = %s \n"
            where_parm1.append(sel_item_class)
        # 依頼状況
        if sel_maintenance_status != "":
            where_str += " AND fms_measure.maintenance_status = %s \n"
            where_parm1.append(sel_maintenance_status)
        # 故障/作業種別
        if sel_malfunction_class != "":
            where_str += " AND fms_measure.malfunction_class = %s \n"
            where_parm1.append(sel_malfunction_class)
        # 希望納期(期限)開始
        if sel_desired_delivery_date_filter_start != "":
            date_str = date_to_many_type(sel_desired_delivery_date_filter_start)
            sel_desired_delivery_date_filter_start_date = date_str.str_type_date_hyphen
            where_str += " AND fms_measure.desired_delivery_date_end >= '""" + sel_desired_delivery_date_filter_start_date + """ ' \n"""
            # where_str += " AND fms_measure.desired_delivery_date_t >= %s "
            # where_parm1.append(str(sel_desired_delivery_date_filter_start))
        # 希望納期(期限)終了
        if sel_desired_delivery_date_filter_end != "":
            date_str = date_to_many_type(sel_desired_delivery_date_filter_end)
            sel_desired_delivery_date_filter_end_date = date_str.str_type_date_hyphen
            where_str += " AND fms_measure.desired_delivery_date_end <= '""" + sel_desired_delivery_date_filter_end_date + """ '  \n"""
            # where_str += " AND fms_measure.desired_delivery_date_t <= %s "
            # where_parm1.append(sel_desired_delivery_date_filter_end)
        # 部門
        if sel_division != "":
            where_str += " AND fms_departmentmaster.division_cd = %s \n"
            where_parm1.append(sel_division)
        # 担当部署
        if sel_department != "":
            where_str += " AND fms_departmentmaster.department_cd = %s \n"
            where_parm1.append(sel_department)
        # 工場
        if sel_process != "":
            where_str += " AND fms_phenomenon.m_location_skey = %s \n"
            where_parm1.append(int(sel_process))
        # 次作業部門
        if sel_next_division != "":
            where_str += " AND fms_progress.present_division = %s \n"
            where_parm1.append(sel_next_division)
        # 次作業部署
        if sel_next_department != "":
            where_str += " AND fms_progress.present_department = %s \n"
            where_parm1.append(sel_next_department)
        # 次作業者
        if sel_next_parson != "":
            where_str += " AND fms_progress.present_operator = %s \n"
            where_parm1.append(sel_next_parson)
        # 保全G担当者は、検査･診断/方針決定ステップの保存操作をしたユーザーで検索
        if sel_mng_charge_person != "":
            where_str += " AND operator= %s \n"
            where_parm1.append(sel_mng_charge_person)
        # 未処理のみにチェックがある場合、ユーザーを限定する
        if sel_on_work == 'true':
            where_str += " AND fms_stepmaster.step_id > %s \n"
            where_str += " AND fms_stepmaster.step_id < %s \n"
            where_parm1.append(step_st)
            where_parm1.append(step_ed)

        sql = """ SELECT fms_phenomenon.*, fms_user.first_name, fms_user.last_name \n"""
        sql = sql + """     ,fms_stepmaster.step_name, fms_stepmaster.step_id \n"""
        sql = sql + """     ,discovery_user.first_name as discovery_user_first_name, discovery_user.last_name  as discovery_user_last_name \n"""
        sql = sql + """     ,fms_departmentmaster.department_name \n"""
        sql = sql + """     ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_phenomenon.entry_datetime, GETDATE()) \n"""
        sql = sql + """                                                 ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END """
        sql = sql + """ AS days_stay \n"""
        sql = sql + """     , CASE WHEN log_2.action = 'return' THEN 1 ELSE 0 END AS return_flag \n"""
        sql = sql + """     ,entry_log.target_id \n"""
        sql = sql + """     ,entry_log.last_operationtime \n"""
        sql = sql + """     ,entry_log.action \n"""
        sql = sql + """     ,operator \n"""
        # sql = sql + """ FROM ((((( fms_phenomenon \n"""
        sql = sql + """ FROM (((( fms_phenomenon \n"""
        sql = sql + """         LEFT JOIN fms_progress ON fms_phenomenon.phenomenon_id=fms_progress.target_id AND fms_progress.target='phenomenon') \n"""
        sql = sql + """         LEFT JOIN fms_user ON fms_progress.present_operator=fms_user.username) \n"""
        sql = sql + """         LEFT JOIN fms_user discovery_user ON fms_phenomenon.user_id=discovery_user.username) \n"""
        sql = sql + """         LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id) \n"""
        # sql = sql + """         LEFT JOIN fms_departmentmaster ON fms_phenomenon.department_id=fms_departmentmaster.department_cd) \n"""
        sql = sql + """ LEFT JOIN fms_measure ON fms_phenomenon.phenomenon_id=fms_measure.phenomenon_id \n"""
        sql = sql + """ LEFT JOIN fms_departmentmaster ON fms_measure.work_order_charge_department_id=fms_departmentmaster.department_cd \n"""
        sql = sql + """ LEFT JOIN (SELECT [target_id] \n"""
        sql = sql + """                   ,MAX([operation_datetime]) as last_operationtime \n"""
        sql = sql + """             FROM [fms].[dbo].[fms_log] \n"""
        sql = sql + """             WHERE [target]='phenomenon' \n"""
        sql = sql + """               AND [action] != 'temporarily_saved' \n"""
        sql = sql + """             group by [target_id] \n"""
        sql = sql + """           ) as log ON [fms].[dbo].[fms_phenomenon].phenomenon_id=log.target_id \n"""
        sql = sql + """ LEFT JOIN(SELECT main.* \n"""
        sql = sql + """         , sub.[action] \n"""
        sql = sql + """             FROM(SELECT target_id \n"""
        sql = sql + """                         ,MAX(operation_datetime) AS operation_datetime \n"""
        sql = sql + """                    FROM [fms].[dbo].[fms_log] \n"""
        sql = sql + """                   WHERE [target] = 'phenomenon' AND [action] != 'temporarily_saved' \n"""
        sql = sql + """                 GROUP BY [target_id] \n"""
        sql = sql + """                 ) AS main \n"""
        sql = sql + """             INNER JOIN [fms].[dbo].[fms_log] AS sub ON main.operation_datetime=sub.operation_datetime \n"""
        sql = sql + """                                                    AND main.target_id=sub.target_id \n"""
        sql = sql + """             WHERE main.[operation_datetime] = sub.operation_datetime \n"""
        sql = sql + """             AND sub.comment LIKE '%%phenomenon%%' \n"""
        sql = sql + """          ) AS log_2 ON fms_phenomenon.phenomenon_id = log_2.target_id \n"""
        sql = sql + """ LEFT JOIN (SELECT	[target_id] \n"""
        sql = sql + """                     ,MAX([operation_datetime]) as last_operationtime \n"""
        sql = sql + """                     ,action \n"""
        sql = sql + """                     ,operator \n"""
        sql = sql + """              FROM [fms].[dbo].[fms_log] \n"""
        sql = sql + """             WHERE [target]='phenomenon' \n"""
        sql = sql + """               AND [action] = 'entry' \n"""
        sql = sql + """               AND step = 231002001 \n"""
        sql = sql + """             group by [target_id],operator, action \n"""
        sql = sql + """           ) as entry_log  ON [fms].[dbo].[fms_phenomenon].phenomenon_id=entry_log.target_id \n"""
        sql = sql + """ LEFT JOIN fms_user as mng_charge_person_data ON entry_log.operator=mng_charge_person_data.username \n"""
        sql = sql + """                                             and fms_user.lost_flag=0 \n"""
        sql = sql + """ WHERE fms_phenomenon.lost_flag=0 \n"""

        if where_str != "":
            sql += where_str

        if sel_display_order == "1":  # 案件ID
            sql += " ORDER BY fms_phenomenon.phenomenon_id"
        elif sel_display_order == "2":  # 発見日時
            sql += " ORDER BY fms_phenomenon.discovery_date"
        else:
            sql += " ORDER BY days_stay desc"

        if len(where_parm1) == 0:
            phenomenon_lists = Phenomenon.objects.all().raw(sql)

        else:
            phenomenon_lists = Phenomenon.objects.raw(sql, where_parm1)

        phenomenon_lists_num = len(list(phenomenon_lists))

        try:
            for phenomenon_list_item in phenomenon_lists:
                # phenomenon_idにて機器番号のサロゲートキー取得し、機器番号に書き換え
                # maintenance_equipment_data = MaintenanceEquipment.objects.filter(
                #     phenomenon_id=phenomenon_list_item.phenomenon_id,
                #     lost_flag=0)
                maintenance_equipment_data = MaintenanceEquipment.objects.select_related('phenomenon_id').filter(
                    phenomenon_id=phenomenon_list_item.phenomenon_id,
                    lost_flag=0)
                if len(maintenance_equipment_data) > 0:
                    loop = 0
                    equipment_list = ''
                    for maintenance_equipment_data_item in maintenance_equipment_data:
                        if loop != 0:
                            equipment_list += '/'
                        t_fclty_ldgr_skey = str(maintenance_equipment_data_item.t_fclty_ldgr_skey)
                        fclty_ldgr_count = FcltyLdgr.objects.select_related('t_fclty_ldgr_skey').filter(
                            t_fclty_ldgr_skey=t_fclty_ldgr_skey,
                            deleted_flg=0).count()
                        if fclty_ldgr_count > 0:
                            # equipment_list += FcltyLdgr.objects.get(t_fclty_ldgr_skey=t_fclty_ldgr_skey,
                            #                                         deleted_flg=0).eqpt_id
                            equipment_list += FcltyLdgr.objects.select_related('t_fclty_ldgr_skey').get(
                                t_fclty_ldgr_skey=t_fclty_ldgr_skey,
                                deleted_flg=0).eqpt_id
                        loop += 1
                    phenomenon_list_item.equipment_no = equipment_list

        except Exception:
            msg = "ERROR!!"

        data = {
            'phenomenon_lists': phenomenon_lists,
            'phenomenon_lists_num': phenomenon_lists_num,
            'list_type': list_type,
        }

        return render(request, 'fms/parts/maintenance/maintenance_list.html', data)
        # return render(request, return_url, data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 異常報告一覧の絞込のパーツ表示
@require_POST
def phenomenon_filter(request):
    from fms.views.common_def_views import get_next_target, get_department_person_list
    try:
        # 年度選択ソース抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1).all()
        # 部門選択ソース抽出
        division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 部署選択ソース抽出
        departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 工場選択ソース抽出
        facility_list = MasterLocation.objects.all().order_by('display_order')

        # 進捗工程選択ソース抽出
        list_type = request.POST["list_type"]
        if list_type == '':
            level5_step_id = int(request.POST["level5_step_id"])
            step_st = math.floor(level5_step_id / 1000000) * 1000000
            step_ed = step_st + 1000000
        else:
            step_st = 231000000
            step_ed = 232009902

        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        # 次工程選択ソース抽出
        next_departments_list, next_person_list, target_division, target_department, target_person = \
            get_next_target(request.POST["user"], request.POST["user_department_cd"],
                            request.POST["next_division"], request.POST["next_department"], request.POST["next_parson"])

        # 保全G担当者ソース抽出 (ユーザ全体からの抽出)
        mng_charge_person_list = get_department_person_list('MNG')

        data = {
            'step_list': step_list,
            'business_year_list': business_year_list,
            'division_list': division_list,
            'departments_list': departments_list,
            'facility_list': facility_list,
            'next_user_list': next_person_list,
            'next_departments_list': next_departments_list,
            'user_department_cd': target_department,
            'user_division_cd': target_division,
            'user': target_person,
            'mng_charge_person_list': mng_charge_person_list,
        }

        return render(request, 'fms/parts/maintenance/phenomenon_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 故障対応情報コピー用故障対応案件一覧の絞込パーツ表示
@require_POST
def phenomenon_copy_source(request):
    try:
        return render(request, 'fms/parts/maintenance/phenomenon_copy_source/phenomenon_copy_source.html')
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 異常報告情報コピー処理
@require_POST
def phenomenon_copy(request):
    try:
        target_id = int(request.POST['target_phenomenon_unique_id'])

        phenomenon_data_num = Phenomenon.objects.filter(id=target_id, lost_flag=0).count()
        if phenomenon_data_num == 1:
            phenomenon_data = Phenomenon.objects.get(id=target_id, lost_flag=0)

            phenomenon_unique_id = phenomenon_data.id
            project_title = phenomenon_data.project_title
            # department_cd = phenomenon_data.department.department_cd
            username = phenomenon_data.user.username
            m_condition_cd_skey = phenomenon_data.m_condition_cd_skey
            condition_detail = phenomenon_data.condition_detail
            improvement_proposal = phenomenon_data.improvement_proposal
            m_mgt_cls_skey = phenomenon_data.m_mgt_cls_skey
            m_location_skey = phenomenon_data.m_location_skey

            measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0).count()
            msg = "故障対応情報をコピーしました！\n" + "保存されていないので、保存してください！！"
        else:
            phenomenon_unique_id = ""
            project_title = ""
            # department_cd = ""
            username = ""
            m_condition_cd_skey = ""
            condition_detail = ""
            improvement_proposal = ""
            m_mgt_cls_skey = ""
            m_location_skey = ""
            measure_data_num = 0
            msg = "コピー対象の故障対応情報が見つかりません！"

        data = {
            'id': phenomenon_unique_id,
            'project_title': project_title,
            # 'department_cd': department_cd,
            'username': username,
            'm_condition_cd_skey': m_condition_cd_skey,
            'condition_detail': condition_detail,
            'improvement_proposal': improvement_proposal,
            'm_mgt_cls_skey': m_mgt_cls_skey,
            'm_location_skey': m_location_skey,
            'measure_data_num': measure_data_num,
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 対応方針情報コピー処理
@require_POST
def measure_copy(request):
    try:
        target_id = int(request.POST['target_phenomenon_unique_id'])

        phenomenon_data_num = Phenomenon.objects.filter(id=target_id, lost_flag=0).count()
        if phenomenon_data_num == 1:
            phenomenon_data = Phenomenon.objects.get(id=target_id, lost_flag=0)
            measure_data_num = Measure.objects.filter(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0).count()
            if measure_data_num == 1:
                measure_data = Measure.objects.get(phenomenon_id=phenomenon_data.phenomenon_id, lost_flag=0)

                measure_order_detail = measure_data.measure_order_detail
                m_exe_cls_skey = measure_data.m_exe_cls_skey
                malfunction_class = measure_data.malfunction_class
                username = measure_data.work_order_department_charge_person.username
                department_cd = measure_data.work_order_charge_department_id
                instruction_no = measure_data.instruction_no
                cost_center = measure_data.cost_center
                account_cd = measure_data.account_cd
                diagnosis_class = measure_data.diagnosis_class
                desired_vendor = measure_data.desired_vendor
                maintenance_status = measure_data.maintenance_status
                orders_received_person = measure_data.orders_received_person

                msg = "対応方針情報をコピーしました！\n" + "保存されていないので、保存してください！！"
            else:
                measure_order_detail = ""
                m_exe_cls_skey = ""
                malfunction_class = ""
                username = ""
                department_cd = ""
                instruction_no = ""
                cost_center = ""
                account_cd = ""
                diagnosis_class = ""
                desired_vendor = ""
                maintenance_status = ""
                orders_received_person = ""
                msg = "コピー対象の対応方針情報が見つかりません！"
        else:
            measure_order_detail = ""
            m_exe_cls_skey = ""
            malfunction_class = ""
            username = ""
            department_cd = ""
            instruction_no = ""
            cost_center = ""
            account_cd = ""
            diagnosis_class = ""
            desired_vendor = ""
            maintenance_status = ""
            orders_received_person = ""
            msg = "コピー対象の対応方針情報が見つかりません！"

        data = {
            'measure_order_detail': measure_order_detail,
            'm_exe_cls_skey': m_exe_cls_skey,
            'malfunction_class': malfunction_class,
            'username': username,
            'department_cd': department_cd,
            'instruction_no': instruction_no,
            'cost_center': cost_center,
            'account_cd': account_cd,
            'diagnosis_class': diagnosis_class,
            'desired_vendor': desired_vendor,
            'maintenance_status': maintenance_status,
            'orders_received_person': orders_received_person,
            'msg': msg,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器を削除処理
@login_required
@require_POST
def phenomenon_equipment_delete(request):
    try:
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        maintenance_equipment_data = MaintenanceEquipment.objects.get(id=request.POST["id"])
        maintenance_equipment_data.lost_flag = 1
        maintenance_equipment_data.update_datetime = now
        maintenance_equipment_data.update_operator = operator
        maintenance_equipment_data.save()
        msg = "関連機器データ削除完了！！"

        maintenance_equipment_id = maintenance_equipment_data.phenomenon_id
        equipment_list = get_maintenance_equipment_list(maintenance_equipment_id, 1)
        data = {
            'msg': msg,
            'equipment_list': equipment_list,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def phenomenon_condition_list(m_mgt_cls_skey):

    if m_mgt_cls_skey is None:
        condition_list = MasterConditionCode.objects.filter(m_site_skey=2)
    else:
        condition_list = MasterConditionCode.objects.filter(m_site_skey=2, m_mgt_cls_skey=m_mgt_cls_skey)

    return condition_list


def get_maintenance_equipment_list(phenomenon_id, flag):

    maintenance_equipment_list = '<font size="5">機器は登録されていません</font>'
    if phenomenon_id != 0:  # 更新時のみ
        maintenance_equipment_data = MaintenanceEquipment.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0)
        if maintenance_equipment_data.count() != 0:  # 機器が存在する時のみ
            maintenance_equipment_list = '<table>'
            equipment_no = ''
            for equipment in maintenance_equipment_data:
                fcltyldgr = FcltyLdgr.objects.get(t_fclty_ldgr_skey=equipment.t_fclty_ldgr_skey)
                maintenance_equipment_list += '<tr><td><font size="5">(' + fcltyldgr.eqpt_id + ')' + None_to_blank(fcltyldgr.fclty_nm) + '</font></td>'
                if flag == 1:  # edit時のみ
                    maintenance_equipment_list += '<td><input type = "button" id = "equipment_delete_button_' + str(equipment.id) + '" value = "　削除　" ' \
                                    + 'onclick = "equipment_delete(' + str(equipment.id) + ')"></td>'
                maintenance_equipment_list += '</tr>'
                if equipment == maintenance_equipment_data[0]:
                    equipment_no += None_to_blank(fcltyldgr.fclty_nm)
                else:
                    equipment_no += '/' + None_to_blank(fcltyldgr.fclty_nm)

            maintenance_equipment_list += '</table>'
            phenomenon_data = Phenomenon.objects.get(phenomenon_id=phenomenon_id)
            phenomenon_data.equipment_no = equipment_no
            phenomenon_data.save()

    return maintenance_equipment_list
