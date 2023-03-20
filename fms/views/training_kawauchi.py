import datetime
import mimetypes
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# Oracle接続
import cx_Oracle
from fms.views.common_def_views import convert_charge_department
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


def test(request, id, name):
    if id == 1:
        msg = '<b>てすと入力です</b>'
    elif id == 2:
        msg = '<u>てすと入力です</u>'
    elif id == 3:
        msg = '<s>てすと入力です</s>'
    else:
        id = 0
        msg = 'IDを1～3で選択して'

    # user = User.objects.exclude(username='y-kawauchi')
    # user = User.objects.exclude(username=<y-kawauchi>,<sh-imamura>)
    # test1 = ['y-kawauchi', 'sh-imamura']
    # test2 = User.objects.filter(username__in=test).values()
    # user = User.objects.exclude(username__in=test)


    # if 'NAME' in request.GET:
    #     name = request.GET['NAME']
    # else:
    #     name = 'なし'

    # from fms.models import PlanningChargePerson
    # if PlanningChargePerson.objects.filter(budget_id=id).count() == 0:
    #     msg = 'データがありません。'
    # else:
    #     msg = 'データあります。'

    data = {
        'id': id,
        'name': name,
        'msg': msg,
    }
    return render(request, 'fms/parts/training/kawauchi/TEST.html', data)


