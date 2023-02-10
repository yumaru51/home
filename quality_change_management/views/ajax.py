# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
import datetime
import os
import mimetypes
import glob
import openpyxl
from socket import gethostname
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayPage, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, LogForm
from .sub import department_lists


# ajax処理
# 次工程
def ajax_next_step(request):
    present_step = request.session['present_step']
    next_step = ''
    step = StepRelation.objects.filter(present_step_id=present_step, lost_flag=0).first().next_step_id  # 最初開いたときは先頭　forのfirst_loopのnext_step_idとなる。

    # StepRelationから選択肢抽出
    for step_relation_list in StepRelation.objects.filter(present_step_id=present_step, type='next', lost_flag=0):
        # 次工程を選択している場合は、選んだまま
        if str(step_relation_list.next_step_id) == request.POST.get('next_step'):
            step = request.POST.get('next_step')
            next_step = next_step + '<option value="' + str(step_relation_list.next_step_id) + '" selected>' + str(step_relation_list.next_step.step_name) + '</option>'
        else:
            next_step = next_step + '<option value="' + str(step_relation_list.next_step_id) + '">' + str(step_relation_list.next_step.step_name) + '</option>'

    next_department = ajax_next_department(request, step)
    next_operator = ajax_next_operator(request, next_department['department'])

    data = {
        'next_step': next_step,
        'next_department': next_department['next_department'],
        'next_operator': next_operator,
    }
    return JsonResponse(data)


# 次部署
def ajax_next_department(request, step):
    next_department = ''

    department_cd_lists = department_lists(request, step)
    department = department_cd_lists[0]  # 最初開いたときは先頭　forのfirst_loopのdepartment_cdとなる。
    for department_cd_list in department_cd_lists:
        # 次部署を選択している場合は、選んだまま
        if department_cd_list == request.POST.get('next_department'):
            department = request.POST.get('next_department')
            next_department = next_department + '<option value="' + department_cd_list + '" selected>' + DepartmentMaster.objects.get(department_cd=department_cd_list).department_name + '</option>'
        else:
            next_department = next_department + '<option value="' + department_cd_list + '">' + DepartmentMaster.objects.get(department_cd=department_cd_list).department_name + '</option>'

    data = {
        'next_department': next_department,
        'department': department,
    }
    return data


# 次作業者
def ajax_next_operator(request, department):
    next_operator = ''

    # UserAttributeから選択肢抽出
    for user_attribute_list in UserAttribute.objects.filter(department=department, lost_flag=0):
        # 次作業者を選択している場合は、選んだまま
        if str(user_attribute_list.username) == request.POST.get('next_operator'):
            next_operator = next_operator + '<option value="' + str(user_attribute_list.username) + '" selected>' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'
        else:
            if not request.POST.get('next_operator') and user_attribute_list.username == str(request.user):
                next_operator = next_operator + '<option value="' + str(user_attribute_list.username) + '" selected>' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'
            else:
                next_operator = next_operator + '<option value="' + str(user_attribute_list.username) + '">' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'

    return next_operator


# 部門変更時の部署リスト絞り込み処理
def ajax_department(request):
    request_id = request.session['request_id']
    data = ''

    # 新規データ初期値 ログイン情報より初期値選択
    if request_id == 0 or request_id is None:
        for department_master_list in DepartmentMaster.objects.filter(division_cd=request.POST['division']):
            if department_master_list.department_cd == UserAttribute.objects.filter(username=request.user).first().department:
                data = data + '<option value="' + department_master_list.department_cd + '" selected>' + department_master_list.department_name + '</option>'
            else:
                data = data + '<option value="' + department_master_list.department_cd + '">' + department_master_list.department_name + '</option>'

    # 既存データ初期値 登録データより初期値選択
    else:
        for department_master_list in DepartmentMaster.objects.filter(division_cd=request.POST['division']):
            if department_master_list.department_cd == Request.objects.get(id=request_id).department:
                data = data + '<option value="' + department_master_list.department_cd + '" selected>' + department_master_list.department_name + '</option>'
            else:
                data = data + '<option value="' + department_master_list.department_cd + '">' + department_master_list.department_name + '</option>'

    ary = {
        'department': data,
    }
    return JsonResponse(ary)


# 部署変更時のユーザーリスト絞り込み処理
def ajax_user(request):
    # request_id = request.session['request_id']
    request_id = request.session.get('request_id')
    data = ''

    # 新規データ初期値 ログイン情報より初期値選択
    if request_id == 0 or request_id is None:
        for user_attribute_list in UserAttribute.objects.filter(department=request.POST['department']):
            if user_attribute_list.username == str(request.user):
                data = data + '<option value="' + str(user_attribute_list.username) + '" selected>' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'
            else:
                data = data + '<option value="' + str(user_attribute_list.username) + '">' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'

    # 既存データ初期値 登録データより初期値選択
    else:
        for user_attribute_list in UserAttribute.objects.filter(department=request.POST['department']):
            if user_attribute_list.username == Request.objects.get(id=request_id).user:
                data = data + '<option value="' + str(user_attribute_list.username) + '" selected>' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'
            else:
                data = data + '<option value="' + str(user_attribute_list.username) + '">' + str(User.objects.get(username=user_attribute_list.username)) + '</option>'

    ary = {
        'user': data,
    }
    return JsonResponse(ary)


