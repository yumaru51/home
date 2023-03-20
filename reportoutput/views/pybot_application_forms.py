import subprocess


def equipment_borrowing_application(command):
    response = "パソコン・機器借用申請書の処理"
    subprocess.Popen(['start', r'\\yintrasrv\html\gyomukanri\RENTAL.docx'], shell=True)
    return response


def non_standard_software_usage_application(command):
    response = "標準外ソフト使用申請書の処理"
    return response


def application_forms_command(command):
    application_forms, type = command.split()
    if 'パソコン・機器借用申請書' in type:
        response = equipment_borrowing_application(command)
    if '標準外ソフト使用申請書' in type:
        response = non_standard_software_usage_application(command)
    return response
