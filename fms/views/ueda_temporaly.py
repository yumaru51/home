import datetime
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from fms.models import Progress, DepartmentMaster
from fms.models import UserAttribute, StepMaster, StepRelation, Log
from django.utils.timezone import make_aware
from fms.views.common_def_views import get_next_operator_cs


# 次の進捗工程(step)に進む処理
@login_required
@require_POST
def go_next_step_for_cs(request):

    DIFF_JST_FROM_UTC = 9
    # JST = timezone(timedelta(hours=+9), 'JST')

    # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    now_naive = datetime.datetime.now()
    now = make_aware(now_naive)

    # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
    operator = request.user.username

    # 4G長差戻フラグ
    four_department_send_back_flag = 0
    # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
    this_step = int(request.POST["this_step"])
    if request.POST["action"] == "return" and this_step == 134007001:
        next_step = None
        next_person_id = None
        next_person = None
        next_division = None
        next_department = None
        send_buck_target = request.POST.getlist("next_step[]")
        four_department_send_back_flag = 1
    else:
        next_step = int(request.POST["next_step"])
        next_person_id = int(request.POST["next_person_id"])
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
    target_id = int(request.POST["target_id"])
    this_department = request.POST["this_department"]
    this_division = request.POST["this_division"]
    action = request.POST["action"]
    comment = request.POST["comment"]
    target = request.POST["target"]
    target_budget_id = int(request.POST["target_budget_id"])
    err_count = 0

    # 次作業者データをユーザー属性マスタから取得
    if UserAttribute.objects.filter(id=next_person_id).count() > 0:
        user_attribute_data = UserAttribute.objects.get(id=next_person_id)
        next_person = user_attribute_data.username
    else:
        next_person = None

    # 並行処理FLを定義(「０」)
    parallel_processing_flag = 0

    # 現在の担当部署区分を取得
    this_step_data = StepMaster.objects.get(steo_id=this_step)
    charge_department_class = this_step_data.charge_department_class
    # 次のstep数をカウント
    step_relation_data_num = StepRelation.objects.filter(step_id=this_step).count()

    # 現在の担当部署区分が原課(「BD」)　＆　次のstep数が２以上　＆　targetが「CS」 & 現stepと次stepが違うの時、並行処理FLを「１」
    if charge_department_class == 'BD' and step_relation_data_num > 1 and target == 'CS' and this_step != next_step:
        parallel_processing_flag = 1

    # 進捗状況に対して「target」と「target_id」で該当するものがあれば、呼び出し、なければ新規登録
    progress_data, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=this_step)

    if this_step == next_step:
        progress_data.present_operator = operator
        progress_data.present_department = this_department
        progress_data.present_division = this_division

    elif parallel_processing_flag == 1:
        progress_data.present_operator = 'LegalJurisdictionDep'  # 検討中
        progress_data.present_department = 'LegalJurisdictionDep'  # 検討中
        progress_data.present_division = 'LegalJurisdictionDiv'  # 検討中
        progress_data.present_step = next_step

        # 総務Gの次のstep_idを抽出
        next_step_ga = next_step + 1
        # stepマスターから総務Gの次のstep_idの対象データ抽出
        cs_ga_stepmaster_data = StepMaster.objects.get(step_id=next_step_ga, target='cs')
        # 総務Gの進捗(progress)レコード作成、あれば抽出
        progress_data_ga, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=next_step_ga)

        # 次作業者を抽出
        next_operator = get_next_operator_cs(cs_ga_stepmaster_data.charge_department_class)
        # 各項目を設定
        progress_data_ga.present_step = next_step_ga
        progress_data_ga.present_operator = next_operator.username
        progress_data_ga.last_operation_step = this_step
        progress_data_ga.present_department = cs_ga_stepmaster_data.charge_department_class
        progress_data_ga.present_division = DepartmentMaster.objects.get(department_cd=cs_ga_stepmaster_data.charge_department_class, lost_flag=0).division_cd

        # 環境Gの次のstep_idを抽出
        next_step_env = next_step + 2
        # stepマスターから環境Gの次のstep_idの対象データ抽出
        cs_env_stepmaster_data = StepMaster.objects.get(step_id=next_step_env, target='cs')
        # 環境Gの進捗(progress)レコード作成、あれば抽出
        progress_data_env, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=next_step_env)

        # 次作業者を抽出
        next_operator = get_next_operator_cs(cs_env_stepmaster_data.charge_department_class)
        # 各項目を設定
        progress_data_env.present_step = next_step_ga
        progress_data_env.present_operator = next_operator.username
        progress_data_env.last_operation_step = this_step
        progress_data_env.present_department = cs_env_stepmaster_data.charge_department_class
        progress_data_env.present_division = DepartmentMaster.objects.get(department_cd=cs_env_stepmaster_data.charge_department_class, lost_flag=0).division_cd

        # 安全Gの次のstep_idを抽出
        next_step_sh = next_step + 3
        # stepマスターから安全Gの次のstep_idの対象データ抽出
        cs_sh_stepmaster_data = StepMaster.objects.get(step_id=next_step_sh, target='cs')
        # 安全Gの進捗(progress)レコード作成、あれば抽出
        progress_data_sh, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=next_step_sh)

        # 次作業者を抽出
        next_operator = get_next_operator_cs(cs_sh_stepmaster_data.charge_department_class)

        # 各項目を設定
        progress_data_sh.present_step = next_step_sh
        progress_data_sh.present_operator = next_operator.username
        progress_data_sh.last_operation_step = this_step
        progress_data_sh.present_department = cs_sh_stepmaster_data.charge_department_class
        progress_data_sh.present_division = DepartmentMaster.objects.get(department_cd=cs_sh_stepmaster_data.charge_department_class, lost_flag=0).division_cd

        # 工務Gの次のstep_idを抽出
        next_step_eng = next_step + 4
        # stepマスターから安全Gの次のstep_idの対象データ抽出
        cs_eng_stepmaster_data = StepMaster.objects.get(step_id=next_step_sh, target='cs')
        # 安全Gの進捗(progress)レコード作成、あれば抽出
        progress_data_eng, created = Progress.objects.get_or_create(target=target, target_id=target_id, present_step=next_step_eng)

        # 次作業者を抽出
        next_operator = get_next_operator_cs(cs_eng_stepmaster_data.charge_department_class)
        # 各項目を設定
        progress_data_eng.present_step = next_step_eng
        progress_data_eng.present_operator = next_operator.username
        progress_data_eng.last_operation_step = this_step
        progress_data_eng.present_department = cs_eng_stepmaster_data.charge_department_class
        progress_data_eng.present_division = DepartmentMaster.objects.get(department_cd=cs_eng_stepmaster_data.charge_department_class, lost_flag=0).division_cd

        progress_data.save()
        progress_data_ga.save()
        progress_data_env.save()
        progress_data_sh.save()
        progress_data_eng.save()

    elif next_step == 989999999:  # 「989999999」は仮の値→所管部署承認完了のstep_id

        progress_data_self = Progress.objects.get(target=target, target_id=target_id, present_step=this_step)
        progress_data_self.present_step = next_step
        progress_data_self.present_operator = 'end'
        progress_data_self.last_operation_step = this_step
        progress_data_self.present_department = ''
        progress_data_self.present_division = ''
        progress_data_self.save()

        go_next_step = 0
        with connections['fmsdb'].cursor() as cursor:
            try:
                # DBテーブル「fms_progress」をロック
                cursor.execute("SELECT * FROM fms_progress WITH(TABLOCKX)")
                end_count = 0
                end_count = Progress.objects.filter(target='cs', target_id=target_id, present_step=next_step).count()
                end_count += Progress.objects.filter(target='cs', target_id=target_id, present_step=next_step).count()
                end_count += Progress.objects.filter(target='cs', target_id=target_id, present_step=next_step).count()
                end_count += Progress.objects.filter(target='cs', target_id=target_id, present_step=next_step).count()

                if end_count == 4:
                    # 4部長の承認が下りたら次ステップへの移行を許可
                    go_next_step = 1

            except ImportError as exc:
                err_count = 1

        if end_count == 4:
            # 4部署の承認が完了したら大本の進捗(progress)を次ステップへの移行を許可
            go_next_step = 1

        # 4部長が承認済みの場合
        if go_next_step == 1:
            # targetが「CS」 ＆ target_idが本id ＆ present_operator='LegalJurisdictionDep' で大元の進捗データを抽出
            progress_data = Progress.objects.get(target=target, target_id=target_id, present_operator='LegalJurisdictionDep')
            # 現在のstepから次のstepを抽出
            this_step = progress_data.present_step
            step_relation_data = StepRelation.objects.get(step_id=this_step)
            next_step = step_relation_data.next_step

            progress_data.present_step = next_step
            progress_data.present_operator = next_person
            progress_data.last_operation_step = this_step
            progress_data.present_department = next_department
            progress_data.present_division = next_division
            progress_data.save()

    elif charge_department_class == 'KA&A'and this_step > next_step:
        step_data_BD = StepMaster.objects.filter(target='CS', charge_department_class='BD').Order_By('step_id')
        for step_data_BD in step_data_BD:
            step_relation_data_num = StepRelation.objects.filter(step_id=this_step).count()
            if step_relation_data_num > 1:
                step_data_BD_permit = step_data_BD
                break

        progress_data = Progress.objects.get(target=target, target_id=target_id, present_step=this_step)
        progress_data.present_step = next_step
        progress_data.present_operator = next_person
        progress_data.last_operation_step = this_step
        progress_data.present_department = next_department
        progress_data.present_division = next_division
        progress_data.save()

        # コメントログの確認
        # 対象のチェックシートに関するlogデータ数を取得・・・   取得条件：このチェックシートのログ　　
        #                                                       除外条件：「一時保存」、コメントなし
        log_data_num = Log.objects.filter(target="cs", target_id=target_id, step__gt=step_data_BD_permit.step_id).exclude(action="temporarily_saved").exclude(comment="").count()







        if four_department_send_back_flag == 1:
            for send_buck_target in send_buck_target:
                if send_buck_target == "1":
                    # 総務
                    # 総務G承認状態のステップを呼び出し
                    progress_data_ga = Progress.objects.filter(target='cs', target_id=target_id, present_step=989999999)[0]
                    next_step_ga = next_step + 1
                    # stepマスターから総務Gの次のstep_idの対象データ抽出
                    cs_ga_stepmaster_data = StepMaster.objects.get(step_id=next_step_ga, target='cs')

                    # 次作業者を抽出
                    next_operator = get_next_operator_cs(cs_ga_stepmaster_data.charge_department_class)

                    progress_data_ga.present_step = next_step_ga
                    progress_data_ga.present_operator = next_operator
                    progress_data_ga.last_operation_step = this_step
                    progress_data_ga.present_department = cs_ga_stepmaster_data.charge_department_class
                    progress_data_ga.present_division = DepartmentMaster.objects.get(department_cd=cs_ga_stepmaster_data.charge_department_class, lost_flag=0).division_cd
                    progress_data_ga.save()

                elif send_buck_target == "2":
                    # 環境
                    # 環境G承認状態のステップを呼び出し
                    progress_data_env = Progress.objects.filter(target='cs', target_id=target_id, present_step=989999999)[0]
                    next_step_env = next_step + 2
                    # stepマスターから環境Gの次のstep_idの対象データ抽出
                    cs_env_stepmaster_data = StepMaster.objects.get(step_id=next_step_env, target='cs')

                    # 次作業者を抽出
                    next_operator = get_next_operator_cs(cs_env_stepmaster_data.charge_department_class)

                    progress_data_env.present_step = next_step_env
                    progress_data_env.present_operator = next_operator
                    progress_data_env.last_operation_step = this_step
                    progress_data_env.present_department = cs_env_stepmaster_data.charge_department_class
                    progress_data_env.present_division = DepartmentMaster.objects.get(department_cd=cs_env_stepmaster_data.charge_department_class, lost_flag=0).division_cd
                    progress_data_env.save()

                elif send_buck_target == "3":
                    # 安全
                    # 安全G承認状態のステップを呼び出し
                    progress_data_sh = Progress.objects.filter(target='cs', target_id=target_id, present_step=989999999)[0]
                    next_step_sh = next_step + 3
                    # stepマスターから安全Gの次のstep_idの対象データ抽出
                    cs_sh_stepmaster_data = StepMaster.objects.get(step_id=next_step_sh, target='cs')

                    # 次作業者を抽出
                    next_operator = get_next_operator_cs(cs_sh_stepmaster_data.charge_department_class)

                    progress_data_sh.present_step = next_step_sh
                    progress_data_sh.present_operator = next_operator
                    progress_data_sh.last_operation_step = this_step
                    progress_data_sh.present_department = cs_sh_stepmaster_data.charge_department_class
                    progress_data_sh.present_division = DepartmentMaster.objects.get( department_cd=cs_sh_stepmaster_data.charge_department_class, lost_flag=0).division_cd
                    progress_data_sh.save()

                elif send_buck_target == "4":
                    # 工務
                    # 工務G承認状態のステップを呼び出し
                    progress_data_eng = Progress.objects.filter(target='cs', target_id=target_id, present_step=989999999)[0]
                    next_step_eng = next_step + 4
                    # stepマスターから工務Gの次のstep_idの対象データ抽出
                    cs_eng_stepmaster_data = StepMaster.objects.get(step_id=next_step_eng, target='cs')

                    # 次作業者を抽出
                    next_operator = get_next_operator_cs(cs_eng_stepmaster_data.charge_department_class)

                    progress_data_eng.present_step = next_step_eng
                    progress_data_eng.present_operator = next_operator
                    progress_data_eng.last_operation_step = this_step
                    progress_data_eng.present_department = cs_eng_stepmaster_data.charge_department_class
                    progress_data_eng.present_division = DepartmentMaster.objects.get( department_cd=cs_eng_stepmaster_data.charge_department_class, lost_flag=0).division_cd
                    progress_data_eng.save()

    else:
        progress_data = Progress.objects.get(target=target, target_id=target_id, present_step=this_step)
        progress_data.present_step = next_step
        progress_data.present_operator = next_person
        progress_data.last_operation_step = this_step
        progress_data.present_department = next_department
        progress_data.present_division = next_division
        progress_data.save()

    # ログデータに新規登録
    Log(target=target, target_id=target_id, action=action, operator=operator, operation_datetime=now,step=this_step,comment=comment, operator_department=this_department, operator_division=this_division,budget_id=target_budget_id).save()


    '''

        elif this_step == cs_esh_stepmaster_data.step_id and next_step != this_step:
            # コメントログの確認
            # 対象のチェックシートに関するlogデータ数を取得・・・   取得条件：このチェックシートのログ　　
            #                                                       除外条件：「一時保存」、コメントなし
            log_data_num = Log.objects.filter(target="cs", target_id=target_id,
                                              step__gt=cs_approval_stepmaster_data.step_id).exclude(
                action="temporarily_saved").exclude(comment="").count()



            elif log_data_num > 0:
                # 環境安全衛生部長承認のステップを呼び出し(念のため)
                progress_count = Progress.objects.filter(target=target, target_id=target_id,
                                                         present_step=cs_esh_stepmaster_data.step_id).count()
                if progress_count == 1:
                    progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                         present_step=cs_esh_stepmaster_data.step_id)
                elif progress_count == 0:
                    progress_data = Progress.objects.get(target=target, target_id=target_id,
                                                         present_step=cs_end_step_stepmaster_data.step_id)
                # 次作業者を抽出
                log_data = Log.objects.filter(target=target, target_id=target_id,
                                              step=cs_approval_stepmaster_data.step_id
                                              ).all().order_by('-operation_datetime')[0]

                # 各項目を設定
                progress_data.present_step = cs_order_department_approve_confirm_stepmaster_data.step_id
                progress_data.present_operator = log_data.operator
                progress_data.last_operation_step = this_step
                progress_data.present_department = log_data.operator_department
                progress_data.present_division = log_data.operator_division
                progress_data.last_operator = operator
                progress_data.last_operation_datetime = now
                # 進捗状況のレコードを保存
                progress_data.save()

    # メッセージのためのstep名、アクション名を取得
    step_data = StepMaster.objects.get(step_id=this_step)
    step_name = step_data.step_name
    action_data = ActionMaster.objects.get(action_cd=action)
    action_name = action_data.action_name

    if err_count > 0:
        msg = "システムエラー データベースへのアクセスに失敗しました"
    elif action == "complete" or action == "entry" or action == "entry_complete":
        msg = step_name + action_name
    elif action == "permit" or  action == "accept":
        msg = step_name + "完了"
    else:
        msg = step_name + action_name + "完了"
    '''
    data = {
        'msg': '保留処理を実行しました'
    }
    return JsonResponse(data)
