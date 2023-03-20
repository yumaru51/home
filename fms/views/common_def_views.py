# import pywin32 as pywin32
from django.contrib.auth.decorators import login_required
from datetime import datetime, timezone
import os
import glob
import traceback
from django import template

from django.db.models import Q

from socket import gethostname
# from django.contrib.auth.models import User
from django.shortcuts import render
from fms.models import Log, Progress, StepMaster, UserAttribute, StepRelation, User, UserAccessPermission
from enum import Enum


# 稼働サーバー判定
def is_production_server():
    if gethostname() == 'YWEBSERV1':  # 本番
        return True
    return False


# 共有フォルダベースパス取得
def get_facility_data_base_path():
    return r'\\Ydomnserv\common\部門間フォルダ\FacilityData'


# テンプレートファイル配置パス取得
def get_template_file_base_path(target_folder):
    return get_facility_data_base_path() + r'\template_files' + "\\" + target_folder


# テンプレートファイルパス取得
def get_template_file_path(target_folder, templates_file_name):
    return get_template_file_base_path(target_folder) + "\\" + templates_file_name


# 出力ファイル配置パス取得
def get_output_file_base_path(target_folder):
    return get_template_file_base_path(target_folder) + r'\output_files'


# 出力ファイルパス取得
def get_output_file_path(target_folder, output_file_name):
    return get_output_file_base_path(target_folder) + "\\" + output_file_name


# 出力フォルダファイル削除(前回ファイル削除用)
def clear_output_file_folder(target_folder):
    target_folder = get_output_file_base_path(target_folder) + r'\*'
    file_list = glob.glob(target_folder)
    for file in file_list:
        os.remove(file)
    return


# 入力ファイル配置パス取得
def get_input_file_base_path(target_folder):
    return get_template_file_base_path(target_folder) + r'\input_files'


# 入力ファイルパス取得
def get_input_file_path(target_folder, input_file_name):
    return get_input_file_base_path(target_folder) + "\\" + input_file_name


# 入力フォルダファイル削除(前回ファイル削除用)
def clear_input_file_folder(target_folder):
    target_folder = get_input_file_base_path(target_folder) + r'\*'
    file_list = glob.glob(target_folder)
    for file in file_list:
        os.remove(file)
    return


# 添付ファイルベースパス取得
def get_attachment_file_base_path():
    if is_production_server():
        return get_facility_data_base_path() + r'\Production'
    return get_facility_data_base_path() + r'\test'


# 添付ファイル配置パス取得
def get_attachment_folder_name(target, budget_id, work_id, target_folder):
    attach_folder_name = "\\" + target + "\\" + str(budget_id) + "\\" + str(work_id) + "\\"
    folder_name = get_attachment_file_base_path() + attach_folder_name + target_folder + "\\"
    return folder_name, attach_folder_name


# 詳細仕様_自由記入テンプレートタイプ
class TemplateType(Enum):
    FREE_SPEC_DATA = 1  # 機器詳細仕様
    CONFIDENTIALITY = 2  # 秘密保持条件
    WARRANTY = 3  # 瑕疵担保責任
    ACCEPTANCE_CONDITIONS = 4  # 検収条件
    TEST_RUN_PASS = 5  # 試運転の合格基準
    INSPECTION_PERIOD = 6  # 検査の期間


# 絞込条件マスタ情報取得
def get_filter_master():
    from fms.models import BudgetConditionMaster, BusinessYearMaster, BudgetClassMaster,\
        DivisionMaster, DepartmentMaster, ProcessMaster

    # 予算状態選択ソース抽出
    budget_condition_list = BudgetConditionMaster.objects.filter(lost_flag=0).all()
    # 年度選択ソース抽出
    business_year_list = BusinessYearMaster.objects.filter(lost_flag=0, display_flag=1)
    # 予算区分選択ソース抽出
    budget_class_list = BudgetClassMaster.objects.filter(lost_flag=0).all().order_by('display_order')
    # 部門選択ソース抽出
    division_list = DivisionMaster.objects.filter(lost_flag=0).all().order_by('display_order')
    # 部署選択ソース抽出
    departments_list = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')
    # 工程選択ソース抽出
    process_list = ProcessMaster.objects.filter(lost_flag=0).all().order_by('display_order')

    return budget_condition_list, business_year_list, budget_class_list, division_list,\
           departments_list, process_list