# 「対応要請」画面を表示
@login_required
@require_POST
def ResponseRequest(request):
    # ログインユーザー情報取得
    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name

    # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
    target_unique_id = int(request.POST['target_unique_id'])
    # target_unique_id = 0
    new_step = int(request.POST['new_step'])
    user_division_cd = request.POST['user_division_cd']
    user_department_cd = request.POST['user_department_cd']
    user_authority = int(request.POST['user_authority'])
    confirm_user = request.POST['confirm_user']
    permit_user = request.POST['permit_user']
    level5_step_id = int(request.POST['level5_step_id'])


    # 20201125y-kawauchi 初期値(_default)
    if DepartmentMaster.objects.filter(lost_flag=0, department_cd=user_department_cd).count() == 1:
        division_default = DepartmentMaster.objects.get(lost_flag=0, department_cd=user_department_cd)
    else:
        division_default = ''

    if UserAttribute.objects.filter(username=request.user.username).count() == 1:
        discoverer_default = UserAttribute.objects.get(username=request.user.username)
    else:
        discoverer_default = ''

    # 20201118y-kawauchi Oracle接続
    HOST = "yplantia"
    PORT = 1521
    SVS = "PLANTIAU"
    tns = cx_Oracle.makedsn(HOST, PORT, service_name =SVS)
    conn = cx_Oracle.connect("PLANTIA44", "PLANTIA44", tns)
    cur = conn.cursor()

    # 20201125y-kawauchi 参照(テーブル名大文字)
    DEPARTMENTMASTER = DepartmentMaster.objects.filter(lost_flag=0).all().order_by('display_order')
    DISCOVERER = UserAttribute.objects.all()
    cur.execute("""SELECT MGT_CLS, MGT_CLS_DESC FROM MGT_CLS_MST""")
    MGT_CLS_MST = cur.fetchall()
    cur.execute("""SELECT FCLTY_CD, FCLTY_NM FROM FCLTY_CD""")
    FCLTY_CD = cur.fetchall()
    cur.execute("""SELECT EQPT_BASIC_MST.EQPT_ID, EQPT_BASIC_MST.EQPT_NM FROM EQPT_BASIC_MST WHERE EQPT_BASIC_MST.FCLTY_CD = 'SF2'""")
    EQPT_BASIC_MST = cur.fetchall()
    cur.execute("""SELECT CONDITION_CD, CONDITION_DESC FROM CONDITION_CD WHERE CONDITION_CD.MGT_CLS = 'M'""")
    CONDITION_CD = cur.fetchall()

    # 新規登録(target_mainte_id=0)を判定
    # 新規ではないときの処理
    if target_unique_id > 0:
        # 対象データの現在の工程IDを取得
        mainte_manage_data = CsManage.objects.get(id=target_unique_id)
        mainte_general_affairs_data = CsGeneralAffairs.objects.get(mainte_no=mainte_manage_data.mainte_no)
        # 工場立地法
        if mainte_general_affairs_data.factory_location_act is not None:
            factory_location_act = mainte_general_affairs_data.factory_location_act
        else:
            factory_location_act = False

        # 工場立地法_設置/変更
        if mainte_general_affairs_data.motive is not None:
            factory_location_act_motive = mainte_general_affairs_data.motive
        else:
            factory_location_act_motive = "設置/変更"

        # 港湾法
        if mainte_general_affairs_data.port_harbour_act is not None:
            port_harbour_act = mainte_general_affairs_data.port_harbour_act
        else:
            port_harbour_act = False

        # 港則法
        if mainte_general_affairs_data.port_regulations is not None:
            port_regulations = mainte_general_affairs_data.port_regulations
        else:
            port_regulations = False

        # 市中高層建築物等条例
        if mainte_general_affairs_data.buildings_regulations is not None:
            buildings_regulations = mainte_general_affairs_data.buildings_regulations
        else:
            buildings_regulations = False

        # 市都市景観条例
        if mainte_general_affairs_data.cityscape_regulations is not None:
            cityscape_regulations = mainte_general_affairs_data.cityscape_regulations
        else:
            cityscape_regulations = False

        # 備考
        if mainte_general_affairs_data.note is not None:
            note = mainte_general_affairs_data.note
        else:
            note = ""

        # rev_no
        # チェックシートデータののRevNO取得
        mainte_rev_no = mainte_general_affairs_data.mainte_rev_no

        # 継承する値を取得
        mainte_no = mainte_general_affairs_data.mainte_no
        str_mainte_no = str(mainte_no)
        target_budget_id = mainte_manage_data.budget_id
        str_target_budget_id = str(target_budget_id)
        budget_data = Budget.objects.get(budget_id=target_budget_id)
        present_step_data = Progress.objects.get(target_id=mainte_no, target='mainte')
        present_step = present_step_data.present_step
        step_data = StepMaster.objects.get(step_id=present_step)
        step_name = step_data.step_name
        previous_step = step_data.previous_step
        charge_department_class = convert_charge_department(step_data.charge_department_class)

        charge_name = mainte_manage_data.budget_charge_id
        if charge_name is not None:
            charge_data = User.objects.get(username=charge_name)
        else:
            charge_data = budget_data.budget_department_charge_person_id
        mainte_department = mainte_manage_data.wo_department_id
        if mainte_department is None:
            mainte_department = budget_data.budget_main_department_id
        # department_data = DepartmentMaster.objects.get(department_cd=mainte_department)
        department_name = department_data.department_name
        if charge_department_class == 'BD':
            next_division = department_data.division_cd
            next_department = department_data.department_cd
        else:
            next_division = ""
            next_department = charge_department_class

        # rev_noの古い同じ予算IDのデータの有無を確認
        old_mainte_data_num = CsManage.objects.filter(mainte_no=mainte_no, lost_flag=1).count()

    else:
        # 新規登録時処理
        mainte_general_affairs_data = ""
        str_mainte_no = ""
        str_target_budget_id = ""
        # 工場立地法
        factory_location_act = False

        # 工場立地法_設置/変更
        factory_location_act_motive = "設置/変更"

        # 港湾法
        port_harbour_act = False

        # 港則法
        port_regulations = False

        # 市中高層建築物等条例
        buildings_regulations = False

        # 市都市景観条例
        cityscape_regulations = False

        # 備考
        note = ""

        mainte_no = 0
        mainte_rev_no = 0
        department_name = ""
        step_name = ""
        previous_step = 0
        present_step = new_step
        next_division = user_division_cd
        next_department = user_department_cd
        charge_department_class = "BD"
        charge_data = ""
        charge_name = ""
        old_mainte_data_num = 0

    # マスタソースとなるリスト抽出
    # 工場立地法_設置/変更リスト
    factory_location_act_motive_list = FactoryLocationActMotiveMaster.objects.filter(lost_flag=0).all()
    # factory_location_act_motive_list = FactoryLocationActMotiveMaster.objects.all()

    # rev_no比較
    if old_mainte_data_num > 0:
        old_mainte_data = CsManage.objects.filter(mainte_no=mainte_no, lost_flag=1).all().order_by('-id')[0]
    else:
        old_mainte_data = ""

    # データ編集機能要否判定
    mainte_edit_action_num = 0

    mainte_edit_action_num = mainte_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step,
                                                                                 target_table='mainte_general_affairs').count()

    edit_flag = 0

    if mainte_edit_action_num > 0:
        edit_flag = 1

    # データ保存
    data = {
        'mainte_general_affairs_data': mainte_general_affairs_data,
        'old_mainte_data_num': old_mainte_data_num,
        'old_mainte_data': old_mainte_data,
        't_username': t_username,
        't_user_last_name': t_user_last_name,
        't_user_first_name': t_user_first_name,
        'department_name': department_name,
        'charge_name': charge_name,
        'charge_data': charge_data,
        'step_name': step_name,
        'previous_step': previous_step,
        'charge_department_class': charge_department_class,
        'next_division': next_division,
        'next_department': next_department,
        'factory_location_act': factory_location_act,
        'factory_location_act_motive': factory_location_act_motive,
        'factory_location_act_motive_list': factory_location_act_motive_list,
        'port_harbour_act': port_harbour_act,
        'port_regulations': port_regulations,
        'buildings_regulations': buildings_regulations,
        'cityscape_regulations': cityscape_regulations,
        'mainte_no': str_mainte_no,
        'target_budget_id': str_target_budget_id,
        # 'relation_budget_id': str_relation_budget_id,
        'target_id': mainte_no,
        # 'user_authority': user_authority,
        # 'confirm_user': confirm_user,
        # 'permit_user': permit_user,
        # 'level5_step_id': level5_step_id,
        'note': note,
        'mainte_rev_no': mainte_rev_no,
        # 'edit_flag': edit_flag,


        # 20201125y-kawauchi 初期値(_default)
        'division_default': division_default,
        'discoverer_default': discoverer_default,

        # 20201124y-kawauchi DB参照 テーブル名(API,SQL)
        'DEPARTMENTMASTER': DEPARTMENTMASTER,
        'DISCOVERER': DISCOVERER,

        'MGT_CLS_MST': MGT_CLS_MST,
        'FCLTY_CD': FCLTY_CD,
        'EQPT_BASIC_MST': EQPT_BASIC_MST,
        'CONDITION_CD': CONDITION_CD,
    }

    if edit_flag == 1:
        return render(request, 'fms/parts/mainte/ResponseRequest/edit.html', data)

    else:
        return render(request, 'fms/parts/mainte/ResponseRequest/info.html', data)


