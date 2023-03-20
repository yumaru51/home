import traceback

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from fms.models import StepNoticeMaster, DepartmentMaster, Work, Budget, Progress, StepMaster, Phenomenon, Measure


# メール送信機能
def mail_send(param):
    import email.utils
    from smtplib import SMTP
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from fms.views.common_def_views import is_production_server, output_log_info
    from django.contrib.auth.models import User

    from_address = param['from_address']
    from_name = param['from_name']

    # 送信先アドレス
    to_user = User.objects.get(username=param['to_address'])
    to_address = to_user.email

    # 環境を識別して題名と本文に追加1
    server_msg = ''
    if not is_production_server():
        server_msg = '[テスト環境]'
    mail_body = server_msg + '\n' + param['body']
    subject = server_msg + param['subject']

    # メール送信内容をINFOログに残す
    log_str = '\n'
    log_str += 'From:<' + from_name + '>' + from_address + '\n'
    log_str += 'To:' + to_address + '\n'
    log_str += 'Subject:' + subject + '\n'
    log_str += 'Body:' + mail_body
    output_log_info(log_str)

    if param['to_address'] == '':
        msg = '送信先アドレス未設定のため、送信できません！！'
        output_log_info(msg)
        return msg

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

    msg = '送信完了'
    return msg


