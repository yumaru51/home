# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
from quality_change_management.models import TargetMaster, StepMaster, StepPageEntryMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, LogForm, TestForm
from .sub import department_lists
from django.contrib import messages


# info処理
def info_change(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    edit = 'off'

    if request_id == 0:     # 新規のとき
        edit = 'on'
        request_list = ''
        request_form = RequestForm(initial=dict(division=UserAttribute.objects.filter(username=request.user).first().division,
                                                department=UserAttribute.objects.filter(username=request.user).first().department,  # 部署・ユーザー画面描写時に再読み込み
                                                user=UserAttribute.objects.filter(username=request.user).first().username,          # 部署・ユーザー画面描写時に再読み込み
                                                delivery_date=datetime.datetime.now()),
                                   edit=edit)

    else:                   # 既存のとき
        request_list = Request.objects.get(id=request_id)
        # todo edit/info切替、form毎に制御をかける ③未対応
        # ①ステップ&ページ制御
        if StepPageEntryMaster.objects.filter(step_id=present_step, page='change', lost_flag=0).count() == 1:
            # ②担当部署制御
            department_cd_list = department_lists(request, present_step)
            for department_cd_list in department_cd_list:
                if department_cd_list == UserAttribute.objects.filter(username=request.user).first().department:
                    edit = 'on'
                    # ③ユーザー制御
        request_form = RequestForm(instance=request_list, edit=edit)

    log_form = LogForm()
    messages.info(request, 'まだ企業情報が登録されていません。')

    params = {
        'request_list': request_list,
        'request_form': request_form,
        'log_form': log_form,
    }
    return render(request, 'quality_change_management/change.html', params)


def info_history(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    if request_id == 0:     # 新規のとき
        request_list = ''

    else:                   # 既存のとき
        request_list = Request.objects.get(id=request_id)

    params = {
        'request_list': request_list,
        'present_step': present_step,
    }
    return render(request, 'quality_change_management/history.html', params)


def info_comment(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    if request_id == 0:     # 新規のとき
        request_list = ''
        log_list = ''

    else:                   # 既存のとき
        request_list = Request.objects.get(id=request_id)
        log_list = Log.objects.filter(target='request', target_table_id=request_id).order_by('-operation_datetime')

    params = {
        'request_list': request_list,
        'log_list': log_list,
    }
    return render(request, 'quality_change_management/comment.html', params)

