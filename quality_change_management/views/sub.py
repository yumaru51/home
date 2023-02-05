# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
from django.db.models import Q
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, ProgressForm, LogForm


# 担当部署制御　原課部署(BD)対応のため、部署コードリストを再取得する共通関数
def department_lists(request, step=''):
    request_id = request.session['request_id']
    present_step = request.session['present_step']

    # department_cdを配列にいれて、'BD'だったら置き換える。
    department_cd_lists = []
    for step_charge_department_list in StepChargeDepartment.objects.filter(step_id=step, lost_flag=0):
        if step_charge_department_list.charge_department == 'BD':
            if request_id == 0:     # 新規のとき
                department_cd_lists.append(UserAttribute.objects.filter(username=request.user).first().department)
            else:                   # 既存のとき
                department_cd_lists.append(Request.objects.get(id=request_id).department)
        else:
            department_cd_lists.append(step_charge_department_list.charge_department)

    return department_cd_lists

