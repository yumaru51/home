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
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 取扱物質情報表示処理
@login_required
@require_POST
def handling_material_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_budget_unique_id = int(request.POST['target_budget_unique_id'])
        new_step = int(request.POST['new_step'])
        this_step = int(request.POST['this_step'])
        level5_step_id = int(request.POST['level5_step_id'])
        budget_material_id = int(request.POST['budget_material_id'])
        work_id = request.POST['work_id']
        data_source = request.POST['data_source']
        target_type = request.POST['target_type']
        page_display_flag = 1

        # 取扱物質データがある場合の処理･･･(ない場合はbudget_material_idが「0」)
        if budget_material_id != 0:
            # 予算idを取得(予算の主キーの値から)
            budget_data = Budget.objects.get(id=target_budget_unique_id)
            budget_id = budget_data.budget_id
            # 進捗状況データから該当の予算idの現在のstepを取得
            if target_type == 'budget':
                present_step_data = Progress.objects.get(target_id=budget_id, target='budget')
            else:
                present_step_data = Progress.objects.get(target_id=work_id, target='work')
            present_step = present_step_data.present_step

            # データ取得元が登録済取扱物質一覧の場合の処理
            if data_source == "d":
                # 取扱物質情報の主キーの値でレコードを取得し、「sub_no」と「物質名」の値を取得
                budget_material_data = BudgetMaterial.objects.get(id=budget_material_id, work_id=None if work_id == "" else work_id,lost_flag=0)
                sub_no = budget_material_data.sub_no
                material_name = budget_material_data.material_name
                # 各項目の値を取得･･･「NULL」の場合は空欄にする処理を実施
                if budget_material_data.material_name is None:
                    material_name = ""
                else:
                    material_name = budget_material_data.material_name
                if budget_material_data.material_cd is None:
                    material_cd = ""
                else:
                    material_cd = budget_material_data.material_cd
                if budget_material_data.material_name is None:
                    chemical_formula = ""
                else:
                    chemical_formula = budget_material_data.chemical_formula
                if budget_material_data.material_cd is None:
                    chemical_cd = ""
                else:
                    material_cd = budget_material_data.material_cd
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
                if budget_material_data.str_normal_pressure is None:
                    str_normal_pressure = ""
                else:
                    str_normal_pressure = budget_material_data.str_normal_pressure
                if budget_material_data.maximum_pressure is None:
                    maximum_pressure = ""
                else:
                    maximum_pressure = budget_material_data.maximum_pressure
                if budget_material_data.minimum_pressure is None:
                    minimum_pressure = ""
                else:
                    minimum_pressure = budget_material_data.minimum_pressure
                pressure_unit = budget_material_data.pressure_unit_id
                if budget_material_data.normal_temperature is None:
                    normal_temperature = ""
                else:
                    normal_temperature = budget_material_data.normal_temperature
                if budget_material_data.str_normal_temperature is None:
                    str_normal_temperature = ""
                else:
                    str_normal_temperature = budget_material_data.str_normal_temperature
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
                if budget_material_data.str_ph is None:
                    str_ph = ""
                else:
                    str_ph = budget_material_data.str_ph
                if budget_material_data.viscosity is None:
                    viscosity = ""
                else:
                    viscosity = budget_material_data.viscosity
                if budget_material_data.angle_of_repose is None:
                    angle_of_repose = ""
                else:
                    angle_of_repose = budget_material_data.angle_of_repose
                if budget_material_data.str_bulk_specific_gravity is None:
                    bulk_specific_gravity = ""
                else:
                    bulk_specific_gravity = budget_material_data.str_bulk_specific_gravity
                if budget_material_data.str_bulk_specific_gravity is None:
                    str_bulk_specific_gravity = ""
                else:
                    str_bulk_specific_gravity = budget_material_data.str_bulk_specific_gravity
                if budget_material_data.true_specific_gravity is None:
                    true_specific_gravity = ""
                else:
                    true_specific_gravity = budget_material_data.true_specific_gravity
                if budget_material_data.str_true_specific_gravity is None:
                    str_true_specific_gravity = ""
                else:
                    str_true_specific_gravity = budget_material_data.str_true_specific_gravity
                if budget_material_data.apparent_specific_gravity is None:
                    apparent_specific_gravity = ""
                else:
                    apparent_specific_gravity = budget_material_data.apparent_specific_gravity
                if budget_material_data.str_apparent_specific_gravity is None:
                    str_apparent_specific_gravity = ""
                else:
                    str_apparent_specific_gravity = budget_material_data.str_apparent_specific_gravity
                if budget_material_data.particle_size is None:
                    particle_size = ""
                else:
                    particle_size = budget_material_data.particle_size
                if budget_material_data.str_particle_size is None:
                    str_particle_size = ""
                else:
                    str_particle_size = budget_material_data.str_particle_size
                if budget_material_data.moisture is None:
                    moisture = ""
                else:
                    moisture = budget_material_data.moisture
                if budget_material_data.str_moisture is None:
                    str_moisture = ""
                else:
                    str_moisture = budget_material_data.str_moisture
                if budget_material_data.others is None:
                    others = ""
                else:
                    others = budget_material_data.others

                # 古い(無効となった)レコード数を取得
                old_budget_material_data_num = BudgetMaterial.objects.filter(budget_id=budget_id, sub_no=sub_no, material_name=material_name, lost_flag=1).count()

            # データ取得元がマイマスタ一覧の場合の処理
            else:
                # データ取得元が登録済取扱物質一覧の時の必要項目(今回は不要項目)を仮設定
                budget_material_data = ""
                old_budget_material_data_num = 0

                if data_source == "m":
                    # マイマスタの物質情報の主キーの値でレコードを取得
                    my_budget_material_data = MyBudgetMaterialData.objects.get(id=budget_material_id, lost_flag=0)
                else:   # data_source == "s"
                    # 物質情報マスタのレコードを取得
                    my_budget_material_data = MaterialMaster.objects.get(id=budget_material_id, lost_flag=0)

                # 各項目の値を取得･･･「NULL」の場合は空欄にする処理を実施
                material_name = my_budget_material_data.material_name
                material_cd = my_budget_material_data.material_cd
                if material_cd is None:
                    material_cd = ""
                chemical_formula = my_budget_material_data.chemical_formula
                sub_no = ""
                state = my_budget_material_data.state
                normal_pressure = my_budget_material_data.normal_pressure
                if normal_pressure is None:
                    normal_pressure = ""
                str_normal_pressure = my_budget_material_data.str_normal_pressure
                if str_normal_pressure is None:
                    str_normal_pressure = ""
                maximum_pressure = my_budget_material_data.maximum_pressure
                if maximum_pressure is None:
                    maximum_pressure = ""
                minimum_pressure = my_budget_material_data.minimum_pressure
                if minimum_pressure is None:
                    minimum_pressure = ""
                pressure_unit = my_budget_material_data.pressure_unit_id
                normal_temperature = my_budget_material_data.normal_temperature
                if normal_temperature is None:
                    normal_temperature = ""
                str_normal_temperature = my_budget_material_data.str_normal_temperature
                if str_normal_temperature is None:
                    str_normal_temperature = ""
                maximum_temperature = my_budget_material_data.maximum_temperature
                if maximum_temperature is None:
                    maximum_temperature = ""
                minimum_temperature = my_budget_material_data.minimum_temperature
                if minimum_temperature is None:
                    minimum_temperature = ""
                concentration_unit = my_budget_material_data.concentration_unit
                concentration = my_budget_material_data.concentration
                if concentration is None:
                    concentration = ""
                ph = my_budget_material_data.ph
                if ph is None:
                    ph = ""
                str_ph = my_budget_material_data.str_ph
                if str_ph is None:
                    str_ph = ""
                viscosity = my_budget_material_data.viscosity
                if viscosity is None:
                    viscosity = ""
                angle_of_repose = my_budget_material_data.angle_of_repose
                if angle_of_repose is None:
                    angle_of_repose = ""
                bulk_specific_gravity = my_budget_material_data.bulk_specific_gravity
                if bulk_specific_gravity is None:
                    bulk_specific_gravity = ""
                str_bulk_specific_gravity = my_budget_material_data.str_bulk_specific_gravity
                if str_bulk_specific_gravity is None:
                    str_bulk_specific_gravity = ""
                true_specific_gravity = my_budget_material_data.true_specific_gravity
                if true_specific_gravity is None:
                    true_specific_gravity = ""
                str_true_specific_gravity = my_budget_material_data.str_true_specific_gravity
                if str_true_specific_gravity is None:
                    str_true_specific_gravity = ""
                apparent_specific_gravity = my_budget_material_data.apparent_specific_gravity
                if apparent_specific_gravity is None:
                    apparent_specific_gravity = ""
                str_apparent_specific_gravity = my_budget_material_data.str_apparent_specific_gravity
                if str_apparent_specific_gravity is None:
                    str_apparent_specific_gravity = ""
                particle_size = my_budget_material_data.particle_size
                if particle_size is None:
                    particle_size = ""
                str_particle_size = my_budget_material_data.str_particle_size
                if str_particle_size is None:
                    str_particle_size = ""
                moisture = my_budget_material_data.moisture
                if moisture is None:
                    moisture = ""
                str_moisture = my_budget_material_data.str_moisture
                if str_moisture is None:
                    str_moisture = ""
                others = my_budget_material_data.others

        # 取扱物質データがない場合の処理
        else:
            # 予算データがある場合の処理
            if target_budget_unique_id != 0:
                # 予算idを取得(予算の主キーの値から)
                budget_data = Budget.objects.get(id=target_budget_unique_id)
                budget_id = budget_data.budget_id
                # 進捗状況データから該当の予算idの現在のstepを取得
                if target_type == 'budget':
                    present_step_data = Progress.objects.get(target_id=budget_id, target='budget')
                else:
                    present_step_data = Progress.objects.get(target_id=work_id, target='work')
                present_step = present_step_data.present_step

            # 予算データがない場合の処理
            else:
                # 「present_step」、「予算id」に仮の値を設定
                present_step = new_step
                budget_id = 0
                page_display_flag = 0

            # 各項目に値を設定
            budget_material_data = ""
            old_budget_material_data_num = 0
            material_name = ""
            material_cd = ""
            chemical_formula = ""
            sub_no = ""
            state = ""
            normal_pressure = ""
            str_normal_pressure = ""
            maximum_pressure = ""
            minimum_pressure = ""
            pressure_unit = ""
            normal_temperature = ""
            str_normal_temperature = ""
            maximum_temperature = ""
            minimum_temperature = ""
            concentration_unit = ""
            concentration = ""
            ph = ""
            str_ph = ""
            viscosity = ""
            angle_of_repose = ""
            bulk_specific_gravity = ""
            str_bulk_specific_gravity = ""
            true_specific_gravity = ""
            str_true_specific_gravity = ""
            apparent_specific_gravity = ""
            str_apparent_specific_gravity = ""
            particle_size = ""
            str_particle_size = ""
            moisture = ""
            str_moisture = ""
            others = ""


        # 対象の予算の取扱物質のレコード数を取得
        handling_material_data_num = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=0).count()
        # if handling_material_data_num > 0:
        # 対象の予算の取扱物質のレデータを取得
        handling_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, lost_flag=0).all()

        # 物質状態の選択用ソースを取得
        state_list = MaterialStateMaster.objects.filter(lost_flag=0).all()

        # 濃度単位の選択用ソースを取得
        concentration_unit_list = ConcentrationUnitMaster.objects.filter(lost_flag=0).all()

        # 圧力単位の選択用ソースを取得
        pressure_unit_list = PressureUnitMaster.objects.filter(lost_flag=0).all()

        # 容量単位の選択用ソースを取得
        amount_unit_list = PressureUnitMaster.objects.filter(lost_flag=0).all()

        # 古い(無効となった)レコードがある場合
        if old_budget_material_data_num > 0:
            # 古い(無効となった)情報のうち最終のものを取得
            old_budget_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, sub_no=sub_no,
                                                                     material_name=material_name, lost_flag=1
                                                                     ).all().order_by('-id')[0]
        else:
            old_budget_material_data = ""

        data = {
            'target_id': budget_id,
            'handling_material_id': budget_material_id,
            'handling_material_data_num': handling_material_data_num,
            'handling_material_data': handling_material_data,
            'state_list': state_list,
            'concentration_unit_list': concentration_unit_list,
            'pressure_unit_list': pressure_unit_list,
            'old_budget_material_data_num': old_budget_material_data_num,
            'budget_material_data': budget_material_data,
            'old_budget_material_data': old_budget_material_data,
            # 'budget_id': budget_id.
            'material_cd': material_cd,
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
            'others': others,
            'str_normal_pressure': str_normal_pressure,
            'str_normal_temperature': str_normal_temperature,
            'str_bulk_specific_gravity': str_bulk_specific_gravity,
            'str_true_specific_gravity': str_true_specific_gravity,
            'str_apparent_specific_gravity': str_apparent_specific_gravity,
            'str_particle_size': str_particle_size,
            'str_moisture': str_moisture,
            'str_ph': str_ph,
            'angle_of_repose': angle_of_repose,
            'page_display_flag': page_display_flag,
        }

        # データ編集機能要否判定
        budget_material_edit_action_num = 0
        if target_type == 'budget':
            # 対象stepで「budget_material」がデータ更新対象か確認
            budget_material_edit_action_num = budget_material_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='budget_material').count()
        else:
            # 対象stepで「budget_material」がデータ更新対象か確認('budget_material'と区別する)
            budget_material_edit_action_num = budget_material_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='work_material').count()

        edit_flag = 0
        if budget_material_edit_action_num > 0 and level5_step_id != 133009902:
            edit_flag = 1

        if edit_flag == 1:
            if target_type == 'budget':
                return render(request, 'fms/parts/budget/handling_material/handling_material_edit.html', data)
            else:
                return render(request, 'fms/parts/work/handling_material/work_handling_material_edit.html', data)

        else:
            if target_type == 'budget':
                return render(request, 'fms/parts/budget/handling_material/handling_material_info.html', data)
            else:
                return render(request, 'fms/parts/work/handling_material/work_handling_material_info.html', data)
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
        handling_material_data = BudgetMaterial.objects.get(id=target_id,lost_flag=0)
        handling_material_id = handling_material_data.id
        handling_material = handling_material_data.material_name
        sub_no = handling_material_data.sub_no
        chemical_formula = handling_material_data.chemical_formula
        normal_pressure = handling_material_data.normal_pressure
        str_normal_pressure = handling_material_data.str_normal_pressure
        maximum_pressure = handling_material_data.maximum_pressure
        minimum_pressure = handling_material_data.minimum_pressure
        pressure_unit = handling_material_data.pressure_unit
        # リレーション対応対策
        if pressure_unit is not None:
            pressure_unit_data = PressureUnitMaster.objects.get(unit=pressure_unit,lost_flag=0)
            pressure_unit_name = pressure_unit_data.unit
        else:
            pressure_unit_name = ""

        normal_temperature = handling_material_data.normal_temperature
        str_normal_temperature = handling_material_data.str_normal_temperature
        maximum_temperature = handling_material_data.maximum_temperature
        minimum_temperature = handling_material_data.minimum_temperature
        state = handling_material_data.state
        # リレーション対応対策
        if state is not None:
            state_data = MaterialStateMaster.objects.get(state_name=state,lost_flag=0)
            state_name = state_data.state_name
        else:
            state_name = ""
        concentration = handling_material_data.concentration
        concentration_unit = handling_material_data.concentration_unit
        # リレーション対応対策
        if concentration_unit is not None:
            concentration_unit_data = ConcentrationUnitMaster.objects.get(unit=concentration_unit,lost_flag=0)
            concentration_unit_name = concentration_unit_data.unit
        else:
            concentration_unit_name = ""
        ph = handling_material_data.ph
        str_ph = handling_material_data. str_ph
        viscosity = handling_material_data.viscosity
        angle_of_repose = handling_material_data.angle_of_repose
        bulk_specific_gravity = handling_material_data.bulk_specific_gravity
        str_bulk_specific_gravity = handling_material_data.str_bulk_specific_gravity
        true_specific_gravity = handling_material_data.true_specific_gravity
        str_true_specific_gravity = handling_material_data.str_true_specific_gravity
        apparent_specific_gravity = handling_material_data.apparent_specific_gravity
        str_apparent_specific_gravity = handling_material_data.str_apparent_specific_gravity
        particle_size = handling_material_data.particle_size
        str_particle_size = handling_material_data.str_particle_size
        moisture = handling_material_data.moisture
        str_moisture = handling_material_data.str_moisture
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
            'str_normal_pressure': str_normal_pressure,
            'str_normal_temperature': str_normal_temperature,
            'str_ph': str_ph,
            'angle_of_repose': angle_of_repose,
            'str_bulk_specific_gravity': str_bulk_specific_gravity,
            'str_true_specific_gravity': str_true_specific_gravity,
            'str_apparent_specific_gravity': str_apparent_specific_gravity,
            'str_particle_size': str_particle_size,
            'str_moisture': str_moisture,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済取扱物質一覧表示処理