# 絞込条件エリア管理者者マスタ情報取得
def get_area_manager_master():
    from fms.models import DepartmentMaster

    # 部署選択ソース抽出
    departments_list = DepartmentMaster.objects.filter(lost_flag=0, area_manager_id__isnull=False).all()
    area_manager_list = {}
    for department_item in departments_list:
        area_manager_name = department_item.area_manager.last_name + ' ' + department_item.area_manager.first_name
        area_manager_list[department_item.area_manager_id] = area_manager_name

    return area_manager_list


# 次担当者情報取得
def get_next_target(user_cd, user_department_cd, next_division, next_department, next_parson):
    from fms.models import DepartmentMaster

    next_departments_list = {}
    next_person_list = {}

    department_data = DepartmentMaster.objects.get(department_cd=user_department_cd)
    user_division_cd = department_data.division_cd

    # 次担当者選択、空欄対応
    if next_division == "no_data":
        target_division = user_division_cd
    else:
        target_division = next_division

    if next_department == "no_data":
        target_department = user_department_cd
    else:
        target_department = next_department

    if next_parson == "no_data":
        target_person = user_cd
    else:
        target_person = next_parson

    # 上位のボックスが未選択だった場合、下位も未選択とする
    if target_division == "":
        target_department = ""

    if target_department == "":
        target_person = ""

    # 次部署選択ソース抽出
    if target_division != "":
        next_departments_list = \
            DepartmentMaster.objects.filter(lost_flag=0, division_cd=target_division).all().order_by('display_order')

    if target_department != "":
        # ユーザー選択ソース抽出
        next_person_list = get_department_person_list(target_department)

    return next_departments_list, next_person_list, target_division, target_department, target_person


# 差戻者の選択ソースの取得
# @login_required
def get_return_person(target, target_id, this_step, t_username, progress_target):
    last_operation_step = 0
    last_operation_operation_datetime = datetime(2000, 1, 1, 1, 0, 0, 0, timezone.utc)
    last_operator = ""
    last_operator_department = ""
    last_operator_division = ""

    if this_step == 213002001:
        # 全仕様書発行済み確認のみ、仕様書発行中ステップに差戻
        return_step_id = 211001011
        ans = get_return_log_data(target, target_id, return_step_id, progress_target)

        last_operation_step = ans['last_operation_step']
        last_operator = ans['last_operator']
        last_operator_department = ans['last_operator_department']
        last_operator_division = ans['last_operator_division']

    else:
        # テーブル「steprelation」から現在のステップがnext_stepになっているstep_idを取得
        step_relation_list = StepRelation.objects.filter(next_step=this_step, lost_flag=0)

        # 差戻step_idに対して繰り返し処理
        for step_relation_item in step_relation_list:
            # 対象の差戻のstep_idを取得
            step_id = step_relation_item.step_id
            ans = get_return_log_data(target, target_id, step_id, progress_target)

            # 差戻可能なログがあった場合、操作時刻が一番最近のログを保存
            if ans['success_flag'] == 1:
                if ans['last_operation_operation_datetime'] > last_operation_operation_datetime:
                    last_operation_step = ans['last_operation_step']
                    last_operation_operation_datetime = ans['last_operation_operation_datetime']
                    last_operator = ans['last_operator']
                    last_operator_department = ans['last_operator_department']
                    last_operator_division = ans['last_operator_division']

    data = {
        'last_operation_step': last_operation_step,
        'last_operator': last_operator,
        'last_operator_department': last_operator_department,
        'last_operator_division': last_operator_division
    }

    return data


