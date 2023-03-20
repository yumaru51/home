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
from fms.views.heat_exchange_spec_views import heat_exchange_data_info
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 詳細仕様情報表示処理
# @login_required
@require_POST
def template_function_data_info(request):
    try:
        # JSからのPOST引数を取得・・・空欄処理、数値項目は数値に変換(int関数)
        target_work_id_str = request.POST["work_id"]
        if target_work_id_str == "":
            target_work_id = 0
        else:
            target_work_id = int(request.POST["work_id"])
        if target_work_id != 0:
            target_work_rev_no = int(request.POST["work_rev_no"])
        else:
            target_work_rev_no = 0
        template_function_id = int(request.POST["template_function_id"])
        this_step = int(request.POST['this_step'])
        select_function = request.POST['choice_function']
        eqpt_tp = request.POST['eqpt_tp']

        # 変数宣言･･･初期値(空欄)設定
        edit_url = ""
        info_url = ""

        # 選択した(JSからの引数)機能CDに対するレコード数を取得
        function_data_num = FunctionMaster.objects.filter(function_cd=select_function).count()

        # 選択した(JSからの引数)機能CDに対するレコードがない場合･･･マスタに未登録の機能を選択
        if function_data_num == 0:
            # 選択した(JSからの引数)機能名に対する機能CDを取得
            function_data = FunctionMaster.objects.get(function_name=select_function)
            select_function = function_data.function_cd

        # 選択した機能CDが「EX」(熱交)の場合の処理
        if select_function == "EX":
            # 「target_work_id」、「target_work_rev_no」、「template_function_id」、「this_step」、「select_function」、「eqpt_tp」を引数とし、「heat_exchange_spec_views.py」の「heat_exchange_data_info」関数を呼び出し
            template_data = heat_exchange_data_info(target_work_id, target_work_rev_no, template_function_id, this_step, select_function, eqpt_tp)
            # heat_exchange_data_info」関数から受け取ったデータを格納
            data = template_data['dict_data']
            edit_url = template_data['edit_url']
            info_url = template_data['info_url']

        # データ編集機能要否判定
        work_spec_edit_action_num = 0
        # 対象stepで「work_spec」がデータ更新対象か確認
        work_spec_edit_action_num = work_spec_edit_action_num + DataEntryStepMaster.objects.filter(step_id=this_step, target_table='work_spec').count()

        edit_flag = 0
        if work_spec_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, edit_url, data)

        else:
            return render(request, info_url, data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