@require_POST
def handling_material_list(request):
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
            return render(request, 'fms/parts/budget/handling_material/handling_material_lists.html', data)
        else:
            return render(request, 'fms/parts/work/handling_material/work_handling_material_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# マイマスタ取扱物質一覧表示処理
@login_required
@require_POST
def handling_material_my_master_list(request):
    try:
        target_type = request.POST['target_type']

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        user = request.user.username
        # 共通ユーザーに「common」を設定
        common_user = "common"

        # 登録者がユーザーか共通ユーザーであるレコード数を取得
        handling_material_my_master_lists_num = 0
        handling_material_my_master_lists_num = handling_material_my_master_lists_num + MyBudgetMaterialData.objects.filter(entry_operator=user, lost_flag=0).count()
        handling_material_my_master_lists_num = handling_material_my_master_lists_num + MyBudgetMaterialData.objects.filter(entry_operator=common_user, lost_flag=0).count()

        # 登録者がユーザーか共通ユーザーであるデータを取得
        sql = """ SELECT fms_mybudgetmaterialdata.*, fms_materialstatemaster.state_name, c_u.unit as c_unit """
        sql = sql + """ , p_u.unit as p_unit  """
        sql = sql + """ FROM ((fms_mybudgetmaterialdata """
        sql = sql + """ LEFT JOIN fms_materialstatemaster ON fms_mybudgetmaterialdata.state_id=fms_materialstatemaster.state_id) """
        sql = sql + """ LEFT JOIN fms_concentrationunitmaster c_u ON fms_mybudgetmaterialdata.concentration_unit_id=c_u.unit_id )"""
        sql = sql + """ LEFT JOIN fms_pressureunitmaster p_u ON fms_mybudgetmaterialdata.pressure_unit_id=p_u.unit_id """
        sql = sql + """ WHERE (fms_mybudgetmaterialdata.entry_operator='""" + user + """' OR fms_mybudgetmaterialdata.entry_operator='common') AND fms_mybudgetmaterialdata.lost_flag=0 """

        handling_material_my_master_lists = MyBudgetMaterialData.objects.all().raw(sql)

        # データ取得元情報にマイマスタ取扱物質一覧を設定
        data_source = "m"

        data = {
            'handling_material_lists': handling_material_my_master_lists,
            'handling_material_lists_num': handling_material_my_master_lists_num,
            'data_source': data_source
        }

        if target_type == 'budget':
            return render(request, 'fms/parts/budget/handling_material/handling_material_my_master_lists.html', data)
        else:
            return render(request, 'fms/parts/work/handling_material/work_handling_material_my_master_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 取扱物質登録･更新処理
@login_required
@require_POST
def handling_material_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        action_type = int(request.POST["action_type"])
        budget_id = int(request.POST["budget_id"])
        budget_rev_no = int(request.POST["budget_rev_no"])
        this_budget_id = budget_id
        handling_material_name = request.POST["handling_material_name"]
        handling_material_cd = request.POST["handling_material_cd"]
        sub_no_str = request.POST["sub_no"]
        # 新規登録か更新化を判定･･･新規時にはsub_noは空欄のため「1」を設定
        if sub_no_str is not "":
            sub_no = int(sub_no_str)
        else:
            sub_no = 1
        chemical_formula = request.POST["chemical_formula"]
        normal_pressure_str = request.POST["normal_pressure"]
        maximum_pressure_str = request.POST["maximum_pressure"]
        minimum_pressure_str = request.POST["minimum_pressure"]
        pressure_unit_str = request.POST["pressure_unit"]
        normal_temperature_str = request.POST["normal_temperature"]
        maximum_temperature_str = request.POST["maximum_temperature"]
        minimum_temperature_str = request.POST["minimum_temperature"]
        state_str = request.POST["state"]
        concentration_str = request.POST["concentration"]
        concentration_unit_str = request.POST["concentration_unit"]
        pH_str = request.POST["pH"]
        viscosity_str = request.POST["viscosity"]
        angle_of_repose_str = request.POST["angle_of_repose"]
        bulk_specific_gravity_str = request.POST["bulk_specific_gravity"]
        true_specific_gravity_str = request.POST["true_specific_gravity"]
        apparent_specific_gravity_str = request.POST["apparent_specific_gravity"]
        particle_size_str = request.POST["particle_size"]
        moisture_str = request.POST["moisture"]
        others = request.POST["others"]
        work_id = request.POST['work_id']

        # 新規登録時の処理
        if action_type == 0:
            action = "entry"
            # 対象の予算id、物質名での登録済取扱物質レコード数を取得
            budget_material_num = BudgetMaterial.objects.filter(budget_id=budget_id, material_name=handling_material_name,
                                                                work_id=None if work_id == "" else work_id).count()

            # 対象の予算id、物質名での登録済取扱物質のデータがある場合の処理
            if budget_material_num > 0:
                # 最終のsub_noを取得
                budget_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, material_name=handling_material_name,
                                                                     work_id=None if work_id == "" else work_id).order_by('-sub_no')[0]
                latest_sub_no = budget_material_data.sub_no
            # 対象の予算id、物質名での登録済取扱物質のデータがない場合の処理
            else:
                # 最終のsub_noに「0」を設定
                latest_sub_no = 0

            # 今回のsub_noを設定(=最終のsub_no+1)
            this_sub_no = latest_sub_no + 1

            # 「budget_id」、「sub_no」、「取扱物質名」で登録済の見積情報を抽出･･･あれば読み込み、なければ新規登録
            budget_material_data, created = BudgetMaterial.objects.get_or_create(budget_id=budget_id, material_name=handling_material_name,
                                                                                 sub_no=this_sub_no, entry_datetime=now,
                                                                                 entry_operator=operator, work_id=None if work_id == "" else work_id)
            # 各項目の値を格納
            budget_material_data.rev_no = 0
            target_rev_no = 0
            budget_material_data.entry_on_progress_flag = 1
            budget_material_data.lost_flag = 0
            # 取扱物質のレコードを保存
            budget_material_data.save()

            msg = "取扱物質を登録しました！！"

        # 更新時の処理
        elif action_type == 1:
            action = "update"

            # 作業中取扱物質のレコード数を取得
            on_progress_budget_material_num = BudgetMaterial.objects.filter(budget_id=budget_id, material_name=handling_material_name,
                                                                            sub_no=sub_no, entry_on_progress_flag=1,
                                                                            work_id=None if work_id == "" else work_id).count()

            # 完了取扱物質のレコード数を取得
            complete_entry_budget_material_num = BudgetMaterial.objects.filter(budget_id=budget_id, material_name=handling_material_name,
                                                                               sub_no=sub_no, entry_on_progress_flag=0,
                                                                               work_id=None if work_id == "" else work_id).count()

            # 今回のsub_noを設定
            this_sub_no = sub_no

            # 完了取扱物質のレコードがある場合
            if complete_entry_budget_material_num > 0:
                # 最終のrev_noを取得
                budget_material_data = BudgetMaterial.objects.filter(budget_id=budget_id, material_name=handling_material_name,
                                                                     sub_no=sub_no, entry_on_progress_flag=0,
                                                                     work_id=None if work_id == "" else work_id).order_by('-id')[0]
                latest_rev_no = budget_material_data.rev_no
                # 取扱物質レコードを無効化
                budget_material_data.lost_flag = 1
                # 取扱物質のレコードを保存
                budget_material_data.save()

            # 完了取扱物質のレコードがない場合
            else:
                # 最終のrev_noに「-1」を設定
                latest_rev_no = -1

            # 作業中取扱物質のレコードがない場合
            if on_progress_budget_material_num == 0:
                # 「budget_id」、「物質名」、「sub_no」、「登録日時」、「登録者」で新規登録
                BudgetMaterial(budget_id=budget_id, material_name=handling_material_name, sub_no=sub_no, entry_datetime=now,
                               entry_operator=operator, work_id=None if work_id == "" else work_id).save()
                # 「登録日時」、「登録者」で登録した取扱物質のレコードを抽出
                budget_material_data = BudgetMaterial.objects.get(entry_datetime=now, entry_operator=operator,work_id=None if work_id == "" else work_id)
                # 取扱物質の主キーの値を取得
                budget_material_unique_id = budget_material_data.id
                # 「取扱物質の主キー」で登録した取扱物質のレコードを抽出
                budget_material_data = BudgetMaterial.objects.get(id=budget_material_unique_id)
                # budget_material_data.rev_no = latest_rev_no + 1
                # 各項目の値を格納
                budget_material_data.rev_no = budget_rev_no
                target_rev_no = latest_rev_no + 1
                budget_material_data.entry_on_progress_flag = 1
                budget_material_data.lost_flag = 0
                # 取扱物質のレコードを保存
                budget_material_data.save()

            # 作業中取扱物質のレコードがある場合
            else:
                # rev_noを設定
                target_rev_no = budget_rev_no
                # 「budget_id」、「物質名」、「sub_no」、「rev_no」で取扱物質のレコードを抽出
                budget_material_data = BudgetMaterial.objects.get(budget_id=budget_id, material_name=handling_material_name, sub_no=this_sub_no, work_id=None if work_id == "" else work_id)
                # 各項目の値を格納
                budget_material_data.update_datetime = now
                budget_material_data.update_operator = operator
                # 取扱物質のレコードを保存
                budget_material_data.save()

            msg = "取扱物質を更新しました！！"

        # 「budget_id」、「物質名」、「sub_no」、「rev_no」で取扱物質のレコードを抽出
        budget_material_data = BudgetMaterial.objects.get(budget_id=budget_id, material_name=handling_material_name, sub_no=this_sub_no, work_id=None if work_id == "" else work_id)
        # 各項目の値を格納･･･空欄処理、数値化処理を含む
        budget_material_data.chemical_formula = chemical_formula
        budget_material_data.material_cd = handling_material_cd
        if state_str is not "":
            state = int(state_str)
            st = MaterialStateMaster.objects.get(state_id=state,lost_flag=0)
            budget_material_data.state = st
        else:
            budget_material_data.state = None
        if normal_pressure_str is not "":
            budget_material_data.str_normal_pressure = normal_pressure_str
        else:
            budget_material_data.str_normal_pressure = None
        if maximum_pressure_str is not "":
            budget_material_data.maximum_pressure = float(maximum_pressure_str)
        else:
            budget_material_data.maximum_pressure = None
        if minimum_pressure_str is not "":
            budget_material_data.minimum_pressure = float(minimum_pressure_str)
        else:
            budget_material_data.minimum_pressure = None
        if pressure_unit_str is not "":
            pressure_unit = int(pressure_unit_str)
            pu = PressureUnitMaster.objects.get(unit_id=pressure_unit)
            budget_material_data.pressure_unit = pu
        else:
            budget_material_data.pressure_unit = None
        if normal_temperature_str is not "":
            budget_material_data.str_normal_temperature = normal_temperature_str
        else:
            budget_material_data.str_normal_temperature = None
        if maximum_temperature_str is not "":
            budget_material_data.maximum_temperature = float(maximum_temperature_str)
        else:
            budget_material_data.maximum_temperature = None
        if minimum_temperature_str is not "":
            budget_material_data.minimum_temperature = float(minimum_temperature_str)
        else:
            budget_material_data.minimum_temperature = None
        if concentration_str is not "":
            budget_material_data.concentration = float(concentration_str)
        else:
            budget_material_data.concentration = None
        if concentration_unit_str is not "":
            concentration_unit = int(concentration_unit_str)

            cu = ConcentrationUnitMaster.objects.get(unit_id=concentration_unit)
            budget_material_data.concentration_unit = cu
        else:
            budget_material_data.concentration_unit = None
        if pH_str is not "":
            budget_material_data.str_ph =pH_str
        else:
            budget_material_data.str_ph = None
        if viscosity_str is not "":
            budget_material_data.viscosity = float(viscosity_str)
        else:
            budget_material_data.viscosity = None
        if angle_of_repose_str is not "":
            budget_material_data.angle_of_repose = float(angle_of_repose_str)
        else:
            budget_material_data.angle_of_repose = None
        if bulk_specific_gravity_str is not "":
            budget_material_data.str_bulk_specific_gravity = bulk_specific_gravity_str
        else:
            budget_material_data.str_bulk_specific_gravity = None
        if true_specific_gravity_str is not "":
            budget_material_data.str_true_specific_gravity = true_specific_gravity_str
        else:
            budget_material_data.str_true_specific_gravity = None
        if apparent_specific_gravity_str is not "":
            budget_material_data.str_apparent_specific_gravity = apparent_specific_gravity_str
        else:
            budget_material_data.str_apparent_specific_gravity = None

        # if true_specific_gravity_str is not "":
            # budget_material_data.true_specific_gravity = float(true_specific_gravity_str)
        # else:
            # budget_material_data.true_specific_gravity = None
        if particle_size_str is not "":
            budget_material_data.str_particle_size = particle_size_str
        else:
            budget_material_data.str_particle_size = None
        if moisture_str is not "":
            budget_material_data.str_moisture = moisture_str
        else:
            budget_material_data.str_moisture = None
        if work_id is not "":
            budget_material_data.work_id = int(work_id)
        else:
            budget_material_data.work_id = None
        budget_material_data.others = others
        # 取扱物質のレコードを保存
        budget_material_data.save()

        # コメント作成
        comment = "物質名：" + handling_material_name + "、サブNO：" + str(this_sub_no)

        # ログを新規登録
        Log(target='budgetmaterial', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        ary = {
            'sub_no': this_sub_no,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 取扱物質削除処理
@login_required
@require_POST
def handling_material_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        handling_material_id = int(request.POST["handling_material_id"])

        # 対象の取扱物質レコードを取得
        budget_material_data = BudgetMaterial.objects.get(id=handling_material_id,lost_flag=0)
        # 各項目の値を格納
        budget_material_data.lost_flag = 1
        budget_id = budget_material_data.budget_id
        handling_material_name = budget_material_data.material_name
        this_sub_no = budget_material_data.sub_no
        this_budget_id = budget_material_data.budget_id
        action = "delete"

        # 取扱物質のレコードを保存
        budget_material_data.save()

        # コメント作成
        comment = "物質名：" + handling_material_name + "、サブNO：" + str(this_sub_no)

        # ログを新規登録
        Log(target='budgetmaterial', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        msg = "削除しました！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 取扱物質マイマスタへの登録･更新処理
@login_required
@require_POST
def handling_material_my_master_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        action_type = int(request.POST["action_type"])
        handling_material_id = int(request.POST["handling_material_id"])
        budget_id = 0
        handling_material_name = request.POST["handling_material_name"]
        handling_material_cd = request.POST["handling_material_cd"]
        chemical_formula = request.POST["chemical_formula"]
        normal_pressure_str = request.POST["normal_pressure"]
        maximum_pressure_str = request.POST["maximum_pressure"]
        minimum_pressure_str = request.POST["minimum_pressure"]
        pressure_unit_str = request.POST["pressure_unit"]
        normal_temperature_str = request.POST["normal_temperature"]
        maximum_temperature_str = request.POST["maximum_temperature"]
        minimum_temperature_str = request.POST["minimum_temperature"]
        state_str = request.POST["state"]
        concentration_str = request.POST["concentration"]
        concentration_unit_str = request.POST["concentration_unit"]
        pH_str = request.POST["pH"]
        viscosity_str = request.POST["viscosity"]
        angle_of_repose_str = request.POST["angle_of_repose"]
        bulk_specific_gravity_str = request.POST["bulk_specific_gravity"]
        true_specific_gravity_str = request.POST["true_specific_gravity"]
        apparent_specific_gravity_str = request.POST["apparent_specific_gravity"]
        particle_size_str = request.POST["particle_size"]
        moisture_str = request.POST["moisture"]
        others = request.POST["others"]

        # 新規登録時の処理
        if action_type == 0:
            action = "entry"
            # マイマスタに「登録日時」、「登録者」項目に値を入れ新規登録
            MyBudgetMaterialData(entry_datetime=now, entry_operator=operator, lost_flag=0).save()
            # 「登録日時」、「登録者」でマイマスタよりレコード抽出
            budget_material_my_master_data = MyBudgetMaterialData.objects.get(entry_datetime=now, entry_operator=operator,lost_flag=0)
            # マスタの主キーの値を取得
            handling_material_id = budget_material_my_master_data.id
            msg = "取扱物質をマイマスターに登録しました！！"
            # 編集可能FLを「1」(編集可)に
            edit_ok_flag = 1

        # 更新時の処理
        elif action_type == 1:
            # 「主キー」でマイマスタよりレコード抽出し、登録者を取得
            budget_material_my_master_data = MyBudgetMaterialData.objects.get(id=handling_material_id, lost_flag=0)
            entry_operator = budget_material_my_master_data.entry_operator

            # 登録者が共通でない場合の処理
            if entry_operator != "common":
                action = "update"
                msg = "取扱物質をマイマスターで更新しました！！"
                # 編集可能FLを「1」(編集可)に
                edit_ok_flag = 1
            # 登録者が共通者である場合の処理
            else:
                # 編集可能FLを「0」(編集不可)に
                edit_ok_flag = 0
                msg = "共通マスタは変更できません！！"

        # 編集可能な場合の処理
        if edit_ok_flag == 1:

            # 「主キー」でマイマスタよりレコード抽出
            budget_material_my_master_data = MyBudgetMaterialData.objects.get(id=handling_material_id,lost_flag=0)

            # 各項目の値を格納･･･空欄処理、数値化処理を含む
            budget_material_my_master_data.chemical_formula = chemical_formula
            budget_material_my_master_data.material_name = handling_material_name
            budget_material_my_master_data.material_cd = handling_material_cd

            if state_str is not "":
                state = int(state_str)
                st = MaterialStateMaster.objects.get(state_id=state)
                budget_material_my_master_data.state = st
            else:
                budget_material_my_master_data.state = None
            if normal_pressure_str is not "":
                budget_material_my_master_data.str_normal_pressure = normal_pressure_str
            else:
                budget_material_my_master_data.str_normal_pressure = None
            if maximum_pressure_str is not "":
                budget_material_my_master_data.maximum_pressure = float(maximum_pressure_str)
            else:
                budget_material_my_master_data.maximum_pressure = None
            if minimum_pressure_str is not "":
                budget_material_my_master_data.minimum_pressure = float(minimum_pressure_str)
            else:
                budget_material_my_master_data.minimum_pressure = None
            if pressure_unit_str is not "":
                pressure_unit = int(pressure_unit_str)
                pu = PressureUnitMaster.objects.get(unit_id=pressure_unit)
                budget_material_my_master_data.pressure_unit = pu
            else:
                budget_material_my_master_data.pressure_unit = None
            if normal_temperature_str is not "":
                budget_material_my_master_data.str_normal_temperature = normal_temperature_str
            else:
                budget_material_my_master_data.str_normal_temperature = None
            if maximum_temperature_str is not "":
                budget_material_my_master_data.maximum_temperature = float(maximum_temperature_str)
            else:
                budget_material_my_master_data.maximum_temperature = None
            if minimum_temperature_str is not "":
                budget_material_my_master_data.minimum_temperature = float(minimum_temperature_str)
            else:
                budget_material_my_master_data.minimum_temperature = None
            if concentration_str is not "":
                budget_material_my_master_data.concentration = float(concentration_str)
            else:
                budget_material_my_master_data.concentration = None
            if concentration_unit_str is not "":
                concentration_unit = int(concentration_unit_str)
                cu = ConcentrationUnitMaster.objects.get(unit_id=concentration_unit)
                budget_material_my_master_data.concentration_unit = cu
            else:
                budget_material_my_master_data.concentration_unit = None
            if pH_str is not "":
                budget_material_my_master_data.str_ph = pH_str
            else:
                budget_material_my_master_data.str_ph = None
            if viscosity_str is not "":
                budget_material_my_master_data.viscosity = float(viscosity_str)
            else:
                budget_material_my_master_data.viscosity = None
            if angle_of_repose_str is not "":
                budget_material_my_master_data.angle_of_repose = angle_of_repose_str
            else:
                budget_material_my_master_data.angle_of_repose = None

            if bulk_specific_gravity_str is not "":
                budget_material_my_master_data.str_bulk_specific_gravity = bulk_specific_gravity_str
            else:
                budget_material_my_master_data.str_bulk_specific_gravity = None
            if true_specific_gravity_str is not "":
                budget_material_my_master_data.str_true_specific_gravity = true_specific_gravity_str
            else:
                budget_material_my_master_data.str_true_specific_gravity = None
            if apparent_specific_gravity_str is not "":
                budget_material_my_master_data.str_apparent_specific_gravity = apparent_specific_gravity_str
            else:
                budget_material_my_master_data.str_apparent_specific_gravity = None

            if particle_size_str is not "":
                budget_material_my_master_data.str_particle_size = particle_size_str
            else:
                budget_material_my_master_data.str_particle_size = None
            if moisture_str is not "":
                budget_material_my_master_data.str_moisture = moisture_str
            else:
                budget_material_my_master_data.str_moisture = None
            budget_material_my_master_data.others = others
            # マイマスタ取扱物質のレコードを保存
            budget_material_my_master_data.save()

            # コメント作成
            comment = "マスタID：" + str(handling_material_id) + "、物質名：" + handling_material_name

            # ログを新規登録
            Log(target='my_budget_material_data', target_id=handling_material_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 取扱物質マイマスタへの削除処理
@login_required
@require_POST
def handling_material_my_master_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        this_step = int(request.POST["this_step"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]
        handling_material_id = int(request.POST["handling_material_id"])

        # budget_idに「0」･･･仮設定
        budget_id = 0

        # 「主キー」でマイマスタよりレコード抽出し、登録者を取得
        budget_material_my_master_data = MyBudgetMaterialData.objects.get(id=handling_material_id,lost_flag=0)
        entry_operator = budget_material_my_master_data.entry_operator

        # 登録者と作業者が同じ場合の処理
        if entry_operator == operator:
            # 各項目の値を格納
            budget_material_my_master_data.lost_flag = 1
            handling_material_name = budget_material_my_master_data.material_name
            action = "delete"

            # マイマスタ取扱物質のレコードを保存
            budget_material_my_master_data.save()

            # コメント作成
            comment = "マスタID：" + str(handling_material_id) + "、物質名：" + handling_material_name

            # ログを新規登録
            Log(target='my_budget_material_data', target_id=handling_material_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

            msg = "削除しました！！"

        # 登録者と作業者が違う場合の処理
        else:
            msg = "共通マスタは削除できません！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 物質情報マスタ一覧
@require_POST
def handling_material_master_list(request):
    try:
        target_type = request.POST['target_type']
        sql = """
            SELECT fms_materialmaster.*, fms_materialstatemaster.state_name, c_u.unit as c_unit, p_u.unit as p_unit
            FROM ((fms_materialmaster
            LEFT JOIN fms_materialstatemaster ON fms_materialmaster.state_id=fms_materialstatemaster.state_id)
            LEFT JOIN fms_concentrationunitmaster c_u ON fms_materialmaster.concentration_unit_id=c_u.unit_id )
            LEFT JOIN fms_pressureunitmaster p_u ON fms_materialmaster.pressure_unit_id=p_u.unit_id """
        material_master_lists = MaterialMaster.objects.raw(sql)
        material_master_num = material_master_lists.__len__()

        # データ取得元情報に物質情報マスタ一覧を設定
        data_source = "s"

        data = {
            'handling_material_lists': material_master_lists,
            'handling_material_lists_num': material_master_num,
            'data_source': data_source
        }

        if target_type == 'budget':
            return render(request, 'fms/parts/budget/handling_material/handling_material_master_lists.html', data)
        else:
            return render(request, 'fms/parts/work/handling_material/work_handling_material_master_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


