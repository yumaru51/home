# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, LogForm
from .sub import department_lists


# ajax処理
# 次工程
def ajax_next_step(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    next_step = ''
    step = StepRelation.objects.filter(present_step_id=present_step, lost_flag=0).first().next_step_id  # 最初開いたときは先頭　forのfirst_loopのnext_step_idとなる。

    # StepRelationから選択肢抽出
    for step_relation_list in StepRelation.objects.filter(present_step_id=present_step, lost_flag=0):
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
    request_id = request.session['request_id']
    present_step = request.session['present_step']
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
    request_id = request.session['request_id']
    present_step = request.session['present_step']
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


def ajax_department(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    data = ''

    # 新規データ初期値 ログイン情報より初期値選択
    if request_id == 0:
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


def ajax_user(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    data = ''

    # 新規データ初期値 ログイン情報より初期値選択
    if request_id == 0:
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