# 差戻時のログデータ検索
def get_return_log_data(target, target_id, return_step_id, progress_target):
    last_operation_step = return_step_id
    last_operation_operation_datetime = datetime(2000, 1, 1, 1, 0, 0, 0, timezone.utc)
    last_operator = ''
    last_operator_department = ''
    last_operator_division = ''
    success_flag = 0

    # 対象のstep_idのログのを取得（差戻、一時保存を除外、phenomenonはcommentのtargetを含めて検索する）
    if target == 'phenomenon':
        log_data_list = Log.objects.filter(
            target=target, target_id=target_id, step=return_step_id, comment__contains=f'target:{progress_target}:'
        ).exclude(action="return").exclude(action="temporarily_saved").order_by('-operation_datetime').all()
    else:
        log_data_list = Log.objects.filter(
            target=target, target_id=target_id, step=return_step_id
        ).exclude(action="return").exclude(action="temporarily_saved").order_by('-operation_datetime').all()

    # 対象のstep_idのログのレコードがあった場合、最後のログを取得
    if log_data_list.count() > 0:
        log_data = log_data_list.first()
        last_operation_step = return_step_id
        last_operation_operation_datetime = log_data.operation_datetime
        last_operator = log_data.operator
        last_operator_department = log_data.operator_department
        last_operator_division = log_data.operator_division
        success_flag = 1

    ans = {
        'success_flag': success_flag,
        'last_operation_step': last_operation_step,
        'last_operation_operation_datetime': last_operation_operation_datetime,
        'last_operator': last_operator,
        'last_operator_department': last_operator_department,
        'last_operator_division': last_operator_division,
    }

    return ans


# 作業件数カウント用の条件辞書を取得
def get_job_count_filter(step_level, start_step_id, end_step_id):

    step_filter_list = {}

    # 特殊処理：仕様書発行中(211001011)の件数は、予算関連側に含める
    step_ext_data = StepMaster.objects.filter(lost_flag=0, step_id=211001011).first()
    ext_q_obj = Q()
    ext_q_obj.add(Q(target=step_ext_data.target), Q.AND)
    ext_q_obj.add(Q(present_step=step_ext_data.step_id), Q.AND)
    if start_step_id == 213000000 and (step_level == 4 or step_level == 5):
        ext_query_step_list = Q()
        ext_query_step_list.add(ext_q_obj, Q.OR)
        step_filter_list[str(step_ext_data.step_id)] = [step_ext_data.step_name, ext_query_step_list, 1]

    # 集計単位となるLevelのステップリストを取得
    step_data_list = StepMaster.objects.filter(lost_flag=0, step_level=step_level,
                                               step_id__gte=start_step_id,
                                               step_id__lt=end_step_id
                                               ).exclude(hidden_flag=1).order_by('display_order').order_by('step_id')
    # レベルごとのステップ値オフセットを設定
    step_level_offset = 0
    if step_level == 3:
        step_level_offset = 1000000
    elif step_level == 4:
        step_level_offset = 1000
    elif step_level == 5:
        step_level_offset = 1

    # 対象のステップリストごとに、含まれるLevel5ステップの条件を取得
    for step_data in step_data_list:
        # 対象となる始まりのstepを取得
        start_level_step_id = step_data.step_id
        end_level_step_id = step_data.step_id + step_level_offset

        # 含まれるLevel5のstepを抽出 仕様書発行中(211001011)のみ特殊処理のため除外
        step_data_level5_list = StepMaster.objects.filter(lost_flag=0, step_level=5,
                                                          step_id__gte=start_level_step_id,
                                                          step_id__lt=end_level_step_id
                                                          ).exclude(hidden_flag=1).exclude(step_id=211001011).order_by('display_order').order_by('step_id')
        filter_count = step_data_level5_list.count()

        # stepごとにtargetとステップ番号をAND条件で連結したQオブジェクトを生成
        query_step_list = Q()
        for step_data_level5 in step_data_level5_list:
            q_obj = Q()
            q_obj.add(Q(target__istartswith=step_data_level5.target), Q.AND)
            q_obj.add(Q(present_step=step_data_level5.step_id), Q.AND)
            query_step_list.add(q_obj, Q.OR)

        # 特殊処理：仕様書発行中(211001011)の件数は、予算関連側に含める
        if step_data.step_id == 213000000 and step_level == 3:
            query_step_list.add(ext_q_obj, Q.OR)
            filter_count = filter_count + 1

        # 連想配列に格納
        step_filter_list[str(step_data.step_id)] = [step_data.step_name, query_step_list, filter_count]

    return step_filter_list


