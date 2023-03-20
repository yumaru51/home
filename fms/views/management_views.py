from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from fms.models import ProcessMaster, StepMaster, Progress
from fms.models import Log, Budget, StepAction, ActionMaster, DataEntryStepMaster
from django.contrib.auth.models import User
# from common.models import UserAttribute, DivisionMaster, DepartmentMaster
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work
from fms.models import FunctionMaster, BudgetRequiredFunction, StepMaster
import datetime
import traceback
from fms.views.common_def_views import get_return_person, get_job_count
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# step管理画面表示処理
@login_required
def step_edit(request):
    try:
        # サイドメニュー用継承データ取得
        t_username = request.user.username

        user_data = UserAttribute.objects.filter(username=t_username, lost_flag=0).all().order_by('display_order')[0]

        user_division_cd = user_data.division
        user_department_cd = user_data.department
        user_authority = user_data.authority
        confirm_user = user_data.confirm_username
        permit_user = user_data.permit_username

        data = {
            'user_division_cd': user_division_cd,
            'user_department_cd': user_department_cd,
            'user_authority': user_authority,
            'confirm_user': confirm_user,
            'permit_user': permit_user,
        }

        return render(request, 'fms/parts/management/step_edit.html', data)
        # return render(request, 'fms/parts/management/step_management.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepマスタの一覧の表示処理
