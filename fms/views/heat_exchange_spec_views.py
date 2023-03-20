import datetime
import traceback
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, BudgetRequiredFunction, AmountUnitMaster
from fms.models import DisplayRequiredItemForFunction, FunctionMaster, WorkSpecMEX, DisplayItemForHeatExchange
from fms.models import ExchangeTypeMaster, SpecmanAttrs, Eqpt_Category
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 熱交情報の表示処理
# @login_required
# @require_POST
def heat_exchange_data_info(target_work_id, target_work_rev_no, template_function_id, this_step, select_function, eqpt_tp):
    # 「work_id」、「rev_no」で熱交情報のレコード数を取得
    work_spec_data_num = WorkSpecMEX.objects.filter(work_id=target_work_id, entry_class='計画', rev_no=target_work_rev_no).count()
    # if template_function_id != 0:･･･削除予定
    # 熱交情報のレコードがある場合
    if work_spec_data_num > 0:
        # 「work_id」、「rev_no」で熱交情報のデータ取得
        work_spec_data = WorkSpecMEX.objects.get(work_id=target_work_id, entry_class='計画', rev_no=target_work_rev_no,lost_flag=0)
        # select_function = work_spec_data.required_function･･･削除予定
        # 各項目の値取得･･･「NULL」の場合の処理を含む
        if work_spec_data.work_id is None:
            work_id = ""
        else:
            work_id = work_spec_data.work_id
        if work_spec_data.rev_no is None:
            rev_no = 0
        else:
            rev_no = work_spec_data.rev_no
        if work_spec_data.exchange_capacity is None:
            exchange_capacity = ""
        else:
            exchange_capacity = work_spec_data.exchange_capacity
        if work_spec_data.exchange_type is None:
            exchange_type = "999"
            # exchange_type_name = ""･･･削除予定
            type_data = Eqpt_Category.objects.get(mgt_cls='M', eqpt_family='EX', eqpt_tp=exchange_type)
            exchange_type_name = type_data.eqpt_cat_nm
        else:
            exchange_type = work_spec_data.exchange_type.mex_type_cd
            exchange_type_name = work_spec_data.exchange_type.mex_type_name
            # exchange_type_name = work_spec_data.exchange_type･･･削除予定
            # type_data = Eqpt_Category.objects.get(mgt_cls='M', eqpt_family='EX', eqpt_cat_nm=exchange_type_name)･･･削除予定
            # exchange_type = type_data.eqpt_tp･･･削除予定
        if work_spec_data.exchange_area is None:
            exchange_area = ""
        else:
            exchange_area = work_spec_data.exchange_area
        if work_spec_data.hot_fluid is None:
            hot_fluid = ""
        else:
            hot_fluid = work_spec_data.hot_fluid
        if work_spec_data.hot_design_temperature is None:
            hot_design_temperature = ""
        else:
            hot_design_temperature = work_spec_data.hot_design_temperature
        if work_spec_data.hot_regular_use_temperature is None:
            hot_regular_use_temperature = ""
        else:
            hot_regular_use_temperature = work_spec_data.hot_regular_use_temperature
        if work_spec_data.hot_input_temperature is None:
            hot_input_temperature = ""
        else:
            hot_input_temperature = work_spec_data.hot_input_temperature
        if work_spec_data.hot_output_temperature is None:
            hot_output_temperature = ""
        else:
            hot_output_temperature = work_spec_data.hot_output_temperature
        if work_spec_data.hot_fluid_capacity is None:
            hot_fluid_capacity = ""
        else:
            hot_fluid_capacity = work_spec_data.hot_fluid_capacity
        if work_spec_data.hot_fluid_capacity_unit is None:
            hot_fluid_capacity_unit = ""
        else:
            hot_fluid_capacity_unit_name = work_spec_data.hot_fluid_capacity_unit
            hot_fluid_capacity_unit_data = AmountUnitMaster.objects.get(unit=hot_fluid_capacity_unit_name)
            hot_fluid_capacity_unit = hot_fluid_capacity_unit_data.unit_id
        if work_spec_data.hot_design_pressure is None:
            hot_design_pressure = ""
        else:
            hot_design_pressure = work_spec_data.hot_design_pressure
        if work_spec_data.hot_regular_use_pressure is None:
            hot_regular_use_pressure = ""
        else:
            hot_regular_use_pressure = work_spec_data.hot_regular_use_pressure
        if work_spec_data.hot_pressure_unit is None:
            hot_pressure_unit = ""
        else:
            hot_pressure_unit_name = work_spec_data.hot_pressure_unit
            hot_pressure_unit_data = PressureUnitMaster.objects.get(unit=hot_pressure_unit_name)
            hot_pressure_unit = hot_pressure_unit_data.unit_id
        if work_spec_data.cool_fluid is None:
            cool_fluid = ""
        else:
            cool_fluid = work_spec_data.cool_fluid
        if work_spec_data.cool_design_temperature is None:
            cool_design_temperature = ""
        else:
            cool_design_temperature = work_spec_data.cool_design_temperature
        if work_spec_data.cool_regular_use_temperature is None:
            cool_regular_use_temperature = ""
        else:
            cool_regular_use_temperature = work_spec_data.cool_regular_use_temperature
        if work_spec_data.cool_input_temperature is None:
            cool_input_temperature = ""
        else:
            cool_input_temperature = work_spec_data.cool_input_temperature
        # model修正後は以下の4行を復活
        # if work_spec_data.cool_output_temperature is None:
            # cool_output_temperature = ""
        # else:
            # cool_output_temperature = work_spec_data.cool_output_temperature
        # model修正後は以下の4行を削除
        if work_spec_data.cool_output_use_temperature is None:
            cool_output_temperature = ""
        else:
            cool_output_temperature = work_spec_data.cool_output_use_temperature
        if work_spec_data.cool_fluid_capacity is None:
            cool_fluid_capacity = ""
        else:
            cool_fluid_capacity = work_spec_data.cool_fluid_capacity
        if work_spec_data.cool_fluid_capacity_unit is None:
            cool_fluid_capacity_unit = ""
        else:
            cool_fluid_capacity_unit_name = work_spec_data.cool_fluid_capacity_unit
            cool_fluid_capacity_unit_data = AmountUnitMaster.objects.get(unit=cool_fluid_capacity_unit_name)
            cool_fluid_capacity_unit = cool_fluid_capacity_unit_data.unit_id
        if work_spec_data.cool_design_pressure is None:
            cool_design_pressure = ""
        else:
            cool_design_pressure = work_spec_data.cool_design_pressure
        if work_spec_data.cool_regular_use_pressure is None:
            cool_regular_use_pressure = ""
        else:
            cool_regular_use_pressure = work_spec_data.cool_regular_use_pressure
        if work_spec_data.cool_pressure_unit is None:
            cool_pressure_unit = ""
        else:
            cool_pressure_unit_name = work_spec_data.cool_pressure_unit
            cool_pressure_unit_data = PressureUnitMaster.objects.get(unit=cool_pressure_unit_name)
            cool_pressure_unit = cool_pressure_unit_data.unit_id
        if work_spec_data.heat_exchange_rem is None:
            heat_exchange_rem = ""
        else:
            heat_exchange_rem = work_spec_data.heat_exchange_rem
        # 1つ前のrev_noの設定(=現在のrev_no-1)
        old_rev_no = rev_no - 1
        # 1つ前のrev_noのレコード数を取得
        old_work_spec_data_num = WorkSpecMEX.objects.filter(work_id=target_work_id, entry_class='計画', rev_no=old_rev_no).count()

    # 熱交情報のレコードがない場合
    else:
        select_function = select_function
        # 該当の工事idが指定されている場合の処理
        if target_work_id != 0:
            work_id = target_work_id
        # 該当の工事idが指定されていない場合の処理
        else:
            work_id = ""
        work_spec_data = ""
        # 各項目に値設定
        rev_no = 0
        exchange_capacity = ""
        exchange_type = eqpt_tp
        type_data = Eqpt_Category.objects.get(mgt_cls='M', eqpt_family='EX', eqpt_tp=eqpt_tp)
        exchange_type_name = type_data.eqpt_cat_nm
        exchange_area = ""
        hot_fluid = ""
        hot_design_temperature = ""
        hot_regular_use_temperature = ""
        hot_input_temperature = ""
        hot_output_temperature = ""
        hot_fluid_capacity = ""
        hot_fluid_capacity_unit = ""
        hot_design_pressure = ""
        hot_regular_use_pressure = ""
        hot_pressure_unit = ""
        cool_fluid = ""
        cool_design_temperature = ""
        cool_regular_use_temperature = ""
        cool_input_temperature = ""
        cool_output_temperature = ""
        cool_fluid_capacity = ""
        cool_fluid_capacity_unit = ""
        cool_design_pressure = ""
        cool_regular_use_pressure = ""
        cool_pressure_unit = ""
        heat_exchange_rem = ""
        old_work_spec_data_num = 0

    # 熱交型選択ソースのリスト取得
    heat_exchange_type_list = Eqpt_Category.objects.filter(mgt_cls='M', eqpt_family='EX').all()

    # 濃度単位選択ソースのリスト取得
    concentration_unit_list = ConcentrationUnitMaster.objects.filter(lost_flag=0).all()

    # 圧力単位選択ソースのリスト取得
    pressure_unit_list = PressureUnitMaster.objects.filter(lost_flag=0).all()

    # 容量単位選択ソースのリスト取得
    amount_unit_list = AmountUnitMaster.objects.filter(lost_flag=0).all()

    # 伝熱面積表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_exchange_area_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='H_AREA', using_type__contains=exchange_type).count()

    # 高温物質表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_fluid_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='S_FLUID', using_type__contains=exchange_type).count()

    # 高温物質設計温度表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_design_temperature_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='S_D_TEMP', using_type__contains=exchange_type).count()

    # 高温物質常用温度表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_regular_use_temperature_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='S_R_TEMP', using_type__contains=exchange_type).count()

    # 高温入口、出口温度表示FLの処理
    if display_hot_fluid_flag > 0:
        display_hot_input_temperature_flag = 1
        display_hot_output_temperature_flag = 1
    else:
        display_hot_input_temperature_flag = 0
        display_hot_output_temperature_flag = 0

    # 高温物質容量表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_fluid_capacity_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='S_CAP', using_type__contains=exchange_type).count()

    # 高温物質容量単位表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_fluid_capacity_unit_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='S_U_CAP', using_type__contains=exchange_type).count()

    # 高温物質設計圧力表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_design_pressure_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='HT_D_PRES', using_type__contains=exchange_type).count()

    # 高温物質常用圧力表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_hot_regular_use_pressure_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='HT_R_PRES', using_type__contains=exchange_type).count()

    # 高温圧力単位表示FLの処理
    if display_hot_design_pressure_flag > 0 or display_hot_regular_use_pressure_flag > 0:
        display_hot_pressure_unit_flag = 1
    else:
        display_hot_pressure_unit_flag = 0

    # 低温物質表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_fluid_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='T_FLUID', using_type__contains=exchange_type).count()

    # 低温物質設計温度表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_design_temperature_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='T_D_TEMP', using_type__contains=exchange_type).count()

    # 低温物質常用温度表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_regular_use_temperature_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='T_R_TEMP', using_type__contains=exchange_type).count()

    # 低温入口、出口温度表示FLの処理
    if display_cool_fluid_flag > 0:
        display_cool_input_temperature_flag = 1
        display_cool_output_temperature_flag = 1
    else:
        display_cool_input_temperature_flag = 1
        display_cool_output_temperature_flag = 1

    # 低温物質容量表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_fluid_capacity_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='T_CAP', using_type__contains=exchange_type).count()

    # 低温物質容量単位表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_fluid_capacity_unit_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='T_U_CAP', using_type__contains=exchange_type).count()

    # 低温物質設計圧力表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_design_pressure_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='LT_D_PRES', using_type__contains=exchange_type).count()

    # 低温物質常用圧力表示FLのレコード数を取得･･･熱交型式が含まれている件数で確認。1件以上あればFLとしては「ON」
    display_cool_regular_use_pressure_flag = SpecmanAttrs.objects.filter(section='M', eqp_family='EX', column_name='LT_R_PRES', using_type__contains=exchange_type).count()

    # 低温圧力単位表示FLの処理
    if display_cool_design_pressure_flag > 0 or display_cool_regular_use_pressure_flag > 0:
        display_cool_pressure_unit_flag = 1
    else:
        display_cool_pressure_unit_flag = 0

    display_template_item_for_function_list = {
        'display_exchange_area_flag': display_exchange_area_flag,
        'display_hot_fluid_flag': display_hot_fluid_flag,
        'display_hot_design_temperature_flag': display_hot_design_temperature_flag,
        'display_hot_regular_use_temperature_flag': display_hot_regular_use_temperature_flag,
        'display_hot_input_temperature_flag': display_hot_input_temperature_flag,
        'display_hot_output_temperature_flag': display_hot_output_temperature_flag,
        'display_hot_fluid_capacity_flag': display_hot_fluid_capacity_flag,
        'display_hot_fluid_capacity_unit_flag': display_hot_fluid_capacity_unit_flag,
        'display_hot_design_pressure_flag': display_hot_design_pressure_flag,
        'display_hot_regular_use_pressure_flag': display_hot_regular_use_pressure_flag,
        'display_hot_pressure_unit_flag': display_hot_pressure_unit_flag,
        'display_cool_fluid_flag': display_cool_fluid_flag,
        'display_cool_design_temperature_flag': display_cool_design_temperature_flag,
        'display_cool_regular_use_temperature_flag': display_cool_regular_use_temperature_flag,
        'display_cool_input_temperature_flag': display_cool_input_temperature_flag,
        'display_cool_output_temperature_flag': display_cool_output_temperature_flag,
        'display_cool_fluid_capacity_flag': display_cool_fluid_capacity_flag,
        'display_cool_fluid_capacity_unit_flag': display_cool_fluid_capacity_unit_flag,
        'display_cool_design_pressure_flag': display_cool_design_pressure_flag,
        'display_cool_regular_use_pressure_flag': display_cool_regular_use_pressure_flag,
        'display_cool_pressure_unit_flag': display_cool_pressure_unit_flag
    }

    # 1つ前のrev_noのレコードがある場合
    if old_work_spec_data_num > 0:
        # 1つ前のrev_noの情報取得
        old_work_spec_data_data = WorkSpecMEX.objects.filter(work_id=target_work_id, entry_class='計画', lost_flag=1).all().order_by('-id')[0]
    else:
        old_work_spec_data_data = ""

    # 仕様機能に「熱交」設定
    specification_function = "EX"

    # データ編集機能要否判定
    work_edit_action_num = 0
    # 対象stepで「work」がデータ更新対象か確認
    work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='work').count()

    if work_edit_action_num > 0:
        work_entry_pb_disp_flag = 1

    else:
        work_entry_pb_disp_flag = 0

    dict_data = {
        'display_template_item_for_function_list': display_template_item_for_function_list,
        'work_spec_data': work_spec_data,
        'old_work_spec_data_num': old_work_spec_data_num,
        'old_work_spec_data_data': old_work_spec_data_data,
        'template_function_id': template_function_id,
        'work_id': target_work_id,
        'rev_no': rev_no,
        'specification_function': specification_function,
        'exchange_capacity': exchange_capacity,
        'exchange_type': exchange_type,
        'exchange_type_name': exchange_type_name,
        'exchange_area': exchange_area,
        'hot_fluid': hot_fluid,
        'hot_design_temperature': hot_design_temperature,
        'hot_regular_use_temperature': hot_regular_use_temperature,
        'hot_input_temperature': hot_input_temperature,
        'hot_output_temperature': hot_output_temperature,
        'hot_fluid_capacity': hot_fluid_capacity,
        'hot_fluid_capacity_unit': hot_fluid_capacity_unit,
        'hot_design_pressure': hot_design_pressure,
        'hot_regular_use_pressure': hot_regular_use_pressure,
        'hot_pressure_unit': hot_pressure_unit,
        'cool_fluid': cool_fluid,
        'cool_design_temperature': cool_design_temperature,
        'cool_regular_use_temperature': cool_regular_use_temperature,
        'cool_input_temperature': cool_input_temperature,
        'cool_output_temperature': cool_output_temperature,
        'cool_fluid_capacity': cool_fluid_capacity,
        'cool_fluid_capacity_unit': cool_fluid_capacity_unit,
        'cool_design_pressure': cool_design_pressure,
        'cool_regular_use_pressure': cool_regular_use_pressure,
        'cool_pressure_unit': cool_pressure_unit,
        'heat_exchange_rem': heat_exchange_rem,
        'work_entry_pb_disp_flag': work_entry_pb_disp_flag,
        'heat_exchange_type_list': heat_exchange_type_list,
        'concentration_unit_list': concentration_unit_list,
        'pressure_unit_list': pressure_unit_list,
        'amount_unit_list': amount_unit_list,
        'div_id_name': 'heat_exchange_edit',

    }

    edit_url = "fms/parts/work/work_spec/heat_exchange/heat_exchange_edit.html"

    info_url = "fms/parts/work/work_spec/heat_exchange/heat_exchange_info.html"

    data = {
        'dict_data': dict_data,
        'edit_url': edit_url,
        'info_url': info_url
    }

    return (data)


