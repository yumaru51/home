# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import datetime
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayPage, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
from quality_change_management.forms import RequestForm, Request2Form, Request3Form, QualityForm, SafetyForm, Quality2Form, Safety2Form, LogForm
import os
import inspect
import logging
import traceback
import sys


# 例外ログ出力
def output_log_exception(request, traceback_str):
    # 呼び出し元関数、ファイル名を取得
    f_object = inspect.currentframe().f_back
    func_name = f_object.f_code.co_name
    file_name = os.path.basename(f_object.f_code.co_filename)
    # line_no = str(f_object.f_lineno)

    # ログ出力
    log_msg = '\r' + ' [ファイル名]:' + '\t' + file_name
    log_msg = log_msg + '\r' + ' [関数名]:' + '\t' + func_name
    log_msg = log_msg + '\r' + ' [POST]: ' + '\t' + str(request.POST)
    log_msg = log_msg + '\r' + ' ' + traceback_str
    logger = logging.getLogger("error")  # "error"とはなにか？"%(name)s",？
    logger.error(log_msg)
    return


# ***action***
def action(request, function_name):
    try:
        request_id = request.session['request_id']
        print('「action」',
              '現在のステップ:', Progress.objects.filter(request_id=request_id), ';',
              '部署:', UserAttribute.objects.filter(username=request.user).first().department, ';',
              'ユーザーID:', request.user, ';',
              'ID:', request_id, ';',
              '通信:', '「'+request.method+'」', ';',
              'action_id:', function_name, ';',)
        globals()[function_name](request)

        # ログ記述
        entry_log(request, function_name)

        request_id = request.session['request_id']
        target = request.session['target']
        present_step = request.session['present_step']

        # 各ボタンを押した後の挙動を設定する。続けて処理したい場合は登録後、詳細画面のままにする。
        if 'entry' in function_name:
            return redirect('quality_change_management:detail', present_step, target, request_id)
        if 'approval' in function_name:
            return redirect('quality_change_management:top_page')
        if 'completed' in function_name:
            return redirect('quality_change_management:top_page')
        if 'confirm' in function_name:
            return redirect('quality_change_management:top_page')
        if 'copy' in function_name:
            return
        if 'print' in function_name:
            return
        if 'rejected' in function_name:
            return HttpResponse("<script>alert('却下しました！');location.href = '../../';</script>")
        if 'remand' in function_name:
            return redirect('quality_change_management:top_page')
        return redirect('quality_change_management:top_page')

    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# ***entry***
