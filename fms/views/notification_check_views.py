import datetime
import json
import math
import traceback
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from fms.models import BusinessYearMaster, DepartmentMaster, DivisionMaster, UserAttribute, User, StepFunctionUserMaster
from fms.models import CheckListItemRelation, CheckListDepartmentRelation
from fms.models import CheckItemMaster, CheckList
from fms.models import DataEntryStepMaster, Progress, Log, StepMaster
from fms.models import Phenomenon, Measure, NotificationCheck
from common.common_def import date_to_many_type
from plantia.models import MasterLocation
from .common_views import blank_to_None
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_exception, get_department_person_list, get_next_target
from fms.views.notice_mail_views import step_notice


# 届出チェック情報で表示
@login_required
@require_POST
def notification_check_data_info(request):
    try:
        DIFF_JST_FROM_UTC = 9
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        phenomenon_unique_id = int(request.POST['phenomenon_unique_id'])
        ph_nc_progress_id = int(request.POST['ph_nc_progress_id'])
        new_step = int(request.POST['new_step'])
        user_division_cd = request.POST['user_division_cd']
        user_department_cd = request.POST['user_department_cd']
        user_authority = int(request.POST['user_authority'])
        confirm_user = request.POST['confirm_user']
        permit_user = request.POST['permit_user']
        level5_step_id = int(request.POST['level5_step_id'])
        this_step = int(request.POST['this_step'])
        target = request.POST['target']
        div_id_name = request.POST['div_id_name']
        action_button_id = target + '_' + div_id_name + '_action_button'
        present_step = new_step
        check_list_data = ''
        check_items_set = ''
        check_comment_set = ''

        step_master_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)

        # 異常報告保存前
        if phenomenon_unique_id == 0:
            target_notification_check_id = 0
        # 異常報告保存済
        else:
            phenomenon_data = Phenomenon.objects.get(id=phenomenon_unique_id)
            phenomenon_id = phenomenon_data.phenomenon_id
            notification_check_data_num = NotificationCheck.objects.filter(phenomenon_id=phenomenon_id).count()

            if notification_check_data_num == 0:
                target_notification_check_id = 0
            else:
                notification_check_data = NotificationCheck.objects.get(phenomenon_id=phenomenon_id)
                target_notification_check_id = notification_check_data.phenomenon_id

        # チェック項目マスタ取得
        check_item_list = CheckItemMaster.objects.filter(lost_flag=0).order_by('display_order')

        # 新規でないときの処理･･･該当のデータを読み込み
        if target_notification_check_id > 0:
            notification_check_data = NotificationCheck.objects.get(phenomenon_id=phenomenon_id)
            notification = notification_check_data.notification
            law_facility = notification_check_data.law_facility
            comment = notification_check_data.comment

            # チェックリストデータの取得
            check_list_list = CheckList.objects.filter(function_cd='ph_nc', target='notification_check', target_id=notification_check_data.phenomenon_id)
            if check_list_list.count() > 0:
                check_list_data = check_list_list.first()
                check_items_set = CheckListItemRelation.objects.filter(check_list_id=check_list_data.id)
                check_comment_set = CheckListDepartmentRelation.objects.filter(check_list_id=check_list_data.id)

        # 新規の時の処理･･･基本的にはほぼすべての項目空欄
        else:
            notification_check_data = ""
            notification = None
            law_facility = None
            comment = ""

        # データ編集機能要否判定
        edit_flag = DataEntryStepMaster.objects.filter(step_id=this_step, target_table='notification_check').count()

        # 部署ごとのコメント部分編集権限判定
        edit_department_flag = ''
        if step_master_data.target == 'phenomenon':
            edit_department_flag = 'BD'
        elif step_master_data.target == 'ph_nc' and notification_check_data != '' and check_list_data != '':
            # progressを取得し、編集権限を判定する
            if ph_nc_progress_id != 0:
                progress_data = Progress.objects.get(id=ph_nc_progress_id)
                if progress_data.target == 'ph_nc':
                    edit_department_flag = 'BD'
                else:
                    edit_department_flag = progress_data.target.replace('ph_nc_', '')

        department_progress_list = {}

        # 原課部署の進捗状況
        if notification_check_data != '':
            progress_list = Progress.objects.filter(target='ph_nc', target_id=notification_check_data.phenomenon_id)
            if progress_list.count() > 0:
                progress_data = progress_list.first()
                step_name = StepMaster.objects.get(step_id=progress_data.present_step, lost_flag=0).step_name
                if progress_data.present_operator is not None:
                    user_data = User.objects.get(username=progress_data.present_operator, lost_flag=0)
                else:
                    user_data = ''
                department_progress_list['BD'] = {'step_name': step_name, 'user': str(user_data)}
            else:
                department_progress_list['BD'] = {'step_name': '', 'user': ''}

        # 所管部署の進捗状況
        department_progress_complete_flag = 0
        if check_list_data != '':
            progress_list = Progress.objects.filter(target__startswith='ph_nc_', target_id=check_list_data.target_id)
            department_progress_complete_flag = 1
            for progress_data in progress_list:
                step_name = StepMaster.objects.get(step_id=progress_data.present_step, lost_flag=0).step_name
                if progress_data.present_operator is None or progress_data.present_operator == '':
                    user_data = ''
                else:
                    user_data = User.objects.get(username=progress_data.present_operator, lost_flag=0)
                department_progress_list[progress_data.target.replace('ph_nc_', '')] = {'step_name': step_name, 'user': str(user_data)}
                if progress_data.present_step != 233002091:
                    department_progress_complete_flag = 0

        data = {
            'notification_check_data': notification_check_data,
            'notification_check_id': target_notification_check_id,
            'notification': notification,
            'law_facility': law_facility,
            'comment': comment,

            'check_item_list': check_item_list,
            'check_list_data': check_list_data,
            'check_items_set': check_items_set,
            'check_comment_set': check_comment_set,

            't_username': t_username,
            'user_department_cd': user_department_cd,
            'action_button_id': action_button_id,

            'div_id_name': div_id_name,
            'this_step': this_step,

            'edit_department_flag': edit_department_flag,

            'department_progress_list': department_progress_list,
            'department_progress_complete_flag': department_progress_complete_flag,
        }

        if edit_flag > 0:
            return render(request, 'fms/parts/maintenance/notification_check/notification_check_edit.html', data)
        else:
            return render(request, 'fms/parts/maintenance/notification_check/notification_check_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 届出チェック情報を登録･更新処理
@login_required
@require_POST
def notification_check_entry(request):
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
        permit_user = request.POST["permit_user"]
        user_attribute_id = int(request.POST["user_attribute_id"])
        edit_department_flag = request.POST["edit_department_flag"]
        ph_nc_progress_id = int(request.POST["ph_nc_progress_id"])

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        if request.POST["phenomenon_id"] is not "":
            phenomenon_id = int(request.POST["phenomenon_id"])
        else:
            raise ValueError("Phenomenon id not specified.")

        if request.POST["notification_check_id"] is not "":
            notification_check_id = int(request.POST["notification_check_id"])
        else:
            notification_check_id = 0

        sub_no = 0
        notification = int(request.POST["notification"])
        law_facility = int(request.POST["law_facility"])
        comment = request.POST["comment"]
        cancel_comment = request.POST["cancel_comment"]

        # 入力情報は連想配列形式で取得
        input_value_array = json.loads(request.POST['input_value_array'])

        # 新規登録時の処理
        if notification_check_id == 0:
            notification_check_id = phenomenon_id
            notification_check_data, created = NotificationCheck.objects.get_or_create(phenomenon_id=notification_check_id, lost_flag=0)
            if created:
                # 登録の日時、登録者を登録
                notification_check_data.entry_datetime = now
                notification_check_data.entry_operator = operator
                # 届出チェックのレコードを保存
                notification_check_data.save()
            action_type = "add"
        # 更新時の処理
        else:
            action_type = "edit"

        # 主キーで届出チェックレコードを抽出
        notification_check_data = NotificationCheck.objects.get(phenomenon_id=notification_check_id, lost_flag=0)

        notification_check_data.phenomenon_id = phenomenon_id
        notification_check_data.sub_no = sub_no

        notification_check_data.notification = notification
        notification_check_data.law_facility = law_facility

        # 原課コメント入力可能のステップ以外では、コメントを上書きしない
        if edit_department_flag == 'BD':
            notification_check_data.comment = blank_to_None(comment)
            notification_check_data.cancel_comment = blank_to_None(cancel_comment)

        if action_type == "add":
            msg = "小口届出チェックデータ新規登録完了！！"
        # 更新の場合の処理
        else:
            notification_check_data.update_datetime = now
            notification_check_data.update_operator = operator
            msg = "小口届出チェックデータ更新完了！！"

        # 届出チェックのレコードを保存
        notification_check_data.save()

        # チェック項目マスタ取得
        check_item_list = CheckItemMaster.objects.filter(lost_flag=0).order_by('display_order')

        # チェックリストのデータ保存
        if action_type == "add":
            # 新規レコード作成
            check_list_data, created = CheckList.objects.get_or_create(
                function_cd='ph_nc', target='notification_check',
                target_id=phenomenon_id, lost_flag=0)
            if created:
                check_list_data.save()

            # チェック項目の関連追加
            check_list_data = CheckList.objects.get(function_cd='ph_nc', target='notification_check', target_id=notification_check_id, lost_flag=0)
            for check_item in check_item_list:
                check_data, created = CheckListItemRelation.objects.get_or_create(
                    check_item_id=check_item.check_cd,
                    check_list_id=check_list_data.id,
                    check_status=0,
                )
                check_data.save()
            check_list_data.save()

        else:
            check_list_data = CheckList.objects.get(function_cd='ph_nc', target='notification_check', target_id=notification_check_id, lost_flag=0)

        # チェック状態と入力テキストの保存
        check_count = 0
        for check_item in check_item_list:
            # DB上に新規項目が追加された時に備えてget_or_createする
            check_data, created = CheckListItemRelation.objects.get_or_create(check_list_id=check_list_data.id, check_item_id=check_item.check_cd)

            # DB上に新規項目が追加された時は一致するキーがPOSTされないので、考慮する
            if check_item.check_cd in input_value_array:
                if input_value_array[check_item.check_cd] == 1:
                    check_data.check_status = 1
                    check_count = check_count + 1
                else:
                    check_data.check_status = 0

                if check_data.check_item.text_input_flag == 1:
                    check_data.input_text = blank_to_None(input_value_array[f'{check_item.check_cd}_text'])
            else:
                check_data.check_status = 0

            check_data.save()

        # 所管部署コメントの保存
        if edit_department_flag != '' and edit_department_flag != 'BD':
            check_department_list = CheckListDepartmentRelation.objects.filter(check_list_id=check_list_data.id, department_id=edit_department_flag)
            if check_department_list.count() > 0:
                check_department = check_department_list.first()
                check_department.comment = blank_to_None(input_value_array[f'{edit_department_flag}_notification_comment'])
                check_department.save()


        # ログのコメント作成
        comment = "notification_check_id : " + str(notification_check_id)

        if this_step == next_step:
            action = "temporarily_saved"
        elif next_step == 233009902:
            action = "stop"
        else:
            action = "entry"

        if ph_nc_progress_id != 0:
            # ログにtarget情報を残す
            progress_data = Progress.objects.get(id=ph_nc_progress_id)
            comment = f'{comment}\ntarget:{progress_data.target}:'
        else:
            comment = f'{comment}\ntarget:phenomenon:'

        # ログを新規登録
        Log(target='phenomenon', target_id=phenomenon_id, action=action, operator=operator,
            operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
            operator_division=this_division).save()

        # 届出チェック側Progressの進行
        step_master_data = StepMaster.objects.get(step_id=this_step, lost_flag=0)

        # 工程完了に進む時は届出チェックのprogressは作成しない
        if step_master_data.target == 'phenomenon' and this_step <= 231001011 < next_step != 232009901:
            # 対応方針以降のステップに移行する場合(その前はphenomenonのprogressで管理する)
            progress_data, created = Progress.objects.get_or_create(target="ph_nc",
                                                                    target_id=notification_check_id)
            # progress作成済の場合はデータ更新しない
            if created:
                measure_data = Measure.objects.get(phenomenon_id=phenomenon_id)
                progress_data.present_step = 233001001
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now

                # 次部署は原課
                progress_data.present_department = measure_data.work_order_charge_department_id
                department_data = DepartmentMaster.objects.get(department_cd=progress_data.present_department)
                progress_data.present_division = department_data.division_cd

                # 依頼部門の主任(101以上)のユーザーに割り当てる
                function_user_list = StepFunctionUserMaster.objects.filter(
                    step_id=progress_data.present_step,
                    department_id=progress_data.present_department,
                    lost_flag=0).order_by('user_order')
                if function_user_list.count() > 0 and function_user_list.first().user_id is not None:
                    progress_data.present_operator = function_user_list.first().user_id
                else:
                    step_data = StepMaster.objects.get(step_id=progress_data.present_step)
                    progress_data.present_operator = None
                    msg = msg + f'\n【要確認】依頼部署の担当者情報が無いため、\n{step_data.step_name}の進捗は部署のみ設定しました。\n確認をお願いします。'

                progress_data.save()
                # 進捗通知機能
                step_notice(progress_data)

        elif step_master_data.target == 'ph_nc':

            # 小口CS承認より先に進む場合 所管部署を確認し、RelationとProgressを作成する
            if this_step <= 233001011 < next_step:
                relation_departments = {}
                item_relation_list = CheckListItemRelation.objects.filter(check_list_id=check_list_data.id)
                for item_relation in item_relation_list:
                    if item_relation.check_status == 1:
                        for department in item_relation.check_item.assign_departments.all():
                            relation_departments[department.department_cd] = 1

                for department_cd in relation_departments.keys():
                    relation_data, created = CheckListDepartmentRelation.objects.get_or_create(
                        check_list_id=check_list_data.id,
                        department_id=department_cd)
                    if created:
                        relation_data.save()
                        # 新規作成された場合は所管部署用のprogressを作成する
                        progress_data, created = Progress.objects.get_or_create(target=f"ph_nc_{department_cd}",
                                                                                target_id=notification_check_id)
                        if created:
                            progress_data.present_step = 233002001
                            progress_data.present_department = relation_data.department.department_cd
                            progress_data.present_division = relation_data.department.division_cd

                            # 所管部署の担当者の設定
                            function_user_list = StepFunctionUserMaster.objects.filter(
                                step_id=progress_data.present_step,
                                department_id=progress_data.present_department,
                                lost_flag=0).order_by('user_order')
                            if function_user_list.count() > 0 and function_user_list.first().user_id is not None:
                                progress_data.present_operator = function_user_list.first().user_id
                            else:
                                step_data = StepMaster.objects.get(step_id=progress_data.present_step)
                                progress_data.present_operator = None
                                msg = msg + f'\n【要確認】所管部署の担当者情報が無いため、\n{step_data.step_name}の進捗は部署のみ設定しました。\n確認をお願いします。'

                            progress_data.last_operation_step = this_step
                            progress_data.last_operator = operator
                            progress_data.last_operation_datetime = now
                            progress_data.save()
                            # 進捗通知機能
                            step_notice(progress_data)

            # 小口CS法令施設確認で法令該当施設が無い場合 小口届出チェック完了に移行して終了
            if this_step <= 233001001 < next_step and check_count == 0:
                next_step = 233009901
                progress_data = Progress.objects.get(id=ph_nc_progress_id)
                progress_data.present_step = next_step
                progress_data.present_department = 'END'
                progress_data.present_division = 'END'
                progress_data.present_operator = 'END'
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                progress_data.save()
                msg = msg + "\n法令施設非該当のため、小口届出チェックを完了します。"

            elif this_step < 233009902 == next_step:
                # 小口届出チェック中止処理
                notification_check_data = NotificationCheck.objects.get(phenomenon_id=notification_check_id,
                                                                        lost_flag=0)
                notification_check_data.cancel_flag = 1
                notification_check_data.save()
                msg = "小口工事実施前チェック中止"

                progress_data = Progress.objects.get(id=ph_nc_progress_id)
                progress_data.present_step = next_step
                progress_data.present_department = 'END'
                progress_data.present_division = 'END'
                progress_data.present_operator = 'END'
                progress_data.last_operation_step = this_step
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                progress_data.save()

                # 所管部署側の進捗を完了させる
                progress_sub_list = Progress.objects.filter(target__startswith='ph_nc_', target_id=notification_check_id)
                for progress_sub_data in progress_sub_list:
                    progress_sub_data.present_department = 'END'
                    progress_sub_data.present_division = 'END'
                    progress_sub_data.present_operator = 'END'
                    progress_sub_data.last_operation_step = progress_sub_data.present_step
                    progress_sub_data.present_step = 233002091
                    progress_sub_data.last_operator = operator
                    progress_sub_data.last_operation_datetime = now
                    progress_sub_data.save()

            else:
                # 通常のステップ進行
                progress_data = Progress.objects.get(id=ph_nc_progress_id)
                progress_data.present_step = next_step
                progress_data.present_department = next_department
                department_data = DepartmentMaster.objects.get(department_cd=next_department)
                progress_data.present_division = department_data.division_cd
                progress_data.present_operator = next_person
                if this_step != next_step:
                    progress_data.last_operation_step = this_step
                    progress_data.last_operator = operator
                    progress_data.last_operation_datetime = now
                progress_data.save()

            # 進捗通知機能
            if this_step != next_step:
                step_notice(progress_data)

        ary = {
            'msg': msg,
            'this_notification_check_id': notification_check_id
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 届出チェックデータ一覧
@require_POST
def get_notification_check_lists(request):
    try:
        # 絞込条件設定値取得
        sel_step = request.POST['sel_step']
        sel_phenomenon_id = request.POST['sel_phenomenon_id']
        sel_project_name = request.POST['sel_project_name']
        sel_item_class = request.POST['sel_item_class']
        sel_maintenance_status = request.POST['sel_maintenance_status']
        sel_malfunction_class = request.POST['sel_malfunction_class']

        sel_delivery_date_start = request.POST['sel_delivery_date_start']
        sel_delivery_date_end = request.POST['sel_delivery_date_end']
        sel_division = request.POST['sel_division']
        sel_department = request.POST['sel_department']
        sel_process = request.POST['sel_process']

        sel_mng_charge_person = request.POST['sel_mng_charge_person']
        sel_next_division = request.POST['sel_next_division']
        sel_next_department = request.POST['sel_next_department']
        sel_next_parson = request.POST['sel_next_parson']

        sel_on_work = request.POST['sel_on_work']
        sel_display_order = request.POST['sel_display_order']

        level5_step_id = int(request.POST['level5_step_id'])
        username = request.user.username

        step_st = math.floor(level5_step_id / 1000) * 1000
        step_ed = step_st + 1000
        where_str = ""

        # 検索条件where文字列作成
        if sel_step != "":
            where_str += f" AND fms_stepmaster.step_id = {sel_step} \n"
        if sel_phenomenon_id != "":
            where_str += f" AND fms_phenomenon.phenomenon_id = {sel_phenomenon_id} \n"
        if sel_project_name != "":
            where_str += f" AND fms_phenomenon.project_title LIKE '%%{sel_project_name}%%' \n"
        if sel_item_class != "":
            where_str += f" AND fms_measure.m_exe_cls_skey = {sel_item_class} \n"
        if sel_maintenance_status != "":
            where_str += f" AND fms_measure.maintenance_status = {sel_maintenance_status} \n"
        if sel_malfunction_class != "":
            where_str += f" AND fms_measure.malfunction_class = '{sel_malfunction_class}' \n"

        if sel_delivery_date_start != "":
            date_str = date_to_many_type(sel_delivery_date_start)
            start_date = date_str.str_type_date_hyphen
            where_str += f" AND fms_measure.desired_delivery_date_end >= '{start_date}' \n"
        if sel_delivery_date_end != "":
            date_str = date_to_many_type(sel_delivery_date_end)
            end_date = date_str.str_type_date_hyphen
            where_str += f" AND fms_measure.desired_delivery_date_end <= '{end_date}' \n"

        # 保全G担当者は、検査･診断/方針決定ステップの保存操作をしたユーザーで検索
        if sel_mng_charge_person != "":
            where_str += f" AND entry_log.operator= '{sel_mng_charge_person}' \n"

        if sel_division != "":
            where_str += f" AND phenomenon_department.division_cd = '{sel_division}' \n"
        if sel_department != "":
            where_str += f" AND phenomenon_department.department_cd = '{sel_department}' \n"
        if sel_process != "":
            where_str += f" AND fms_phenomenon.m_location_skey = '{sel_process}' \n"

        if sel_next_division != "":
            where_str += f" AND fms_progress.present_division = '{sel_next_division}' \n"
        if sel_next_department != "":
            where_str += f" AND fms_progress.present_department = '{sel_next_department}' \n"
        if sel_next_parson != "":
            where_str += f" AND fms_progress.present_operator = '{sel_next_parson}' \n"

        # 未処理のみ
        if sel_on_work == 'true':
            where_str += f" AND fms_stepmaster.step_id > {step_st} \n"
            where_str += f" AND fms_stepmaster.step_id < {step_ed} \n"

        # 表示順序
        if sel_display_order == "1":  # 案件ID
            order_str = " ORDER BY fms_phenomenon.phenomenon_id \n"
        elif sel_display_order == "2":  # 発見日時
            order_str = " ORDER BY fms_phenomenon.discovery_date \n"
        else:
            order_str = " ORDER BY days_stay desc \n"

        # SQL作成
        sql = """ SELECT fms_notificationcheck.* """

        sql = sql + """  ,fms_user.first_name, fms_user.last_name """
        sql = sql + """  ,fms_stepmaster.step_name, fms_stepmaster.step_id """
        sql = sql + """  ,discovery_user.first_name AS discovery_user_first_name """
        sql = sql + """  ,discovery_user.last_name AS discovery_user_last_name"""
        sql = sql + """  ,fms_phenomenon.id AS phenomenon_unique_id  """
        sql = sql + """  ,fms_phenomenon.project_title  """
        sql = sql + """  ,fms_phenomenon.discovery_date  """
        sql = sql + """  ,fms_phenomenon.equipment_no  """
        sql = sql + """  ,phenomenon_department.department_name  AS phenomenon_department_name"""
        sql = sql + """  ,fms_progress.present_step """
        sql = sql + """  ,fms_progress.id AS progress_id"""
        sql = sql + """  ,progress_department.department_name AS progress_department_name"""

        sql = sql + """ ,CASE WHEN [log].last_operationtime IS NULL THEN DATEDIFF(DAY, fms_notificationcheck.entry_datetime, GETDATE()) """
        sql = sql + """                                     ELSE DATEDIFF(DAY, [log].last_operationtime, GETDATE()) END """
        sql = sql + """ AS days_stay  \n"""
        sql = sql + """ , CASE WHEN log_2.action = 'return' THEN 1 ELSE 0 END AS return_flag \n"""

        sql = sql + """ FROM fms_notificationcheck """
        sql = sql + """ LEFT JOIN fms_checklist ON fms_checklist.target='notification_check' AND fms_notificationcheck.phenomenon_id=fms_checklist.target_id """

        sql = sql + """ LEFT JOIN fms_progress ON """
        sql = sql + """ ( fms_progress.target='ph_nc' AND fms_notificationcheck.phenomenon_id=fms_progress.target_id ) OR """
        sql = sql + """ ( fms_progress.target LIKE 'ph_nc_%%' AND fms_checklist.target_id=fms_progress.target_id  )  """
        sql = sql + """ LEFT JOIN fms_departmentmaster progress_department ON fms_progress.present_department=progress_department.department_cd """
        sql = sql + """ LEFT JOIN fms_user ON fms_progress.present_operator=fms_user.username """
        sql = sql + """ LEFT JOIN fms_stepmaster ON fms_progress.present_step=fms_stepmaster.step_id """

        sql = sql + """ LEFT JOIN fms_phenomenon ON fms_notificationcheck.phenomenon_id=fms_phenomenon.phenomenon_id """
        sql = sql + """ LEFT JOIN fms_user discovery_user ON fms_phenomenon.user_id=discovery_user.username """
        sql = sql + """ LEFT JOIN fms_departmentmaster phenomenon_department ON fms_phenomenon.department_id=phenomenon_department.department_cd """

        sql = sql + """ LEFT JOIN fms_measure ON fms_measure.phenomenon_id=fms_phenomenon.phenomenon_id """

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
        sql = sql + """             AND sub.comment LIKE '%%ph_nc%%' \n"""
        sql = sql + """          ) AS log_2 ON fms_notificationcheck.phenomenon_id = log_2.target_id \n"""

        sql = sql + """ LEFT JOIN (SELECT \n"""
        sql = sql + """             [target_id]  \n"""
        sql = sql + """             ,MAX([operation_datetime]) as last_operationtime  \n"""
        sql = sql + """             FROM [fms].[dbo].[fms_log]  \n"""
        sql = sql + """             WHERE [target]='notificationcheck'  \n"""
        sql = sql + """                             AND [action] != 'temporarily_saved'  \n"""
        sql = sql + """             group by [target_id]) as log  \n"""
        sql = sql + """ ON [fms].[dbo].[fms_notificationcheck].phenomenon_id=log.target_id  \n"""

        sql = sql + """ LEFT JOIN (SELECT	[target_id] \n"""
        sql = sql + """                     ,MAX([operation_datetime]) as last_operationtime \n"""
        sql = sql + """                     ,action \n"""
        sql = sql + """                     ,operator \n"""
        sql = sql + """              FROM [fms].[dbo].[fms_log] \n"""
        sql = sql + """             WHERE [target]='phenomenon' \n"""
        sql = sql + """               AND [action] = 'entry' \n"""
        sql = sql + """               AND step = 231002001 \n"""
        sql = sql + """             group by [target_id],operator, action \n"""
        sql = sql + """           ) as entry_log  \n """
        sql = sql + """ ON [fms].[dbo].[fms_phenomenon].phenomenon_id=entry_log.target_id \n"""

        sql = sql + """ WHERE fms_notificationcheck.lost_flag=0 \n"""
        sql = sql + where_str

        sql = sql + order_str

        notification_check_lists = NotificationCheck.objects.all().raw(sql)
        notification_check_lists_num = len(list(notification_check_lists))

        data = {
            'notification_check_lists': notification_check_lists,
            'notification_check_lists_num': notification_check_lists_num,
        }

        return render(request, 'fms/parts/maintenance/notification_check_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 小口届出チェック一覧の絞込のパーツ表示
@require_POST
def notification_check_filter(request):
    try:
        # 進捗工程選択ソース抽出
        level5_step_id = int(request.POST["level5_step_id"])
        step_st = math.floor(level5_step_id / 1000000) * 1000000
        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5, lost_flag=0).all().order_by('step_id')

        # 年度選択ソース抽出
        business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1).all()
        # 部門選択ソース抽出
        division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 部署選択ソース抽出
        departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')
        # 工場選択ソース抽出
        facility_list = MasterLocation.objects.all().order_by('display_order')

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

        return render(request, 'fms/parts/maintenance/notification_check_filter.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


