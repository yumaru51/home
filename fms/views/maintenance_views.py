# インポート
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
# modelをインポート
from fms.models import MaintenanceCostCenterMaster
from gcsystem.models import AccountCodeMaster, InstructionNoMaster, CostCenterMaster
# 共通関数をインポート
from fms.views.common_def_views import output_log_exception, get_department_person_option_list


# 部署をキーに、原価センタなどの候補リストを取得する
def get_maintenance_gc_data_list(department):

    # 選択した部署に所属する工程マスタを取得
    maintenance_gc_list = MaintenanceCostCenterMaster.objects.filter(lost_flag=0, department=department).order_by('-year')
    # 各コードリスト化
    cost_center_cd_list = [d.cost_center for d in maintenance_gc_list]
    instruction_no_cd_list = [d.instruction_no for d in maintenance_gc_list]
    account_code_cd_list = [d.account_code for d in maintenance_gc_list]

    # 原価センター候補リストを取得
    cost_center_list = CostCenterMaster.objects.filter(原価センタ__in=cost_center_cd_list)

    # 指図書マスター候補リストを取得(新しい年度を上に表示するために、テキスト短の降順で取得)
    instruction_no_list = InstructionNoMaster.objects.filter(指図書コード__in=instruction_no_cd_list).order_by('-テキスト短')

    # 勘定コード候補リストを取得
    account_code_list = AccountCodeMaster.objects.filter(勘定コード__in=account_code_cd_list)

    data = {
        'maintenance_gc_list': maintenance_gc_list,
        'instruction_no_list': instruction_no_list,
        'cost_center_list': cost_center_list,
        'account_code_list': account_code_list,
    }

    return data


# 特定部署の指図書コードなどのオプションリストを取得
def get_maintenance_option_list(department, sel_cost_center_cd='', sel_instruction_no='', sel_account_code=''):

    instruction_no_option_list = ''
    cost_center_option_list = ''
    account_code_option_list = ''
    person_lists = ''
    if department is not None:
        gc_data = get_maintenance_gc_data_list(department)
        maintenance_gc_list = gc_data['maintenance_gc_list']
        cost_center_list = gc_data['cost_center_list']
        instruction_no_list = gc_data['instruction_no_list']
        account_code_list = gc_data['account_code_list']

        # 注意:画面の表示は各項目の前後の空白を除去(strip)して表示するが、選択結果のvalueはそのままマスタの値を用いる
        cost_center_option_list = '<option value=""></option>'
        for cost_center in cost_center_list:
            cost_center_option_list += '<option value="' + cost_center.原価センタ + '" '
            cost_center_option_list += 'data-filter_key="' + cost_center.原価センタ.strip() + '：' + cost_center.原価センタテキスト.strip() + '" '
            if cost_center.原価センタ.strip() == sel_cost_center_cd.strip():
                cost_center_option_list += ' selected'
            cost_center_option_list += '>'
            cost_center_option_list += cost_center.原価センタ.strip() + '：' + cost_center.原価センタテキスト.strip() + '</option>'

        instruction_no_option_list = '<option value=""></option>'
        for instruction_no in instruction_no_list:
            maintenance_gc_data_list = maintenance_gc_list.filter(instruction_no=instruction_no.指図書コード.strip())
            cost_center_cd_list = [d.cost_center for d in maintenance_gc_data_list]
            instruction_no_option_list += '<option value="' + instruction_no.指図書コード + '" '
            instruction_no_option_list += 'data-filter_key="' + str(cost_center_cd_list) + '" '
            if instruction_no.指図書コード.strip() == sel_instruction_no.strip():
                instruction_no_option_list += ' selected'
            instruction_no_option_list += '>'
            instruction_no_option_list += instruction_no.指図書コード.strip() + '：' + instruction_no.テキスト短.strip() + '</option>'

        account_code_option_list = '<option value=""></option>'
        for account_code in account_code_list:
            maintenance_gc_data_list = maintenance_gc_list.filter(account_code=account_code.勘定コード.strip())
            instruction_no_list = [d.instruction_no for d in maintenance_gc_data_list]
            account_code_option_list += '<option value="' + account_code.勘定コード + '" '
            account_code_option_list += 'data-filter_key="' + str(instruction_no_list) + '"'
            if account_code.勘定コード.strip() == sel_account_code.strip():
                account_code_option_list += ' selected'
            account_code_option_list += '>'
            account_code_option_list += account_code.勘定コード.strip() + '：' + account_code.テキスト短.strip() + '</option>'

        person_lists = get_department_person_option_list(department)

    data = {
        'person_lists': person_lists,
        'cost_center_option_list': cost_center_option_list,
        'instruction_no_option_list': instruction_no_option_list,
        'account_code_option_list': account_code_option_list,
    }

    return data


# 部署情報変更時、候補リストを取得
@login_required
@require_POST
def maintenance_change_department(request):
    try:
        order_department = request.POST['order_department']
        data = get_maintenance_option_list(order_department)
        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 原価センタの取得（テキスト取得用）
def get_maintenance_cost_center(cost_center_cd):
    cost_center_list = CostCenterMaster.objects.filter(原価センタ=cost_center_cd)
    if cost_center_list.count() > 0:
        cost_center_data = cost_center_list[0]
    else:
        cost_center_data = ''
    return cost_center_data


# 指図書コードの取得（テキスト取得用）
def get_maintenance_instruction_no(instruction_no):
    instruction_no_list = InstructionNoMaster.objects.filter(指図書コード=instruction_no)
    if instruction_no_list.count() > 0:
        instruction_no_data = instruction_no_list[0]
    else:
        instruction_no_data = ''
    return instruction_no_data


# 勘定コードの取得（テキスト取得用）
def get_maintenance_account_code(account_cd):
    account_code_list = AccountCodeMaster.objects.filter(勘定コード=account_cd)
    if account_code_list.count() > 0:
        account_code_data = account_code_list[0]
    else:
        account_code_data = ''
    return account_code_data

