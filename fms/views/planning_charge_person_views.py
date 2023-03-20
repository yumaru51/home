import datetime
import traceback
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
# from django.db.models import Q･･･削除予定

from fms.models import PlanningChargePerson, User, DataEntryStepMaster
from fms.models import Budget, Progress, Log, BudgetMaterial, MyBudgetMaterialData
from django.utils.timezone import make_aware
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception, get_department_person_list


# 計画担当者情報表示処理
@login_required
@require_POST
def planning_charge_person_data_info(request):
    try:
        # t_username = request.user.username･･･削除予定

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)を含む
        target_id = int(request.POST['target_id'])
        present_step = int(request.POST['this_step'])
        present_step_str = request.POST['this_step']

        # 計画担当者候補リストの情報を取得　設備部管理部工事企画Gのみで絞り込み「CPG」
        user_cpg = get_department_person_list('CPG')

        # 追加予算側の処理の場合は、CWGリストのリストを表示
        user_cwg = get_department_person_list('CWG')

        display_cwg_list_flag = 0
        if present_step_str[0:3] == '136':
            display_cwg_list_flag = 1

        user_list = get_department_person_list('CPG')

        # 主担当者FLに「0」を設定
        main_person_flag = 0

        data = {
            'target_id': target_id,
            'user_cpg': user_cpg,
            'user_cwg': user_cwg,
            'main_person_flag': main_person_flag,
            'display_cwg_list_flag': display_cwg_list_flag,
        }

        # データ編集機能要否判定
        planning_charge_person_edit_action_num = 0
        # 対象stepで「planning_charge_person」がデータ更新対象か確認
        planning_charge_person_edit_action_num = \
            planning_charge_person_edit_action_num + \
            DataEntryStepMaster.objects.filter(step_id=present_step, target_table='planning_charge_person').count()

        edit_flag = 0
        if planning_charge_person_edit_action_num > 0:
            edit_flag = 1

        if edit_flag == 1:
            return render(request, 'fms/parts/budget/budget_planning_charge_person/budget_planning_charge_person_edit.html', data)

        else:
            return render(request, 'fms/parts/budget/budget_planning_charge_person/budget_planning_charge_person_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 担当者を候補リストから選択したときの処理
@login_required
@require_POST
def select_charge_person(request):
    try:
        # JSからのPOST引数を取得
        user_name = request.POST['user_name']

        # ユーザーマスタよりユーザーのフルネームを取得
        user_data = User.objects.get(username=user_name)
        user_full_name = user_data.last_name + "　" + user_data.first_name

        data = {
            'user_name': user_name,
            'user_full_name': user_full_name,
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 担当者登録･更新処理
@login_required
@require_POST
def planning_charge_person_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        action_type = request.POST['action_type']
        budget_id = int(request.POST['budget_id'])

        # 20201202y-kawauchi 担当者未選択のときの処理
        # if 'planning_person' in request.GET:
        #     planning_person = request.GET['planning_person']
        # else:
        #     return JsonResponse({'msg': '担当者を入力してください'})

        planning_charge_ng = False
        planning_person = request.POST['planning_person']
        this_step = int(request.POST['this_step'])
        this_department = request.POST['this_department']
        this_division = request.POST['this_division']
        main_charge_flag = int(request.POST['main_person_flag'])
        planning_charge_person_lists_num = PlanningChargePerson.objects.filter(budget_id=budget_id, main_charge_flag=1,
                                                                               lost_flag=0).exclude(charge_person=planning_person).count()
        if main_charge_flag == 0 and planning_charge_person_lists_num < 1:
            msg = "主担当者を必ず1人登録してください！"
            planning_charge_ng = True
        elif main_charge_flag == 1 and planning_charge_person_lists_num > 0:
            # 既に他の主担当者がいる場合は、主担当者を変更するためにいったん解除する
            main_charge_person_list = PlanningChargePerson.objects.filter(budget_id=budget_id, main_charge_flag=1, lost_flag=0)
            for main_charge_person in main_charge_person_list:
                main_charge_person.main_charge_flag = 0
                main_charge_person.save()

        if planning_charge_ng == False:
            # 「budget_id」、「担当者」で予算計画担当者テーブルからレコード抽出、あれば読み込み、なければ新規登録
            planning_charge_person_data, created = PlanningChargePerson.objects.get_or_create(budget_id=budget_id, charge_person=planning_person)
            # 各項目の値を格納
            planning_charge_person_data.budget_id = budget_id
            planning_charge_person_data.charge_person = planning_person
            planning_charge_person_data.main_charge_flag = main_charge_flag
            planning_charge_person_data.lost_flag = 0
            # 新規登録時の処理
            if action_type == "add":
                planning_charge_person_data.entry_datetime = now
                planning_charge_person_data.entry_operator = operator
                planning_charge_person_data.complete_flag = 0
                msg = "計画担当者新規登録完了！！"
            # 更新時の処理
            else:
                planning_charge_person_data.update_datetime = now
                planning_charge_person_data.update_operator = operator
                msg = "計画担当者新更新完了！！"

            # 予算計画担当者のレコードを保存
            planning_charge_person_data.save()
            # 予算計画担当者の主キー値取得
            planning_person_id = planning_charge_person_data.id

            # コメント作成
            comment = "budget_id : " + str(budget_id) + "、計画担当者 : " + planning_person + ""

            # ログを新規登録
            Log(target='planningchargeperson', target_id=planning_person_id, action=action_type, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=budget_id).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 担当者削除処理
@login_required
@require_POST
def planning_charge_person_delete(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # JST = timezone(timedelta(hours=+9), 'JST')

        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])
        planning_person_id = int(request.POST["planning_person_id"])
        planning_person = request.POST["planning_person"]
        this_step = int(request.POST["this_step"])
        this_budget_id = int(request.POST["this_budget_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # 主キーで予算計画担当者テーブルからレコード抽出
        planning_charge_person_lists_num = PlanningChargePerson.objects.filter(budget_id=budget_id, main_charge_flag=1,
                                                                               lost_flag=0).exclude(charge_person=planning_person).count()

        planning_charge_person_num = PlanningChargePerson.objects.filter(budget_id=budget_id, lost_flag=0).exclude(charge_person=planning_person).count()

        if planning_charge_person_lists_num < 1:
            msg = "主担当者は必ず1人以上登録してください！"
        elif planning_charge_person_num < 1:
            msg = "担当者は必ず1人以上登録してください！"
        else:
            planning_charge_person_data = PlanningChargePerson.objects.get(id=planning_person_id)
            # 無効FLに「1」を設定･･･レコードの無効化
            planning_charge_person_data.lost_flag = 1
            # 予算計画担当者のレコードを保存
            planning_charge_person_data.save()

            msg = "計画担当者データ削除完了！！"
            action_type = "delete"

            # コメント作成
            comment = "budget_id : " + str(budget_id) + "、計画担当者 : " + planning_person + ""

            # ログを新規登録
            Log(target='planningchargeperson', target_id=planning_person_id, action=action_type, operator=operator,
                operation_datetime=now, step=this_step, comment=comment, operator_department=this_department,
                operator_division=this_division, budget_id=this_budget_id
                ).save()

        ary = {
            'msg': msg
        }

        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise


# 登録済計画担当者リスト表示処理
@require_POST
def get_planning_charge_person_list(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])
        budget_id_str = str(budget_id)
        charge_person_list_edit_flag = request.POST["charge_person_list_edit_flag"]
        planning_charge_person_lists = ""
        main_charge_person_name = ""

        # 対象の予算idに対する登録済の計画担当者のレコード数を取得
        planning_charge_person_lists_num = PlanningChargePerson.objects.filter(budget_id=budget_id, lost_flag=0).count()

        # 登録済の計画担当者のレコードがある場合の処理
        if planning_charge_person_lists_num > 0:
            # 対象の予算idに対する登録済の計画担当者のデータを取得
            sql = """ SELECT fms_planningchargeperson.* , fms_user.first_name , fms_user.last_name """
            sql = sql + """ FROM fms_planningchargeperson """
            sql = sql + """ LEFT JOIN fms_user ON fms_planningchargeperson.charge_person = fms_user.username """
            sql = sql + """ WHERE fms_planningchargeperson.lost_flag=0 AND fms_planningchargeperson.budget_id=""" + budget_id_str

            planning_charge_person_lists = PlanningChargePerson.objects.raw(sql)

            # 主担当者名を取得
            main_charge_person_list = PlanningChargePerson.objects.filter(
                budget_id=budget_id, main_charge_flag=1, lost_flag=0)
            if main_charge_person_list.count() > 0:
                main_charge_person_name = main_charge_person_list[0].charge_person

        data = {
            'planning_charge_person_lists_num': planning_charge_person_lists_num,
            'planning_charge_person_lists': planning_charge_person_lists,
            'charge_person_list_edit_flag': charge_person_list_edit_flag,
            'main_charge_person_name': main_charge_person_name
        }

        return render(request, 'fms/parts/budget/budget_planning_charge_person/planning_charge_person_list.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 登録済計画担当者リスト取得
@require_POST
def get_planning_charge_person_user_list(request):
    import json
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST["budget_id"])

        # 対象の予算idに対する登録済の計画担当者のレコード数を取得
        planning_charge_person_lists = PlanningChargePerson.objects.filter(budget_id=budget_id, lost_flag=0)

        # 重要度点数リスト生成
        charge_person_user_id_list = []
        charge_person_user_name_list = []
        index = 0
        for planning_charge_person in planning_charge_person_lists:
            user_data = User.objects.get(username=planning_charge_person.charge_person)
            planning_person_full_name = user_data.last_name + "　" + user_data.first_name
            charge_person_user_id_list.append(planning_charge_person.charge_person)
            charge_person_user_name_list.append(planning_person_full_name)
        ary = {
            'charge_person_user_id_list': charge_person_user_id_list,
            'charge_person_user_name_list': charge_person_user_name_list
        }

        # ary = {
        #     'charge_person_user_id_list': json.dumps(charge_person_user_list)
        #     'charge_person_user_id_list': json.dumps(charge_person_user_list)
        # }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 登録済計画担当者の詳細表示処理
@require_POST
def planning_charge_person_detail(request):
    try:
        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        charge_person_id = int(request.POST["charge_person_id"])

        # 主キーの値で予算計画担当者テーブルからレコード抽出
        planning_charge_person_data = PlanningChargePerson.objects.get(id=charge_person_id)
        # 各項目の値を取得
        planning_person = planning_charge_person_data.charge_person
        charge_person = planning_charge_person_data.charge_person
        # ユーザーのフルネームを取得
        user_data = User.objects.get(username=planning_person)
        planning_person_full_name = user_data.last_name + "　" + user_data.first_name

        main_person_flag = planning_charge_person_data.main_charge_flag
        # 主キーの値を再取得･･･不要か？(「charge_person_id」と同じ値)
        planning_person_id = planning_charge_person_data.id

        data = {
            'planning_person': planning_person,
            'planning_person_full_name': planning_person_full_name,
            'main_person_flag': main_person_flag,
            'planning_person_id': planning_person_id
        }

        return JsonResponse(data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

