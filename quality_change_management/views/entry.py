# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User
from quality_change_management.forms import RequestForm, LogForm
import inspect


# entry処理
def entry(request, action):
    print(action)
    function_name = 'entry_' + action
    globals()[function_name](request)

    return redirect('top_page')


def entry_request(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    edit = 'on'

    if request_id == 0:     # 新規作成のとき
        obj = Request.objects.create(id=None)
        request_form = RequestForm(data=request.POST, instance=obj, edit=edit)
        request_form.save()
        request_id = obj.id
    else:                   # 更新のとき
        obj = Request.objects.get(id=request_id)
        request_form = RequestForm(data=request.POST, instance=obj, edit=edit)
        request_form.save()

    entry_progress(request, request_id, present_step)
    entry_log(request, request_id, present_step)
    return


def entry_quality(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']

    entry_progress(request_id, present_step)
    entry_log(request_id, present_step, request.POST['comment'])
    return


def entry_safety(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']

    entry_progress(request_id, present_step)
    entry_log(request_id, present_step, request.POST['comment'])
    return


def entry_progress(request, request_id, present_step):
    Progress.objects.update_or_create(
        request_id=request_id,
        present_step=present_step,
        defaults={'present_step': StepMaster.objects.get(step=request.POST['next_step']),
                  'present_department': request.POST['next_department'],
                  'present_operator': request.POST['next_operator'],
                  'last_step': StepMaster.objects.get(step=present_step)
                  }
    )
    return


def entry_log(request, request_id, present_step):
    progress = Progress.objects.get(request_id=request_id, last_step=present_step)
    # todo action_idパラメーターで取得
    f_object = inspect.currentframe().f_back
    function_name = f_object.f_code.co_name.replace('entry_', '')
    print(function_name)

    Log(target_id=progress.present_step.target.target,
        target_table_id=request_id,
        step=progress.present_step,
        action_id=function_name,
        operation_datetime=datetime.datetime.now(),
        operator=request.POST['next_operator'],
        operator_department=request.POST['next_department'],
        comment=request.POST['comment']
        ).save()
    return
