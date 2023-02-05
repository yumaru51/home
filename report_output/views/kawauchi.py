import datetime
import mimetypes
import glob
import os
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# Oracle接続
# import cx_Oracle
# excel操作
import openpyxl
# SQLSERVER接続
import pyodbc
from .pybot import pybot


def bootstrap(request):
    return render(request, 'report_output/bootstrap.html', )

def report(request):
    # DB接続
    # server = 'YSQLSERV4'
    # database = 'OP_ENTRY_M3P'
    # username = 'cmd_user'
    # password = 'cmd_user'
    # cnxn = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    # cursor = cnxn.cursor()

    data = {
        'test': 'test',
    }
    return render(request, 'report_output/report.html', data)


def chatwindow(request):
    # DB接続
    # server = 'YSQLSERV4'
    # database = 'OP_ENTRY_M3P'
    # username = 'cmd_user'
    # password = 'cmd_user'
    # cnxn = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    # cursor = cnxn.cursor()

    params = {
        'status': 0,
        'user_input_output': '',
        'robot_output': '',
    }

    if request.method == 'POST':
        params['user_input_output'] = request.POST['userInput']
        params['robot_output'] = pybot(request.POST['userInput'])
        return JsonResponse(params)

    return render(request, 'report_output/chatwindow.html', params)