# 作業件数をカウント
def get_job_count(start_step_id, end_step_id, step_level, division_cd, department_cd, username):
    from fms.views.budget_views import get_budget_make_specification

    # 指定レベルのフィルター条件を取得
    step_filter_list = get_job_count_filter(step_level, start_step_id, end_step_id)

    # ステップリストの連想配列化
    step_num_list = {}

    for key, step_data in step_filter_list.items():
        division_step_num = 0
        department_step_num = 0
        user_step_num = 0

        if step_data[2] > 0:
            division_step_num = Progress.objects.filter(step_data[1],
                                                        present_division=division_cd).count()
            # トップページは部署の件数を表示しないので抽出しない
            if not step_level == 3:
                department_step_num = Progress.objects.filter(step_data[1],
                                                              present_department=department_cd).count()

            user_step_num = Progress.objects.filter(step_data[1],
                                                    present_department=department_cd,
                                                    present_operator=username).count()

        # 連想配列に「step_id」、「step_name」、「部門に対する件数」、「部署に対する件数」、「ユーザーに対する件数」を格納
        step_num_list[key] = [step_data[0], division_step_num, department_step_num, user_step_num]

    # 詳細仕様検討中で自分が計画担当の予算の件数を加算
    if step_level == 3:
        user_count = get_budget_make_specification(133002011, department_cd, username)
        step_num_list['133000000'][3] += user_count
        user_count = get_budget_make_specification(136002011, department_cd, username)
        step_num_list['136000000'][3] += user_count
        user_count = get_budget_make_specification(132002011, department_cd, username)
        step_num_list['132000000'][3] += user_count
    elif step_level == 4:
        if start_step_id == 133000000:
            user_count = get_budget_make_specification(133002011, department_cd, username)
            step_num_list['133002000'][3] += user_count
        elif start_step_id == 136000000:
            user_count = get_budget_make_specification(136002011, department_cd, username)
            step_num_list['136002000'][3] += user_count
        elif start_step_id == 132000000:
            user_count = get_budget_make_specification(132002011, department_cd, username )
            step_num_list['132002000'][3] += user_count
    elif step_level == 5:
        if start_step_id == 133002000:
            user_count = get_budget_make_specification(133002011, department_cd, username)
            step_num_list['133002011'][3] += user_count
        elif start_step_id == 136002000:
            user_count = get_budget_make_specification(136002011, department_cd, username)
            step_num_list['136002011'][3] += user_count
        elif start_step_id == 132002000:
            user_count = get_budget_make_specification(132002011, department_cd, username)
            step_num_list['132002011'][3] += user_count

    return step_num_list


# def outlook_mail_send(to, cc, subject, body):
'''
    outlook = pywin32.client.Dispatch("Outlook.Application")

    mail = outlook.CreateItem(0)

    mail.to = to
    mail.cc = cc
    # mail.bcc = 'momoko@mahodo.com'
    mail.subject = subject
    mail.bodyFormat = 1
    mail.body = body

    mail.display(True)
    
    '''