# プルダウン絞り込み機能
@require_POST
def __select__discoverer(request):
    return render(request, 'fms/parts/mainte/ResponseRequest/__select__discoverer.html', {'DISCOVERER': UserAttribute.objects.filter(department=request.POST["department"])})


@require_POST
def __select__status(request):
    cur = cx_Oracle.connect("PLANTIA44", "PLANTIA44", cx_Oracle.makedsn("yplantia", 1521, service_name="PLANTIAU")).cursor()
    cur.execute("""SELECT CONDITION_CD, CONDITION_DESC FROM CONDITION_CD WHERE CONDITION_CD.MGT_CLS = &1""", [request.POST["management_kbn"]])
    CONDITION_CD = cur.fetchall()
    return render(request, 'fms/parts/mainte/ResponseRequest/__select__status.html', {'CONDITION_CD': CONDITION_CD})


@require_POST
def __select__equipment_no(request):
    cur = cx_Oracle.connect("PLANTIA44", "PLANTIA44", cx_Oracle.makedsn("yplantia", 1521, service_name="PLANTIAU")).cursor()
    cur.execute("""SELECT EQPT_BASIC_MST.EQPT_ID, EQPT_BASIC_MST.EQPT_NM FROM EQPT_BASIC_MST WHERE EQPT_BASIC_MST.FCLTY_CD = &1""", [request.POST["factory_name"]])
    EQPT_BASIC_MST = cur.fetchall()
    return render(request, 'fms/parts/mainte/ResponseRequest/__select__equipment_no.html', {'EQPT_BASIC_MST': EQPT_BASIC_MST})


@require_POST
def __select__cost_center(request):
    cur = cx_Oracle.connect("PLANTIA44", "PLANTIA44", cx_Oracle.makedsn("yplantia", 1521, service_name="PLANTIAU")).cursor()
    cur.execute("""SELECT U_M_FCLSECTION.U_FCLSECTIONCD AS 原価センタCD, U_M_FCLSECTION.U_FCLSECTIONNM AS 原価センタ名
                    FROM U_M_DIVNO, U_M_BNFTSECTION, U_M_FCLSECTION
                    WHERE U_M_BNFTSECTION.U_FCLTY_CD = &1
                    AND U_M_BNFTSECTION.U_BNFTSECTIONCD = U_M_FCLSECTION.U_BNFTSECTIONCD
                    GROUP BY U_M_FCLSECTION.U_FCLSECTIONCD, U_M_FCLSECTION.U_FCLSECTIONNM""", [request.POST["factory_name"]])
    U_M_FCLSECTION = cur.fetchall()
    return render(request, 'fms/parts/mainte/ResponseRequest/__select__cost_center.html', {'U_M_FCLSECTION': U_M_FCLSECTION})