def get_step_list(request):
    try:
        # stepマスタのレコード数取得
        step_master_lists_num = StepMaster.objects.all().count()

        # stepマスタにレコードがある場合の処理
        if step_master_lists_num > 0:
            # stepマスタのデータ取得
            step_master_lists = StepMaster.objects.all()
        else:
            step_master_lists = ""

        data = {
            'step_master_lists_num': step_master_lists_num,
            'step_master_lists': step_master_lists
        }

        return render(request, 'fms/parts/management/step_master_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# step関係マスタの一覧の表示処理
def get_step_relation_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        # 対象のstepのstep関係マスタのレコード数取得
        step_relation_lists_num = StepRelation.objects.filter(step_id=step_id).count()

        # step関係マスタにレコードがある場合の処理
        if step_relation_lists_num > 0:
            # 対象のstepのstep関係マスタのデータ取得
            step_relation_lists = StepRelation.objects.filter(step_id=step_id).all()
        else:
            step_relation_lists = ""

        data = {
            'step_relation_lists_num': step_relation_lists_num,
            'step_relation_lists': step_relation_lists
        }

        return render(request, 'fms/parts/management/step_relation_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工程アクションマスタの一覧の表示処理
def get_step_action_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        # 対象のstepの工程アクションマスタのレコード数取得
        step_action_lists_num = StepAction.objects.filter(step_id=step_id).count()

        # 工程アクションマスタにレコードがある場合の処理
        if step_action_lists_num > 0:
            # 対象のstepの工程アクションマスタのデータ取得
            step_action_lists = StepAction.objects.filter(step_id=step_id).all()
        else:
            step_action_lists = ""

        data = {
            'step_action_lists_num': step_action_lists_num,
            'step_action_lists': step_action_lists
        }

        return render(request, 'fms/parts/management/step_action_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 進捗工程表示項目の一覧の表示処理
def get_step_display_item_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        # 対象のstepの進捗工程表示項目のレコード数取得
        step_display_item_lists_num = StepDisplayItem.objects.filter(step=step_id).count()

        # 進捗工程表示項目にレコードがある場合の処理
        if step_display_item_lists_num > 0:
            # 対象のstepの進捗工程表示項目のデータ取得
            step_display_item_lists = StepDisplayItem.objects.filter(step=step_id).all()
        else:
            step_display_item_lists = ""

        data = {
            'step_display_item_lists_num': step_display_item_lists_num,
            'step_display_item_lists': step_display_item_lists
        }

        return render(request, 'fms/parts/management/step_display_item_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# データ登録工程マスタの一覧の表示処理
def get_data_entry_step_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        # 対象のstepのデータ登録工程マスタのレコード数取得
        data_entry_step_list_num = DataEntryStepMaster.objects.filter(step_id=step_id).count()

        # データ登録工程マスタにレコードがある場合の処理
        if data_entry_step_list_num > 0:
            # 対象のstepのデータ登録工程マスタのデータ取得
            data_entry_step_list = DataEntryStepMaster.objects.filter(step_id=step_id).all()
        else:
            data_entry_step_list = ""

        data = {
            'data_entry_step_list_num': data_entry_step_list_num,
            'data_entry_step_list': data_entry_step_list
        }

        return render(request, 'fms/parts/management/data_entry_step_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 作業マスタの一覧の表示処理
def get_action_master_list(request):
    try:
        # 作業マスタのレコード数取得
        action_master_list_num = ActionMaster.objects.all().count()

        # 作業マスタにレコードがある場合の処理
        if action_master_list_num > 0:
            # 作業マスタのデータ取得
            action_master_list = ActionMaster.objects.all()
        else:
            action_master_list = ""

        data = {
            'action_master_list_num': action_master_list_num,
            'action_master_list': action_master_list
        }

        return render(request, 'fms/parts/management/action_master_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepマスタの一覧から選択し時の処理
@require_POST
def step_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        # 対象の「step_id」で進捗マスタからレコード取得
        step_data = StepMaster.objects.get(step_id=step_id)
        # 各項目を取得
        step_name = step_data.step_name
        charge_department_class = step_data.charge_department_class
        step_level = step_data.step_level
        template_class = step_data.template_class
        new_entry_flag = step_data.new_entry_flag
        target = step_data.target
        lost_flag = step_data.lost_flag

        ary = {
            'step_id': step_id,
            'step_name': step_name,
            'charge_department_class': charge_department_class,
            'step_level': step_level,
            'template_class': template_class,
            'new_entry_flag': new_entry_flag,
            'target': target,
            'lost_flag': lost_flag
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# step管理イメージ画面の表示処理
@require_POST
def step_management(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        step_id = int(request.POST['step_id'])

        step_data = StepMaster.objects.get(step_id=step_id)
        step_name = step_data.step_name
        target_charge_department_class = step_data.charge_department_class
        target_step_level = step_data.step_level
        target_target = step_data.target
        target_new_entry_flag = step_data.new_entry_flag
        target_display_order = step_data.display_order
        target_lost_flag = step_data.lost_flag

        return_step_list_num = StepRelation.objects.filter(next_step=step_id).count()
        if return_step_list_num > 0:
            sql = """SELECT fms_steprelation.*, fms_stepmaster.step_name"""
            sql = sql + """ FROM fms_steprelation"""
            sql = sql + """ LEFT JOIN fms_stepmaster ON fms_steprelation.step_id=fms_stepmaster.step_id"""
            sql = sql + """ WHERE fms_steprelation.next_step=""" + str(step_id)
            sql = sql + """ ORDER BY fms_steprelation.next_step"""
            return_step_list = StepRelation.objects.raw(sql)
        else:
            return_step_list = ""

        step_display_item_list_num = StepDisplayItem.objects.filter(step=step_id).count()
        if step_display_item_list_num > 0:
            step_display_item_list = StepDisplayItem.objects.filter(step=step_id).order_by('page')
        else:
            step_display_item_list = ""

        step_action_list_num = StepAction.objects.filter(step_id=step_id, lost_flag=0).count()
        if step_action_list_num > 0:
            sql = """ SELECT fms_stepaction.*, fms_actionmaster.action_name"""
            sql = sql + """ FROM fms_stepaction"""
            sql = sql + """ LEFT JOIN fms_actionmaster ON fms_stepaction.action_cd=fms_actionmaster.action_cd"""
            sql = sql + """ WHERE fms_stepaction.step_id=""" + str(step_id)
            sql = sql + """ ORDER BY fms_stepaction.display_order"""
            step_action_list = StepAction.objects.raw(sql)
        else:
            step_action_list = ""

        data_entry_step_list_num = DataEntryStepMaster.objects.filter(step_id=step_id).count()
        if data_entry_step_list_num > 0:
            data_entry_step_list = DataEntryStepMaster.objects.filter(step_id=step_id)
        else:
            data_entry_step_list = ""

        next_step_list_num = StepRelation.objects.filter(step_id=step_id).count()
        if next_step_list_num > 0:
            sql = """ SELECT fms_steprelation.*, fms_stepmaster.step_name"""
            sql = sql + """ FROM fms_steprelation"""
            sql = sql + """ LEFT JOIN fms_stepmaster ON fms_steprelation.next_step=fms_stepmaster.step_id"""
            sql = sql + """ WHERE fms_steprelation.step_id=""" + str(step_id)
            sql = sql + """ ORDER BY fms_steprelation.next_step"""
            next_step_list = StepRelation.objects.raw(sql)
        else:
            next_step_list = ""

        data = {
            'return_step_list_num': return_step_list_num,
            'return_step_list': return_step_list,
            'step_display_item_list_num': step_display_item_list_num,
            'step_display_item_list': step_display_item_list,
            'step_action_list_num': step_action_list_num,
            'step_action_list': step_action_list,
            'data_entry_step_list_num': data_entry_step_list_num,
            'data_entry_step_list': data_entry_step_list,
            'next_step_list_num': next_step_list_num,
            'next_step_list': next_step_list,
            'target_step_id': step_id,
            'target_step_name': step_name,
            'target_charge_department_class': target_charge_department_class,
            'target_step_level': target_step_level,
            'target_target': target_target,
            'target_new_entry_flag': target_new_entry_flag,
            'target_display_order': target_display_order,
            'target_lost_flag': target_lost_flag
        }

        return render(request, 'fms/parts/management/step_management.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済step_display_itemの一覧から選択し時の処理
@require_POST
def step_display_item_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['id'])

        # 対象の「step_id」で進捗マスタからレコード取得
        step_display_item_data = StepDisplayItem.objects.get(id=target_id)
        # 各項目を取得
        step_display_item_id = step_display_item_data.id
        step_display_item_step_id = step_display_item_data.step
        step_display_item_page = step_display_item_data.page
        step_display_item_div_id_name = step_display_item_data.div_id_name
        step_display_item_item_name = step_display_item_data.item_name
        step_display_item_action_pb_flag = step_display_item_data.action_pb_flag
        step_display_item_default_page = step_display_item_data.default_page
        step_display_item_lost_flag = step_display_item_data.lost_flag

        ary = {
            'step_display_item_id': step_display_item_id,
            'step_display_item_step_id': step_display_item_step_id,
            'step_display_item_page': step_display_item_page,
            'step_display_item_div_id_name': step_display_item_div_id_name,
            'step_display_item_item_name': step_display_item_item_name,
            'step_display_item_action_pb_flag': step_display_item_action_pb_flag,
            'step_display_item_default_page': step_display_item_default_page,
            'step_display_item_lost_flag': step_display_item_lost_flag
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済step_actionの一覧から選択し時の処理
@require_POST
def step_action_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['id'])

        # 対象の「step_id」で進捗マスタからレコード取得
        step_action_data = StepAction.objects.get(id=target_id)
        # 各項目を取得
        step_action_id = step_action_data.id
        step_action_action_cd = step_action_data.action_cd
        step_action_target = step_action_data.target
        step_action_display_order = step_action_data.display_order
        step_action_lost_flag = step_action_data.lost_flag
        action_data = ActionMaster.objects.get(action_cd=step_action_action_cd)
        step_action_action_name = action_data.action_name

        ary = {
            'step_action_id': step_action_id,
            'step_action_action_cd': step_action_action_cd,
            'step_action_target': step_action_target,
            'step_action_display_order': step_action_display_order,
            'step_action_lost_flag': step_action_lost_flag,
            'step_action_action_name': step_action_action_name
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済data_entry_stepの一覧から選択し時の処理
@require_POST
def data_entry_step_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['id'])

        # 対象の「step_id」で進捗マスタからレコード取得
        data_entry_step_data = DataEntryStepMaster.objects.get(id=target_id)
        # 各項目を取得
        data_entry_step_id = data_entry_step_data.id
        data_entry_step_target_table = data_entry_step_data.target_table
        data_entry_step_lost_flag = data_entry_step_data.lost_flag

        ary = {
            'data_entry_step_id': data_entry_step_id,
            'data_entry_step_target_table': data_entry_step_target_table,
            'data_entry_step_lost_flag': data_entry_step_lost_flag
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepmasterデータ登録処理
@require_POST
def step_data_entry(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        entry_type = int(request.POST['entry_type'])
        target_step_id = int(request.POST['target_step_id'])
        target_step_name = request.POST['target_step_name']
        target_charge_department_class = request.POST['target_charge_department_class']
        target_target = request.POST['target_target']
        target_step_level = int(request.POST['target_step_level'])
        target_new_entry_flag = int(request.POST['target_new_entry_flag'])
        target_display_order = int(request.POST['target_display_order'])
        target_lost_flag = int(request.POST['target_lost_flag'])

        if entry_type == 0:


            StepMaster(step_id=target_step_id).save()
            step_master_data = StepMaster.objects.get(step_id=target_step_id)
            msg = "新規登録実行！！"

        else:
            step_master_data = StepMaster.objects.get(step_id=target_step_id)
            msg = "更新実行！！"

        step_master_data.step_name = target_step_name
        step_master_data.charge_department_class = target_charge_department_class
        step_master_data.step_level = target_step_level
        step_master_data.lost_flag = target_lost_flag
        step_master_data.new_entry_flag = target_new_entry_flag
        step_master_data.target = target_target
        step_master_data.display_order = target_display_order
        step_master_data.template_class = target_target + "_base"
        step_master_data.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepmasterデータ削除処理
@require_POST
def step_data_delete(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_step_id = int(request.POST['target_step_id'])

        step_master_data = StepMaster.objects.get(step_id=target_step_id)
        step_master_data.lost_flag = 1
        step_master_data.save()

        msg = "削除(無効化)実行！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepdisplayitemデータ登録処理
@require_POST
def step_display_item_entry(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        entry_type = int(request.POST['entry_type'])
        target_id = int(request.POST['target_id'])
        target_step_id = int(request.POST['target_step_id'])
        page = int(request.POST['page'])
        div_id_name = request.POST['div_id_name']
        item_name = request.POST['item_name']
        action_pb_flag = int(request.POST['action_pb_flag'])
        default_page = int(request.POST['default_page'])
        lost_flag = int(request.POST['lost_flag'])

        if entry_type == 0:
            StepDisplayItem(step=target_step_id, div_id_name=div_id_name).save()
            step_display_item_data = StepDisplayItem.objects.get(step=target_step_id, div_id_name=div_id_name)
            msg = "新規登録実行！！"

        else:
            step_display_item_data = StepDisplayItem.objects.get(step=target_step_id, div_id_name=div_id_name)
            msg = "更新実行！！"

        step_display_item_data.step_name = page
        step_display_item_data.item_name = item_name
        step_display_item_data.action_pb_flag = action_pb_flag
        step_display_item_data.lost_flag = lost_flag
        step_display_item_data.default_page = default_page

        step_display_item_data.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepdisplayitemデータ削除処理
@require_POST
def step_display_item_delete(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])

        step_display_item_data = StepDisplayItem.objects.get(id=target_id)
        step_display_item_data.lost_flag = 1
        step_display_item_data.save()

        msg = "削除(無効化)実行！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepactionデータ登録処理
@require_POST
def step_action_entry(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        entry_type = int(request.POST['entry_type'])
        target_id = int(request.POST['target_id'])
        target_step_id = int(request.POST['target_step_id'])
        action_cd = request.POST['action_cd']
        target = request.POST['target']
        display_order = int(request.POST['display_order'])
        lost_flag = int(request.POST['lost_flag'])

        if entry_type == 0:
            StepAction(step_id=target_step_id, action_cd=action_cd).save()
            step_action_data = StepAction.objects.get(step_id=target_step_id, action_cd=action_cd)
            msg = "新規登録実行！！"

        else:
            step_action_data = StepAction.objects.get(step_id=target_step_id, action_cd=action_cd)
            msg = "更新実行！！"

        step_action_data.display_order = display_order
        step_action_data.target = target
        step_action_data.lost_flag = lost_flag

        step_action_data.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# stepactionデータ削除処理
@require_POST
def step_action_delete(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])

        step_action_data = StepAction.objects.get(id=target_id)
        step_action_data.lost_flag = 1
        step_action_data.save()

        msg = "削除(無効化)実行！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# dataentrystepmasterデータ登録処理
@require_POST
def data_entry_step_master_entry(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        entry_type = int(request.POST['entry_type'])
        target_id = int(request.POST['target_id'])
        target_step_id = int(request.POST['target_step_id'])
        target_table = request.POST['target_table']
        lost_flag = int(request.POST['lost_flag'])

        if entry_type == 0:
            DataEntryStepMaster(step_id=target_step_id, target_table=target_table).save()
            data_entry_step_master_data = DataEntryStepMaster.objects.get(step_id=target_step_id, target_table=target_table)
            msg = "新規登録実行！！"

        else:
            data_entry_step_master_data = DataEntryStepMaster.objects.get(step_id=target_step_id, target_table=target_table)
            msg = "更新実行！！"

        data_entry_step_master_data.lost_flag = lost_flag

        data_entry_step_master_data.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# dataentrystepmasterデータ削除処理
@require_POST
def data_entry_step_master_delete(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])

        data_entry_step_master_data = DataEntryStepMaster.objects.get(id=target_id)
        data_entry_step_master_data.lost_flag = 1
        data_entry_step_master_data.save()

        msg = "削除(無効化)実行！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise



# steprelationデータ登録処理
@require_POST
def step_relation_entry(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])
        target_step_id = int(request.POST['target_step_id'])
        next_step = int(request.POST['next_step'])
        lost_flag = int(request.POST['lost_flag'])
        display_order = int(request.POST['display_order'])


        if target_id == 0:
            StepRelation(step_id=target_step_id, next_step=next_step).save()
            step_relation_data = StepRelation.objects.get(step_id=target_step_id, next_step=next_step)
            msg = "新規登録実行！！"

        else:
            step_relation_data = StepRelation.objects.get(step_id=target_step_id, next_step=next_step)
            msg = "更新実行！！"

        step_relation_data.display_order = display_order
        step_relation_data.lost_flag = lost_flag

        step_relation_data.save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# steprelationデータ削除処理
@require_POST
def step_relation_delete(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])

        step_relation_data = StepRelation.objects.get(id=target_id)
        step_relation_data.lost_flag = 1
        step_relation_data.save()

        msg = "削除(無効化)実行！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