# 次工程の部署リストを取得
def get_next_department_list(charge_department_class, target, target_id, user_department_cd):
    from fms.models import Budget
    from fms.models import DepartmentMaster
    from fms.models import Measure
    from fms.models import CsManage

    department_cd_list = []
    # &BDの分割を行い部署コードリストを作成
    if '&BD' in charge_department_class:
        department_cd_list.append(charge_department_class.replace('&BD', ''))
        department_cd_list.append('BD')
    else:
        department_cd_list.append(charge_department_class)

    next_department_list = []
    main_department_id = ''
    main_department_name = ''

    # 部署コードごとの処理
    for i, department_cd in enumerate(department_cd_list):
        department_id = ''
        # USERの置き換え
        if department_cd.endswith('USER'):
            if user_department_cd != '':
                department_cd = user_department_cd
            else:
                # パラメータ未指定の場合はBDと同処理とする
                department_cd = 'BD'

        # BDの場合のdepartment_idの取得
        if department_cd == 'BD':
            # 対象に応じて、メイン部署取得
            if target == 'budget' or target == 'probudgetunit':
                # 予算に登録されている部署を取得
                object_data_list = Budget.objects.filter(budget_id=target_id, lost_flag=0)
                if object_data_list.count() > 0:
                    department_id = object_data_list[0].budget_main_department_id
                else:
                    department_id = user_department_cd

            elif target == 'phenomenon' or target.startswith('ph_nc'):
                # 対応方針に登録されている部署を取得
                object_data_list = Measure.objects.filter(phenomenon_id=target_id, lost_flag=0)
                if object_data_list.count() > 0:
                    department_id = object_data_list[0].work_order_charge_department.department_cd
                else:
                    department_id = user_department_cd

            elif target == 'cs':
                # CsManageの参照先予算の部署を取得
                object_data_list = CsManage.objects.filter(cs_no=target_id, lost_flag=0)
                if object_data_list.count() > 0:
                    object_data_id = object_data_list[0].budget_id
                    object_data_list = Budget.objects.filter(budget_id=object_data_id, lost_flag=0)
                    if object_data_list.count() > 0:
                        department_id = object_data_list[0].budget_main_department_id
                    else:
                        department_id = user_department_cd
                else:
                    department_id = user_department_cd
        else:
            department_id = department_cd

        if i == 0:
            # リストの先頭の場合は、該当部署の所属部門の全部署を追加
            main_department_data = DepartmentMaster.objects.get(department_cd=department_id)
            department_list = DepartmentMaster.objects.filter(lost_flag=0, division_cd=main_department_data.division_cd).order_by('display_order')
            next_department_list += [department for department in department_list]
            main_department_id = department_id
            main_department_name = main_department_data.department_name
        else:
            # リストの先頭以外は、１部署だけ追加
            department_data = DepartmentMaster.objects.get(department_cd=department_id)
            next_department_list.append(department_data)

    data = {
        'next_departments_list': next_department_list,
        'department_id': main_department_id,
        'department_name': main_department_name,
    }
    return data


# 主担当部署の特殊定義を変換('CPG&BD','CWG&BD','SI&BD'など)
def convert_charge_department(value, user_department_cd=''):
    # 主担当部署がUSERの場合、パラメータで渡されたuser_departmentに置き換える
    if value.endswith('USER'):
        if user_department_cd != '':
            ret_value = user_department_cd
        else:
            # パラメータ未指定の場合はBDと同処理とする
            ret_value = 'BD'
    elif value.endswith('&BD'):
        ret_value = value.replace('&BD', '')
    else:
        ret_value = value

    return ret_value


# 計画担当者候補取得
def get_filter_planning_charge_person_list():
    return get_department_person_list('CPG')


# 部署の選択リスト(optionリストを取得)
def get_department_option_list(department_cd=''):
    from fms.models import BusinessYearMaster, DepartmentMaster
    department_option_list = ''
    department_list = DepartmentMaster.objects.filter(lost_flag=0).order_by('display_order')
    for department in department_list:
        if department.department_cd == department_cd:
            department_option_list += '<option value="' + department.department_cd + '" selected>' \
                                                 + department.department_name + '</option>'
        else:
            department_option_list += '<option value="' + department.department_cd + '">' \
                                                 + department.department_name + '</option>'

    return department_option_list


# 特定部署のユーザー選択リスト(optionリストを取得,ユーザー指定で選択済)
def get_department_person_option_list(department, username='', user_full_name=''):
    person_option_list = ''
    person_full_name = ''
    if department is not None:
        person_list = get_department_person_list(department)
        for person_item in person_list:
            if person_item.username == username or person_item.full_name == user_full_name.replace('　', ' '):
                person_option_list += '<option value="' + person_item.username + '" selected>'\
                                      + person_item.full_name + '</option>'
                person_full_name = person_item.full_name
            else:
                person_option_list += '<option value="' + person_item.username + '">'\
                                      + person_item.full_name + '</option>'

    return person_option_list, person_full_name