@require_POST
def __div__plantia(request):

    # 20201124y-kawauchi データがあれば格納
    if 'factory_name' in request.POST:
        factory_name = request.POST['factory_name']
    else:
        factory_name = ''

    if 'equipment_no' in request.POST:
        equipment_no = request.POST['equipment_no']
    else:
        equipment_no = ''

    cur = cx_Oracle.connect("PLANTIA44", "PLANTIA44", cx_Oracle.makedsn("yplantia", 1521, service_name="PLANTIAU")).cursor()
    cur.execute("""SELECT
    EQPT_BASIC_MST.FCLTY_CD AS 工場コード
    , FCLTY_CD.FCLTY_NM AS 工場名
    , EQPT_BASIC_MST.EQPT_ID AS 機器番号
    , EQPT_BASIC_MST.EQPT_NM AS 機器名称
    , EQPT_BASIC_MST.EQPT_FMLY AS 機器ファミリコード
    , EQPT_FMLY_MST.EQPT_FMLY_NM AS 機器ファミリ名
    , EQPT_BASIC_MST.REGULATION_CD_1 AS 適用法規1
    , REGULATION_CD.REGULATION_NM AS 適用法規名1
    , EQPT_BASIC_MST.REGULATION_CD_2 AS 適用法規2
    , REGULATION_CD.REGULATION_NM AS 適用法規名2
    , EQPT_BASIC_MST.REGULATION_CD_3 AS 適用法規3
    , REGULATION_CD.REGULATION_NM AS 適用法規名3
    , EQPT_BASIC_MST.U_REGULATION_CD_4 AS 適用法規4
    , REGULATION_CD.REGULATION_NM AS 適用法規名4
    , EQPT_BASIC_MST.U_REGULATION_CD_5 AS 適用法規5
    , REGULATION_CD.REGULATION_NM AS 適用法規名5
    , EQPT_BASIC_MST.U_REG_EQPT_NM AS 法定施設名
    , EQPT_BASIC_MST.U_REG_AREA AS 法定エリア
    FROM FCLTY_CD
    INNER JOIN EQPT_BASIC_MST ON FCLTY_CD.FCLTY_CD = EQPT_BASIC_MST.FCLTY_CD
    INNER JOIN EQPT_FMLY_MST ON EQPT_FMLY_MST.EQPT_FMLY = EQPT_BASIC_MST.EQPT_FMLY
    LEFT OUTER JOIN REGULATION_CD ON REGULATION_CD.REGULATION_CD = EQPT_BASIC_MST.REGULATION_CD_1
    LEFT OUTER JOIN REGULATION_CD ON REGULATION_CD.REGULATION_CD = EQPT_BASIC_MST.REGULATION_CD_2
    LEFT OUTER JOIN REGULATION_CD ON REGULATION_CD.REGULATION_CD = EQPT_BASIC_MST.REGULATION_CD_3
    LEFT OUTER JOIN REGULATION_CD ON REGULATION_CD.REGULATION_CD = EQPT_BASIC_MST.U_REGULATION_CD_4
    LEFT OUTER JOIN REGULATION_CD ON REGULATION_CD.REGULATION_CD = EQPT_BASIC_MST.U_REGULATION_CD_5
    WHERE EQPT_BASIC_MST.FCLTY_CD = &1 AND EQPT_BASIC_MST.EQPT_ID = &2 ORDER BY  EQPT_DSTNCT_ID"""
    , (factory_name, equipment_no))
    JOIN_DATA_SOURCE1 = cur.fetchall()
    return render(request, 'fms/parts/mainte/ResponseRequest/__div__plantia.html', {'JOIN_DATA_SOURCE1': JOIN_DATA_SOURCE1})


@require_POST
def __select__person_in_charge(request):
    return render(request, 'fms/parts/mainte/ResponseRequest/__select__person_in_charge.html', {'PERSON_IN_CHARGE': UserAttribute.objects.filter(department=request.POST["department_p"])})
