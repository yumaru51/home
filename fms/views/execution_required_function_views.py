import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, BudgetRequiredFunction, AmountUnitMaster
from fms.models import DisplayRequiredItemForFunction, FunctionMaster
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 要求機能登録･更新処理
@login_required
@require_POST
def required_function_entry(request):
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
        this_budget_id = budget_id
        budget_rev_no = int(request.POST["budget_rev_no"])
        required_function = request.POST["required_function"]
        budget_required_function_id = int(request.POST["budget_required_function_id"])
        material = request.POST["material"]
        sub_no_str = request.POST["sub_no"]
        # 取得したsub_noの空欄処理(空欄時は「1」を設定)
        if sub_no_str is not "":
            sub_no = int(sub_no_str)
        else:
            sub_no = 1
        required_material_capacity_str = request.POST["required_material_capacity"]
        material_capacity_unit_str = request.POST["material_capacity_unit"]
        required_cooling_temperature_str = request.POST["required_cooling_temperature"]
        required_heating_temperature_str = request.POST["required_heating_temperature"]
        temperature_str = request.POST["temperature"]
        required_compress_pressure_str = request.POST["required_compress_pressure"]
        required_vacuum_pressure_str = request.POST["required_vacuum_pressure"]
        pressure_str = request.POST["pressure"]
        pressure_unit_str = request.POST["pressure_unit"]
        required_moisture_str = request.POST["required_moisture"]
        required_concentration_str = request.POST["required_concentration"]
        concentration_unit_str = request.POST["concentration_unit"]
        required_particle_size_str = request.POST["required_particle_size"]
        required_transfer_length_str = request.POST["required_transfer_length"]
        required_others_str = request.POST["required_others"]
        # リレーションの関係で、対応するマスタのレコードを抽出
        rf = FunctionMaster.objects.get(function_cd=required_function, lost_flag=0)
        # rf = FunctionMaster.objects.get(function_name=required_function)

        # 新規登録時の処理
        if action_type == 0:
            action = "entry"

            # 「budget_id」、「required_function」で登録済のレコード数を取得
            budget_required_function_num = BudgetRequiredFunction.objects.filter(budget_id=budget_id, required_function=rf).count()
            # 登録済のレコードがある場合
            if budget_required_function_num > 0:
                # 「budget_id」、「required_function」で登録済のデータ(最新の1件)を取得し、最終のsub_noを取得
                budget_required_function_data = BudgetRequiredFunction.objects.filter(budget_id=budget_id, required_function=rf).order_by('-sub_no')[0]
                latest_sub_no = budget_required_function_data.sub_no
            # 登録済のレコードがない場合
            else:
                # 最終のsub_noに「0」を設定
                latest_sub_no = 0

            # 今回のsub_noを設定(最終のsub_no+1)
            this_sub_no = latest_sub_no + 1

            # 「budget_id」、「required_function」、「sub_no」、「登録日時」、「登録者」でレコードを抽出、あれば取得、なければ新規登録･･･ないはずなので新規登録
            budget_required_function_data, created = BudgetRequiredFunction.objects.get_or_create(budget_id=budget_id, required_function=rf, sub_no=this_sub_no, entry_datetime=now, entry_operator=operator)

            # 各項目の値を格納
            budget_required_function_data.rev_no = 0
            target_rev_no = 0
            budget_required_function_data.entry_on_progress_flag = 1
            budget_required_function_data.lost_flag = 0
            # 要求機能のレコードを保存
            budget_required_function_data.save()

            msg = "要求機能を登録しました！！"

        # 更新時の処理
        elif action_type == 1:
            action = "update"

            # 作業中の要求機能のレコード件数を取得
            on_progress_budget_required_function_num = BudgetRequiredFunction.objects.filter(budget_id=budget_id, required_function=rf, sub_no=sub_no, entry_on_progress_flag=1).count()

            # 完了（作業中でない）の要求機能のレコード件数を取得
            complete_entry_budget_required_function_num = BudgetRequiredFunction.objects.filter(budget_id=budget_id, required_function=rf, sub_no=sub_no, entry_on_progress_flag=0).count()

            # sub_noの変数名変更(sub_no→this_sub_no)
            this_sub_no = sub_no

            # 完了の要求仕様のレコードがある場合の処理
            if complete_entry_budget_required_function_num > 0:
                # 完了の要求機能のデータ(最新のもの)を取得
                budget_required_function_data = BudgetRequiredFunction.objects.filter(budget_id=budget_id, required_function=rf, sub_no=sub_no, entry_on_progress_flag=0).order_by('-id')[0]
                # 最終のrev_noを取得･･･不要？
                latest_rev_no = budget_required_function_data.rev_no
                # レコードの無効化(lost_flag = 1)
                budget_required_function_data.lost_flag = 1
                # 要求機能のレコードを保存
                budget_required_function_data.save()

            # 完了の要求機能のレコードがない場合の処理
            else:
                # 最終のrev_noに「-1」を設定･･･不要?
                latest_rev_no = -1

            # 作業中の要求機能のレコードがない場合の処理
            if on_progress_budget_required_function_num == 0:
                # 「budget_id」、「required_function」、「sub_no」、「登録日時」、「登録者」の値で要求機能に新規登録
                BudgetRequiredFunction(budget_id=budget_id, required_function=rf, sub_no=sub_no, entry_datetime=now, entry_operator=operator).save()
                # 「登録日時」、「登録者」で登録したレコードを抽出
                budget_required_function_data = BudgetRequiredFunction.objects.get(entry_datetime=now, entry_operator=operator)
                # 主キーの値を取得
                budget_required_function_unique_id = budget_required_function_data.id
                # 主キーの値で登録したレコードを抽出
                budget_required_function_data = BudgetRequiredFunction.objects.get(id=budget_required_function_unique_id)
                # 各項目の値を格納
                budget_required_function_data.rev_no = budget_rev_no
                target_rev_no = budget_rev_no
                budget_required_function_data.entry_on_progress_flag = 1
                budget_required_function_data.lost_flag = 0
                # 要求機能のレコードを保存
                budget_required_function_data.save()
            # 作業中の要求機能のレコードがある場合の処理
            else:
                # 対象のrev_noに予算情報のrev_noを設定
                target_rev_no = budget_rev_no
                # 「budget_id」、「required_function」、「sub_no」、「rev_no」でレコードを抽出
                budget_required_function_data = BudgetRequiredFunction.objects.get(budget_id=budget_id, required_function=rf, sub_no=this_sub_no, lost_flag=0)
                # 各項目の値を格納
                budget_required_function_data.update_datetime = now
                budget_required_function_data.update_operator = operator
                # 要求機能のレコードを保存
                budget_required_function_data.save()

            msg = "要求機能を更新しました！！"

        # 「budget_id」、「required_function」、「sub_no」、「rev_no」でレコードを抽出
        budget_required_function_data = BudgetRequiredFunction.objects.get(budget_id=budget_id, required_function=rf, sub_no=this_sub_no, lost_flag=0)
        # 主キーの値を取得
        budget_required_function_id = budget_required_function_data.id
        # 各項目の値を格納･･･空欄処理、数値化処理を含む
        budget_required_function_data.material = material
        if required_material_capacity_str is not "":
            budget_required_function_data.required_material_capacity = float(required_material_capacity_str)
        else:
            budget_required_function_data.required_material_capacity = None
        if material_capacity_unit_str is not "":
            material_capacity_unit = int(material_capacity_unit_str)
            au = AmountUnitMaster.objects.get(unit_id=material_capacity_unit)
            budget_required_function_data.material_capacity_unit = au
        else:
            budget_required_function_data.pressure_unit = None
        if required_cooling_temperature_str is not "":
            budget_required_function_data.required_cooling_temperature = float(required_cooling_temperature_str)
        else:
            budget_required_function_data.required_cooling_temperature = None
        if required_heating_temperature_str is not "":
            budget_required_function_data.required_heating_temperature = float(required_heating_temperature_str)
        else:
            budget_required_function_data.required_heating_temperature = None
        if temperature_str is not "":
            budget_required_function_data.temperature = float(temperature_str)
        else:
            budget_required_function_data.temperature = None
        if required_compress_pressure_str is not "":
            budget_required_function_data.required_compress_pressure = float(required_compress_pressure_str)
        else:
            budget_required_function_data.required_compress_pressure = None
        if required_vacuum_pressure_str is not "":
            budget_required_function_data.required_vacuum_pressure = float(required_vacuum_pressure_str)
        else:
            budget_required_function_data.required_vacuum_pressure = None
        if pressure_str is not "":
            budget_required_function_data.pressure = float(pressure_str)
        else:
            budget_required_function_data.pressure = None
        if pressure_unit_str is not "":
            pressure_unit = int(pressure_unit_str)
            pu = PressureUnitMaster.objects.get(unit_id=pressure_unit)
            budget_required_function_data.pressure_unit = pu
        else:
            budget_required_function_data.pressure_unit = None
        if required_moisture_str is not "":
            budget_required_function_data.required_moisture = float(required_moisture_str)
        else:
            budget_required_function_data.required_moisture = None
        if required_concentration_str is not "":
            budget_required_function_data.required_concentration = float(required_concentration_str)
        else:
            budget_required_function_data.required_concentration = None
        if concentration_unit_str is not "":
            concentration_unit = int(concentration_unit_str)

            cu = ConcentrationUnitMaster.objects.get(unit_id=concentration_unit)
            budget_required_function_data.concentration_unit = cu
        else:
            budget_required_function_data.concentration_unit = None

        if required_particle_size_str is not "":
            budget_required_function_data.required_particle_size = float(required_particle_size_str)
        else:
            budget_required_function_data.required_particle_size = None

        if required_transfer_length_str is not "":
            budget_required_function_data.required_transfer_length = float(required_transfer_length_str)
        else:
            budget_required_function_data.required_transfer_length = None
        budget_required_function_data.required_others = required_others_str
        # 要求機能のレコードを保存
        budget_required_function_data.save()

        # コメント作成
        comment = "要求機能：" + required_function + "、サブNO：" + str(this_sub_no)

        # ログを新規登録
        Log(target='budget_required_function', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        ary = {
            'budget_required_function_id': budget_required_function_id,
            'sub_no': this_sub_no,
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 要求機能削除処理
@login_required
@require_POST
def required_function_delete(request):
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
        budget_required_function_id = int(request.POST["budget_required_function_id"])

        # 主キーの値で要求機能のレコードを抽出
        budget_required_function_data = BudgetRequiredFunction.objects.get(id=budget_required_function_id)
        # レコードの無効化(lost_flag = 1)
        budget_required_function_data.lost_flag = 1
        # 各項目の値取得･･･ログのため
        budget_id = budget_required_function_data.budget_id
        required_function = budget_required_function_data.required_function
        this_sub_no = budget_required_function_data.sub_no
        this_budget_id = budget_required_function_data.budget_id
        action = "delete"

        # 要求機能のレコードを保存
        budget_required_function_data.save()

        # 要求機能名を取得
        function_data = FunctionMaster.objects.get(function_name=required_function)
        function_name = function_data.function_name

        # コメント作成
        comment = "要求機能：" + function_name + "、サブNO：" + str(this_sub_no)

        # ログを新規登録
        Log(target='budget_required_function', target_id=this_budget_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        msg = "削除しました！！"

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 要求機能情報表示処理
@login_required
@require_POST
def execution_required_function_data_info(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = int(request.POST["budget_id"])
        work_id = int(request.POST["work_id"])
        budget_required_function_id = int(request.POST["budget_required_function_id"])
        new_step = int(request.POST['new_step'])
        select_function = request.POST['select_function']

        # 予算情報の新規追加でない(既に存在する予算情報)場合の処理
        if target_id != 0:
            # 変数の置き換え(target_id→budget_id)
            budget_id = target_id
            # 現在のstepを取得
            present_step_data = Progress.objects.get(target_id=budget_id, target='budget')
            present_step = present_step_data.present_step
        # 予算情報の新規追加の場合の処理
        else:
            # 現在のstepにnew_stepを設定
            present_step = new_step

        # 登録済の要求機能がすでにある場合の処理
        if budget_required_function_id != 0:
            # 主キーの値でレコードを抽出
            budget_required_function_data = BudgetRequiredFunction.objects.get(id=budget_required_function_id)
            # 各項目の値を取得･･･空欄処理を含む
            select_function = budget_required_function_data.required_function
            if budget_required_function_data.required_function is None:
                required_function = ""
            else:
                required_function = budget_required_function_data.required_function
            if budget_required_function_data.budget_id is None:
                budget_id = ""
            else:
                budget_id = budget_required_function_data.budget_id
            if budget_required_function_data.rev_no is None:
                rev_no = 0
            else:
                rev_no = budget_required_function_data.rev_no
            if budget_required_function_data.sub_no is None:
                sub_no = ""
            else:
                sub_no = budget_required_function_data.sub_no
            if budget_required_function_data.material is None:
                material = ""
            else:
                material = budget_required_function_data.material
            if budget_required_function_data.required_material_capacity is None:
                required_material_capacity = ""
            else:
                required_material_capacity = budget_required_function_data.required_material_capacity
            material_capacity_unit_mane = budget_required_function_data.material_capacity_unit
            if material_capacity_unit_mane is not None:
                material_capacity_unit_data = AmountUnitMaster.objects.get(unit=material_capacity_unit_mane)
                material_capacity_unit = material_capacity_unit_data.unit_id
            else:
                material_capacity_unit = ""
            if budget_required_function_data.required_cooling_temperature is None:
                required_cooling_temperature = ""
            else:
                required_cooling_temperature = budget_required_function_data.required_cooling_temperature
            if budget_required_function_data.required_heating_temperature is None:
                required_heating_temperature = ""
            else:
                required_heating_temperature = budget_required_function_data.required_heating_temperature
            if budget_required_function_data.temperature is None:
                temperature = ""
            else:
                temperature = budget_required_function_data.temperature
            if budget_required_function_data.required_compress_pressure is None:
                required_compress_pressure = ""
            else:
                required_compress_pressure = budget_required_function_data.required_compress_pressure
            if budget_required_function_data.required_vacuum_pressure is None:
                required_vacuum_pressure = ""
            else:
                required_vacuum_pressure = budget_required_function_data.required_vacuum_pressure
            if budget_required_function_data.pressure is None:
                pressure = ""
            else:
                pressure = budget_required_function_data.pressure
            pressure_unit_mane = budget_required_function_data.pressure_unit
            if pressure_unit_mane is not None:
                pressure_unit_data = PressureUnitMaster.objects.get(unit=pressure_unit_mane)
                pressure_unit = pressure_unit_data.unit_id
            else:
                pressure_unit = ""
            if budget_required_function_data.required_moisture is None:
                required_moisture = ""
            else:
                required_moisture = budget_required_function_data.required_moisture
            if budget_required_function_data.required_concentration is None:
                required_concentration = ""
            else:
                required_concentration = budget_required_function_data.required_concentration
            concentration_unit_mane = budget_required_function_data.concentration_unit
            if concentration_unit_mane is not None:
                concentration_unit_data = ConcentrationUnitMaster.objects.get(unit=concentration_unit_mane)
                concentration_unit = concentration_unit_data.unit_id
            else:
                concentration_unit = ""
            if budget_required_function_data.required_particle_size is None:
                required_particle_size = ""
            else:
                required_particle_size = budget_required_function_data.required_particle_size
            if budget_required_function_data.required_transfer_length is None:
                required_transfer_length = ""
            else:
                required_transfer_length = budget_required_function_data.required_transfer_length
            if budget_required_function_data.required_others is None:
                required_others = ""
            else:
                required_others = budget_required_function_data.required_others
            # 無効化した(変更前)の要求機能のレコード数を取得
            old_budget_required_function_data_num = BudgetRequiredFunction.objects.filter(budget_id=budget_id, sub_no=sub_no, required_function=required_function, lost_flag=1).count()

            # 予算情報の新規追加でない(既に存在する予算情報)場合の処理
            if work_id != 0:
                # 変数の置き換え(target_id→budget_id)
                budget_id = target_id
                # 現在のstepを取得
                present_step_data = Progress.objects.get(target_id=work_id, target='work')
                work_present_step = present_step_data.present_step

                # workテーブルがデータ編集機能要否判定
                work_edit_action_num = 0
                # 対象stepで「work」がデータ更新対象か確認
                work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=work_present_step, target_table='work').count()

                if work_edit_action_num > 0:
                    work_entry_pb_disp_flag = 1
                else:
                    work_entry_pb_disp_flag = 0
            else:
                work_entry_pb_disp_flag = 0

        # 登録済の要求機能がない(新た追加する)場合の処理
        else:
            # 各項目を設定
            budget_id = ""
            rev_no = 0
            # required_function = ""
            select_function = "すべて"
            sub_no = ""
            material = ""
            required_material_capacity = ""
            material_capacity_unit = ""
            required_cooling_temperature = ""
            required_heating_temperature = ""
            temperature = ""
            required_compress_pressure = ""
            required_vacuum_pressure = ""
            pressure = ""
            pressure_unit = ""
            required_moisture = ""
            required_concentration = ""
            concentration_unit = ""
            required_particle_size = ""
            required_transfer_length = ""
            required_others = ""
            old_budget_required_function_data_num = 0
            budget_required_function_data = ""
            work_entry_pb_disp_flag = 0

        # 濃度単位選択のリストソースの情報を取得
        concentration_unit_list = ConcentrationUnitMaster.objects.filter(lost_flag=0).all()

        # 圧力単位選択のリストソースの情報を取得
        pressure_unit_list = PressureUnitMaster.objects.filter(lost_flag=0).all()

        # 容量単位選択のリストソースの情報を取得
        amount_unit_list = AmountUnitMaster.objects.filter(lost_flag=0).all()

        # 要求機能選択のソースとなる一覧取得
        function_list = FunctionMaster.objects.filter(lost_flag=0)

        #仮の値･･･???

        # 要求機能の機能CDを機能マスタから取得
        function_data = FunctionMaster.objects.get(function_name=select_function)
        select_function_cd = function_data.function_cd
        # 変数置き換え(select_function→required_function)
        required_function = select_function_cd

        # 要求機能画面で入力項目表示/非表示情報取得
        display_required_item_for_function_list = DisplayRequiredItemForFunction.objects.get(required_function=select_function_cd)

        # 無効化した(変更前)の要求機能のレコードがある場合の処理
        if old_budget_required_function_data_num > 0:
            # (無効化した)1つ前の要求機能の情報取得
            old_budget_required_function_data = BudgetRequiredFunction.objects.filter(budget_id=budget_id, sub_no=sub_no, required_function=required_function, lost_flag=1).all().order_by('-id')[0]
        else:
            old_budget_required_function_data = ""

        data = {
            'display_required_item_for_function_list': display_required_item_for_function_list,
            'budget_required_function_data': budget_required_function_data,
            'old_budget_required_function_data_num': old_budget_required_function_data_num,
            'old_budget_required_function_data': old_budget_required_function_data,
            'budget_required_function_id': budget_required_function_id,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'required_function': required_function,
            'sub_no': sub_no,
            'material': material,
            'required_material_capacity': required_material_capacity,
            'material_capacity_unit': material_capacity_unit,
            'required_cooling_temperature': required_cooling_temperature,
            'required_heating_temperature': required_heating_temperature,
            'temperature': temperature,
            'required_compress_pressure': required_compress_pressure,
            'required_vacuum_pressure': required_vacuum_pressure,
            'pressure': pressure,
            'pressure_unit': pressure_unit,
            'required_moisture': required_moisture,
            'required_concentration': required_concentration,
            'concentration_unit': concentration_unit,
            'required_particle_size': required_particle_size,
            'required_transfer_length': required_transfer_length,
            'required_others': required_others,
            'work_entry_pb_disp_flag': work_entry_pb_disp_flag,
            'concentration_unit_list': concentration_unit_list,
            'pressure_unit_list': pressure_unit_list,
            'amount_unit_list': amount_unit_list,
            'function_list': function_list

        }

        # データ編集機能要否判定
        budget_required_function_edit_action_num = 0
        # 対象stepで「budget_required_function」がデータ更新対象か確認
        budget_required_function_edit_action_num = budget_required_function_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='budget_required_function').count()

        edit_flag = 0
        if budget_required_function_edit_action_num > 0:
            edit_flag = 1

        # if edit_flag == 1:
        #     return render(request, 'fms/parts/budget/required_function/required_function_edit.html', data)
        #
        # else:
        return render(request, 'fms/parts/execution/execution_required_function/execution_required_function_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 詳細仕様入力ページに要求機能を表示させる処理
@login_required
@require_POST
def execution_required_function_data_info_2(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id = int(request.POST["budget_id"])
        budget_required_function_id = int(request.POST["budget_required_function_id"])
        new_step = int(request.POST['new_step'])
        select_function = request.POST['select_function']

        # 予算情報の新規追加でない(既に存在する予算情報)場合の処理
        if target_id != 0:
            # 変数の置き換え(target_id→budget_id)
            budget_id = target_id
            present_step_data = Progress.objects.get(target_id=budget_id, target='budget')
            present_step = present_step_data.present_step
        # 予算情報の新規追加の場合の処理
        else:
            # 現在のstepにnew_stepを設定
            present_step = new_step

        # 登録済の要求機能がすでにある場合の処理
        if budget_required_function_id != 0:
            # 主キーの値でレコードを抽出
            budget_required_function_data = BudgetRequiredFunction.objects.get(id=budget_required_function_id)
            # 各項目の値を取得･･･空欄処理を含む
            select_function = budget_required_function_data.required_function.function_cd
            if budget_required_function_data.required_function is None:
                required_function = ""
            else:
                required_function = budget_required_function_data.required_function
            if budget_required_function_data.budget_id is None:
                budget_id = ""
            else:
                budget_id = budget_required_function_data.budget_id
            if budget_required_function_data.rev_no is None:
                rev_no = 0
            else:
                rev_no = budget_required_function_data.rev_no
            # required_function = budget_required_function_data.required_function
            if budget_required_function_data.sub_no is None:
                sub_no = ""
            else:
                sub_no = budget_required_function_data.sub_no
            if budget_required_function_data.material is None:
                material = ""
            else:
                material = budget_required_function_data.material
            if budget_required_function_data.required_material_capacity is None:
                required_material_capacity = ""
            else:
                required_material_capacity = budget_required_function_data.required_material_capacity
            material_capacity_unit_mane = budget_required_function_data.material_capacity_unit
            if material_capacity_unit_mane is not None:
                material_capacity_unit_data = AmountUnitMaster.objects.get(unit=material_capacity_unit_mane)
                material_capacity_unit = material_capacity_unit_data.unit_id
            else:
                material_capacity_unit = ""
            if budget_required_function_data.required_cooling_temperature is None:
                required_cooling_temperature = ""
            else:
                required_cooling_temperature = budget_required_function_data.required_cooling_temperature
            if budget_required_function_data.required_heating_temperature is None:
                required_heating_temperature = ""
            else:
                required_heating_temperature = budget_required_function_data.required_heating_temperature
            if budget_required_function_data.temperature is None:
                temperature = ""
            else:
                temperature = budget_required_function_data.temperature
            if budget_required_function_data.required_compress_pressure is None:
                required_compress_pressure = ""
            else:
                required_compress_pressure = budget_required_function_data.required_compress_pressure
            if budget_required_function_data.required_vacuum_pressure is None:
                required_vacuum_pressure = ""
            else:
                required_vacuum_pressure = budget_required_function_data.required_vacuum_pressure
            if budget_required_function_data.pressure is None:
                pressure = ""
            else:
                pressure = budget_required_function_data.pressure
            pressure_unit_mane = budget_required_function_data.pressure_unit
            if pressure_unit_mane is not None:
                pressure_unit_data = PressureUnitMaster.objects.get(unit=pressure_unit_mane)
                pressure_unit = pressure_unit_data.unit_id
            else:
                pressure_unit = ""
            if budget_required_function_data.required_moisture is None:
                required_moisture = ""
            else:
                required_moisture = budget_required_function_data.required_moisture
            if budget_required_function_data.required_concentration is None:
                required_concentration = ""
            else:
                required_concentration = budget_required_function_data.required_concentration
            concentration_unit_mane = budget_required_function_data.concentration_unit
            if concentration_unit_mane is not None:
                concentration_unit_data = ConcentrationUnitMaster.objects.get(unit=concentration_unit_mane)
                concentration_unit = concentration_unit_data.unit_id
            else:
                concentration_unit = ""
            if budget_required_function_data.required_particle_size is None:
                required_particle_size = ""
            else:
                required_particle_size = budget_required_function_data.required_particle_size
            if budget_required_function_data.required_transfer_length is None:
                required_transfer_length = ""
            else:
                required_transfer_length = budget_required_function_data.required_transfer_length
            if budget_required_function_data.required_others is None:
                required_others = ""
            else:
                required_others = budget_required_function_data.required_others
            # 無効化した(変更前)の要求機能のレコード数を取得
            old_budget_required_function_data_num = BudgetRequiredFunction.objects.filter(budget_id=budget_id, sub_no=sub_no, required_function=required_function, lost_flag=1).count()

        # 登録済の要求機能がない(新た追加する)場合の処理
        else:
            # 各項目を設定
            budget_id = ""
            rev_no = 0
            # required_function = """"
            sub_no = ""
            material = ""
            required_material_capacity = ""
            material_capacity_unit = ""
            required_cooling_temperature = ""
            required_heating_temperature = ""
            temperature = ""
            required_compress_pressure = ""
            required_vacuum_pressure = ""
            pressure = ""
            pressure_unit = ""
            required_moisture = ""
            required_concentration = ""
            concentration_unit = ""
            required_particle_size = ""
            required_transfer_length = ""
            required_others = ""
            old_budget_required_function_data_num = 0
            budget_required_function_data = ""

        # 濃度単位選択のリストソースの情報を取得
        concentration_unit_list = ConcentrationUnitMaster.objects.filter(lost_flag=0).all()

        # 圧力単位選択のリストソースの情報を取得
        pressure_unit_list = PressureUnitMaster.objects.filter(lost_flag=0).all()

        # 容量単位選択のリストソースの情報を取得
        amount_unit_list = AmountUnitMaster.objects.filter(lost_flag=0).all()

        #仮の値･･･???

        # 要求機能の機能名を機能マスタから取得
        function_data = FunctionMaster.objects.get(function_cd=select_function)
        select_function_cd = function_data.function_cd
        required_function = function_data.function_name

        # 要求機能画面で入力項目表示/非表示情報取得
        display_required_item_for_function_list = DisplayRequiredItemForFunction.objects.get(required_function=select_function_cd)

        # 無効化した(変更前)の要求機能のレコードがある場合の処理
        if old_budget_required_function_data_num > 0:
            # (無効化した)1つ前の要求機能の情報取得
            old_budget_required_function_data = BudgetRequiredFunction.objects.filter(budget_id=budget_id, sub_no=sub_no, required_function=required_function, lost_flag=1).all().order_by('-id')[0]
        else:
            old_budget_required_function_data = ""

        data = {
            'display_required_item_for_function_list': display_required_item_for_function_list,
            'budget_required_function_data': budget_required_function_data,
            'old_budget_required_function_data_num': old_budget_required_function_data_num,
            'old_budget_required_function_data': old_budget_required_function_data,
            'budget_required_function_id': budget_required_function_id,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'required_function': required_function,
            'sub_no': sub_no,
            'material': material,
            'required_material_capacity': required_material_capacity,
            'material_capacity_unit': material_capacity_unit,
            'required_cooling_temperature': required_cooling_temperature,
            'required_heating_temperature': required_heating_temperature,
            'temperature': temperature,
            'required_compress_pressure': required_compress_pressure,
            'required_vacuum_pressure': required_vacuum_pressure,
            'pressure': pressure,
            'pressure_unit': pressure_unit,
            'required_moisture': required_moisture,
            'required_concentration': required_concentration,
            'concentration_unit': concentration_unit,
            'required_particle_size': required_particle_size,
            'required_transfer_length': required_transfer_length,
            'required_others': required_others,
            # 'work_entry_pb_disp_flag': work_entry_pb_disp_flag,･･･削除予定
            'concentration_unit_list': concentration_unit_list,
            'pressure_unit_list': pressure_unit_list,
            'amount_unit_list': amount_unit_list

        }

        return render(request, 'fms/parts/execution/execution_required_function/execution_required_function_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 登録済の要求機能の表示処理
@require_POST
def execution_required_function_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        target_id_str = request.POST['target_id']
        target_id = int(target_id_str)

        # 対象予算idに対する登録済要求機能のレコード数取得
        required_function_lists_num = BudgetRequiredFunction.objects.filter(budget_id=target_id, lost_flag=0).count()

        # 対象予算idに対する登録済要求機能のデータ取得
        sql = """ SELECT fms_budgetrequiredfunction.*, c_u.unit as c_unit """
        sql = sql + """ , p_u.unit as p_unit  , a_u.unit as a_unit"""
        sql = sql + """ FROM ((fms_budgetrequiredfunction """
        sql = sql + """ LEFT JOIN fms_concentrationunitmaster c_u ON fms_budgetrequiredfunction.concentration_unit_id=c_u.unit_id )"""
        sql = sql + """ LEFT JOIN fms_pressureunitmaster p_u ON fms_budgetrequiredfunction.pressure_unit_id=p_u.unit_id )"""
        sql = sql + """ LEFT JOIN fms_amountunitmaster a_u ON fms_budgetrequiredfunction.pressure_unit_id=a_u.unit_id """
        sql = sql + """ WHERE fms_budgetrequiredfunction.budget_id=""" + target_id_str + """ AND fms_budgetrequiredfunction.lost_flag=0 """

        required_function_lists = BudgetRequiredFunction.objects.all().raw(sql)

        data = {
            'required_function_lists': required_function_lists,
            'required_function_lists_num': required_function_lists_num
        }

        return render(request, 'fms/parts/execution/execution_required_function/execution_required_function_lists.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise




