from django.db import connections
from django.views.decorators.http import require_POST
from cpexcel.models import Programs, Files, Tasks
from django.template.response import TemplateResponse
from django.views.generic import TemplateView
from django.http import HttpResponse
from datetime import datetime
import datetime
from django.db import connection
from django.db.models import Sum


@require_POST
def program_list(request):
    entry_person = request.POST['entry_person']
    program_name_text = request.POST['program_name_text']
    description_text = request.POST['description_text']
    from_page = int(request.POST['from_page'])

    sql = """ SELECT cpexcel_programs.* """
    sql = sql + """ FROM cpexcel_programs """
    sql = sql + """ WHERE 1=1 """

    if entry_person != "":
        sql = sql + """ AND entry_operator='""" + entry_person + """' """

    if program_name_text != "":
        sql = sql + """ AND program_name like '%%""" + program_name_text + """%%' """

    if description_text != "":
        sql = sql + """ AND description like '%%""" + description_text + """%%' """

    sql = sql + """ ORDER BY id """

    program_lists = Programs.objects.all().raw(sql)
    program_lists_num = Programs.objects.all().count

    data = {
        'program_lists': program_lists,
        'order_lists_num': program_lists_num,
        'from_page': from_page
    }

    return TemplateResponse(request, 'cpexcel/parts/program_list.html', data)


@require_POST
def task_list(request):
    program_id = int(request.POST['program_id'])

    task_lists = Tasks.objects.all().filter(program_id=program_id, lost_flag=0)
    task_amount = Tasks.objects.all().filter(program_id=program_id, lost_flag=0).count

    data = {
        'task_lists': task_lists,
        'task_amount': task_amount
    }

    return TemplateResponse(request, 'cpexcel/parts/task_list.html', data)

