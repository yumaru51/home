import datetime
import psycopg2
import psycopg2.extras
import traceback
from psycopg2.extras import DictCursor
from collections import namedtuple
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db import connections
from fms.models import RegulationMaster, SuppliesMaster
from fms.models import Supplies, WorkLaw, BudgetLaw, BudgetEquipment, WorkEquipment
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, Estimate, Discount, DataEntryStepMaster, Log
from fms.models import EquipmentFamilyMaster, Eqpt_Category, FCLTYCDMaster, EQPTBASICMST
from plantia.models import MasterMgtCls, MasterFncCtg, MasterLocation, FcltyLdgr
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 予算
# 法令、機器表示処理
@require_POST
def budget_law_equipment_data_info(request):
    try:
        present_step = int(request.POST["this_step"])

        # 法令マスタのうち、基本となる法令(=法令CDに「000」が含まれるもの)を抽出
        law_master_lists = RegulationMaster.objects.filter(regulation_cd__contains="000", lost_flag=0)
        law_master_lists_1 = RegulationMaster.objects.filter(regulation_cd__contains="000", lost_flag=0)[0:10]
        law_master_lists_2 = RegulationMaster.objects.filter(regulation_cd__contains="000", lost_flag=0)[10:20]
        law_master_lists_3 = RegulationMaster.objects.filter(regulation_cd__contains="000", lost_flag=0)[20:30]

        # 機器を絞込(抽出する)ための、機器ファミリマスタデータと設備コードマスタデータを抽出
        # equip_family_lists = EqptFmlyMst.objects.all()
        # equip_family_lists = MasterFncCtg.objects.all()
        # equip_type_lists = EqptCategory.objects.all()
        # facility_lists = FcltyCd.objects.all()
        equip_family_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey=None, deleted_flg=0)
        equip_type_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey__isnull=False, deleted_flg=0)
        management_class_lists = MasterMgtCls.objects.all()
        facility_lists = MasterLocation.objects.filter(parent_m_location_skey=None, deleted_flg=0)
        fclty_cd_lists = MasterLocation.objects.filter(parent_m_location_skey__isnull=False, deleted_flg=0)

        data = {
            'management_class_lists': management_class_lists,
            'law_master_lists': law_master_lists,
            'equip_family_lists': equip_family_lists,
            'equip_type_lists': equip_type_lists,
            'facility_lists': facility_lists,
            'fclty_cd_lists': fclty_cd_lists,
            'law_master_lists_1': law_master_lists_1,
            'law_master_lists_2': law_master_lists_2,
            'law_master_lists_3': law_master_lists_3,
        }
        # データ編集機能要否判定
        budget_law_equipment_edit_action_num = 0
        # 対象stepで「budget_law」がデータ更新対象か確認
        budget_law_equipment_edit_action_num = budget_law_equipment_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='budget_law').count()
        # 対象stepで「budget_equipment」がデータ更新対象か確認
        budget_law_equipment_edit_action_num = budget_law_equipment_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='budget_equipment').count()

        edit_flag = 0
        if budget_law_equipment_edit_action_num > 0:
            edit_flag = 1
        if edit_flag == 1:
            return render(request, 'fms/parts/budget/law_equipment/law_equipment_edit.html', data)
        else:
            return render(request, 'fms/parts/budget/law_equipment/law_equipment_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の法令一覧表示
@require_POST
def get_budget_law_list(request):
    try:
        budget_id_str = request.POST["budget_id"]
        if budget_id_str != "":
            budget_id = int(request.POST["budget_id"])
        else:
            budget_id = 0
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])

        budget_law_lists_num = BudgetLaw.objects.filter(budget_id=budget_id, lost_flag=0).count()

        if budget_law_lists_num > 0:
            budget_law_lists = BudgetLaw.objects.filter(budget_id=budget_id, lost_flag=0).all()
        else:
            budget_law_lists = ""

        data = {
            'budget_law_lists_num': budget_law_lists_num,
            'budget_law_lists': budget_law_lists,
            'select_pb_disp_flag': select_pb_disp_flag
        }
        return render(request, 'fms/parts/budget/law_equipment/budget_law_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の機器一覧表示
@require_POST
def get_budget_equipment_list(request):
    try:
        budget_id_str = request.POST["budget_id"]
        if budget_id_str != "":
            budget_id = int(request.POST["budget_id"])
        else:
            budget_id = 0
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])

        budget_equipment_lists = BudgetEquipment.objects.filter(budget_id=budget_id, lost_flag=0)
        budget_equipment_lists_num = budget_equipment_lists.__len__()
        # eqptfmlymst_list = EqptFmlyMst.objects.all()
        # eqptcategory_list = EqptCategory.objects.all()

        eqptfmlymst_list = []
        first_loop_flag = 1
        for budget_equipment_item in budget_equipment_lists:
            if budget_equipment_item.management_class is not None:
                budget_equipment_item.management_class = budget_equipment_item.management_class.lower()
            else:
                budget_equipment_item.management_class = ""

            if budget_equipment_item.equip_family is not None and budget_equipment_item.equip_type is not None:
                if budget_equipment_item.equip_family in budget_equipment_item.equip_type:
                    budget_equipment_item.equip_type = budget_equipment_item.equip_type
                else:
                    # 旧型式で保存された機器のファミリ、タイプの表示に対応（equip_family:'PI',equip_type'999'->'pi','pi999'）
                    budget_equipment_item.equip_family = budget_equipment_item.equip_family.lower()
                    budget_equipment_item.equip_type = budget_equipment_item.equip_family + budget_equipment_item.equip_type.lower()
            else:
                budget_equipment_item.equip_type = ""
                budget_equipment_item.equip_family = ""

            if budget_equipment_item.facility is None:
                budget_equipment_item.facility = ""

            filter_data_ary = {
                'mgt_cls': budget_equipment_item.management_class,
                'location_cd': budget_equipment_item.facility,
                'family_cd': budget_equipment_item.equip_family,
                'type_cd': budget_equipment_item.equip_type,
                'eqpt_id': budget_equipment_item.equip_no,
            }

            if first_loop_flag == 1:
                eqptfmlymst_list = get_all_equip_family_type_filtered_lists_data(filter_data_ary)
                first_loop_flag = 0
            else:
                eqptfmlymst_list += get_all_equip_family_type_filtered_lists_data(filter_data_ary)

        data = {
            'budget_equipment_lists': budget_equipment_lists,
            'budget_equipment_lists_num': budget_equipment_lists_num,
            'eqptfmlymst_list': eqptfmlymst_list,
            # 'eqptcategory_list': eqptcategory_list,
            'select_pb_disp_flag': select_pb_disp_flag
        }
        return render(request, 'fms/parts/budget/law_equipment/budget_equipment_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 法令を登録･更新処理
@login_required
@require_POST
def budget_law_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        action_type = request.POST["action_type"]
        budget_id = int(request.POST["budget_id"])
        rev_no = int(request.POST["rev_no"])
        # budget_law_id = int(request.POST["budget_law_id"])
        budget_law_name = request.POST["budget_law_name"]
        # display_order = int(request.POST["display_order"])
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # if this_step < 200000000:
            # entry_class = "計画"
        # else:
            # entry_class = "実行"

        # 予算ID、rev_no、法令名で該当レコードがあれば更新、なければ新規登録
        budget_law_data, created = BudgetLaw.objects.get_or_create(budget_id=budget_id, rev_no=rev_no,
                                                                   law_name=budget_law_name)
        # 各項目の値を設定
        budget_law_data.budget_id = budget_id
        budget_law_data.rev_no = rev_no
        # budget_law_data.entry_class = entry_class
        budget_law_data.lost_flag = 0
        budget_law_data.entry_on_progress_flag = 1
        # 新規登録時の処理
        if action_type == "add":
            budget_law_data.entry_datetime = now
            budget_law_data.entry_operator = operator
            msg = "適用法規データ新規登録完了！！"
        # 更新時の処理
        else:
            budget_law_data.update_datetime = now
            budget_law_data.update_operator = operator
            msg = "適用法規データ更新完了！！"

        # レコードを保存
        budget_law_data.save()
        budget_law_id = budget_law_data.id

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、Rev: " + str(rev_no) + "、適用法規名 : " + budget_law_name + ""

        # ログデータを新規登録
        Log(target='budgetlaw', target_id=budget_law_id, action=action_type, operator=operator, operation_datetime=now,
            step=this_step, comment=comment, operator_department=this_department, operator_division=this_division,
            budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器を登録･更新処理
@login_required
@require_POST
def budget_equipment_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username
        action_type = request.POST["action_type"]
        budget_id = int(request.POST["budget_id"])
        rev_no = int(request.POST["rev_no"])
        # budget_equipment_id = int(request.POST["budget_equipment_id"])
        equipment_no = request.POST["equipment_no"]
        equipment_name = request.POST["equipment_name"]
        management_class = request.POST["management_class"]
        equip_family = request.POST["equip_family"]
        equipment_type = None if request.POST["equipment_type"] == '' else request.POST["equipment_type"]
        facility = request.POST["facility"]
        # display_order = int(request.POST["display_order"])
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # if this_step < 200000000:
            # entry_class = "計画"
        # else:
            # entry_class = "実行"

        # 予算ID、rev_no、機器NOで該当レコードがあれば更新、なければ新規登録
        budget_equipment_data, created = BudgetEquipment.objects.get_or_create(budget_id=budget_id,
                                                                               equip_type=equipment_type, rev_no=rev_no,
                                                                               equip_no=equipment_no)
        # 各項目の値を設定
        budget_equipment_data.equip_name = equipment_name
        budget_equipment_data.management_class = management_class
        budget_equipment_data.equip_family = equip_family
        budget_equipment_data.facility = facility
        # budget_equipment_data.entry_class = entry_class
        budget_equipment_data.lost_flag = 0
        budget_equipment_data.entry_on_progress_flag = 1
        # 新規登録時の処理
        if action_type == "add":
            budget_equipment_data.entry_datetime = now
            budget_equipment_data.entry_operator = operator
            msg = "関連機器データ新規登録完了！！"
        # 更新時の処理
        else:
            budget_equipment_data.update_datetime = now
            budget_equipment_data.update_operator = operator
            msg = "関連機器データ更新完了！！"

        # レコードを保存
        budget_equipment_data.save()
        budget_equipment_id = budget_equipment_data.id

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、Rev: " + str(rev_no) + "、関連機器名 : " + equipment_no + ""

        # ログデータを新規登録
        Log(target='budgetequipment', target_id=budget_equipment_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済み法令リスト選択時のフォーム反映処理
@require_POST
def budget_law_detail(request):
    try:
        budget_law_id = int(request.POST["budget_law_id"])
        budget_law_data = BudgetLaw.objects.get(id=budget_law_id, lost_flag=0)
        budget_law_name = budget_law_data.law_name
        budget_law_id = budget_law_data.id

        data = {
            'budget_law_name': budget_law_name,
            'budget_law_id': budget_law_id
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済み機器リスト選択時のフォーム反映処理
@require_POST
def budget_equipment_detail(request):
    try:
        budget_equipment_id = int(request.POST["budget_equipment_id"])

        sql = """
                SELECT A.*,
                       IsNull(B.equipment_family_name, '') as equipment_family_name,
                       IsNull(C.eqpt_cat_nm, '') as eqpt_cat_nm
                FROM fms_budgetequipment AS A
                LEFT JOIN fms_equipmentfamilymaster AS B
                  ON A.management_class = B.management_class AND
                     A.equip_family = B.equipment_family_cd
                LEFT JOIN fms_eqpt_category AS C
                  ON A.management_class = C.mgt_cls AND
                     B.equipment_family_cd = C.eqpt_family AND
                     A.equip_type = C.eqpt_tp
                WHERE A.id = %s AND
                      A.lost_flag = 0 """

        budget_equipment_data = BudgetEquipment.objects.raw(sql, [budget_equipment_id])
        equip_no = budget_equipment_data[0].equip_no
        equip_name = budget_equipment_data[0].equip_name
        management_class = budget_equipment_data[0].management_class
        facility = budget_equipment_data[0].facility
        equip_family_nm = budget_equipment_data[0].equipment_family_name
        equip_type_nm = budget_equipment_data[0].eqpt_cat_nm

        data = {
            'equipment_no': equip_no,
            'equipment_name': equip_name,
            'management_class': management_class,
            'equip_family': equip_family_nm,
            'equip_type': equip_type_nm,
            'facility': facility,
            'budget_equipment_id': budget_equipment_id
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 法令を削除処理
@login_required
@require_POST
def budget_law_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        rev_no = int(request.POST["rev_no"])
        budget_law_id = int(request.POST["budget_law_id"])
        budget_law_name = request.POST["budget_law_name"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 対象のレコードを抽出
        budget_law_data = BudgetLaw.objects.get(id=budget_law_id)
        # 無効FL=「0」
        budget_law_data.lost_flag = 1
        # レコードを保存
        budget_law_data.save()

        msg = "関連法規データ削除完了！！"
        action_type = "delete"

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、Rev: " + str(rev_no) + "、適用法規名 : " + budget_law_name + ""

        # ログデータを新規登録
        Log(target='budgetlaw', target_id=budget_law_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器を削除処理
@login_required
@require_POST
def budget_equipment_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        rev_no = int(request.POST["rev_no"])
        budget_equipment_id = int(request.POST["budget_equipment_id"])
        budget_equipment_no = request.POST["budget_equipment_no"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 対象のレコードを抽出
        budget_equipment_data = BudgetEquipment.objects.get(id=budget_equipment_id, lost_flag=0)
        # 無効FL=「0」
        budget_equipment_data.lost_flag = 1
        # レコードを保存
        budget_equipment_data.save()
        # document_data.entry_on_progress_flag = 1

        msg = "関連機器データ削除完了！！"
        action_type = "delete"

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、Rev: " + str(rev_no) + "、関係機器NO : " + budget_equipment_no + ""

        # ログデータを新規登録
        Log(target='budgetequipment', target_id=budget_equipment_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 工事
# 機器表示処理
@require_POST
def work_equipment_data_info(request):
    try:
        present_step = int(request.POST["this_step"])
        level5_step_id = int(request.POST["level5_step_id"])
        # 機器を絞込(抽出する)ための、機器ファミリマスタデータと設備コードマスタデータを抽出
        # equip_family_lists = EqptFmlyMst.objects.all()
        # equip_type_lists = EqptCategory.objects.all()
        # facility_lists = FcltyCd.objects.all()
        management_class_lists = MasterMgtCls.objects.all()
        equip_family_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey=None, deleted_flg=0)
        equip_type_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey__isnull=False, deleted_flg=0)
        facility_lists = MasterLocation.objects.filter(parent_m_location_skey=None, deleted_flg=0)
        fclty_cd_lists = MasterLocation.objects.filter(parent_m_location_skey__isnull=False, deleted_flg=0)

        # データ編集機能要否判定
        # 対象stepで「budget_equipment」がデータ更新対象か確認
        budget_law_equipment_edit_action_num = DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                  target_table='work_equipment',
                                                                                  lost_flag=0).count()

        if level5_step_id == 920000000:
            budget_law_equipment_edit_action_num = 0

        data = {
            'management_class_lists': management_class_lists,
            'equip_family_lists': equip_family_lists,
            'equip_type_lists': equip_type_lists,
            'facility_lists': facility_lists,
            'fclty_cd_lists': fclty_cd_lists,
        }
        edit_flag = 0
        if budget_law_equipment_edit_action_num > 0:
            edit_flag = 1
        if edit_flag == 1:
            return render(request, 'fms/parts/budget/law_equipment/equipment_edit.html', data)
        else:
            return render(request, 'fms/parts/budget/law_equipment/equipment_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済の機器一覧を表示
@require_POST
def get_work_equipment_list(request):
    try:
        budget_id_str = request.POST["budget_id"]
        if budget_id_str != "":
            budget_id = int(request.POST["budget_id"])
        else:
            budget_id = 0
        work_id_str = request.POST["work_id"]
        if work_id_str != "":
            work_id = int(request.POST["work_id"])
        else:
            work_id = 0
        select_pb_disp_flag = int(request.POST["select_pb_disp_flag"])

        work_equipment_lists = WorkEquipment.objects.filter(budget_id=budget_id, work_id=work_id, lost_flag=0)
        work_equipment_lists_num = work_equipment_lists.__len__()

        eqptfmlymst_list = []
        first_loop_flag = 1
        for work_equipment_item in work_equipment_lists:
            if work_equipment_item.management_class is not None:
                work_equipment_item.management_class = work_equipment_item.management_class.lower()
            else:
                work_equipment_item.management_class = ""

            if work_equipment_item.equip_family is not None and work_equipment_item.equip_type is not None:
                if work_equipment_item.equip_family in work_equipment_item.equip_type:
                    work_equipment_item.equip_type = work_equipment_item.equip_type
                else:
                    # 旧型式で保存された機器のファミリ、タイプの表示に対応（equip_family:'PI',equip_type'999'->'pi','pi999'）
                    work_equipment_item.equip_family = work_equipment_item.equip_family.lower()
                    work_equipment_item.equip_type = work_equipment_item.equip_family + work_equipment_item.equip_type.lower()

            else:
                work_equipment_item.equip_type = ""
                work_equipment_item.equip_family = ""

            if work_equipment_item.facility is None:
                work_equipment_item.facility = ""

            filter_data_ary = {
                'mgt_cls': work_equipment_item.management_class,
                'location_cd': work_equipment_item.facility,
                'family_cd': work_equipment_item.equip_family,
                'type_cd': work_equipment_item.equip_type,
                'eqpt_id': work_equipment_item.equip_no,
            }

            if first_loop_flag == 1:
                eqptfmlymst_list = get_all_equip_family_type_filtered_lists_data(filter_data_ary)
                first_loop_flag = 0
            else:
                eqptfmlymst_list += get_all_equip_family_type_filtered_lists_data(filter_data_ary)

        data = {
            'work_equipment_lists': work_equipment_lists,
            'work_equipment_lists_num': work_equipment_lists_num,
            'eqptfmlymst_list': eqptfmlymst_list,
            'select_pb_disp_flag': select_pb_disp_flag
        }
        return render(request, 'fms/parts/budget/law_equipment/work_equipment_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器を登録･更新処理
@login_required
@require_POST
def work_equipment_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        action_type = request.POST["action_type"]
        budget_id = int(request.POST["budget_id"])
        work_id = int(request.POST["work_id"])
        rev_no = int(request.POST["rev_no"])
        # work_equipment_id = int(request.POST["work_equipment_id"])
        equipment_no = request.POST["equipment_no"]
        equipment_name = request.POST["equipment_name"]
        management_class = request.POST["management_class"]
        equip_family = request.POST["equip_family"]
        equipment_type = request.POST["equipment_type"]
        equipment_purchase = 1 if request.POST["equipment_purchase"] == 'true' else 0
        construction = 1 if request.POST["construction"] == 'true' else 0
        facility = request.POST["facility"]
        # display_order = int(request.POST["display_order"])
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # if this_step < 200000000:
            # entry_class = "計画"
        # else:
            # entry_class = "実行"

        # 予算ID、rev_no、機器NOで該当レコードがあれば更新、なければ新規登録
        work_equipment_data, created = WorkEquipment.objects.get_or_create(budget_id=budget_id, work_id=work_id,
                                                                           equip_type=equipment_type, rev_no=rev_no,
                                                                           equip_no=equipment_no)
        # 各項目の値を設定
        work_equipment_data.equip_name = equipment_name
        work_equipment_data.management_class = management_class
        work_equipment_data.equip_family = equip_family
        work_equipment_data.facility = facility
        work_equipment_data.equipment_purchase = equipment_purchase
        work_equipment_data.construction = construction
        # work_equipment_data.entry_class = entry_class
        work_equipment_data.lost_flag = 0
        work_equipment_data.entry_on_progress_flag = 1
        # 新規登録時の処理
        if action_type == "add":
            work_equipment_data.entry_datetime = now
            work_equipment_data.entry_operator = operator
            msg = "関連機器データ新規登録完了！！"
        # 更新時の処理
        else:
            work_equipment_data.update_datetime = now
            work_equipment_data.update_operator = operator
            msg = "関連機器データ更新完了！！"

        # レコードを保存
        work_equipment_data.save()
        work_equipment_id = work_equipment_data.id

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、work_id : " + str(work_id) +"、Rev: " + str(rev_no) + "、関連機器名 : " + equipment_no + ""

        # ログデータを新規登録
        Log(target='workequipment', target_id=work_equipment_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 選択した機器の表示処理
@require_POST
def work_equipment_detail(request):
    try:
        work_equipment_id = int(request.POST["work_equipment_id"])

        sql = """
                SELECT A.*, B.equipment_family_name, C.eqpt_cat_nm
                FROM fms_workequipment AS A
                LEFT JOIN fms_equipmentfamilymaster AS B
                  ON A.management_class = B.management_class AND
                     A.equip_family = B.equipment_family_cd
                LEFT JOIN fms_eqpt_category AS C
                  ON A.management_class = C.mgt_cls AND
                     B.equipment_family_cd = C.eqpt_family AND
                     A.equip_type = C.eqpt_tp
                WHERE A.id = %s AND
                      A.lost_flag = 0 """
        work_equipment_data = WorkEquipment.objects.raw(sql, [work_equipment_id])
        equip_no = work_equipment_data[0].equip_no
        equip_name = work_equipment_data[0].equip_name
        management_class = work_equipment_data[0].management_class
        facility = work_equipment_data[0].facility
        equipment_purchase = work_equipment_data[0].equipment_purchase
        construction = work_equipment_data[0].construction
        equip_family_nm = work_equipment_data[0].equipment_family_name
        equip_type_nm = work_equipment_data[0].eqpt_cat_nm

        data = {
            'equipment_no': equip_no,
            'equipment_name': equip_name,
            'management_class': management_class,
            'equipment_purchase': equipment_purchase,
            'construction': construction,
            'equip_family': equip_family_nm,
            'equip_type': equip_type_nm,
            'facility': facility,
            'work_equipment_id': work_equipment_id
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 選択した機器の表示処理
@require_POST
def work_equipment_detail_info(request):
    try:
        work_equipment_id = int(request.POST["work_equipment_id"])

        sql = """
                SELECT A.*,
                      CASE
                        WHEN A.equipment_purchase = 1 AND A.construction = 1 THEN '機器購入・工事'
                        WHEN A.equipment_purchase = 1 AND A.construction = 0 THEN '機器購入'
                        WHEN A.equipment_purchase = 0 AND A.construction = 1 THEN '工事'
                        ELSE ''
                      END purchase, 
                 B.equipment_family_name, C.eqpt_cat_nm
                FROM fms_workequipment AS A
                LEFT JOIN fms_equipmentfamilymaster AS B
                  ON A.management_class = B.management_class AND
                     A.equip_family = B.equipment_family_cd
                LEFT JOIN fms_eqpt_category AS C
                  ON A.management_class = C.mgt_cls AND
                     B.equipment_family_cd = C.eqpt_family AND
                     A.equip_type = C.eqpt_tp
                WHERE A.id = %s AND
                      A.lost_flag = 0 """
        work_equipment_data = WorkEquipment.objects.raw(sql, [work_equipment_id])
        equip_no = work_equipment_data[0].equip_no
        equip_name = work_equipment_data[0].equip_name
        management_class = work_equipment_data[0].management_class
        facility = work_equipment_data[0].facility
        equipment_purchase = work_equipment_data[0].equipment_purchase
        construction = work_equipment_data[0].construction
        purchase = work_equipment_data[0].purchase
        equip_family_nm = work_equipment_data[0].equipment_family_name
        equip_type_nm = work_equipment_data[0].eqpt_cat_nm

        data = {
            'equipment_no': equip_no,
            'equipment_name': equip_name,
            'management_class': management_class,
            'equipment_purchase': equipment_purchase,
            'construction': construction,
            'purchase': purchase,
            'equip_family': equip_family_nm,
            'equip_type': equip_type_nm,
            'facility': facility,
            'work_equipment_id': work_equipment_id
        }
        return render(request, 'fms/parts/budget/law_equipment/equipment_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器を削除処理
@login_required
@require_POST
def work_equipment_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)
        operator = request.user.username
        budget_id = int(request.POST["budget_id"])
        work_id = int(request.POST["work_id"])
        rev_no = int(request.POST["rev_no"])
        work_equipment_id = int(request.POST["work_equipment_id"])
        budget_equipment_no = request.POST["budget_equipment_no"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 対象のレコードを抽出
        budget_equipment_data = WorkEquipment.objects.get(id=work_equipment_id, lost_flag=0)
        # 無効FL=「0」
        budget_equipment_data.lost_flag = 1
        # レコードを保存
        budget_equipment_data.save()
        # document_data.entry_on_progress_flag = 1

        msg = "関連機器データ削除完了！！"
        action_type = "delete"

        # ログのコメント内容を作成
        comment = "budget_id : " + str(budget_id) + "、work_id : " + str(work_id) + "、Rev: " + str(rev_no) + "、関係機器NO : " + budget_equipment_no + ""

        # ログデータを新規登録
        Log(target='workequipment', target_id=work_equipment_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 共通
# 機器一覧表示
@require_POST
def get_equipment_list(request):
    try:
        management_class = request.POST["management_class"]
        equip_family = request.POST["equip_family"]
        # equip_type = request.POST["equip_type"]
        facility = request.POST["facility"]

        # where_str = ""
        # where_parm = []
        #
        # if management_class != "":
        #     where_str += " AND A.MGT_CLS = %s"
        #     where_parm.append(management_class)
        # if equip_family != "":
        #     where_str += " AND A.EQPT_FMLY = %s"
        #     where_parm.append(equip_family)
        # if equip_type != "":
        #     where_str += " AND A.EQPT_TP = %s"
        #     where_parm.append(equip_type)
        # if facility != "":
        #     where_str += " AND A.FCLTY_CD = %s"
        #     where_parm.append(facility)
        #
        # sql = 'SELECT * FROM EQPT_BASIC_MST A \
        # LEFT JOIN EQPT_FMLY_MST B ON A.MGT_CLS = B.MGT_CLS AND A.EQPT_FMLY = B.EQPT_FMLY \
        # LEFT JOIN EQPT_CATEGORY C ON A.MGT_CLS = C.MGT_CLS AND A.EQPT_FMLY = C.EQPT_FMLY WHERE 1 = 1'
        #
        # if where_str != "":
        #     sql += where_str + ' ORDER BY A.FCLTY_CD'
        # else:
        #     sql += ' ORDER BY A.FCLTY_CD'
        #
        # # equipment_list = EqptBasicMst.objects.raw(sql, where_parm)

        filter_data_ary = {
            'mgt_cls': management_class,
            'location_cd': facility,
            'family_cd': equip_family,
            'type_cd': "",
            'eqpt_id': "",
        }
        equipment_list = get_all_equip_family_type_filtered_lists_data(filter_data_ary)

        data = {
            'equipment_list': equipment_list,
            'filtered_equipment_list_num': len(equipment_list),
        }
        return render(request, 'fms/parts/select/equipment_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 共通
# 機器一覧表示リセット
@require_POST
def reset_equipment_list(request):
    try:
        equipment_list = []

        data = {
            'equipment_list': equipment_list,
            'filtered_equipment_list_num': len(equipment_list),
        }
        return render(request, 'fms/parts/select/equipment_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 法令リスト選択時のフォーム反映処理
@require_POST
def select_budget_law(request):
    try:
        budget_law_master_id = request.POST["budget_law_cd"]
        regulation_master_data = RegulationMaster.objects.get(regulation_cd=budget_law_master_id, lost_flag=0)
        regulation_name = regulation_master_data.regulation_name
        regulation_cd = regulation_master_data.regulation_cd
        display_order = regulation_master_data.display_order
        budget_law_id = 0

        data = {
            'regulation_name': regulation_name,
            'regulation_cd': regulation_cd,
            'display_order': display_order,
            'budget_law_id': budget_law_id
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器リスト選択時のフォーム反映処理
@require_POST
def select_budget_equipment(request):
    try:
        equipment_id = request.POST["equipment_id"]
        equipment_type = request.POST["equipment_type"]
        sql = """
            select
                A.id
              , A.MGT_CLS
              , A.FCLTY_CD
              , A.EQPT_ID
              , A.EQPT_NM
              , A.EQPT_FMLY
              , B.id
              , B.equipment_family_name
              , C.id
              , C.eqpt_tp
              , C.eqpt_cat_nm
            from fms_eqptbasicmst as A
            left join fms_equipmentfamilymaster as B
                on A.MGT_CLS = B.management_class and
                   A.EQPT_FMLY = B.equipment_family_cd and
                   B.lost_flag = 0
            left join fms_eqpt_category as C
                on A.MGT_CLS = C.mgt_cls and
                   A.EQPT_FMLY = C.eqpt_family
            where
                A.id = %s and
                C.eqpt_tp = %s and
                A.lost_flag = 0 """
        # equipment_data = EQPTBASICMST.objects.raw(sql, (equipment_id, equipment_type))
        equipment_data = FcltyLdgr.objects.raw(sql, (equipment_id, equipment_type))
        equipment_no = equipment_data[0].EQPT_ID
        equipment_name = equipment_data[0].EQPT_NM
        management_class = equipment_data[0].MGT_CLS
        equip_family = equipment_data[0].EQPT_FMLY
        equip_family_nm = equipment_data[0].equipment_family_name
        equip_type_nm = equipment_data[0].eqpt_cat_nm
        facility = equipment_data[0].FCLTY_CD

        data = {
            'equipment_id': equipment_id,
            'equipment_no': equipment_no,
            'equipment_name': equipment_name,
            'management_class': management_class,
            'equip_family': equip_family,
            'equip_family_nm': equip_family_nm,
            'equip_type_nm': equip_type_nm,
            'facility': facility,
        }
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器ファミリ表示の処理
@require_POST
def filter_equip_family(request):
    try:
        management_class = request.POST["management_class"]

        # 区分未選択時の処理
        if management_class == '':
            # equip_family_lists = EqptFmlyMst.objects.all()
            equip_family_lists = MasterFncCtg.objects.filter(m_site_skey=2, parent_m_fnc_ctg_skey=None, deleted_flg=0)
        # 区分選択時の処理
        else:
            # equip_family_lists = EqptFmlyMst.objects.filter(MGT_CLS=management_class)
            mgt_cls_data = MasterMgtCls.objects.get(mgt_cls=management_class.lower(), deleted_flg=0)
            equip_family_lists = MasterFncCtg.objects.filter(m_site_skey=2,
                                                             m_mgt_cls_skey=mgt_cls_data.m_mgt_cls_skey,
                                                             parent_m_fnc_ctg_skey=None,
                                                             deleted_flg=0)

        data = {
            'equip_family_lists': equip_family_lists
        }
        return render(request, 'fms/parts/select/select_equip_family.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器タイプ表示の処理
@require_POST
def filter_equip_type(request):
    try:
        management_class = request.POST["management_class"]
        equip_family = request.POST["equip_family"]
        filter_mgt_cls = ""
        filter_family_cd = ""

        # 区分未選択時の処理
        if management_class == '':
            # # ファミリ未選択時の処理
            if equip_family == '':
                # equip_type_lists = EqptCategory.objects.all()
                equip_type_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey__isnull=False, deleted_flg=0)
            # ファミリ選択時の処理
            else:  # equip_family != '':
                # equip_type_lists = EqptCategory.objects.filter(EQPT_FMLY=equip_family)
                equip_family_skey = MasterFncCtg.objects.filter(fnc_ctg_cd=equip_family, deleted_flg=0).m_fnc_ctg_skey
                equip_type_lists = MasterFncCtg.objects.filter(parent_m_fnc_ctg_skey__isnull=equip_family_skey,
                                                               deleted_flg=0)
                # filter_family_cd = equip_family
        # 区分選択時の処理
        else:
            # ファミリ未選択時の処理
            if equip_family == '':
                # equip_type_lists = EqptCategory.objects.filter(MGT_CLS=management_class)
                management_class_skey = MasterMgtCls.objects.get(mgt_cls=management_class.lower(),
                                                                 deleted_flg=0).m_mgt_cls_skey
                equip_type_lists = MasterFncCtg.objects.filter(m_mgt_cls_skey=management_class_skey,
                                                               deleted_flg=0)
                # filter_mgt_cls = management_class.lower()
            # ファミリ選択時の処理
            else:
                # equip_type_lists = EqptCategory.objects.filter(MGT_CLS=management_class, EQPT_FMLY=equip_family)
                management_class_skey = MasterMgtCls.objects.get(mgt_cls=management_class.lower(),
                                                                 deleted_flg=0).m_mgt_cls_skey
                equip_family_skey = MasterFncCtg.objects.filter(m_mgt_cls_skey=management_class_skey,
                                                                fnc_ctg_cd=equip_family, deleted_flg=0).m_fnc_ctg_skey
                equip_type_lists = MasterFncCtg.objects.filter(m_mgt_cls_skey=management_class_skey,
                                                               parent_m_fnc_ctg_skey__isnull=equip_family_skey,
                                                               deleted_flg=0)
                # filter_mgt_cls = management_class.lower()
                # filter_family_cd = equip_family

        # filter_data_ary = {
        #     'mgt_cls': filter_mgt_cls,
        #     'location_cd': "",
        #     'family_cd': filter_family_cd,
        #     'type_cd': "",
        #     'eqpt_id': "",
        # }
        # equip_family_lists = get_all_equip_family_type_filtered_lists_data(filter_data_ary)

        data = {
            'equip_type_lists': equip_type_lists
            # 'equip_family_lists': equip_family_lists
        }
        return render(request, 'fms/parts/select/select_equip_type.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 機器タイプ表示の処理
@require_POST
def filter_facility_code(request):
    try:
        facility_class_code_skey = request.POST["facility_class_code_skey"]

        if facility_class_code_skey == "":
            facility_code_lists = MasterLocation.objects.filter(m_site_skey=2,
                                                                parent_m_location_skey__isnull=False,
                                                                deleted_flg=0)
        else:
            facility_code_lists = MasterLocation.objects.filter(m_site_skey=2,
                                                                parent_m_location_skey=facility_class_code_skey,
                                                                deleted_flg=0)

        data = {
            'facility_code_lists': facility_code_lists
        }
        return render(request, 'fms/parts/select/select_facility_code.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


def namedtuplefetchall(cursor):
    # Return all rows from a cursor as a namedtuple
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])

    return [nt_result(*row) for row in cursor.fetchall()]


# ポストグレスSQLから機器ファミリと機器タイプのデータを取得
def get_all_equip_family_type_filtered_lists_data(filter_data_ary):
    conn = connections['plantiav05']
    conn.ensure_connection()
    # with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
    with conn.cursor() as cursor:
        sql = """ SELECT t_fclty_ldgr_skey, """                     # 設備台帳_サロゲートキー
        # sql += """ t_fclty_ldgr.m_site_skey, """                    # 拠点_サロゲートキー
        # sql += """ t_fclty_ldgr.m_mgt_cls_skey, """                 # 管理区分マスタ_サロゲートキー
        # sql += """ t_fclty_ldgr.m_location_skey, """                # ロケーション_サロゲートキー
        sql += """ t_fclty_ldgr.eqpt_id, """                        # 機番
        # sql += """ t_fclty_ldgr.fclty_dstnct_id, """                # 設備_識別_ID
        # sql += """ t_fclty_ldgr.parent_t_fclty_ldgr_skey, """       # 参照先_設備台帳_サロゲートキー
        # sql += """ t_fclty_ldgr.m_fclty_ctg_skey, """               # 設備種別_サロゲートキー
        # sql += """ t_fclty_ldgr.m_fnc_ctg_1_skey, """               # 機能分類_1_サロゲートキー(EQPT_FMLY)
        # sql += """ t_fclty_ldgr.m_fnc_ctg_2_skey, """               # 機能分類_2_サロゲートキー(EQPT_TP)
        sql += """ t_fclty_ldgr.fclty_nm, """                       # 設備_名称
        sql += """ m_mgt_cls.mgt_cls, """                           # 管理_区分
        sql += """ m_mgt_cls.mgt_cls_nm_1, """                      # 管理_区分_名称_1
        sql += """ m_location.location_cd, """                      # ロケーション_コード
        sql += """ m_location.location_nm_1, """                    # ロケーション_名称_1
        sql += """ family_table.fnc_ctg_cd as family_cd, """        # 機能_分類_コード(EQPT_FMLY)
        sql += """ family_table.fnc_ctg_nm_1 as family_nm, """      # 機能_分類_名称_1(EQPT_FMLY)
        sql += """ type_table.fnc_ctg_cd as type_cd, """            # 機能_分類_コード(EQPT_TP)
        sql += """ type_table.fnc_ctg_nm_1 as type_nm """           # 機能_分類_名称_1(EQPT_TP)

        sql += """ FROM t_fclty_ldgr """
        sql += """ LEFT JOIN m_mgt_cls on t_fclty_ldgr.m_mgt_cls_skey = m_mgt_cls.m_mgt_cls_skey """
        sql += """ AND m_mgt_cls.deleted_flg=0 """
        sql += """ LEFT JOIN m_location on t_fclty_ldgr.m_location_skey = m_location.m_location_skey """
        sql += """ AND m_location.deleted_flg=0 """
        sql += """ LEFT JOIN m_fnc_ctg as family_table on t_fclty_ldgr.m_fnc_ctg_1_skey = family_table.m_fnc_ctg_skey """
        sql += """ AND family_table.deleted_flg=0 """
        sql += """ LEFT JOIN m_fnc_ctg as type_table on t_fclty_ldgr.m_fnc_ctg_2_skey = type_table.m_fnc_ctg_skey """
        sql += """ AND type_table.deleted_flg=0 """
        sql += """ WHERE t_fclty_ldgr.deleted_flg=0"""
        sql += """ AND t_fclty_ldgr.m_site_skey=2 """

        if filter_data_ary['mgt_cls'] != "":
            sql += """AND m_mgt_cls.mgt_cls='""" + filter_data_ary['mgt_cls'] + """'"""

        if filter_data_ary['location_cd'] != "":
            sql += """AND m_location.location_cd='""" + filter_data_ary['location_cd'] + """'"""

        if filter_data_ary['family_cd'] != "":
            sql += """AND family_table.fnc_ctg_cd='""" + filter_data_ary['family_cd'] + """'"""

        if filter_data_ary['type_cd'] != "":
            sql += """AND type_table.fnc_ctg_cd='""" + filter_data_ary['type_cd'] + """'"""

        if filter_data_ary['eqpt_id'] != "":
            sql += """AND t_fclty_ldgr.eqpt_id='""" + filter_data_ary['eqpt_id'] + """'"""

        # sql += """ ORDER BY m_location.location_cd"""
        # sql += """ ORDER BY m_location.location_cd, t_fclty_ldgr.eqpt_id"""
        sql += """ ORDER BY t_fclty_ldgr.eqpt_id"""

        cursor.execute(sql)
        # comment_lists = cursor.fetchall()
        comment_lists = namedtuplefetchall(cursor)
        # equip_family_lists = MasterFncCtg.objects.all().raw(sql)

    return comment_lists