# 添付ファイルアップロード処理
def ajax_file_upload(request):
    request_id = request.session.get('request_id')
    target = request.session.get('target')
    present_step = request.session.get('present_step')
    str_date = datetime.datetime.now().strftime('%Y%m%d')  # 日時フォーマット対応　'YYYYMMDD'

    # ベースディレクトリ
    if gethostname() == 'YWEBSERV1':  # 本番
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\Production\\quality_change_management'
    elif gethostname() == 'I7161DD6':  # テスト
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management'
    else:
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management'

    # ファイルが1件もない、または新規画面の時　アップロード不可
    if request.FILES.__len__() == 0:
        msg = "ファイルが選択されていません！"
    elif request_id == 0:
        msg = "一時保存を行ってからファイルを添付してください！"
    else:
        # ファイルアップロードフォームが複数ある場合1ファイルずつ処理を行う。
        for file_list in request.FILES.dict():
            for file in request.FILES.getlist(file_list):
                file_name = str_date + "_" + file.name

                # アップロードファイルパス
                upload_file_path = base_dir + '\\' + str(request_id) + '\\'

                # 存在チェック　なければフォルダ作成
                if os.path.exists(upload_file_path) is not True:
                    os.makedirs(upload_file_path, exist_ok=True)
                path = os.path.join(upload_file_path, file_name)

                with open(path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)

        msg = "アップロード完了！！"

    ary = {
        'msg': msg,
    }
    # return JsonResponse(ary)
    return redirect('quality_change_management:detail', present_step, target, request_id)


# 添付ファイルリスト表示処理
def ajax_file_list(request):
    # request_id = request.session['request_id']
    request_id = request.session.get('request_id')
    target = request.session.get('target')
    present_step = request.session.get('present_step')

    html = '<h3>ファイル一覧</h3>保存添付ファイル無し'
    delete_flag = 1
    if present_step == 9999:
        delete_flag = 0

    # ベースディレクトリ
    if gethostname() == 'YWEBSERV1':  # 本番
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\Production\\quality_change_management\\'
    elif gethostname() == 'I7161DD6':  # テスト
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'
    else:
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'

    # 指定フォルダ内のファイル名をリストに格納
    path = base_dir + str(request_id)
    # 存在チェック　なければフォルダ作成
    if os.path.exists(path) is True:
        files_file = os.listdir(path)
        # files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]

        # html言語生成
        html = '<h3>ファイル一覧</h3>'
        if len(files_file) > 0:
            for file in files_file:
                html = html + '<div class="row">'
                html = html + '<div class="col-5">' + file + '</div>'
                # html = html + '<div class="col-2"><button type="button" onclick="file_download(\'' + str(request_id) + '\', \'' + file + '\');" class="btn btn-primary mt-2"> 取出 </button></div>'
                html = html + '<div class="col-2"><a href="../../../../ajax_file_list/' + str(request_id) + '/' + file + '/" class="btn btn-primary mt-2"> 取出 </a></div>'
                if delete_flag == 1:
                    # html = html + '<div class="col-2"><button type="button" onclick="file_delete(\'' + file + '\');" class="btn btn-primary mt-2"> 削除 </button></div>'
                    html = html + '<div class="col-2"><a href="../../../../ajax_file_delete/' + file + '/" class="btn btn-primary mt-2"> 削除 </a></div>'
                html = html + '</div>'
        else:
            html = html + '保存添付ファイル無し'

    ary = {
        'html': html,
    }

    return JsonResponse(ary)


# 添付ファイルダウンロード処理
def ajax_file_download(request, data_id, file_name):

    # ベースディレクトリ
    if gethostname() == 'YWEBSERV1':  # 本番
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\Production\\quality_change_management\\'
    elif gethostname() == 'I7161DD6':  # テスト
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'
    else:
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'

    file_full_path = base_dir + data_id + "\\" + file_name

    if os.path.isfile(file_full_path) is False:
        msg = '対象ファイルが存在しません！！'

    return FileResponse(open(file_full_path, "rb"), as_attachment=True, filename=file_name)


# 添付ファイル削除処理
# def ajax_file_delete(request):
def ajax_file_delete(request, file_name):
    request_id = request.session.get('request_id')
    target = request.session.get('target')
    present_step = request.session.get('present_step')
    # file_name = request.POST['file_name']

    # ベースディレクトリ
    if gethostname() == 'YWEBSERV1':  # 本番
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\Production\\quality_change_management\\'
    elif gethostname() == 'I7161DD6':  # テスト
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'
    else:
        base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\test\\quality_change_management\\'

    file_full_path = base_dir + str(request_id) + "\\" + file_name

    # ファイル削除、レコード削除
    if os.path.isfile(file_full_path) is True:
        os.remove(file_full_path)

    ary = {
        'msg': 'データを削除しました',
    }
    # return JsonResponse(ary)
    return redirect('quality_change_management:detail', present_step, target, request_id)

