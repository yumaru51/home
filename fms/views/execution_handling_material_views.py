import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db.models import Q

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, MyBudgetMaterialData
from fms.models import MaterialMaster
from fms.models import ProBudgetUnit
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 取扱物質情報表示処理
@login_required
@require_POST
def execution_handling_material_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['target_budget_id'])
        new_step = int(request.POST['new_step'])
        budget_material_id = int(request.POST['budget_material_id'])
        work_id = request.POST['work_id']
        data_source = request.POST['data_source']
        target_type = request.POST['target_type']

        # 取扱物質データがある場合の処理･･･(ない場合はbudget_material_idが「0」)
        if budget_material_id != 0:
            # 予算idを取得(予算の主キーの値から)
            budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
            # # 進捗状況データから該当の予算idの現在のstepを取得
            # if target_type == 'probudgetunit':
            #     present_step_data = Progress.objects.get(target_id=budget_id, target='probudgetunit')
            # else:
            #     present_step_data = Progress.objects.get(target_id=work_id, target='prospecificationunit')
            # present_step = present_step_data.present_step

            # データ取得元が登録済取扱物質一覧の場合の処理
            # 取扱物質情報の主キーの値でレコードを取得し、「sub_no」と「物質名」の値を取得
            # budget_material_data = BudgetMaterial.objects.get(id=budget_material_id, work_id=None if work_id == "" else work_id)
            budget_material_data = BudgetMaterial.objects.get(id=budget_material_id, lost_flag=0)
            sub_no = budget_material_data.sub_no
            material_name = budget_material_data.material_name
            # 各項目の値を取得･･･「NULL」の場合は空欄にする処理を実施
            if budget_material_data.material_name is None:
                material_name = ""
            else:
                material_name = budget_material_data.material_name
            if budget_material_data.material_name is None:
                chemical_formula = ""
            else:
                chemical_formula = budget_material_data.chemical_formula
            if budget_material_data.sub_no is None:
                sub_no = ""
            else:
                sub_no = budget_material_data.sub_no
            if budget_material_data.state is None:
                state = ""
            else:
                state = budget_material_data.state
            if budget_material_data.normal_pressure is None:
                normal_pressure = ""
            else:
                normal_pressure = budget_material_data.normal_pressure
            if budget_material_data.normal_pressure is None:
                maximum_pressure = ""
            else:
                maximum_pressure = budget_material_data.minimum_pressure
            if budget_material_data.normal_pressure is None:
                minimum_pressure = ""
            else:
                minimum_pressure = budget_material_data.minimum_pressure
            pressure_unit = budget_material_data.pressure_unit
            if budget_material_data.normal_temperature is None:
                normal_temperature = ""
            else:
                normal_temperature = budget_material_data.normal_temperature
            if budget_material_data.maximum_temperature is None:
                maximum_temperature = ""
            else:
                maximum_temperature = budget_material_data.maximum_temperature
            if budget_material_data.minimum_temperature is None:
                minimum_temperature = ""
            else:
                minimum_temperature = budget_material_data.minimum_temperature
            if budget_material_data.concentration is None:
                concentration = ""
            else:
                concentration = budget_material_data.concentration
            concentration_unit = budget_material_data.concentration_unit
            if budget_material_data.ph is None:
                ph = ""
            else:
                ph = budget_material_data.ph
            if budget_material_data.viscosity is None:
                viscosity = ""
            else:
                viscosity = budget_material_data.viscosity
            if budget_material_data.bulk_specific_gravity is None:
                bulk_specific_gravity = ""
            else:
                bulk_specific_gravity = budget_material_data.bulk_specific_gravity
            if budget_material_data.true_specific_gravity is None:
                true_specific_gravity = ""
            else:
                true_specific_gravity = budget_material_data.true_specific_gravity
            if budget_material_data.apparent_specific_gravity is None:
                apparent_specific_gravity = ""
            else:
                apparent_specific_gravity = budget_material_data.apparent_specific_gravity
            if budget_material_data.particle_size is None:
                particle_size = ""
            else:
                particle_size = budget_material_data.particle_size
            if budget_material_data.moisture is None:
                moisture = ""
            else:
                moisture = budget_material_data.moisture
            if budget_material_data.others is None:
                others = ""
            else:
                others = budget_material_data.others

            # 古い(無効となった)レコード数を取得
            old_budget_material_data_num = BudgetMaterial.objects.filter(budget_id=budget_id , sub_no=sub_no, material_name=material_name, lost_flag=1).count()

        # 取扱物質データがない場合の処理
        else:
            # 予算データがある場合の処理
            if budget_id != 0:
                # 予算idを取得(予算の主キーの値から)
                budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0 )
                # # 進捗状況データから該当の予算idの現在のstepを取得
                # if target_type == 'probudgetunit':
                #     present_step_data = Progress.objects.get(target_id=budget_id, target='probudgetunit')
                # else:
                #     present_step_data = Progress.objects.get(target_id=work_id, target='prospecificationunit')
                # present_step = present_step_data.present_step

            # 予算データがない場合の処理
            else:
                # 「present_step」、「予算id」に仮の値を設定
                present_step = new_step
                budget_id  = 0

            # 各項目に値を設定
            budget_material_data = ""
            old_budget_material_data_num = 0
            material_name = ""
            chemical_formula = ""
            sub_no = ""
            state = ""
            normal_pressure = ""
            maximum_pressure = ""
            minimum_pressure = ""
            pressure_unit = ""
            normal_temperature = ""
            maximum_temperature = ""
            minimum_temperature = ""
            concentration_unit = ""
            concentration = ""
            ph = ""
            viscosity = ""
            bulk_specific_gravity = ""
            true_specific_gravity = ""
            apparent_specific_gravity = ""
            particle_size = ""
            moisture = ""
            others = ""

        # 対象の予算の取扱物質のレコード数を取得
        handling_material_data_num = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=0).count()
        # if handling_material_data_num > 0:
        # 対象の予算の取扱物質のレデータを取得
        handling_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=0).all()

        # 古い(無効となった)レコードがある場合
        if old_budget_material_data_num > 0:
            # 古い(無効となった)情報のうち最終のものを取得
            old_budget_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, sub_no=sub_no, material_name=material_name, lost_flag=1).all().order_by('-id')[0]
        else:
            old_budget_material_data = ""

        data = {
            'target_id': budget_id,
            'handling_material_id': budget_material_id,
            'handling_material_data_num': handling_material_data_num,
            'handling_material_data': handling_material_data,
            'old_budget_material_data_num': old_budget_material_data_num,
            'budget_material_data': budget_material_data,
            'old_budget_material_data': old_budget_material_data,
            'material_name': material_name,
            'chemical_formula': chemical_formula,
            'sub_no': sub_no,
            'state': state,
            'normal_pressure': normal_pressure,
            'maximum_pressure': maximum_pressure,
            'minimum_pressure': minimum_pressure,
            'pressure_unit': pressure_unit,
            'normal_temperature': normal_temperature,
            'maximum_temperature': maximum_temperature,
            'minimum_temperature': minimum_temperature,
            'concentration_unit': concentration_unit,
            'concentration': concentration,
            'ph': ph,
            'viscosity': viscosity,
            'bulk_specific_gravity': bulk_specific_gravity,
            'true_specific_gravity': true_specific_gravity,
            'apparent_specific_gravity': apparent_specific_gravity,
            'particle_size': particle_size,
            'moisture': moisture,
            'others': others
        }

        if target_type == 'budget':
            return render(request, 'fms/parts/execution/execution_handling_material/execution_budget_handling_material_info.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_handling_material/execution_work_handling_material_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 以下の関数は不要
@login_required
@require_POST
def handling_material_detail(request):
    try:
        # t_username = request.user.username

        target_id = int(request.POST['target_id'])
        handling_material_data = BudgetMaterial.objects.get(id=target_id, lost_flag=0)
        handling_material_id = handling_material_data.id
        handling_material = handling_material_data.material_name
        sub_no = handling_material_data.sub_no
        chemical_formula = handling_material_data.chemical_formula
        normal_pressure = handling_material_data.normal_pressure
        maximum_pressure = handling_material_data.maximum_pressure
        minimum_pressure = handling_material_data.minimum_pressure
        pressure_unit = handling_material_data.pressure_unit
        # リレーション対応対策
        if pressure_unit is not None:
            pressure_unit_data = PressureUnitMaster.objects.get(unit=pressure_unit, lost_flag=0)
            pressure_unit_name = pressure_unit_data.unit
        else:
            pressure_unit_name = ""

        normal_temperature = handling_material_data.normal_temperature
        maximum_temperature = handling_material_data.maximum_temperature
        minimum_temperature = handling_material_data.minimum_temperature
        state = handling_material_data.state
        # リレーション対応対策
        if state is not None:
            state_data = MaterialStateMaster.objects.get(state_name=state, lost_flag=0)
            state_name = state_data.state_name
        else:
            state_name = ""
        concentration = handling_material_data.concentration
        concentration_unit = handling_material_data.concentration_unit
        # リレーション対応対策
        if concentration_unit is not None:
            concentration_unit_data = ConcentrationUnitMaster.objects.get(unit=concentration_unit, lost_flag=0)
            concentration_unit_name = concentration_unit_data.unit
        else:
            concentration_unit_name = ""
        ph = handling_material_data.ph
        viscosity = handling_material_data.viscosity
        bulk_specific_gravity = handling_material_data.bulk_specific_gravity
        true_specific_gravity = handling_material_data.true_specific_gravity
        apparent_specific_gravity = handling_material_data.apparent_specific_gravity
        particle_size = handling_material_data.particle_size
        moisture = handling_material_data.moisture
        others = handling_material_data.others
        # unit_data = UnitMaster.objects.get(unit_id=concentration_unit_id)
        # concentration_unit = unit_data.unit

        ary = {
            'handling_material_id': handling_material_id,
            'handling_material': handling_material,
            'chemical_formula': chemical_formula,
            'sub_no': sub_no,
            'normal_pressure': normal_pressure,
            'maximum_pressure': maximum_pressure,
            'minimum_pressure': minimum_pressure,
            'pressure_unit': pressure_unit_name,
            'normal_temperature': normal_temperature,
            'maximum_temperature': maximum_temperature,
            'minimum_temperature': minimum_temperature,
            'state': state_name,
            'concentration': concentration,
            'concentration_unit': concentration_unit_name,
            'pH': ph,
            'viscosity': viscosity,
            'bulk_specific_gravity': bulk_specific_gravity,
            'true_specific_gravity': true_specific_gravity,
            'apparent_specific_gravity': apparent_specific_gravity,
            'particle_size': particle_size,
            'moisture': moisture,
            'others': others,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済取扱物質一覧表示処理
@require_POST
def execution_handling_material_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id_str = request.POST['target_id']
        target_id = int(target_id_str)
        work_id = request.POST['work_id']
        work_id_api = None if work_id == '' else work_id
        work_id_str = 'fms_budgetmaterial.work_id is NULL' if work_id == '' else 'fms_budgetmaterial.work_id=' + work_id
        target_type = request.POST['target_type']

        # 登録済取扱物質のレコード数を取得
        handling_material_lists_num = BudgetMaterial.objects.filter(budget_id=target_id, work_id=work_id_api, lost_flag=0).count()

        # 登録済取扱物質の一覧を取得
        sql = """ SELECT fms_budgetmaterial.*, fms_materialstatemaster.state_name, c_u.unit as c_unit """
        sql = sql + """ , p_u.unit as p_unit  """
        sql = sql + """ FROM ((fms_budgetmaterial """
        sql = sql + """ LEFT JOIN fms_materialstatemaster ON fms_budgetmaterial.state_id=fms_materialstatemaster.state_id) """
        sql = sql + """ LEFT JOIN fms_concentrationunitmaster c_u ON fms_budgetmaterial.concentration_unit_id=c_u.unit_id )"""
        sql = sql + """ LEFT JOIN fms_pressureunitmaster p_u ON fms_budgetmaterial.pressure_unit_id=p_u.unit_id """
        sql = sql + """ WHERE fms_budgetmaterial.budget_id=""" + target_id_str + """ AND """ + work_id_str + """ AND fms_budgetmaterial.lost_flag=0 """

        handling_material_lists = BudgetMaterial.objects.all().raw(sql)

        # データ取得元情報に登録済取扱物質一覧を設定
        data_source = "d"

        data = {
            'handling_material_lists': handling_material_lists,
            'handling_material_lists_num': handling_material_lists_num,
            'data_source': data_source
        }

        if target_type == 'budget':
            return render(request, 'fms/parts/execution/execution_handling_material/execution_budget_handling_material_lists.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_handling_material/execution_work_handling_material_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

