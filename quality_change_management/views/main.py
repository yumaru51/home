# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
import os
import mimetypes
import glob
import openpyxl
from django.db.models import Q
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayPage, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, LogForm, ProgressForm, ReportForm
from .info import info_change, info_history, info_comment
from .sub import department_lists


# test
# top_page　progressの情報をリストする
def top_page(request):
    print(datetime.datetime.now(),
          '「top_page」',
          # 兼務用にメイン部署のコードなどを作る？今は一番上のをメインとして扱っている。
          '部署:', UserAttribute.objects.filter(username=request.user).first().department, ';',
          'ユーザーID:', request.user, ';',
          '通信:', '「'+request.method+'」', ';',)

    division_list = []  # ユーザーが所属している部門
    for user_attribute in UserAttribute.objects.filter(username=request.user):
        division_list.append(user_attribute.division)

    department_list = []  # ユーザーが所属している部署
    for user_attribute in UserAttribute.objects.filter(username=request.user):
        department_list.append(user_attribute.department)

    step_list = []  # フローに表示する有効ステップ
    progress_count_dict = {}  # 件数表示
    for step in StepMaster.objects.filter(hidden_flag=0, lost_flag=0):
        step_list.append(step)
        progress_count_dict[str(step.step)] = {
            'step_name': step.step_name,
            'count1': Progress.objects.filter(present_step_id=step, present_division__in=division_list).count(),
            'count2': Progress.objects.filter(present_step_id=step, present_department__in=department_list).count(),
            'count3': Progress.objects.filter(present_step_id=step, present_operator=request.user).count(),
        }

    progress_dict = {}
    for progress_data in Progress.objects.filter(present_step__in=step_list, present_division__in=division_list):
        if progress_data.target == 'request':
            work_class = '原課'
        elif progress_data.target == 'quality':
            work_class = '品質'
        elif progress_data.target == 'safety':
            work_class = '安全'

        progress_dict[str(progress_data.id)] = {
            'request_id': progress_data.request_id,
            'step_name': progress_data.present_step.step_name,
            'work_class': work_class,
            'present_operator': User.objects.get(username=progress_data.present_operator),
            'title': progress_data.request.title,
            'safety_aspect': progress_data.request.safety_aspect,
            'quality_aspect': progress_data.request.quality_aspect,
            'safety_aspect2': progress_data.request.safety_aspect,
            'quality_aspect2': progress_data.request.quality_aspect,
            'delivery_date': progress_data.request.delivery_date,
            'change_target': progress_data.request.change_target.replace('[', '').replace(']', '').
            replace('method', '方法').replace('facility', '設備').replace('material', '原料/副原料').replace('man', '人'),
            'target': progress_data.target,
            'present_step': progress_data.present_step_id,
        }

    # 部署選択後のユーザーリスト入れ替えをクライアント処理に置き換え検討
    # user_list = {}
    # for department_cd in DepartmentMaster.objects.filter(lost_flag=0):
    #     option = ''
    #     for username in UserAttribute.objects.filter(department=department_cd.department_cd, lost_flag=0):
    #         user = User.objects.get(username=username.username, lost_flag=0)
    #         if username.username == str(request.user):
    #             option = option + '<option value="' + str(user) + '" selected>' + str(user)
    #         else:
    #             option = option + '<option value="' + str(user) + '">' + str(user)
    #     user_list[department_cd.department_cd] = option

    data = {
        # 'user_list': user_list,
        'department': DepartmentMaster.objects.get(department_cd=UserAttribute.objects.filter(username=request.user).
                                                   first().department).department_name,  # 兼務の場合、一番上のをメインとして扱っている。
        'progress_count_dict': progress_count_dict,
        'present_step_id': '',
        'progress_dict': progress_dict,
        'progress_form': ProgressForm(initial=dict(
            # 部署名　空
            # present_department=UserAttribute.objects.filter(username=request.user).first().department,
            next_department=UserAttribute.objects.filter(username=request.user).first().department,
            next_user=request.user
        )),  # 所属部門のデータは操作できるため初期は部署・ユーザーの絞り込みをしない。
    }

    if request.method == 'POST':
        # filter処理
        condition1 = {}
        condition2 = {}
        condition3 = {}
        condition4 = {}
        condition5 = {}
        condition6 = {}
        condition7 = {}
        condition8 = {}
        condition9 = {}
        condition10 = {}

        # 条件①:部署
        request_id_list = []
        if request.POST['present_department'] is not '':
            for request_id in Request.objects.filter(department=(request.POST['present_department'])).values_list('id'):
                request_id_list.append(request_id)
            condition1['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition1['request_id__in'] = [0, ]

        # 条件②:進捗状況
        if request.POST['present_step_id'] is not '':
            condition2['present_step'] = request.POST['present_step_id']

        # 条件③:変更管理名称
        request_id_list = []
        if request.POST['title'] is not '':
            for request_id in Request.objects.filter(title=(request.POST['title'])).values_list('id'):
                request_id_list.append(request_id)
            condition3['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition3['request_id__in'] = [0, ]

        # 条件④:作業区分
        if request.POST['work_class'] is not '':
            if request.POST['work_class'] == 'engineering':
                condition4['present_step'] = '1201'
            else:
                condition4['target'] = request.POST['work_class']

        # 条件⑤:変更日FROM～TO
        request_id_list = []
        if request.POST['delivery_date_from'] is not '' and request.POST['delivery_date_to'] is not '':
            for request_id in Request.objects.filter(completion_date__range=(request.POST['delivery_date_from'], request.POST['delivery_date_to'])).values_list('id'):
                request_id_list.append(request_id)
                condition5['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition5['request_id__in'] = [0, ]

        # 条件⑥:安全面レベル
        request_id_list = []
        if request.POST['safety_aspect'] is not '':
            for request_id in Request.objects.filter(safety_aspect=(request.POST['safety_aspect'])).values_list('id'):
                request_id_list.append(request_id)
            condition6['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition6['request_id__in'] = [0, ]

        # 条件⑦:品質面レベル
        request_id_list = []
        if request.POST['quality_aspect'] is not '':
            for request_id in Request.objects.filter(quality_aspect=(request.POST['quality_aspect'])).values_list('id'):
                request_id_list.append(request_id)
            condition7['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition7['request_id__in'] = [0, ]

        # 条件⑧:次作業者部署名
        if request.POST['next_department'] is not '':
            condition8['present_department'] = request.POST['next_department']

        # 条件⑨:次作業者
        if request.POST.get('next_user', default='') is not '':
            condition9['present_operator'] = request.POST['next_user']

        # 条件⑩:表示区分
        progress_form = ProgressForm(request.POST)
        if progress_form.is_valid():
            if progress_form.cleaned_data['display_class'] == ['1', '2']:
                condition10['present_step'] = ('9999', '8201')
            elif progress_form.cleaned_data['display_class'] == ['1']:
                condition10['present_step'] = '9999'
            elif progress_form.cleaned_data['display_class'] == ['2']:
                condition10['present_step'] = '8201'
            else:
                condition10['present_step__in'] = step_list

        progress_dict = {}
        for progress_data in Progress.objects\
                .filter(**condition1).filter(**condition2).filter(**condition3)\
                .filter(**condition4).filter(**condition5).filter(**condition6)\
                .filter(**condition7).filter(**condition8).filter(**condition9).filter(**condition10):
            if progress_data.target == 'request':
                work_class = '原課'
            elif progress_data.target == 'quality':
                work_class = '品質'
            elif progress_data.target == 'safety':
                work_class = '安全'

            progress_dict[str(progress_data.id)] = {
                'request_id': progress_data.request_id,
                'step_name': progress_data.present_step.step_name,
                'work_class': work_class,
                'present_operator': User.objects.get(username=progress_data.present_operator),
                'title': progress_data.request.title,
                'quality_aspect': progress_data.request.quality_aspect,
                'safety_aspect': progress_data.request.safety_aspect,
                'quality_aspect2': progress_data.request.quality_aspect,
                'safety_aspect2': progress_data.request.safety_aspect,
                'delivery_date': progress_data.request.delivery_date,
                'change_target': progress_data.request.change_target.replace('[', '').replace(']', '').
                replace('method', '方法').replace('facility', '設備').replace('material', '原料/副原料').replace('man', '人'),
                'target': progress_data.target,
                'present_step': progress_data.present_step_id,
            }

        data['progress_dict'] = progress_dict
        data['progress_form'] = ProgressForm(request.POST)
        data['present_step_id'] = request.POST['present_step_id']

    # sessionリセット
    if 'request_id' in request.session:
        del request.session['request_id']
    if 'target' in request.session:
        del request.session['target']
    if 'present_step' in request.session:
        del request.session['present_step']
    if 'action' in request.session:
        del request.session['action']
    # request.session.clear()

    return render(request, 'quality_change_management/top_page.html', data)


# 詳細画面テンプレート
def detail(request, present_step, target, request_id):
    print('「detail」',
          '現在のステップ:', Progress.objects.filter(request_id=request_id, target=target, present_step=present_step), ';',
          # 兼務用にメイン部署のコードなどを作る？今は一番上のをメインとして扱っている。
          '部署:', UserAttribute.objects.filter(username=request.user).first().department, ';',
          'ユーザーID:', request.user, ';',
          'ID:', request_id, ';',
          '通信:', '「'+request.method+'」', ';',)

    # step_name取得
    step_name = StepMaster.objects.get(step=present_step).step_name

    # sessionにパラメーター格納
    request.session['request_id'] = request_id
    request.session['target'] = target
    request.session['present_step'] = present_step

    # tab生成処理 多次元辞書編
    step_display_item_lists = StepDisplayPage.objects.filter(step=present_step, lost_flag=0).order_by('page_no')
    page_dict = {}
    for step_display_item_list in step_display_item_lists:
        function_name = 'info_' + step_display_item_list.page.page
        page_dict[step_display_item_list.page_no] = {
            'page_id': step_display_item_list.page_id,
            'page_name': step_display_item_list.page.page_name,
            'page': globals()[function_name](request).content.decode(),
            'default_page': step_display_item_list.default_page
        }

    # todo ボタン制御、entryは1stepにつき1つまで、
    authority_flag = 0
    # ①ステップ制御
    # action_class = 'entry'
    entry_dict = {'action': 'top_page', 'action_name': ''}
    if StepAction.objects.filter(step_id=present_step, action_class='entry', lost_flag=0).exists():
        entry = StepAction.objects.get(step_id=present_step, action_class='entry', lost_flag=0)
        entry_dict['action'] = 'entry_' + entry.action_id
        entry_dict['action_name'] = entry.action.action_name

        # sessionにパラメーター格納
        request.session['action'] = entry_dict['action']

    # action_class = 'function'
    step_action_lists = StepAction.objects.filter(step_id=present_step, action_class='function', lost_flag=0).order_by('display_order')
    function_dict = {}
    index = 0
    for step_action_list in step_action_lists:
        function_dict[index] = {
            'action': 'function_' + step_action_list.action_id,
            'action_name': step_action_list.action.action_name,
        }
        index += 1
    # ②担当部署制御　ステップの担当部署にユーザー所属の担当部署が含まれるか否か
    department_list = []  # ユーザー所属の担当部署リスト
    for user_attribute in UserAttribute.objects.filter(username=request.user):
        department_list.append(user_attribute.department)
    department_cd_lists = department_lists(request, present_step)
    for department_cd_list in department_cd_lists:
        for department in department_list:
            if department_cd_list == department:
                authority_flag = 1
    # ③ユーザー制御

    params = {
        'step_name': step_name,
        'step_display_item_list': step_display_item_lists,
        'page_dict': page_dict,
        'entry_dict': entry_dict,
        'function_dict': function_dict,
        'authority_flag': authority_flag,
    }
    return render(request, 'quality_change_management/detail.html', params)


def report(request, export):
    print('report機能です！')
    print(datetime.datetime.now(),
          '「report」',
          # 兼務用にメイン部署のコードなどを作る？今は一番上のをメインとして扱っている。
          '部署:', UserAttribute.objects.filter(username=request.user).first().department, ';',
          'ユーザーID:', request.user, ';',
          '通信:', '「'+request.method+'」', ';',)

    division_list = []  # ユーザーが所属している部門
    for user_attribute in UserAttribute.objects.filter(username=request.user):
        division_list.append(user_attribute.division)

    department_list = []  # ユーザーが所属している部署
    for user_attribute in UserAttribute.objects.filter(username=request.user):
        department_list.append(user_attribute.department)

    step_list = []  # フローに表示する有効ステップ
    for step in StepMaster.objects.filter(hidden_flag=0, lost_flag=0):
        step_list.append(step)

    progress_dict = {}
    for progress_data in Progress.objects.filter(present_step__in=step_list, present_division__in=division_list):
        if progress_data.target == 'request':
            work_class = '原課'
        elif progress_data.target == 'quality':
            work_class = '品質'
        elif progress_data.target == 'safety':
            work_class = '安全'

        progress_dict[str(progress_data.id)] = {
            'request_id': progress_data.request_id,
            'step_name': progress_data.present_step.step_name,
            'work_class': work_class,
            'present_operator': User.objects.get(username=progress_data.present_operator),
            'title': progress_data.request.title,
            'safety_aspect': progress_data.request.safety_aspect,
            'quality_aspect': progress_data.request.quality_aspect,
            'safety_aspect2': progress_data.request.safety_aspect,
            'quality_aspect2': progress_data.request.quality_aspect,
            'delivery_date': progress_data.request.delivery_date,
            'change_target': progress_data.request.change_target.replace('[', '').replace(']', '').
            replace('method', '方法').replace('facility', '設備').replace('material', '原料/副原料').replace('man', '人'),
            'target': progress_data.target,
            'present_step': progress_data.present_step_id,
        }

    data = {
        'department': DepartmentMaster.objects.get(department_cd=UserAttribute.objects.filter(username=request.user).
                                                   first().department).department_name,  # 兼務の場合、一番上のをメインとして扱っている。
        'progress_dict': progress_dict,
        'report_form': ReportForm(),  # 所属部門のデータは操作できるため初期は部署・ユーザーの絞り込みをしない。
    }

    if request.method == 'POST':
        # filter処理
        condition1 = {}
        condition2 = {}
        condition3 = {}
        condition4 = {}
        condition5 = {}
        condition6 = {}
        condition7 = {}
        condition8 = {}
        condition9 = {}
        condition10 = {}

        # 条件①:進捗区分
        if request.POST['progress_class'] is not '':
            if request.POST['progress_class'] == '1':
                condition1['present_step__in'] = [1102, ]
            if request.POST['progress_class'] == '2':
                condition1['present_step__in'] = [1103, 1104, 1201, 1301, 1302, 1401, 1501, 1601, ]
            if request.POST['progress_class'] == '3':
                condition1['present_step__in'] = [9999, ]

        # 条件②:部署
        request_id_list = []
        if request.POST['present_department'] is not '':
            for request_id in Request.objects.filter(department=(request.POST['present_department'])).values_list('id'):
                request_id_list.append(request_id)
            condition1['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition1['request_id__in'] = [0, ]

        # 条件③:進捗状況
        if request.POST['present_step_id'] is not '':
            condition2['present_step'] = request.POST['present_step_id']

        # 条件④:変更管理名称
        request_id_list = []
        if request.POST['title'] is not '':
            for request_id in Request.objects.filter(title=(request.POST['title'])).values_list('id'):
                request_id_list.append(request_id)
            condition3['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition3['request_id__in'] = [0, ]

        # 条件⑤:作業区分
        if request.POST['work_class'] is not '':
            if request.POST['work_class'] == 'engineering':
                condition4['present_step'] = '1201'
            else:
                condition4['target'] = request.POST['work_class']

        # 条件⑤:変更日FROM～TO
        request_id_list = []
        if request.POST['completion_date_from'] is not '' and request.POST['completion_date_to'] is not '':
            for request_id in Request.objects.filter(completion_date__range=(request.POST['completion_date_from'], request.POST['completion_date_to'])).values_list('id'):
                request_id_list.append(request_id)
                condition5['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition5['request_id__in'] = [0, ]

        # 条件⑥:安全面レベル
        request_id_list = []
        if request.POST['safety_aspect'] is not '':
            for request_id in Request.objects.filter(safety_aspect=(request.POST['safety_aspect'])).values_list('id'):
                request_id_list.append(request_id)
            condition6['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition6['request_id__in'] = [0, ]

        # 条件⑦:品質面レベル
        request_id_list = []
        if request.POST['quality_aspect'] is not '':
            for request_id in Request.objects.filter(quality_aspect=(request.POST['quality_aspect'])).values_list('id'):
                request_id_list.append(request_id)
            condition7['request_id__in'] = request_id_list
            if request_id_list.__len__() == 0:
                condition7['request_id__in'] = [0, ]

        # # 条件⑧:次作業者部署名
        # if request.POST['next_department'] is not '':
        #     condition8['present_department'] = request.POST['next_department']
        #
        # # 条件⑨:次作業者
        # if request.POST['next_user'] is not '':
        #     condition9['present_operator'] = request.POST['next_user']

        # 条件⑩:表示区分
        progress_form = ProgressForm(request.POST)
        if progress_form.is_valid():
            if progress_form.cleaned_data['display_class'] == ['1', '2']:
                condition10['present_step'] = ('9999', '8201')
            elif progress_form.cleaned_data['display_class'] == ['1']:
                condition10['present_step'] = '9999'
            elif progress_form.cleaned_data['display_class'] == ['2']:
                condition10['present_step'] = '8201'

        progress_dict = {}
        for progress_data in Progress.objects.filter(**condition1).filter(**condition2)\
                .filter(**condition3).filter(**condition4).filter(**condition5).filter(**condition6)\
                .filter(**condition7).filter(**condition8).filter(**condition9).filter(**condition10):
            if progress_data.target == 'request':
                work_class = '原課'
            elif progress_data.target == 'quality':
                work_class = '品質'
            elif progress_data.target == 'safety':
                work_class = '安全'

            progress_dict[str(progress_data.id)] = {
                'request_id': progress_data.request_id,                                                         # 管理No
                'step_name': progress_data.present_step.step_name,                                              # 進捗状況
                'work_class': work_class,                                                                       # 作業区分
                'present_operator': str(User.objects.get(username=progress_data.present_operator)),             # 申請者
                'title': progress_data.request.title,                                                           # タイトル
                'quality_aspect': progress_data.request.quality_aspect,                                         #
                'safety_aspect': progress_data.request.safety_aspect,                                           #
                'quality_aspect2': progress_data.request.quality_aspect,                                        #
                'safety_aspect2': progress_data.request.safety_aspect,                                          #
                'delivery_date': progress_data.request.delivery_date,                                           #
                'change_target': progress_data.request.change_target.replace('[', '').replace(']', '').
                replace('method', '方法').replace('facility', '設備').replace('material', '原料/副原料').replace('man', '人'),
                'target': progress_data.target,                                                                 #
                'present_step': progress_data.present_step_id,                                                  #
                'application_date': progress_data.request.application_date,                                     # 申請日
                'department':
                    DepartmentMaster.objects.get(department_cd=progress_data.request.department).department_name,  # 部署名
                'user': progress_data.request.user,                                                             # 申請者
                'level': progress_data.request.level,                                                           # 継続/一過性
                'completion_date': progress_data.request.completion_date,                                       # 変更日
            }

        data['progress_dict'] = progress_dict
        data['report_form'] = ReportForm(request.POST)

        # エクスポート処理
        if export == 1:
            print('exportします！')

            # テンプレート取得 --- (*1)
            base_dir = '\\\\Ydomnserv\\common\\部門間フォルダ\\FacilityData\\template_files\\quality_change_management\\'
            template = base_dir + '変更管理分析原紙.xlsx'

            if os.path.isfile(template) is False:
                print('対象ファイルが存在しません！！')

            # 前回EXCEL削除 --- (*2)
            file_list = glob.glob(base_dir + '*_変更管理分析原紙.xlsx')
            for file in file_list:
                os.remove(file)

            # EXCEL読込 --- (*3)
            workbook = openpyxl.load_workbook(template)

            # EXCEL書込 --- (*4)
            worksheet = workbook["Sheet1"]
            i = 5

            for value in progress_dict.values():
                worksheet["A" + str(i)] = value['request_id']                   # 管理No
                worksheet["B" + str(i)] = value['application_date']             # 申請日
                worksheet["C" + str(i)] = value['title']                        # タイトル
                worksheet["D" + str(i)] = value['department']                   # 部署名
                worksheet["E" + str(i)] = value['present_operator']             # 申請者
                worksheet["F" + str(i)] = value['level']                        # 継続/一過性
                worksheet["G" + str(i)] = value['delivery_date']                # 変更希望日
                worksheet["H" + str(i)] = value['step_name']                    # 進捗状況
                worksheet["I" + str(i)] = value['change_target']                # 4M要因
                worksheet["J" + str(i)] = value['quality_aspect']               # 変更レベル(品質)
                worksheet["K" + str(i)] = value['safety_aspect']                # 変更レベル(安全)
                worksheet["L" + str(i)] = value['quality_aspect2']              # 所管判定(品質)
                worksheet["M" + str(i)] = value['safety_aspect2']               # 所管判定(安全)
                worksheet["N" + str(i)] = value['delivery_date']                # 変更日希望日
                i = i + 1

            # EXCEL保存 --- (*5)
            today = datetime.datetime.now().strftime('%Y%m%d%H%M')
            file_path = '\\\\ydomnserv\\common\\部門間フォルダ\\FacilityData\\template_files\\quality_change_management\\' + today + '_変更管理分析原紙.xlsx'
            file_name = today + '_変更管理分析原紙.xlsx'
            workbook.save(file_path)

            import urllib.parse
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_name)[0] or 'application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename="{fn}"'.format(fn=urllib.parse.quote(file_name))

            return response

    return render(request, 'quality_change_management/report.html', data)