# メール送信機能(画面から呼び出す用)
@login_required
@require_POST
def mail_send_action(request):
    from fms.views.common_def_views import output_log_exception
    try:
        param = {
            'to_address': request.POST['to_address'],
            'subject': request.POST['subject'],
            'body': request.POST['body'],
        }

        msg = mail_send(param)

        ary = {
            'msg': msg
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 進捗通知機能
def step_notice(progress):
    from fms.views.common_def_views import output_log_error
    try:
        # 通知設定確認
        step_id = progress.present_step
        target_id = progress.target
        step_notice_list = StepNoticeMaster.objects.filter(step_id=step_id, target_id=target_id, lost_flag=0)
        if step_notice_list.count() > 0:
            # 進捗通知設定の判定用関数を呼出し
            function_name = step_notice_list[0].check_function
            globals()[function_name](progress, step_notice_list[0])
        # 通知機能での例外は通知せずエラーログのみ記録する(上位の機能に影響を与えないため)
    except Exception:
        output_log_error(traceback.format_exc())
    return


# 汎用進捗関数
def check_notice_target(progress, step_notice_data):
    from fms.models import User
    target_name = step_notice_data.target.target_name
    target_id = progress.target_id
    step_name = step_notice_data.step.step_name
    department_name = DepartmentMaster.objects.filter(department_cd=progress.present_department).first().department_name

    if progress.present_operator is not None:
        user_data = User.objects.filter(username=progress.present_operator).first()
        user_name = user_data.last_name + user_data.first_name
        user_address = progress.present_operator
    else:
        user_name = ''
        user_address = ''

    if progress.last_operator is not None:
        from_user_data = User.objects.filter(username=progress.last_operator).first()
        from_name = '設備管理システム通知:' + from_user_data.last_name + from_user_data.first_name
        from_address = progress.last_operator + '@iskweb.co.jp'
    else:
        from_name = '設備管理システム通知'
        from_address = ''

    mail_body = '通知内容：以下の工程に進捗が進みました。\n'
    mail_body += '対象：' + target_name + '\n'
    mail_body += '対象ID：' + str(target_id) + '\n'
    mail_body += '工程：' + str(step_name) + '\n'
    mail_body += '次部署：' + str(department_name) + '\n'
    mail_body += '次作業者：' + str(user_name) + '\n'
    mail_body += '\n'

    # 基本はprogressの次作業者に通知、送信先アドレスが指定されている場合はそのアドレスに通知
    to_address = user_address
    if step_notice_data.to_address is not None:
        to_address = step_notice_data.to_address

    param = {
        'subject': '【設備管理システム通知】進捗通知',
        'to_address': to_address,
        'from_name': from_name,
        'from_address': from_address,
        'body': mail_body,
    }
    mail_send(param)
    return


# 全工事仕様書予算見積完了判定
def check_notice_work_estimate_complete(progress, step_notice_data):
    from fms.models import User
    # workから予算IDを取得
    work_data = Work.objects.filter(work_id=progress.target_id, lost_flag=0).all().order_by('-id')[0]
    budget_id = work_data.work_budget_id

    # 予算に関連する全ての工事の仕様書予算見積が完了しているか判定
    sql = """ SELECT fms_work.id, fms_work.work_budget_id, fms_work.work_id, fms_progress.present_step """
    sql = sql + """ FROM fms_work """
    sql = sql + """ LEFT JOIN fms_progress ON fms_work.work_id = fms_progress.target_id AND fms_progress.target = 'work' """
    sql = sql + """ WHERE fms_work.lost_flag = 0 AND fms_progress.present_step < 133009904 AND fms_work.work_budget_id ="""
    sql = sql + str(budget_id)
    incomplete_work = Work.objects.raw(sql)
    incomplete_work_num = len(list(incomplete_work))

    # 全工事が仕様書予算見積完了したら、メール通知
    if incomplete_work_num < 1:
        budget_data = Budget.objects.filter(budget_id=budget_id, lost_flag=0).order_by('-id')[0]
        budget_progress = Progress.objects.get(target='budget', target_id=budget_id)
        step_master_data = StepMaster.objects.get(step_id=budget_progress.present_step, lost_flag=0)
        mail_body = '通知内容：全工事の仕様書予算見積が完了しました。予算見積を進めてください。\n'
        mail_body += '予算名：' + str(budget_data.budget_name) + '\n'
        mail_body += '予算ID：' + str(budget_data.budget_id) + '\n'
        mail_body += '予算工程：' + str(step_master_data.step_name) + '\n'
        mail_body += '\n'
        mail_body += '完了工事名：' + str(work_data.work_name) + '\n'
        mail_body += '完了工事ID：' + str(work_data.work_id) + '\n'
        mail_body += '\n'

        if progress.last_operator is not None:
            from_user_data = User.objects.filter(username=progress.last_operator).first()
            from_name = '設備管理システム通知:' + from_user_data.last_name + from_user_data.first_name
            from_address = progress.last_operator + '@iskweb.co.jp'
        else:
            from_name = '設備管理システム通知'
            from_address = ''

        # 基本はprogressの次作業者に通知、送信先アドレスが指定されている場合はそのアドレスに通知
        to_address = budget_progress.present_operator
        if step_notice_data.to_address is not None:
            to_address = step_notice_data.to_address

        param = {
            'subject': '【設備管理システム通知】仕様書予算見積完了',
            'to_address': to_address,
            'from_name': from_name,
            'from_address': from_address,
            'body': mail_body,
        }
        mail_send(param)
    return


# 故障対応メール通知共通処理
def send_notice_ph(from_progress, to_progress, mail_data):
    from fms.models import User
    from plantia.models import MasterLocation
    from fms.views.common_def_views import get_return_log_data

    # 案件情報
    phenomenon_id = from_progress.target_id
    phenomenon_data = Phenomenon.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id').first()
    measure_data = Measure.objects.filter(phenomenon_id=phenomenon_id, lost_flag=0).order_by('-id').first()
    facility_data = MasterLocation.objects.get(m_location_skey=phenomenon_data.m_location_skey)

    # 進捗状況
    step_master_data = StepMaster.objects.get(step_id=to_progress.present_step, lost_flag=0)
    department_name = DepartmentMaster.objects.filter(
        department_cd=to_progress.present_department).first().department_name
    user_data = User.objects.filter(username=to_progress.present_operator).first()
    user_name = user_data.last_name + user_data.first_name

    # 通知先ユーザー
    if mail_data['to_user'] == '次作業者':
        to_address = to_progress.present_operator
    elif mail_data['to_user'] == '原課担当者':
        to_address = measure_data.work_order_department_charge_person.username
    elif mail_data['to_user'] == '工事実施前CS確認者':
        # 小口CS法令施設確認のentry操作者を取得(差戻のログ検索メソッドを利用)
        step_target_data = StepMaster.objects.get(step_id=233001001, lost_flag=0)
        ans = get_return_log_data('phenomenon', phenomenon_id, step_target_data.step_id, step_target_data.target)
        if ans['success_flag'] == 1:
            to_address = ans['last_operator']
        else:
            to_address = ''
    else:
        to_address = from_progress.present_operator

    # 送信者情報
    if from_progress.last_operator is not None:
        from_user_data = User.objects.filter(username=from_progress.last_operator).first()
        from_name = '設備管理システム通知:' + from_user_data.last_name + from_user_data.first_name
        from_address = from_progress.last_operator + '@iskweb.co.jp'
    else:
        from_name = '設備管理システム通知'
        from_address = ''

    # メール内容
    mail_subject = mail_data['subject']
    mail_detail = mail_data['detail']
    mail_body = f'通知内容：{mail_detail} \n'
    mail_body += '\n'
    mail_body += '進捗状況\n'
    mail_body += f'工程：{step_master_data.step_name}\n'
    mail_body += f'次部署：{department_name}\n'
    mail_body += f'次作業者：{user_name}\n'
    mail_body += '\n'
    mail_body += '案件情報\n'
    mail_body += f'案件名：{phenomenon_data.project_title}\n'
    mail_body += f'依頼ID：{phenomenon_data.phenomenon_id}\n'
    mail_body += f'原課担当部署：{measure_data.work_order_charge_department.department_name}\n'
    mail_body += f'原課担当者：{measure_data.work_order_department_charge_person}\n'
    mail_body += f'工場：{facility_data.location_nm_1}\n'
    mail_body += f'工事/依頼内容：\n'
    mail_body += f'{measure_data.measure_order_detail}'

    param = {
        'subject': f'【設備管理システム通知：故障対応】{mail_subject}（{phenomenon_data.phenomenon_id}:{phenomenon_data.project_title}）',
        'to_address': to_address,
        'from_name': from_name,
        'from_address': from_address,
        'body': mail_body,
    }
    mail_send(param)
    return


# 故障対応 汎用進捗通知
def check_notice_ph_target(progress, step_notice_data):
    # 担当者にメール通知
    mail_data = {
        'subject': '進捗通知',
        'detail': '以下の工程に進捗が進みました。',
        'to_user': '次作業者',
    }
    send_notice_ph(progress, progress, mail_data)
    return


# 所管部署届出チェック完了判定
def check_notice_ph_nc_complete(progress, step_notice_data):
    phenomenon_id = progress.target_id

    # 所管部署の進捗状況判定
    department_progress_complete_flag = 1
    progress_list = Progress.objects.filter(target__startswith='ph_nc_', target_id=phenomenon_id)
    for progress_data in progress_list:
        if progress_data.present_step != 233002091:
            department_progress_complete_flag = 0

    # 全所管部署がチェック完了したら、担当者にメール通知
    if department_progress_complete_flag == 1:
        ph_nc_progress = Progress.objects.get(target='ph_nc', target_id=phenomenon_id)
        mail_data = {
            'subject': '所管部署の届出チェック完了',
            'detail': '所管部署の届出チェックが完了しました。工事実施決裁を行ってください。',
            'to_user': '次作業者',
        }
        send_notice_ph(progress, ph_nc_progress, mail_data)

    return


# 届出チェック完了判定
def check_notice_ph_nc_permit_complete(progress, step_notice_data):
    phenomenon_id = progress.target_id
    phenomenon_progress_data = Progress.objects.filter(target='phenomenon', target_id=phenomenon_id).order_by(
        'present_step').first()

    # 原課担当者に通知
    mail_data = {
        'subject': '小口工事実施前チェック完了',
        'detail': '小口工事実施前チェックが完了しました。',
        'to_user': '工事実施前CS確認者',
    }
    send_notice_ph(progress, phenomenon_progress_data, mail_data)

    # 現在の進捗が小口依頼の場合には、担当者に通知
    if phenomenon_progress_data.present_step == 232001001:
        mail_data = {
            'subject': '小口工事実施前チェック完了',
            'detail': '小口工事実施前チェックが完了しました。小口依頼を行ってください。',
            'to_user': '次作業者',
        }
        send_notice_ph(progress, phenomenon_progress_data, mail_data)

    return


# 届出チェック中止時通知
def check_notice_ph_nc_cancel_complete(progress, step_notice_data):
    phenomenon_id = progress.target_id
    phenomenon_progress_data = Progress.objects.filter(target='phenomenon', target_id=phenomenon_id).order_by(
        'present_step').first()

    # 原課担当者に通知
    mail_data = {
        'subject': '小口工事実施前チェック中止',
        'detail': '小口工事実施前チェックが中止されました。中止理由を確認してください。',
        'to_user': '工事実施前CS確認者',
    }
    send_notice_ph(progress, phenomenon_progress_data, mail_data)

    # 担当者に通知
    mail_data = {
        'subject': '小口工事実施前チェック中止',
        'detail': '小口工事実施前チェックが中止されました。中止理由を確認してください。',
        'to_user': '次作業者',
    }
    send_notice_ph(progress, phenomenon_progress_data, mail_data)

    return