# 特定部署のユーザーリストを取得
def get_department_person_list(department):
    if department is not None:
        # 部署ごとの表示優先度に従って取得（user_orderの昇順、authorityの降順、usernameの'-'以降の昇順でソート）
        sql = """SELECT fms_userattribute.* , fms_user.last_name +' '+fms_user.first_name as full_name , """
        sql = sql + """ SUBSTRING( fms_userattribute.username, CHARINDEX('-', fms_userattribute.username, 0) + 1, 150) AS last_username"""
        sql = sql + """ FROM (fms_userattribute """
        sql = sql + """ LEFT JOIN fms_user ON fms_userattribute.username=fms_user.username)"""
        sql = sql + """ WHERE fms_userattribute.lost_flag=0 AND fms_userattribute.department='""" + department + """' """
        sql = sql + """ ORDER BY user_order , CONVERT(int, authority) DESC , last_username """
        user_attribute_list = UserAttribute.objects.all().raw(sql)
    else:
        user_attribute_list = []
    return user_attribute_list


# 届出CSの部署に応じた次担当者を取得
def get_next_operator_cs(department):
    next_operator = UserAttribute.objects.filter(department=department, department_charge_flag='cs').all().order_by('-id')[0]
    return next_operator


# アクセス権限チェック
def check_operator_permission(username, permission):
    ret_flag = False
    permission_list = UserAccessPermission.objects.filter(
        username=username, permission=permission, lost_flag=0)
    if permission_list.count() > 0:
        ret_flag = True
    return ret_flag


# アクセス権限取得
def get_operator_permission(username):
    permission_list = UserAccessPermission.objects.filter(username=username, lost_flag=0).order_by('permission')
    return permission_list


# 禁止文字リストの取得
def get_ng_character_list():
    from fms.models import InputNgCharacter
    # マスタから禁止文字リストを取得
    ng_character_list = list(InputNgCharacter.objects.filter(lost_flag=0).values_list('ng_character', flat=True))
    # 文字列のリストから1つの文字列に結合
    ng_character_str = "".join(ng_character_list)
    # print('禁止文字[' + ng_character_str + ']')
    return ng_character_str


# 予算基本情報修正ステップ判定
def is_edit_budget_step(value):
    if value == 133009911 or value == 136009911 or value == 132008001:
        return True
    return False


# 中期計画ステップ判定
def is_mplan_budget_step(value):
    if 132000000 <= value < 133000000:
        return True
    return False


# 予算名ラベルテキスト取得
def get_budget_name_text(value):
    if is_mplan_budget_step(value):
        return '依頼名'
    return '予算名'


# 工程終了ユーザー取得
def get_progress_end_user():
    user_attribute_data = UserAttribute.objects.get(username='END', lost_flag=0)
    return user_attribute_data


# 通常ログ出力
def output_log_info(message):
    import inspect
    import logging

    # 呼び出し元関数、ファイル名、行数を取得
    f_obj = inspect.currentframe().f_back
    func_name = f_obj.f_code.co_name
    file_name = os.path.basename(f_obj.f_code.co_filename)
    lineno = str(f_obj.f_lineno)

    # ログ出力
    log_msg = '[' + file_name + ':' + lineno + '].' + func_name + ':{' + message + '}'
    logger = logging.getLogger("info")
    logger.info(log_msg)
    return


# 異常ログ出力
def output_log_error(message):
    import inspect
    import logging

    # 呼び出し元関数、ファイル名、行数を取得
    f_obj = inspect.currentframe().f_back
    func_name = f_obj.f_code.co_name
    file_name = os.path.basename(f_obj.f_code.co_filename)
    lineno = str(f_obj.f_lineno)

    # ログ出力
    log_msg = '[' + file_name + ':' + lineno + '].' + func_name + ':{' + message + '}'
    logger = logging.getLogger("error")
    logger.error(log_msg)
    return


# 例外ログ出力
def output_log_exception(request, traceback_str):
    import inspect
    import logging

    # 呼び出し元関数、ファイル名、行数を取得
    f_obj = inspect.currentframe().f_back
    func_name = f_obj.f_code.co_name
    file_name = os.path.basename(f_obj.f_code.co_filename)
    lineno = str(f_obj.f_lineno)

    # 情報文字列化
    request_str = ',request:' + str(request) + ',POST:' + str(request.POST) + ',GET:' + str(request.GET)
    traceback_str = ',exception:' + traceback_str

    # ログ出力
    log_msg = '[' + file_name + ':' + lineno + '].' + func_name + ':' + request_str + traceback_str
    logger = logging.getLogger("error")
    logger.error(log_msg)
    return
