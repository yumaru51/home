from django.db import connections
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.template.response import TemplateResponse
# from isac.models import Orders, Stocks, StockAllocationResult, CompanyReservedItemMaster, OrderStatusMaster, QualityStatusMaster, CompanyMaster, GradeTypeMaster, WarehouseMaster, OrderStatusMaster, IccidentalWorkMaster
from cpexcel.models import Programs, Files, Tasks
import datetime
import calendar
import os


@login_required
def index(request):

    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    new_dir_path = 'C:\\PythonProjects\\isk_tools\\static\\files\\cpexcel\\' + t_username

    if not os.path.isdir(new_dir_path):

        os.mkdir(new_dir_path)

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser
    }

    return render(request, 'cpexcel/top_page.html', data)


@login_required
def entry(request):

    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    program_id = 0

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser,
        'program_id': program_id
    }

    return render(request, 'cpexcel/program_entry.html', data)


@login_required
def execute(request):

    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    program_id = 0

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser,
        'program_id': program_id
    }

    return render(request, 'cpexcel/program_execute.html', data)


@require_POST
def program_filter(request):
    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser,
    }

    return TemplateResponse(request, 'cpexcel/parts/program_filter.html', data)


@login_required
@require_POST
def program_entry_page(request):

    t_username = request.user.username

    program_id = int(request.POST['program_id'])
    program_id_str = request.POST['program_id']

    new_dir_path = 'C:\\work_folder\\' + t_username

    if program_id == 0:
        program_name = ""
        description = ""
        source_file_folder_path = new_dir_path
        source_file = ""
        post_to_file_path = new_dir_path
        post_to_file = ""
        program_id_str = ""
        label = "　登録　"

    else:
        program_data = Programs.objects.all().get(id=program_id)
        program_name = program_data.program_name
        description = program_data.description

        file_data = Files.objects.all().get(program_id=program_id)
        source_file_folder_path = new_dir_path
        source_file = file_data.source_file_name
        post_to_file_path = new_dir_path
        post_to_file = file_data.post_to_file_name

        program_id_str = program_id_str
        label = "　更新　"

    data = {
        'program_id': program_id,
        'program_name': program_name,
        'description': description,
        'source_file_folder_path': source_file_folder_path,
        'source_file': source_file,
        'post_to_file_path': post_to_file_path,
        'post_to_file': post_to_file,
        'program_id_str': program_id_str,
        'label': label
    }

    return TemplateResponse(request, 'cpexcel/parts/program_entry_page.html', data)


@require_POST
def task_entry_page(request):

    program_id = int(request.POST['program_id'])
    task_id = int(request.POST['task_id'])
    task_id_str = request.POST['task_id']

    if task_id == 0:
        source_sheet_name = ""
        source_cell_name = ""
        post_to_sheet_name = ""
        post_to_cell_name = ""
        label = "　登録　"

    else:
        task_data = Tasks.objects.all().get(id=task_id)
        source_sheet_name = task_data.source_sheet_name
        source_cell_name = task_data.source_cell_name
        post_to_sheet_name = task_data.post_to_sheet_name
        post_to_cell_name = task_data.post_to_cell_name
        label = "　更新　"

    data = {
        'program_id': program_id,
        'task_id': task_id,
        'task_id_str': task_id_str,
        'source_sheet_name': source_sheet_name,
        'source_cell_name': source_cell_name,
        'post_to_sheet_name': post_to_sheet_name,
        'post_to_cell_name': post_to_cell_name,
        'label': label
    }

    return TemplateResponse(request, 'cpexcel/parts/task_entry_page.html', data)


@require_POST
def program_detail(request):

    program_id = int(request.POST['program_id'])
    program_id_str = request.POST['program_id']

    program_data = Programs.objects.all().get(id=program_id)
    program_name = program_data.program_name
    description = program_data.description

    file_data = Files.objects.all().get(program_id=program_id)
    source_file_folder_path = file_data.source_file_path
    source_file = file_data.source_file_name
    post_to_file_path = file_data.post_to_file_path
    post_to_file = file_data.post_to_file_name

    program_id_str = program_id_str

    data = {
        'program_id': program_id,
        'program_name': program_name,
        'description': description,
        'source_file_folder_path': source_file_folder_path,
        'source_file': source_file,
        'post_to_file_path': post_to_file_path,
        'post_to_file': post_to_file,
        'program_id_str': program_id_str
    }

    return TemplateResponse(request, 'cpexcel/parts/program_detail.html', data)


@login_required
@login_required
def file_change_check_page(request):
    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    new_dir_path = 'C:\\work_folder\\' + t_username

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser,
        'new_dir_path': new_dir_path
    }

    return TemplateResponse(request, 'cpexcel/file_change_check.html', data)


@login_required
def demo_file_download_page(request):

    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser
    }

    return TemplateResponse(request, 'cpexcel/demo_files.html', data)
