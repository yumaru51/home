# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
import os
from django.db.models import Q
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, ProgressForm, LogForm
from .info import info_change, info_history, info_comment
from .sub import department_lists


# top_page　progressの情報をリストする
def top_page(request):
    print('「'+request.method+'」', '部署:', UserAttribute.objects.filter(username=request.user).first().department, 'ユーザーID:', request.user)

    progress_count = []
    for step in StepMaster.objects.all():
        progress_count.append(Progress.objects.filter(present_department=UserAttribute.objects.filter(username=request.user).first().department, present_step_id=step.step).count)

    data = {
        'department': DepartmentMaster.objects.get(department_cd=UserAttribute.objects.filter(username=request.user).first().department).department_name,
        'progress_count': progress_count,
        'progress_list': Progress.objects.filter(present_department__contains=UserAttribute.objects.filter(username=request.user).first().department,
                                                 present_operator__contains=request.user),
        'progress_form': ProgressForm(initial=dict(present_department=UserAttribute.objects.filter(username=request.user).first().department,
                                                   present_operator=request.user)),
    }

    if request.method == 'POST':
        if request.POST['present_step_id']:
            data['progress_list'] = Progress.objects.filter(present_step=request.POST['present_step_id'],
                                                            present_department__contains=request.POST['present_department'],
                                                            present_operator__contains=request.POST['present_operator'])
        else:
            data['progress_list'] = Progress.objects.filter(present_department__contains=request.POST['present_department'],
                                                            present_operator__contains=request.POST['present_operator'])
        data['progress_form'] = ProgressForm(request.POST)

    return render(request, 'quality_change_management/top_page.html', data)


# 詳細画面テンプレート
def detail(request, request_id):
    print('「'+request.method+'」', '部署:', UserAttribute.objects.filter(username=request.user).first().department, 'ユーザーID:', request.user, request_id)
    if request_id == 0:     # 新規の時　StepMasterのtarget='request'で一番上を取得
        present_step = StepMaster.objects.filter(target='request').first().step

    else:                   # 既存の時　リストから現進捗のターゲットを取得してProgressデータ抽出
        progress = Progress.objects.get(request_id=request_id)
        present_step = progress.present_step.step

    # step_name取得
    step_name = StepMaster.objects.get(step=present_step).step_name

    # sessionにパラメーター格納
    request.session['request_id'] = request_id
    request.session['present_step'] = present_step

    # tab生成処理 多次元辞書編
    step_display_item_lists = StepDisplayItem.objects.filter(step=present_step, lost_flag=0).order_by('page_no')
    page_dict = {}
    for step_display_item_list in step_display_item_lists:
        function_name = 'info_' + step_display_item_list.page.page
        page_dict[step_display_item_list.page_no] = {
            'page_id': step_display_item_list.page_id,
            'page_name': step_display_item_list.page.page_name,
            'page': globals()[function_name](request).content.decode(),
            'default_page': step_display_item_list.default_page
        }

    # todo ボタン制御、entryは1stepにつき1つまで、
    authority_flag = 0
    # ①ステップ制御
    # action_class = 'entry'
    entry_dict = {'action': 'top_page', 'action_name': ''}
    if StepAction.objects.filter(step_id=present_step, action_class='entry', lost_flag=0).exists():
        entry = StepAction.objects.get(step_id=present_step, action_class='entry', lost_flag=0)
        entry_dict['action'] = entry.action_id
        entry_dict['action_name'] = entry.action.action_name

    # action_class = 'function'
    step_action_lists = StepAction.objects.filter(step_id=present_step, action_class='function', lost_flag=0)
    function_dict = {}
    index = 0
    for step_action_list in step_action_lists:
        function_dict[index] = {
            'action': step_action_list.action_id,
            'action_name': step_action_list.action.action_name,
        }
        index += 1

    # ②担当部署制御
    department_cd_lists = department_lists(request, present_step)
    for department_cd_list in department_cd_lists:
        if department_cd_list == UserAttribute.objects.filter(username=request.user).first().department:
            authority_flag = 1
    # ③ユーザー制御

    params = {
        'step_name': step_name,
        'step_display_item_list': step_display_item_lists,
        'page_dict': page_dict,
        'entry_dict': entry_dict,
        'function_dict': function_dict,
        'authority_flag': authority_flag,
    }
    return render(request, 'quality_change_management/detail.html', params)

