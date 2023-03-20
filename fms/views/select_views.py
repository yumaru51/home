import traceback
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from fms.models import ProcessMaster, DepartmentMaster, User, SupplierMaster, UserAttribute, StepMaster, Budget, Measure
from plantia.models import MasterMgtCls, MasterConditionCode
from plantia.models import FcltyLdgr, MasterMgtCls, MasterLocation
from gcsystem.models import InstructionNoMaster, CostCenterMaster
from fms.views.common_def_views import get_department_person_list, get_next_department_list
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# 部門選択時の設備工程のリスト更新
@require_POST
@login_required
def select_division(request):
    # JSからのPOST引数を取得
    division = request.POST['division']

    # 選択した部門に所属する部署データ(一覧)を取得
    department_list = DepartmentMaster.objects.filter(lost_flag=0, division_cd=division).all().order_by('display_order')

    data = {
        'department_list': department_list,
    }

    return render(request, 'fms/parts/select/select_department.html', data)


# 部門選択時の部署のリスト更新･･･入力画面用
@require_POST
@login_required
def input_select_division(request):
    try:
        # JSからのPOST引数を取得
        div_add_name = request.POST['div_add_name']
        division = request.POST['division']

        # 選択した部門に所属する部署データ(一覧)を取得
        department_lists = DepartmentMaster.objects.filter(lost_flag=0, division_cd=division).all().order_by('display_order')

        data = {
            'department_lists': department_lists,
            'div_add_name': div_add_name,
        }

        return render(request, 'fms/parts/select/input_select_department.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 部門選択時の部署のリスト更新･･･入力画面用
@require_POST
@login_required
def input_select_division_without_div_add_name(request):
    try:
        # JSからのPOST引数を取得
        division = request.POST['division']

        # 選択した部門に所属する部署データ(一覧)を取得
        department_lists = DepartmentMaster.objects.filter(lost_flag=0, division_cd=division).all().order_by('display_order')

        data = {
            'department_lists': department_lists,
            'div_add_name': '',
        }

        return render(request, 'fms/parts/select/input_select_department.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise
# 部署選択時の設備工程のリスト更新
@require_POST
@login_required
def select_department(request):
    try:
        # JSからのPOST引数を取得
        department = request.POST['department']

        # 選択した部署に所属する設備工程データ(一覧)を取得
        process_list = ProcessMaster.objects.filter(lost_flag=0, department=department).all().order_by('display_order')

        data = {
            'process_list': process_list,
        }

        return render(request, 'fms/parts/select/select_process.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 部署選択時の設備工程のリスト更新･･･入力画面用
@require_POST
@login_required
def input_select_department(request):
    # JSからのPOST引数を取得
    div_add_name = request.POST['div_add_name']
    department = request.POST['department']

    # 選択した部署に所属する設備工程データ(一覧)を取得
    process_lists = ProcessMaster.objects.filter(lost_flag=0, department=department).all().order_by('display_order')

    data = {
        'process_lists': process_lists,
        'div_add_name': div_add_name,
    }

    return render(request, 'fms/parts/select/input_select_process.html', data)


# 機器絞込
@require_POST
@login_required
def input_select_equipment_list(request):
    try:
        mgt_cls = request.POST['mgt_cls']
        facility = request.POST['facility']

        # 選択した部署に所属する設備工程データ(一覧)を取得
        equipment_basic_list = FcltyLdgr.objects.filter(m_site_skey=2, m_mgt_cls_skey=mgt_cls, m_location_skey=facility, deleted_flg=0).order_by('eqpt_id')

        data = {
            'equipment_basic_list': equipment_basic_list,
        }

        return render(request, 'fms/parts/select/input_select_equipment_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 業者あいまい検索時の業者のリスト更新･･･入力画面用
@require_POST
@login_required
def select_vendor(request):
    try:
        filter_chara = request.POST['filter_chara']

        # 選択した部門に所属する部署データ(一覧)を取得
        vendor_lists_num = SupplierMaster.objects.filter(supplier_name__icontains=filter_chara, lost_flag=0).count()
        vendor_lists = SupplierMaster.objects.filter(supplier_name__icontains=filter_chara, lost_flag=0)

        data = {
            'vendor_lists': vendor_lists,
        }

        return render(request, 'fms/parts/select/select_vendor.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 状況絞込
@require_POST
@login_required
def input_select_condition_list(request):
    try:
        mgt_cls = request.POST['mgt_cls']

        # 選択した部署に所属する設備工程データ(一覧)を取得
        condition_list = MasterConditionCode.objects.filter(m_mgt_cls_skey=mgt_cls)

        data = {
            'condition_list': condition_list,
        }

        return render(request, 'fms/parts/select/input_select_condition_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 人あいまい検索時の人のリスト更新･･･入力画面用
@require_POST
@login_required
def select_person(request):
    try:
        filter_chara = request.POST['filter_chara']

        # 選択した文字を苗字か名前に含む人データ(一覧)を取得
        person_lists = User.objects.filter(Q(last_name__icontains=filter_chara) | Q(first_name__icontains=filter_chara))

        data = {
            'person_lists': person_lists,
        }

        return render(request, 'fms/parts/select/select_person.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 人あいまい検索時の人のリスト更新･･･入力画面用
@require_POST
@login_required
def select_discovery_person(request):
    try:
        filter_chara = request.POST['filter_chara']

        # 選択した文字を苗字か名前に含む人データ(一覧)を取得
        discovery_person_lists = User.objects.filter(Q(last_name__icontains=filter_chara) | Q(first_name__icontains=filter_chara))

        data = {
            'discovery_person_lists': discovery_person_lists,
        }

        return render(request, 'fms/parts/select/select_discovery_person.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次部署選択時の次作業者のリスト更新･･･入力画面用
@require_POST
@login_required
def select_next_department(request):
    try:
        next_department = request.POST.get('department')
        target = request.POST['target']
        next_person_list = get_department_person_list(next_department)
        data = {
            'next_person_list': next_person_list,
            'target': target,
        }

        return render(request, 'fms/parts/select/filter_next_activities/select_next_person.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次部門選択時の次部署のリスト更新･･･入力画面用・・・2021/01/10 ueda追加
@require_POST
@login_required
def select_next_division(request):
    try:
        next_division = request.POST['division']
        target = request.POST['target']

        next_departments_list = DepartmentMaster.objects.filter(lost_flag=0, division_cd=next_division).all().order_by('display_order')
        data = {
            'next_departments_list': next_departments_list,
            'target': target,
        }

        return render(request, 'fms/parts/select/filter_next_activities/select_next_department.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次工程選択時の次部署のリスト更新
@require_POST
@login_required
def select_next_step_department(request):
    try:
        next_step = int(request.POST['next_step'])
        this_step_division = request.POST['this_step_division']
        user_department_cd = request.POST['user_department_cd']

        target = request.POST['target']
        target_id = int(request.POST['target_id'])
        step_data = StepMaster.objects.get(step_id=next_step, lost_flag=0)
        next_department_data = get_next_department_list(step_data.charge_department_class, target, target_id,
                                                        user_department_cd)
        data = {
            'next_departments_list': next_department_data['next_departments_list'],
            'department': next_department_data['department_id']
        }

        return render(request, 'fms/parts/select/next_step_department_select.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 次部署選択時の次作業者のリスト更新･･･入力画面用
@require_POST
@login_required
def next_step_department_select(request):
    try:
        next_department = request.POST['department']
        next_person_list = get_department_person_list(next_department)
        next_person_username = ''

        # 次作業者が一人だけの場合、次作業者を選択
        if len(next_person_list) == 1:
            next_person_username = next_person_list[0].username

        if len(next_department) == 0:
            next_department_name = ''
        else:
            next_department_name = DepartmentMaster.objects.get(department_cd=next_department).department_name

        data = {
            'next_person_list': next_person_list,
            'next_department_name': next_department_name,
            'next_person_username': next_person_username,
        }

        return render(request, 'fms/parts/select/select_next_step_person.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 指図書コードのリスト更新･･･入力画面用
@require_POST
@login_required
def instruction_no_filter(request):
    try:
        fiscal_year = request.POST['fiscal_year']
        fiter_chara_fiscal_year = fiscal_year[2:4]
        filter_chara = '22' + fiter_chara_fiscal_year + 'YY'
        instruction_no_lists = InstructionNoMaster.objects.filter(指図書コード__icontains=filter_chara)

        # print('instruction_no_filter:' + str(fiscal_year) + ':' + filter_chara)
        # for instruction_no in instruction_no_lists:
        #     print(str(instruction_no.指図書コード) + ':' + str(instruction_no.テキスト短) + ':' + str(instruction_no.利益センター))

        data = {
            'instruction_no_lists': instruction_no_lists,
        }

        return render(request, 'fms/parts/select/instruction_no_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 原価センターあいまい検索時の原価センターのリスト更新･･･入力画面用
@require_POST
@login_required
def cost_center_filter(request):
    try:
        filter_chara = request.POST['filter_chara']
        cost_center_lists = CostCenterMaster.objects.filter(Q(原価センタテキスト__icontains=filter_chara) | Q(原価センタ__icontains=filter_chara))

        data = {
            'cost_center_lists': cost_center_lists,
        }

        return render(request, 'fms/parts/select/cost_center_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 絞込の門選択時の部署のリスト更新･･･2021/01/17 ueda追加
@require_POST
@login_required
def select_filter_division(request):
    try:
        filter_division = request.POST['division']
        target = request.POST['target']

        filter_departments_list = DepartmentMaster.objects.filter(lost_flag=0, division_cd=filter_division).all().order_by('display_order')

        data = {
            'filter_departments_list': filter_departments_list,
            'target': target,
        }

        return render(request, 'fms/parts/select/filter_select_items/select_filter_department.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 部署選択時の設備工程のリスト更新
@require_POST
@login_required
def select_filter_department(request):
    try:
        department = request.POST['department']
        target = request.POST['target']

        # 選択した部署に所属する設備工程データ(一覧)を取得
        process_list = ProcessMaster.objects.filter(lost_flag=0, department=department).all().order_by('display_order')

        data = {
            'process_list': process_list,
            'target': target,
        }

        return render(request, 'fms/parts/select/filter_select_items/select_filter_process.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 進捗状況のリスト更新
@require_POST
@login_required
def select_work_step(request):
    try:
        copy_target_table = int(request.POST.get('copy_target_table'))

        if copy_target_table == 1:
            step_st = 133000000     # 予算側
        elif copy_target_table == 2:
            step_st = 211000000     # 実行側
        elif copy_target_table == 3:
            step_st = 132000000  # 中期計画側
        else:
            step_st = 0

        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5,
                                              lost_flag=0).all().order_by('step_id')

        data = {
            'copy_step_list': step_list,
        }

        return render(request, 'fms/parts/select/filter_select_items/select_filter_work_step.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 進捗状況のリスト更新
@require_POST
@login_required
def select_budget_plan(request):
    try:
        copy_target_plan = request.POST.get('copy_target_plan')

        if copy_target_plan == 'S':
            step_st = 133000000
        elif copy_target_plan == 'M':
            step_st = 132000000
        elif copy_target_plan == 'L':
            step_st = 131000000
        else:
            step_st = 0

        step_ed = step_st + 1000000
        step_list = StepMaster.objects.filter(step_id__gte=step_st, step_id__lt=step_ed, step_level=5,
                                              lost_flag=0).all().order_by('step_id')

        data = {
            'copy_step_list': step_list,
        }

        return render(request, 'fms/parts/select/filter_select_items/select_filter_budget_step.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

