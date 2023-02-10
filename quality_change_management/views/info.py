# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
import json
from quality_change_management.models import TargetMaster, StepMaster, StepPageEntryMaster, StepDisplayPage, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, Request2Form, Request3Form, QualityForm, SafetyForm, Quality2Form, Safety2Form, LogForm, TestForm
from .ajax import ajax_file_list
from .sub import department_lists


# info処理
def info_change(request):
    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']
    edit = 'off'

    # request_form
    if request_id == 0:     # 新規のとき
        edit = 'on'
        request_list = ''
        request_form = RequestForm(initial=dict(division=UserAttribute.objects.filter(username=request.user).first().division,
                                                department=UserAttribute.objects.filter(username=request.user).first().department,  # 部署・ユーザー画面描写時に再読み込み
                                                user=UserAttribute.objects.filter(username=request.user).first().username,          # 部署・ユーザー画面描写時に再読み込み
                                                delivery_date=datetime.datetime.now()),
                                   edit=edit, step=present_step)
        request_form.fields['change_target'].initial = []

    else:                   # 既存のとき
        request_list = Request.objects.get(id=request_id)
        # todo edit/info切替、form毎に制御をかける ③未対応
        # ①ステップ&ページ制御
        if StepPageEntryMaster.objects.filter(step_id=present_step, page='change', lost_flag=0).count() >= 1:
            # ②担当部署制御
            department_cd_list = department_lists(request, present_step)
            for department_cd_list in department_cd_list:
                for user_attribute in UserAttribute.objects.filter(username=request.user):
                    if department_cd_list == user_attribute.department:
                        edit = 'on'
                        # ③ユーザー制御

        # チェックボックス形式のデータを置換
        change_target = request_list.change_target.replace('[', '').replace(']', '').replace('\'', '').replace(' ', '')
        change_target = change_target.split(',')
        request_form = RequestForm(instance=request_list, edit=edit, step=present_step, initial=dict(change_target=change_target))

    # formセット
    request2_form = Request2Form(edit=edit, step=present_step)
    request3_form = Request3Form(edit=edit, step=present_step)
    quality_form = QualityForm(edit=edit, step=present_step)
    safety_form = SafetyForm(edit=edit, step=present_step)
    quality2_form = Quality2Form(edit=edit, step=present_step)
    safety2_form = Safety2Form(edit=edit, step=present_step)

    # todo データがない場合エラーになりそう
    # form
    if Progress.objects.filter(request_id=request_id, target='quality', present_step_id__in=(1302, 1303)).count() == 1:
        quality_list = Quality.objects.get(request_id=request_id)
        quality_form = QualityForm(instance=quality_list, edit=edit, step=present_step)
    if Progress.objects.filter(request_id=request_id, target='safety', present_step_id__in=(1302, 1303)).count() == 1:
        safety_list = Safety.objects.get(request_id=request_id)
        safety_form = SafetyForm(instance=safety_list, edit=edit, step=present_step)
    if present_step >= 1401:
        request2_form = Request2Form(instance=request_list, edit=edit, step=present_step)
    if present_step >= 1601:
        request3_form = Request3Form(instance=request_list, edit=edit, step=present_step)
    if Progress.objects.filter(request_id=request_id, target='quality', present_step_id__in=(1502, )).count() == 1:
        quality_list = Quality.objects.get(request_id=request_id)
        quality2_form = Quality2Form(instance=quality_list, edit=edit, step=present_step)
    if Progress.objects.filter(request_id=request_id, target='safety', present_step_id__in=(1502, )).count() == 1:
        safety_list = Safety.objects.get(request_id=request_id)
        safety2_form = Safety2Form(instance=safety_list, edit=edit, step=present_step)

    log_form = LogForm()

    # 添付ファイルリスト表示処理
    file_list = ajax_file_list(request).content.decode()
    file_list = json.loads(file_list)

    params = {
        'target': target,
        'present_step': present_step,
        'request_list': request_list,
        'request_form': request_form,
        'request2_form': request2_form,
        'request3_form': request3_form,
        'quality_form': quality_form,
        'safety_form': safety_form,
        'quality2_form': quality2_form,
        'safety2_form': safety2_form,
        'log_form': log_form,
        'file_list': file_list['html'],  # 添付ファイルリスト表示処理
    }
    return render(request, 'quality_change_management/change.html', params)


def info_history(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']

    step_list = StepMaster.objects.filter(hidden_flag=0)

    if request_id == 0:     # 新規のとき
        request_list = ''

    else:                   # 既存のとき
        request_list = Request.objects.get(id=request_id)

    params = {
        'request_list': request_list,
        'present_step': present_step,
        'step_list': step_list,
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