# 熱交仕様情報登録･更新
@login_required
@require_POST
def heat_exchange_spec_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・空欄処理、数値項目は数値に変換(int関数、float関数)を含む
        work_id = int(request.POST["work_id"])
        # budget_id = int(request.POST["budget_id"])･･･削除予定
        work_rev_no = int(request.POST["work_rev_no"])
        # template_function_id = int(request.POST["template_function_id"])･･･削除予定
        exchange_type = request.POST['exchange_type']
        etrc = ExchangeTypeMaster.objects.get(mex_type_cd=exchange_type)
        exchange_capacity_str = request.POST["exchange_capacity"]
        if exchange_capacity_str == "":
            exchange_capacity = None
        else:
            exchange_capacity = float(request.POST["exchange_capacity"])
        exchange_area_str = request.POST["exchange_area"]
        if exchange_area_str == "":
            exchange_area = None
        else:
            exchange_area = float(request.POST["exchange_area"])
        hot_fluid = request.POST['hot_fluid']
        hot_design_temperature_str = request.POST["hot_design_temperature"]
        if hot_design_temperature_str == "":
            hot_design_temperature = None
        else:
            hot_design_temperature = int(request.POST["hot_design_temperature"])
        hot_regular_use_temperature_syr = request.POST["hot_regular_use_temperature"]
        if hot_regular_use_temperature_syr == "":
            hot_regular_use_temperature = None
        else:
            hot_regular_use_temperature = int(request.POST["hot_regular_use_temperature"])
        hot_input_temperature_str = request.POST["hot_input_temperature"]
        if hot_input_temperature_str == "":
            hot_input_temperature = None
        else:
            hot_input_temperature = int(request.POST["hot_input_temperature"])
        hot_output_temperature_str = request.POST["hot_output_temperature"]
        if hot_output_temperature_str == "":
            hot_output_temperature = None
        else:
            hot_output_temperature = int(request.POST["hot_output_temperature"])
        hot_fluid_capacity_str = request.POST["hot_fluid_capacity"]
        if hot_fluid_capacity_str == "":
            hot_fluid_capacity = None
        else:
            hot_fluid_capacity = float(request.POST["hot_fluid_capacity"])
        hot_fluid_capacity_unit = request.POST["hot_fluid_capacity_unit"]
        hfcurc = AmountUnitMaster.objects.get(unit_id=hot_fluid_capacity_unit)
        hot_design_pressure_str = request.POST["hot_design_pressure"]
        if hot_design_pressure_str == "":
            hot_design_pressure = None
        else:
            hot_design_pressure = float(request.POST["hot_design_pressure"])
        hot_regular_use_pressure_str = request.POST["hot_regular_use_pressure"]
        if hot_regular_use_pressure_str == "":
            hot_regular_use_pressure = None
        else:
            hot_regular_use_pressure = float(request.POST["hot_regular_use_pressure"])
        hot_pressure_unit = request.POST["hot_pressure_unit"]
        hpurc = PressureUnitMaster.objects.get(unit_id=hot_pressure_unit)
        cool_fluid = request.POST['cool_fluid']
        cool_design_temperature_str = request.POST["cool_design_temperature"]
        if cool_design_temperature_str == "":
            cool_design_temperature = None
        else:
            cool_design_temperature = int(request.POST["cool_design_temperature"])
        cool_regular_use_temperature_str = request.POST["cool_regular_use_temperature"]
        if cool_regular_use_temperature_str == "":
            cool_regular_use_temperature = None
        else:
            cool_regular_use_temperature = int(request.POST["cool_regular_use_temperature"])
        cool_input_temperature_str = request.POST["cool_input_temperature"]
        if cool_input_temperature_str == "":
            cool_input_temperature = None
        else:
            cool_input_temperature = int(request.POST["cool_input_temperature"])
        cool_output_temperature_str = request.POST["cool_output_temperature"]
        if cool_output_temperature_str == "":
            cool_output_temperature = None
        else:
            cool_output_temperature = int(request.POST["cool_output_temperature"])
        cool_fluid_capacity_str = request.POST["cool_fluid_capacity"]
        if cool_fluid_capacity_str == "":
            cool_fluid_capacity = None
        else:
            cool_fluid_capacity = float(request.POST["cool_fluid_capacity"])
        cool_fluid_capacity_unit = request.POST["cool_fluid_capacity_unit"]
        cfcurc = AmountUnitMaster.objects.get(unit_id=cool_fluid_capacity_unit)
        cool_design_pressure_str = request.POST["cool_design_pressure"]
        if cool_design_pressure_str == "":
            cool_design_pressure = None
        else:
            cool_design_pressure = float(request.POST["cool_design_pressure"])
        cool_regular_use_pressure_str = request.POST["cool_regular_use_pressure"]
        if cool_regular_use_pressure_str == "":
            cool_regular_use_pressure = None
        else:
            cool_regular_use_pressure = float(request.POST["cool_regular_use_pressure"])
        cool_pressure_unit = request.POST["cool_pressure_unit"]
        cpurc = PressureUnitMaster.objects.get(unit_id=cool_pressure_unit)
        heat_exchange_rem = request.POST["heat_exchange_rem"]
        this_step = int(request.POST['this_step'])
        # next_step = int(request.POST['next_step'])･･･削除予定
        # this_department = request.POST['this_department']･･･削除予定
        # this_division = request.POST['this_division']･･･削除予定

        # 現在のstepからデータ登録タイミングを判定
        if this_step < 200000000:
            entry_class = "計画"
        else:
            entry_class = "実行"

        # 「work_id」、「rev_no」での熱交情報のレコード数を取得
        heat_exchange_spec_data_num = WorkSpecMEX.objects.filter(work_id=work_id, entry_class='計画', rev_no=work_rev_no).count()

        # 「work_id」、「rev_no」での熱交情報のレコードがない場合の処理
        if heat_exchange_spec_data_num == 0:
            # 1つ前のrev_noを設定(=現行のrev_no-1)
            last_rev_no = work_rev_no - 1
            # 1つ前のrev_noの熱交情報のレコード数を取得
            last_heat_exchange_spec_data_num = WorkSpecMEX.objects.filter(work_id=work_id, entry_class='計画', rev_no=last_rev_no).count()
            # 1つ前のrev_noの熱交情報がある場合の処理
            if last_heat_exchange_spec_data_num > 0:
                # 1つ前のrev_noの熱交情報(レコード)を取得
                last_heat_exchange_spec_data = WorkSpecMEX.objects.get(work_id=work_id, entry_class='計画', rev_no=last_rev_no)
                # 無効化
                last_heat_exchange_spec_data.lost_flag = 1
                # 1つ前のrev_noの熱交情報のレコードを保存
                last_heat_exchange_spec_data.save()

            # 「work_id」、「rev_no」、「登録日時」、「登録者」でデー新規登録･･･
            # 「hot_fluid_capacity_unit_id」、「hot_pressure_unit_id」、「cool_fluid_capacity_unit_id」、「cool_pressure_unit_id」は、NULLが不可のため、仮の値(999)を設定
            WorkSpecMEX(work_id=work_id, entry_class='計画', rev_no=work_rev_no, hot_fluid_capacity_unit_id=999, hot_pressure_unit_id=999,
                        cool_fluid_capacity_unit_id=999, cool_pressure_unit_id=999, entry_datetime=now,
                        entry_operator=operator).save()

            # 「登録日時」、「登録者」で登録した熱交情報のレコード取得
            heat_exchange_spec_data = WorkSpecMEX.objects.get(entry_datetime=now, entry_operator=operator)
            # 無効FLに「0」を設定
            heat_exchange_spec_data.lost_flag = 0

        # 「work_id」、「rev_no」での熱交情報のレコードがある場合の処理
        else:
            # 「work_id」、「rev_no」での熱交情報のレコード取得
            heat_exchange_spec_data = WorkSpecMEX.objects.get(work_id=work_id, entry_class='計画', rev_no=work_rev_no)
            # 「更新日時」、「更新者」に値設定
            heat_exchange_spec_data.update_datetime = now
            heat_exchange_spec_data.update_operator = operator

        # 各項目に値格納
        heat_exchange_spec_data.entry_class = entry_class
        heat_exchange_spec_data.exchange_capacity = exchange_capacity
        heat_exchange_spec_data.exchange_type = etrc
        heat_exchange_spec_data.exchange_area = exchange_area
        heat_exchange_spec_data.hot_fluid = hot_fluid
        heat_exchange_spec_data.hot_design_temperature = hot_design_temperature
        heat_exchange_spec_data.hot_regular_use_temperature = hot_regular_use_temperature
        heat_exchange_spec_data.hot_input_temperature = hot_input_temperature
        heat_exchange_spec_data.hot_output_temperature = hot_output_temperature
        heat_exchange_spec_data.hot_fluid_capacity = hot_fluid_capacity
        heat_exchange_spec_data.hot_fluid_capacity_unit = hfcurc
        heat_exchange_spec_data.hot_design_pressure = hot_design_pressure
        heat_exchange_spec_data.hot_regular_use_pressure = hot_regular_use_pressure
        heat_exchange_spec_data.hot_pressure_unit = hpurc
        heat_exchange_spec_data.cool_fluid = cool_fluid
        heat_exchange_spec_data.cool_design_temperature = cool_design_temperature
        heat_exchange_spec_data.cool_regular_use_temperature = cool_regular_use_temperature
        heat_exchange_spec_data.cool_input_temperature = cool_input_temperature
        heat_exchange_spec_data.cool_output_temperature = cool_output_temperature
        heat_exchange_spec_data.cool_fluid_capacity = cool_fluid_capacity
        heat_exchange_spec_data.cool_fluid_capacity_unit = cfcurc
        heat_exchange_spec_data.cool_design_pressure = cool_design_pressure
        heat_exchange_spec_data.cool_regular_use_pressure = cool_regular_use_pressure
        heat_exchange_spec_data.cool_pressure_unit = cpurc
        heat_exchange_spec_data.heat_exchange_rem = heat_exchange_rem
        # 熱交情報のレコードを保存
        heat_exchange_spec_data.save()

        msg = "熱交換機データ登録完了！！"

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