# requestテーブル
def entry_request(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    edit = 'on'

    if present_step == 1102:
        if request_id == 0:     # 新規作成のとき
            obj = Request.objects.create(id=None)
            request_form = RequestForm(data=request.POST, instance=obj, edit=edit, step=present_step)
            request_form.save()
            request_id = obj.id
            # sessionにパラメーター格納
            request.session['request_id'] = request_id

            # progressを作成する。
            Progress.objects.create(
                request_id=request_id,
                target='request',
                present_step=StepMaster.objects.get(step=present_step),
                present_division=DepartmentMaster.objects.get(department_cd=request.POST['next_department']).division_cd,
                present_department=request.POST['next_department'],
                present_operator=request.POST['next_operator'],
                last_step=StepMaster.objects.get(step=present_step)
            )

        else:                   # 更新のとき
            obj = Request.objects.get(id=request_id)
            request_form = RequestForm(data=request.POST, instance=obj, edit=edit, step=present_step)
            request_form.save()

    elif present_step == 1401:
        obj = Request.objects.get(id=request_id)
        request_form = Request2Form(data=request.POST, instance=obj, edit=edit, step=present_step)
        request_form.save()

    elif present_step == 1601:
        obj = Request.objects.get(id=request_id)
        request_form = Request3Form(data=request.POST, instance=obj, edit=edit, step=present_step)
        request_form.save()

    return


# qualityテーブル
def entry_quality(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    edit = 'on'

    if present_step == 1301:  # 新規作成のとき
        obj = Quality.objects.create(id=None, request_id=request_id)
        quality_form = QualityForm(data=request.POST, instance=obj, edit=edit, step=present_step)
        quality_form.save()

    elif present_step == 1501:
        Quality.objects.update_or_create(
            request_id=request_id,
            defaults={'evaluation': request.POST['evaluation'], }
        )

    return


# safetyテーブル
def entry_safety(request):
    request_id = request.session['request_id']
    present_step = request.session['present_step']
    edit = 'on'

    if present_step == 1301:  # 新規作成のとき
        obj = Safety.objects.create(id=None, request_id=request_id)
        safety_form = SafetyForm(data=request.POST, instance=obj, edit=edit, step=present_step)
        safety_form.save()

    elif present_step == 1501:
        Safety.objects.update_or_create(
            request_id=request_id,
            defaults={'evaluation': request.POST['evaluation'], }
        )

    return


# progressテーブル
def entry_progress(request):
    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']

    # # # # # 特殊並列処理 # # # # #

    # # # # # 「原課部長承認」(1104) # # # # #
    # ①評価レベル0, 1と②評価レベル2, 3で分岐
    if present_step == 1104:
        safety_aspect = Request.objects.get(id=request_id).safety_aspect
        quality_aspect = Request.objects.get(id=request_id).quality_aspect

        # ①「工務部長承認」(1201)スキップして、「原課変更実施」(1401)に行く
        if (safety_aspect == '0' or safety_aspect == 'Ⅰ') and (quality_aspect == '0' or quality_aspect == 'Ⅰ'):
            next_step = StepMaster.objects.get(step=1401)
            progress_data = Progress.objects.get(request_id=request_id, target='request')
            present_division = progress_data.present_division
            present_department = progress_data.present_department
            present_operator = progress_data.present_operator

        # ②「工務部長承認」(1201)に行く
        else:
            next_step = StepMaster.objects.get(step=1201)
            present_division = 'KOUMU'
            present_department = 'KOUMU'
            present_operator = 't-hujii'

        Progress.objects.update_or_create(
            request_id=request_id,
            target='request',
            present_step=present_step,
            defaults={'present_step': next_step,
                      'present_division': present_division,
                      'present_department': present_department,
                      'present_operator': present_operator,
                      'last_step': StepMaster.objects.get(step=present_step)
                      }
        )
    # # # # # 「原課部長承認」(1104) # # # # #

    # # # # # 「工務部長承認」(1201) # # # # #
    # 「所管承認」(1301)に行く
    elif present_step == 1201:
        safety_aspect = Request.objects.get(id=request_id).safety_aspect
        quality_aspect = Request.objects.get(id=request_id).quality_aspect
        Progress.objects.update_or_create(
            request_id=request_id,
            target='request',
            present_step=present_step,
            defaults={'present_step': StepMaster.objects.get(step=request.POST['next_step']),
                      'present_division': DepartmentMaster.objects.get(department_cd=request.POST['next_department']).division_cd,
                      'present_department': request.POST['next_department'],
                      'present_operator': request.POST['next_operator'],
                      'last_step': StepMaster.objects.get(step=present_step)
                      }
        )

        # 安全と品質1個ずつ確認して2,3であれば専用プログレス作成
        if safety_aspect == 'Ⅱ' or safety_aspect == 'Ⅲ':
            Progress.objects.create(
                request_id=request_id,
                target='safety',
                present_step=StepMaster.objects.get(step=1301),
                present_division=DepartmentMaster.objects.get(department_cd='A').division_cd,
                present_department='A',
                present_operator='t-akamatsu',
                last_step=StepMaster.objects.get(step=present_step)
            )
        if quality_aspect == 'Ⅱ' or quality_aspect == 'Ⅲ':
            Progress.objects.create(
                request_id=request_id,
                target='quality',
                present_step=StepMaster.objects.get(step=1301),
                present_division=DepartmentMaster.objects.get(department_cd='OPQC').division_cd,
                present_department='OPQC',
                present_operator='m-asoda',
                last_step=StepMaster.objects.get(step=present_step)
            )
    # # # # # 「工務部長承認」(1201) # # # # #

    # # # # # 「所管承認」(1301) # # # # #
    # ①評価レベル2と②評価レベル3で分岐
    elif present_step == 1301:
        safety_aspect = Request.objects.get(id=request_id).safety_aspect
        quality_aspect = Request.objects.get(id=request_id).quality_aspect

        if target == 'safety':
            # 評価レベル2であれば「原課変更実施」(1303)へ
            if safety_aspect == 'Ⅱ':
                Progress.objects.update_or_create(
                    request_id=request_id,
                    target='safety',
                    present_step=present_step,
                    defaults={'present_step': StepMaster.objects.get(step=1303),
                              'last_step': present_step
                              }
                )
            # 評価レベル3であれば「所管承認結果」(1302)へ
            if safety_aspect == 'Ⅲ':
                Progress.objects.update_or_create(
                    request_id=request_id,
                    target='safety',
                    present_step=present_step,
                    defaults={'present_step': StepMaster.objects.get(step=1302),
                              'last_step': present_step
                              }
                )

        if target == 'quality':
            # 評価レベル2であれば「原課変更実施」(1303)へ
            if quality_aspect == 'Ⅱ':
                Progress.objects.update_or_create(
                    request_id=request_id,
                    target='quality',
                    present_step=present_step,
                    defaults={'present_step': StepMaster.objects.get(step=1303),
                              'last_step': present_step
                              }
                )
            # 評価レベル3であれば「所管承認結果」(1302)へ
            if quality_aspect == 'Ⅲ':
                Progress.objects.update_or_create(
                    request_id=request_id,
                    target='quality',
                    present_step=present_step,
                    defaults={'present_step': StepMaster.objects.get(step=1302),
                              'last_step': present_step
                              }
                )

        if Progress.objects.filter(request_id=request_id, present_step=1301).exists() is False:
            Progress.objects.update_or_create(
                request_id=request_id,
                target='request',
                present_step=1202,
                defaults={'present_step': StepMaster.objects.get(step=1401),
                          'last_step': StepMaster.objects.get(step=1201)
                          }
            )
    # # # # # 「所管承認」(1301) # # # # #

    # # # # # 「原課変更実施」(1401) # # # # #
    # 「所管確認評価」(1501)に行く
    elif present_step == 1401:
        safety_aspect = Request.objects.get(id=request_id).safety_aspect
        quality_aspect = Request.objects.get(id=request_id).quality_aspect
        Progress.objects.update_or_create(
            request_id=request_id,
            target='request',
            present_step=present_step,
            defaults={'present_step': StepMaster.objects.get(step=request.POST['next_step']),
                      'present_division': DepartmentMaster.objects.get(department_cd=request.POST['next_department']).division_cd,
                      'present_department': request.POST['next_department'],
                      'present_operator': request.POST['next_operator'],
                      'last_step': StepMaster.objects.get(step=present_step)
                      }
        )

        # 品質評価レベルが2,3の場合は品質プログレス作成。それ以外は安全プログレス作成。
        if quality_aspect == 'Ⅱ' or quality_aspect == 'Ⅲ':
            Progress.objects.create(
                request_id=request_id,
                target='quality',
                present_step=StepMaster.objects.get(step=1501),
                present_division=DepartmentMaster.objects.get(department_cd='OPQC').division_cd,
                present_department='OPQC',
                present_operator='m-asoda',
                last_step=StepMaster.objects.get(step=present_step)
            )
        else:
            Progress.objects.create(
                request_id=request_id,
                target='safety',
                present_step=StepMaster.objects.get(step=1501),
                present_division=DepartmentMaster.objects.get(department_cd='A').division_cd,
                present_department='A',
                present_operator='t-akamatsu',
                last_step=StepMaster.objects.get(step=present_step)
            )

        # ただし安全評価レベルが2,3なら安全プログレスも作成。
        if safety_aspect == 'Ⅱ' or safety_aspect == 'Ⅲ':
            Progress.objects.update_or_create(
                request_id=request_id,
                target='safety',
                present_step=present_step,
                defaults={'present_step': StepMaster.objects.get(step=1501),
                          'present_division': DepartmentMaster.objects.get(department_cd='A').division_cd,
                          'present_department': 'A',
                          'present_operator': 't-akamatsu',
                          'last_step': StepMaster.objects.get(step=present_step)
                          }
            )
    # # # # # 「原課変更実施」(1401) # # # # #

    # # # # # 「所管承認結果」(1302) # # # # #
    elif present_step == 1302:
        Progress.objects.update_or_create(
            request_id=request_id,
            target=target,
            present_step=1302,
            defaults={'present_step': StepMaster.objects.get(step=1303),
                      'last_step': StepMaster.objects.get(step=1302)
                      }
        )
        if Progress.objects.filter(request_id=request_id, present_step=1302).exists() is False:
            Progress.objects.update_or_create(
                request_id=request_id,
                target='request',
                present_step=1202,
                defaults={'present_step': StepMaster.objects.get(step=1401),
                          'last_step': StepMaster.objects.get(step=1201)
                          }
            )
    # # # # # 「所管承認結果」(1302) # # # # #

    # # # # # 「所管確認評価」(1501) # # # # #
    elif present_step == 1501:
        Progress.objects.update_or_create(
            request_id=request_id,
            target=target,
            present_step=1501,
            defaults={'present_step': StepMaster.objects.get(step=1502),
                      'last_step': StepMaster.objects.get(step=1501)
                      }
        )
        if Progress.objects.filter(request_id=request_id, present_step=1501).exists() is False:
            Progress.objects.update_or_create(
                request_id=request_id,
                target='request',
                present_step=1402,
                defaults={'present_step': StepMaster.objects.get(step=1601),
                          'last_step': StepMaster.objects.get(step=1401)
                          }
            )
    # # # # # 「所管確認評価」(1501) # # # # #

    else:
        Progress.objects.update_or_create(
            request_id=request_id,
            target=target,
            present_step=present_step,
            defaults={'present_step': StepMaster.objects.get(step=request.POST['next_step']),
                      'present_division': DepartmentMaster.objects.get(department_cd=request.POST['next_department']).division_cd,
                      'present_department': request.POST['next_department'],
                      'present_operator': request.POST['next_operator'],
                      'last_step': StepMaster.objects.get(step=present_step)
                      }
        )
        # 完了ステップ遷移時requestテーブルに完了日を格納
        if present_step == 1601:
            request_data = Request.objects.get(id=request_id)
            request_data.completion_date = datetime.datetime.now()
            request_data.save()
    return


# logテーブル
def entry_log(request, function_name):
    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']
    function_name = function_name.replace('entry_', '')
    function_name = function_name.replace('function_', '')

    Log(target_id=target,
        target_table_id=request_id,
        step=StepMaster.objects.get(step=present_step),
        action_id=function_name,
        operation_datetime=datetime.datetime.now(),
        operator=request.user,
        operator_department=UserAttribute.objects.filter(username=request.user, lost_flag=0).order_by('display_order').first().division,
        comment=request.POST['comment']
        ).save()
    return


# ***function***
# 承認処理
def function_approval(request):
    print('承認します')
    entry_progress(request)
    return


# 入力完了処理
def function_completed(request):
    print('入力完了します')
    # function_name = request.session['action']
    function_name = 'entry_' + request.session['target']
    globals()[function_name](request)
    entry_progress(request)
    return


# 確認処理
def function_confirm(request):
    print('確認します')
    entry_progress(request)
    return


# 複製処理
def function_copy(request):
    print('複製します')
    return


# 出力処理
def function_print(request):
    print('出力します')
    return


# 却下処理
def function_rejected(request):
    print('却下します')

    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']

    # 現在ステップからステップリレーションの「rejected」のステップ取得
    next_step = StepRelation.objects.get(present_step=present_step, type='rejected', lost_flag=0).next_step_id

    Progress.objects.update_or_create(
        request_id=request_id,
        target=target,
        present_step=present_step,
        defaults={'present_step': StepMaster.objects.get(step=next_step),
                  'present_division': DepartmentMaster.objects.get(department_cd=request.POST['next_department']).division_cd,
                  'present_department': request.POST['next_department'],
                  'present_operator': request.POST['next_operator'],
                  'last_step': StepMaster.objects.get(step=present_step)
                  }
    )

    # メール送信処理
    import email.utils
    from smtplib import SMTP
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from fms.views.common_def_views import is_production_server, output_log_info
    from django.contrib.auth.models import User

    # 送信元情報
    from_address = 'quality_change_management'
    from_name = '品質安全変更管理ツール'

    # logから最後の操作の情報を取得
    action_list = [action.get('action') for action in list(ActionMaster.objects.filter(progress_transition=1, lost_flag=0).values('action'))]
    log = Log.objects.filter(target_table_id=request_id, action_id__in=action_list).order_by('-operation_datetime').first()

    # 送信先情報
    to_address = log.operator + '@iskweb.co.jp'

    # 環境を識別して題名と本文に追加1
    server_msg = ''
    if not is_production_server():
        server_msg = '[テスト環境]'
    mail_body = server_msg + '\n' + '関係者各位(自動送信メール) ' + '\n' + '本変更は下記の理由により却下します。' + '\n' + '「' + request.POST['comment'] + '」' + '\n' + '-以上-'
    subject = server_msg + '(変更管理NO:' + str(request_id) + ')「' + request.POST['title'] + '」却下の件'

    # # メール送信内容をINFOログに残す
    # log_str = '\n'
    # log_str += 'From:<' + from_name + '>' + from_address + '\n'
    # log_str += 'To:' + to_address + '\n'
    # log_str += 'Subject:' + subject + '\n'
    # log_str += 'Body:' + mail_body
    # output_log_info(log_str)
    #
    # if param['to_address'] == '':
    #     msg = '送信先アドレス未設定のため、送信できません！！'
    #     output_log_info(msg)
    #     return msg

    # MIME変換
    mail_msg = MIMEMultipart()
    mail_msg['Subject'] = subject
    mail_msg['From'] = email.utils.formataddr((from_name, from_address))
    mail_msg['To'] = to_address
    mail_msg.attach(MIMEText(mail_body, 'plain', 'utf-8'))

    # SMTPサーバーに接続
    smtp_host = '172.16.110.16'
    smtp_port = 25
    smtpobj = SMTP(smtp_host, smtp_port)
    # smtpobj.login(from_address, password) # ログインは不要
    # メール送信
    # smtpobj.sendmail(from_address, to_address, message) # sendmailだと日本語送信できない
    smtpobj.send_message(mail_msg)
    smtpobj.quit()

    return


# 差戻処理
def function_remand(request):
    print('差戻します')

    # todo コメント入力必須チェック
    # if request.POST['comment'] == '':
    #     return HttpResponse("<script>alert('コメントを入力してください');</script>")

    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']

    # logから最後の操作の情報を取得
    # 案①actionマスタを利用　進捗遷移するアクションの情報を持たせる(progress_transition=1)
    action_list = [action.get('action') for action in list(ActionMaster.objects.filter(progress_transition=1, lost_flag=0).values('action'))]
    log = Log.objects.filter(target_table_id=request_id, action_id__in=action_list).order_by('-operation_datetime').first()
    next_step = log.step_id

    # 案②step_relationを利用　差戻と分かる情報を持たせる(type='prev')
    # next_step = StepRelation.objects.get(present_step=present_step, type='prev', lost_flag=0).next_step_id
    # log = Log.objects.filter(target_table_id=request_id, target_id=target, step_id=next_step).first()

    operator = log.operator
    operator_department = log.operator_department
    operator_division = DepartmentMaster.objects.get(department_cd=operator_department).division_cd

    Progress.objects.update_or_create(
        request_id=request_id,
        target=target,
        present_step=present_step,
        defaults={'present_step': StepMaster.objects.get(step=next_step),
                  'present_division': operator_division,
                  'present_department': operator_department,
                  'present_operator': operator,
                  'last_step': StepMaster.objects.get(step=present_step)
                  }
    )
    return


# 中止処理 却下と同機能のため無くす
# def function_stop(request):
#     print('中止します')
#     return


# 機能検証用
def function_test(request):
    print('テスト機能確認中')

    request_id = request.session['request_id']
    target = request.session['target']
    present_step = request.session['present_step']

    # logから最後の操作の情報を取得
    action_list = [action.get('action') for action in list(ActionMaster.objects.filter(progress_transition=1, lost_flag=0).values('action'))]
    log = Log.objects.filter(target_table_id=request_id, action_id__in=action_list).order_by('-operation_datetime').first()
    print(log.operator)

    return

