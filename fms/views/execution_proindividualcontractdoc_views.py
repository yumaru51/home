# datetimeをインポート
import datetime
import traceback
# ログインユーザーを使用するmoduleをインポート
from django.contrib.auth.decorators import login_required
# django関係のreturn関係のmoduleをインポート
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
# postからの引数を使用できるmoduleをインポート
from django.views.decorators.http import require_POST
# formsをインポート
from fms.forms import BudgetEditFormLeft, BudgetEditFormCenter, BudgetEditFormRight
# modelesをインポート
from fms.models import ApplicationClassMaster, BudgetClassMaster, PurposeClassMaster, StepAction
from fms.models import BudgetConditionMaster, ProcessMaster, StepMaster, ActionMaster, FunctionMaster
from fms.models import MaterialStateMaster, ConcentrationUnitMaster, PressureUnitMaster, DataEntryStepMaster
from fms.models import WorkClassMaster, RegulationMaster
from fms.models import Budget, BudgetCondition, Progress, Log, BudgetMaterial, BudgetRequiredFunction, Work
# from django.contrib.auth.models import User
# from common.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute
from fms.models import BusinessYearMaster, DepartmentMaster, PeriodClassMaster, DivisionMaster, UserAttribute, User
from fms.models import FreeSpecDetail, SubmissionDocument, Estimate, Supplies, WorkLaw
from fms.models import WorkSpecMEX, PlanningChargePerson
from fms.models import UserAttribute, DivisionMaster, DepartmentMaster, StepRelation, StepDisplayItem, Work
from fms.models import ProBudgetUnit, ProSpecificationUnit, ProEstimates, ProVendorEvaluation, ProIndividualContractDoc, ErpConstruction, MCFrame, ErpRelation
from fms.models import ProInspectionResults, ProConstructionPrep, ProConstructionQualityResults
from fms.models import TaxMaster, SupplierMaster
from gcsystem.models import AccountCodeMaster, InstructionNoMaster, CostCenterMaster, AccountCodeDefinitionMaster, ItemGroupMaster, ItemMaster, \
    VendorMaster, UserMaster
from .execution_views import execution_work_common_data
# from fms.views.erpitemconstruction_views import item_construction_record_entry
from django.db.models import Q, Max
import datetime
import jaconv
from django.utils.timezone import make_aware
from common.common_def import date_to_many_type
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception
from fms.views.notice_mail_views import step_notice


# 個別契約書類テーブル詳細画面
@login_required
@require_POST
def execution_proindividualcontractdoc_data_info(request):
    try:
        # now = datetime.date.today()
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        # ユーザー情報取得･･･「isk_tools_base」DBの「auth_user」テーブルの情報
        t_username = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)
        budget_id = int(request.POST['budget_id'])
        construction_id = int(request.POST['construction_id'])
        present_step = int(request.POST['this_step'])
        level5_step_id = int(request.POST['level5_step_id'])
        copy_check = int(request.POST['copy_check'])
        user_list = User.objects.filter(lost_flag=0)
        erp_errormsg = ''
        purchase_order_no = ''

        # ベース部分(ProSpecificationUnit)の読込(そのままrenderに引き渡すこと)
        base_data = execution_work_common_data(budget_id, construction_id)

        proindividualcontractdoc_data_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 対象のデータがある場合
        if proindividualcontractdoc_data_num > 0:
            proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)

            # 各項目の値を取得
            rev_no = proindividualcontractdoc_data.rev_no if proindividualcontractdoc_data.rev_no is not None else ""
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = proindividualcontractdoc_data.sub_id if proindividualcontractdoc_data.sub_id is not None else ""
            order_classification = proindividualcontractdoc_data.order_classification if proindividualcontractdoc_data.order_classification is not None else ""
            if proindividualcontractdoc_data.tax_kbn is None:
                tax_kbn = ''
                tax_kbn_textcontent = ''
            else:
                tax_kbn = proindividualcontractdoc_data.tax_kbn
                tax_kbn_textcontent = TaxMaster.objects.get(tax_cd=tax_kbn).text
            order_issuance_date = proindividualcontractdoc_data.order_issuance_date if proindividualcontractdoc_data.order_issuance_date is not None else ""
            if proindividualcontractdoc_data.order_creator is not None:
                order_creator = proindividualcontractdoc_data.order_creator
                order_creator_text = User.objects.get(username=order_creator, lost_flag=0)
                order_creator_text = order_creator_text.last_name + '　' + order_creator_text.first_name
            else:
                order_creator = ''
                order_creator_text = ''
            individual_contract_terms = proindividualcontractdoc_data.individual_contract_terms if proindividualcontractdoc_data.individual_contract_terms is not None else ""
            order_no = proindividualcontractdoc_data.order_no if proindividualcontractdoc_data.order_no is not None else ""
            construction_classification = proindividualcontractdoc_data.construction_classification if proindividualcontractdoc_data.construction_classification is not None else ""
            order_data = proindividualcontractdoc_data.order_data if proindividualcontractdoc_data.order_data is not None else ""
            order_confirmation_data = proindividualcontractdoc_data.order_confirmation_data if proindividualcontractdoc_data.order_confirmation_data is not None else ""
            vendor_code = proindividualcontractdoc_data.vendor_code if proindividualcontractdoc_data.vendor_code is not None else ""
            if vendor_code == '':
                vendor_code_textcontent = ''
            else:
                vendor_num = SupplierMaster.objects.filter(supplier_cd=vendor_code).count()
                if vendor_num == 1:
                    vendor_code_textcontent = SupplierMaster.objects.get(supplier_cd=vendor_code).supplier_name
                else:
                    vendor_code_textcontent = '不適切な選択'
        else:
            proindividualcontractdoc_data = ''
            rev_no = 0
            budget_no = base_data['budget_no']
            budget_name = base_data['budget_name']
            sub_id = base_data['sub_id']
            order_classification = ''
            tax_kbn = ''
            tax_kbn_textcontent = ''
            order_issuance_date = ''
            order_creator = request.user.username
            order_creator_user = User.objects.get(username=request.user.username, lost_flag=0)
            order_creator_text = order_creator_user.last_name + '　' + order_creator_user.first_name
            individual_contract_terms = ''
            order_no = ''
            construction_classification = ''
            order_data = ''
            order_confirmation_data = ''
            vendor_code = ''
            vendor_code_textcontent = ''

        if order_creator is not "":
            # 注文書作成者
            user_data = User.objects.get(username=order_creator)
            order_creator_text = user_data.last_name + '　' + user_data.first_name

        # 無効となった(=1つ前のrev_noの)対象のデータのレコード数を取得
        old_proindividualcontractdoc_data_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).count()
        # 無効となった(=1つ前のrev_noの)対象のデータのレコードがある場合
        if old_proindividualcontractdoc_data_num > 0:
            # 無効となった(=1つ前のrev_noの)対象のデータを取得
            old_proindividualcontractdoc_data = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=1).all().order_by('-id')[0]
        else:
            old_proindividualcontractdoc_data = ""

        # データ編集機能要否判定
        work_edit_action_num = 0
        # 対象stepで「ProIndividualContractDoc」がデータ更新対象か確認
        work_edit_action_num = work_edit_action_num + DataEntryStepMaster.objects.filter(step_id=present_step, target_table='proindividualcontractdoc').count()

        if level5_step_id == 920000000 or level5_step_id == 212001000:
            work_edit_action_num = 0

        edit_flag = 0

        # 更新対象
        if work_edit_action_num > 0:
            edit_flag = 1

        # 購買データ　新規更新関係なく現在データを参照する
        erpconstruction_num = ErpConstruction.objects.filter(order_id=request.POST["target_work_id"]).count()

        # 20210107 y-kawauchi 工事データがまだ作られていないとき
        construction_start_date = ProSpecificationUnit.objects.get(budget_id=budget_id,
                                                                   construction_id=request.POST['target_work_id'],
                                                                   lost_flag=0).desired_construct_period_from \
            if request.POST['target_work_id'] is not '0' else None
        item_detail_text = '工事ID：' + str(request.POST['target_work_id']) if request.POST['target_work_id'] is not '0' else None
        proestimates_num = ProEstimates.objects.filter(budget_id=budget_id, construction_id=request.POST['target_work_id'], lost_flag=0).count()
        if proestimates_num > 0:
            storage_space_rem = ProEstimates.objects.get(budget_id=budget_id,
                                                     construction_id=request.POST['target_work_id'],
                                                     lost_flag=0
                                                     ).fixed_delivery_location if request.POST['target_work_id'] is not '0' else None
        else:
            storage_space_rem = ""
        # storage_space_rem = ProSpecificationUnit.objects.get(budget_id=budget_id,
        #                                                      construction_id=request.POST['target_work_id'],
        #                                                      lost_flag=0
        #                                                      ).delivery_location if request.POST['target_work_id'] is not '0' else None

        # 新規作成時
        if erpconstruction_num == 0:
            cost_center = ''
            cost_center_textcontent = ''
            if request.POST['target_work_id'] is not '0':
                instruction_code = budget_no
            else:
                instruction_code = None

            instruction_code_textcontent = ''
            construction_start_date = ''
            erp_errormsg = ''

        # 更新時
        elif erpconstruction_num > 0:
            if erpconstruction_num > 1:
                erpconstruction = ErpConstruction.objects.get(order_id=request.POST["target_work_id"], total_price__lt=0)
            else:
                erpconstruction = ErpConstruction.objects.get(order_id=request.POST["target_work_id"])
            total_price = erpconstruction.total_price
            discount_price = erpconstruction.discount_price
            cost_center = erpconstruction.cost_center
            cost_center_textcontent = CostCenterMaster.objects.get(原価センタ=cost_center).原価センタテキスト
            instruction_code = erpconstruction.instruction_code
            instruction_code_textcontent = InstructionNoMaster.objects.get(指図書コード=instruction_code).テキスト短
            purchase_order_no = erpconstruction.purchase_order_no
            if erpconstruction.erp_errormsg is not None and erpconstruction.erp_errormsg is not "":
                erp_errormsg = erpconstruction.erp_errormsg
            else:
                erp_errormsg = ''

        # 20210118 y-kawauchi  候補業者選択機能　対応
        if vendor_code != '':
            confirmed_vendor = vendor_code_textcontent
            vendormaster = SupplierMaster.objects.filter(supplier_name__icontains=confirmed_vendor, lost_flag=0)
        elif ProEstimates.objects.filter(budget_id=budget_id, construction_id=request.POST['target_work_id'], lost_flag=0).exists():
            confirmed_vendor = ProEstimates.objects.get(budget_id=budget_id, construction_id=request.POST['target_work_id'], lost_flag=0).confirmed_vendor
            confirmed_vendor = '' if confirmed_vendor is None else confirmed_vendor
            vendormaster = SupplierMaster.objects.filter(supplier_name__icontains=confirmed_vendor, lost_flag=0)
        else:
            confirmed_vendor = ''
            vendormaster = ''
        vendormaster2 = SupplierMaster.objects.filter(lost_flag=0)
        taxmaster = TaxMaster.objects.filter(lost_flag=0)

        if copy_check == 0:
            # タブ毎のボタン表示対応
            stepdisplayitem_data = StepDisplayItem.objects.get(step=present_step, div_id_name='execution_individualcontract', lost_flag=0)
            this_page = stepdisplayitem_data.page
            action_button_id = 'prospecificationunit' + str(this_page) + '_action_button'
        else:
            this_page = 10
            action_button_id = ''

        file_upload_flag = 0

        if present_step == 241003011:
            file_upload_flag = 1

        data = {
            'work_common_data': base_data,
            'proindividualcontractdoc_data_num': proindividualcontractdoc_data_num,
            'proindividualcontractdoc_data': proindividualcontractdoc_data,
            'old_proindividualcontractdoc_data_num': old_proindividualcontractdoc_data_num,
            'old_proindividualcontractdoc_data': old_proindividualcontractdoc_data,
            't_username': t_username,
            'budget_id': budget_id,
            'rev_no': rev_no,
            'budget_no': budget_no,
            'budget_name': budget_name,
            'construction_id': construction_id,
            'sub_id': sub_id,
            # 20201205y-kawauchi DB参照
            'vendormaster': vendormaster,
            'vendormaster2': vendormaster2,
            'taxmaster': taxmaster,
            'vendor_code': vendor_code,
            'vendor_code_textcontent': vendor_code_textcontent,
            'cost_center': cost_center,
            'instruction_code': instruction_code,
            'cost_center_textcontent': cost_center_textcontent,
            'instruction_code_textcontent': instruction_code_textcontent,
            'construction_start_date': construction_start_date,
            'item_detail_text': item_detail_text,
            'storage_space_rem': storage_space_rem,
            'order_classification': order_classification,
            'tax_kbn': tax_kbn,
            'tax_kbn_textcontent': tax_kbn_textcontent,
            'order_issuance_date': order_issuance_date,
            'order_creator': order_creator,
            'order_creator_text': order_creator_text,
            'individual_contract_terms': individual_contract_terms,
            'order_no': order_no,
            'construction_classification': construction_classification,
            'order_data': order_data,
            'order_confirmation_data': order_confirmation_data,
            'this_page': this_page,
            'action_button_id': action_button_id,
            'user_list': user_list,
            'target': request.POST['target'],
            'target_budget_id': request.POST['target_budget_id'],
            'target_work_id': request.POST['target_work_id'],
            'div_id_name': request.POST['div_id_name'],

            'confirmed_vendor': confirmed_vendor,
            'erp_errormsg': erp_errormsg,
            'purchase_order_no': purchase_order_no,
            'file_upload_flag': file_upload_flag,
        }

        if edit_flag == 1:
            return render(request, 'fms/parts/execution/execution_proindividualcontractdoc/execution_proindividualcontractdoc_edit.html', data)
        else:
            return render(request, 'fms/parts/execution/execution_proindividualcontractdoc/execution_proindividualcontractdoc_info.html', data)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 工事納入情報テーブル登録･更新
@login_required
@require_POST
def execution_proindividualcontractdoc_entry(request):
    try:
        DIFF_JST_FROM_UTC = 9
        # # JST = timezone(timedelta(hours=+9), 'JST')
        # now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        now_naive = datetime.datetime.now()
        now = make_aware(now_naive)

        operator = request.user.username

        # JSからのPOST引数を取得・・・数値項目は数値に変換(int関数)、リレーションがかかった項目は、登録は該当するレコードとなる
        this_step = int(request.POST["this_step"])
        next_step = int(request.POST["next_step"])
        next_person = request.POST["next_person"]
        next_division = request.POST["next_division"]
        next_department = request.POST["next_department"]
        comment = request.POST["comment"]
        budget_id = int(request.POST['budget_id'])
        rev_no = request.POST['rev_no']
        construction_id = int(request.POST['construction_id'])
        sub_id = request.POST['sub_id']

        order_issuance_date = request.POST['order_issuance_date']
        order_date = date_to_many_type(order_issuance_date).str_type_date_erp
        order_issuance_date_str = order_issuance_date.replace('年', '-')
        order_issuance_date_str = order_issuance_date_str.replace('月', '-')
        order_issuance_date = order_issuance_date_str.replace('日', '')

        # budget_no=Noneのときの一時処置　budget_noは発注データとして必須だが現時点では入力されないためmsgを表示する
        # budget_noは本仕様書作成後辺りにBudgetテーブルへ自動付与される予定のため、Budgetテーブルを比較する。
        # 工事実行の予算テーブル
        budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
        budget_no = budget_data.budget_no
        if budget_no is None:
            ary = {
                'msg': '「budget_no」を入力してください',
                'flag': '0',
            }
            return JsonResponse(ary)
        elif budget_no[0] != '1' and budget_no[0] != '2':
            ary = {
                'msg': '「budget_no」が正しくありません。管理者に確認してください。',
                'flag': '0',
            }
            return JsonResponse(ary)

        # 工事納入情報テーブルを予算ID, 工事IDの存在チェック
        proindividualcontractdoc_data_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, lost_flag=0).count()
        # 更新
        if proindividualcontractdoc_data_num > 0:
            # 工事納入情報テーブルを予算ID, 工事IDで読込
            proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(budget_id=budget_id, construction_id=construction_id, lost_flag=0)
            new_record = False
        # 新規登録
        else:
            new_record = True

        user_attribute_id = int(request.POST["user_attribute_id"])
        this_department = request.POST["this_department"]
        this_division = request.POST["this_division"]

        # ユーザー権限に登録されている場合の処理･･･普通はされているはず→次作業者、部署、部門データ取得
        if user_attribute_id > 0:
            user_attribute_data = UserAttribute.objects.get(id=user_attribute_id, lost_flag=0)
            next_person = user_attribute_data.username
            next_division = user_attribute_data.division
            next_department = user_attribute_data.department
        else:
            next_department = this_department
            next_person = operator

        # 予算id(変数)に渡された予算idをセット
        this_budget_id = budget_id

        # 新規登録時の処理
        if new_record == True:
            # 設定した予算ID, 工事IDで新規作成
            proindividualcontractdoc_data, created = ProIndividualContractDoc.objects.get_or_create(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0)
            # 登録の日時、登録者を登録
            proindividualcontractdoc_data.entry_datetime = now
            proindividualcontractdoc_data.entry_operator = operator
            # 工事納入情報テーブルを保存
            proindividualcontractdoc_data.save()
            # 登録日時、登録者で工事納入情報テーブルを抽出
            proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(entry_datetime=now, entry_operator=operator, lost_flag=0)
            # 主キーを取得
            proindividualcontractdoc_unique_id = proindividualcontractdoc_data.id
            # 主キーで工事納入情報テーブルを抽出
            proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(id=proindividualcontractdoc_unique_id, lost_flag=0)
            # rev_no、作業中FL、無効FLに値を代入
            proindividualcontractdoc_data.rev_no = 0
            proindividualcontractdoc_data.entry_on_progress_flag = 1
            proindividualcontractdoc_data.lost_flag = 0
            # 工事納入情報テーブルを保存
            proindividualcontractdoc_data.save()
        # 更新時の処理
        else:
            # 該当の予算ID, 工事IDで作業中FLがONのレコード数をカウント
            on_progress_budget_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=1, lost_flag=0).count()
            # 該当の予算ID, 工事IDで(入力)完了FLがONのレコード数をカウント
            complete_entry_budget_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).count()
            # 完了FLがONの件数が「0」より多い場合
            if complete_entry_budget_num > 0:
                # 該当の予算idで、作業中FLがONのレコードを抽出し、主キーのidが最新のレコードを抽出
                proindividualcontractdoc_data = ProIndividualContractDoc.objects.filter(budget_id=budget_id, construction_id=construction_id, entry_on_progress_flag=0, lost_flag=0).order_by('-id')[0]
                # 該当の予算idで最終のrev_noを取得
                latest_rev_no = proindividualcontractdoc_data.rev_no
                # 該当のレコードを無効
                proindividualcontractdoc_data.lost_flag = 1
                # 予算のレコードを保存
                proindividualcontractdoc_data.save()
            # 完了FLがONの件数が「0」の場合
            else:
                # 最終のrev_noを「-1」に設定
                latest_rev_no = -1

            # 該当の予算idで作業中FLがONのレコード数が「0」の場合
            if on_progress_budget_num == 0:
                # 予算id、登録日時、登録者の情報で新規登録
                ProIndividualContractDoc(budget_id=budget_id, construction_id=construction_id,
                                         entry_datetime=now, entry_operator=operator, lost_flag=0).save()
                # 登録日時、登録者で予算レコードを抽出
                proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(entry_datetime=now,
                                                                                     entry_operator=operator, lost_flag=0)
                # 主キーを取得
                proindividualcontractdoc_unique_id = proindividualcontractdoc_data.id
                # 主キーで予算レコードを抽出
                proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(id=proindividualcontractdoc_unique_id,
                                                                                     lost_flag=0)
                # rev_no、作業中FL、無効FLに値を代入
                proindividualcontractdoc_data.rev_no = latest_rev_no + 1
                proindividualcontractdoc_data.entry_on_progress_flag = 1
                proindividualcontractdoc_data.lost_flag = 0
                # 予算のレコードを保存
                proindividualcontractdoc_data.save()
            # 該当の予算idで作業中FLがONのレコード数が「0」でない場合
            else:
                # 予算id、工事id, 作業中FL=1で予算レコードを抽出
                proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(budget_id=budget_id,
                                                                                     construction_id=construction_id,
                                                                                     entry_on_progress_flag=1, lost_flag=0)
                # 主キーを取得
                proindividualcontractdoc_unique_id = proindividualcontractdoc_data.id

        # 今のstepと次のstepが同じ場合の処理
        if this_step == next_step:
            entry_on_progress_flag_value = 1
            action = "temporarily_saved"
            msg = "一時保存完了"
        # 今のstepと次のstepが違う場合の処理
        else:
            entry_on_progress_flag_value = 0
            action = "entry"
            step_data = StepMaster.objects.get(step_id=this_step)
            step_name = step_data.step_name
            msg = step_name + "完了"

        # 購買発注 DATA取得
        work_id = int(request.POST['work_id'])
        vendor_code = request.POST['vendor_code']
        # storage_space_rem = ProSpecificationUnit.objects.get(budget_id=budget_id,
        #                                                      construction_id=request.POST['work_id'],
        #                                                      lost_flag=0
        #                                                      ).delivery_location
        storage_space_rem = ProEstimates.objects.get(budget_id=budget_id,
                                                     construction_id=request.POST['work_id'],
                                                     lost_flag=0
                                                     ).fixed_delivery_location
        # 着工予定日　要変換
        item_detail_text = request.POST['item_detail_text']
        work_data = ProSpecificationUnit.objects.get(budget_id=budget_id, construction_id=work_id, lost_flag=0)
        work_unique_id = work_data.id
        budget_id = work_data.budget_id
        work_name = work_data.work_name

        budget_no = budget_no.strip()

        # 20210107 y-kawauchi 新規作成の時品目コードを採番する。更新の場合変更しない。
        item_code = ''
        item_code2 = ''
        item_group_code = ''
        if ErpConstruction.objects.filter(order_id=work_id).count() == 0:
            proindividualcontractdoc_data_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id).count()
            if proindividualcontractdoc_data_num == 0:
                this_no = 1
            else:
                last_no_data = ProIndividualContractDoc.objects.filter(budget_id=budget_id).aggregate(Max('numbering'))
                if last_no_data["numbering__max"] is not None:
                    if this_step == next_step:
                        this_no = last_no_data["numbering__max"]
                    else:
                        this_no = last_no_data["numbering__max"] + 1
                else:
                    this_no = 1

            str_this_no = '00' + str(this_no) + '0'
            str_this_no = str_this_no[-4:-1]

            if budget_no in 'S':
                item_group_code = '9Y-108000'
                item_code = ''

            elif budget_no[0] == '1':
                work_class = 'CW'
                if request.POST['construction_classification'] == '工事':
                    item_group_code = '9X-108000'
                    item_code = ''
                elif request.POST['construction_classification'] == 'その他':
                    item_group_code = 'ZT-058000'
                    item_code = 'ZT-'
                    item_code = item_code + budget_no + str_this_no

            elif budget_no[0] == '2':
                work_class = 'RW'
                if request.POST['construction_classification'] == '工事':
                    item_group_code = '9U-108000'
                    item_code = ''
                elif request.POST['construction_classification'] == 'その他':
                    item_group_code = 'ZR-050000'
                    item_code = 'ZR-'
                    item_code = item_code + budget_no + str_this_no
        else:
            # this_no = ProIndividualContractDoc.objects.get(id=proindividualcontractdoc_unique_id, lost_flag=0).numbering
            proindividualcontractdoc_data_num = ProIndividualContractDoc.objects.filter(budget_id=budget_id).count()
            if proindividualcontractdoc_data_num == 0:
                this_no = 1
            else:
                last_no_data = ProIndividualContractDoc.objects.filter(budget_id=budget_id).aggregate(Max('numbering'))
                if last_no_data["numbering__max"] is not None:
                    if this_step == next_step:
                        this_no = last_no_data["numbering__max"]
                    else:
                        this_no = last_no_data["numbering__max"] + 1
                else:
                    this_no = 1

            str_this_no = '00' + str(this_no) + '0'
            str_this_no = str_this_no[-4:-1]
            if budget_no[0] == '1':
                work_class = 'CW'
                if request.POST['construction_classification'] == '工事':
                    item_group_code = '9X-108000'
                    item_code = ''
                elif request.POST['construction_classification'] == 'その他':
                    item_group_code = 'ZT-058000'
                    item_code = 'ZT-'
                    item_code = item_code + budget_no + str_this_no

            elif budget_no[0] == '2':
                work_class = 'RW'
                if request.POST['construction_classification'] == '工事':
                    item_group_code = '9U-108000'
                    item_code = ''
                elif request.POST['construction_classification'] == 'その他':
                    item_group_code = 'ZR-050000'
                    item_code = 'ZR-'
                    item_code = item_code + budget_no + str_this_no
        # 20210107 y-kawauchi 新規作成の時品目コードを採番する。更新の場合変更しない。

        # 勘定設定
        proestimate_data = ProEstimates.objects.get(budget_id=budget_id, construction_id=request.POST['work_id'], lost_flag=0)
        # 工事の場合
        if item_code == '':
            account_class = 'F'
            # 工事着工日
            # str_work_start_date = proestimate_data.fixed_delivery_date_from.strftime('%Y%m%d')
            date_str = date_to_many_type(proestimate_data.fixed_delivery_date_from)
            str_work_start_date = date_str.str_type_date_erp
            # 希望納期
            # str_work_delivery_date = proestimate_data.fixed_delivery_date.strftime('%Y%m%d')
            date_str = date_to_many_type(proestimate_data.fixed_delivery_date_to)
            str_work_delivery_date = date_str.str_type_date_erp
            item_code2 = item_group_code
        # 物品購入の場合
        else:
            account_class = ''
            # 工事着工日
            str_work_start_date = ''
            # 希望納期
            # str_work_delivery_date = proestimate_data.fixed_delivery_date.strftime('%Y%m%d')
            date_str = date_to_many_type(proestimate_data.fixed_delivery_date)
            str_work_delivery_date = date_str.str_type_date_erp
            item_code2 = item_code
        # 発注日
        proindividualcontractdoc_data.order_date = order_issuance_date

        # 個別契約書類 DATA登録
        # 主キーで予算レコードを抽出
        proindividualcontractdoc_data = ProIndividualContractDoc.objects.get(id=proindividualcontractdoc_unique_id, lost_flag=0)

        # 各項目の値を設定
        proindividualcontractdoc_data.sub_id = sub_id if sub_id is not '' else None
        proindividualcontractdoc_data.order_classification = request.POST["order_classification"] if request.POST["order_classification"] is not '' else None
        proindividualcontractdoc_data.tax_kbn = request.POST["tax_kbn"] if request.POST["tax_kbn"] is not '' else None
        proindividualcontractdoc_data.order_issuance_date = order_issuance_date if order_issuance_date is not '' else None
        proindividualcontractdoc_data.order_creator = request.POST["order_creator"] if request.POST["order_creator"] is not '' else None
        proindividualcontractdoc_data.item_code = item_code
        proindividualcontractdoc_data.item_group = item_group_code
        proindividualcontractdoc_data.individual_contract_terms = request.POST["individual_contract_terms"] if request.POST["individual_contract_terms"] is not '' else None
        proindividualcontractdoc_data.order_no = request.POST["order_no"] if request.POST["order_no"] is not '' else None
        proindividualcontractdoc_data.construction_classification = request.POST["construction_classification"] if request.POST["construction_classification"] is not '' else None
        proindividualcontractdoc_data.order_data = request.POST["order_data"] if request.POST["order_data"] is not '' else None
        proindividualcontractdoc_data.order_confirmation_data = request.POST["order_confirmation_data"] if request.POST["order_confirmation_data"] is not '' else None
        proindividualcontractdoc_data.numbering = this_no
        proindividualcontractdoc_data.vendor_code = vendor_code

        # 今のstepと次のstepが違う場合の処理
        if this_step != next_step:
            # 作業中FL=0　にする
            proindividualcontractdoc_data.entry_on_progress_flag = 0
        # 今のstepと次のstepが同じ場合の処理
        else:
            # 作業中FL=1　にする
            proindividualcontractdoc_data.entry_on_progress_flag = 1

        # rev_no取得
        proindividualcontractdoc_rev_no = proindividualcontractdoc_data.rev_no

        # 個別契約書類テーブルのレコードを保存
        proindividualcontractdoc_data.save()

        if this_step == 241003001:

            # 購買DATA登録　order_idがない場合新規作成、ある場合更新　毎回新規作成を行う
            erp_construction_data, created = ErpConstruction.objects.get_or_create(order_id=work_id)
            erp_construction_data.detail_no = 1
            erp_construction_data.order_amount = 1
            erp_construction_data.base_unit_amount = 1
            erp_construction_data.purchase_group_code = 'YA2'
            erp_construction_data.currency_code = 'JPY'
            erp_construction_data.ordering_unit = 'SK'
            erp_construction_data.amount_per_base_unit = 'SK'
            erp_construction_data.plant_code = 'ISKY'
            erp_construction_data.storage_space_code = 'YA2'
            erp_construction_data.purchase_trace_no = ''
            erp_construction_data.rem = ''
            erp_construction_data.vendor_code = vendor_code
            erp_construction_data.account_class = account_class
            erp_construction_data.item_code = item_code
            erp_construction_data.item_group_code = item_group_code
            erp_construction_data.work_class = work_class
            erp_construction_data.order_date = order_date

            prospecificationunit_data = ProSpecificationUnit.objects.get(construction_id=work_id, lost_flag=0)
            erp_construction_data.specification_person_in_charge = str(User.objects.get(username=prospecificationunit_data.specification_person_in_charge, lost_flag=0))
            erp_construction_data.procurement_person_in_charge = str(User.objects.get(username=prospecificationunit_data.procurement_person_in_charge, lost_flag=0))
            request_division = DivisionMaster.objects.get(division_cd=prospecificationunit_data.division, lost_flag=0)
            request_department = DepartmentMaster.objects.get(department_cd=prospecificationunit_data.department, lost_flag=0)
            erp_construction_data.request_department = str(request_division) + '　' + str(request_department)

            # カタカナも半角変換対応
            erp_construction_data.item_text = jaconv.z2h(work_name, kana=True, digit=True, ascii=True).replace("\t", " ")

            erp_construction_data.delivery_date = str_work_delivery_date    # 納入期日
            erp_construction_data.order_person = request.POST["order_creator"]
            erp_construction_data.storage_space_rem = storage_space_rem.replace("\t", " ")     # 納入場所
            erp_construction_data.item_detail_text = item_detail_text
            erp_construction_data.construction_start_date = str_work_start_date # 決定工期FROM
            erp_construction_data.consumption_tax_code = request.POST["tax_kbn"]

            # 候補業者検索機能対応
            proestimate_data = ProEstimates.objects.get(construction_id=work_id, lost_flag=0)
            erp_construction_data.total_price = proestimate_data.confirmed_last_estimated_amount
            erp_construction_data.discount_price = proestimate_data.confirmed_last_estimated_amount - proestimate_data.confirmed_estimated_amount_af_nego
            # discount_price = proestimate_data.confirmed_last_estimated_amount - proestimate_data.confirmed_estimated_amount_af_nego
            # if discount_price == 0:
            #     erp_construction_data.discount_price = None
            # else:
            #     erp_construction_data.discount_price = discount_price
            # 勘定CD取得
            instructionnomaster = InstructionNoMaster.objects.get(指図書コード__istartswith=budget_no)
            cost_center = instructionnomaster.利益センター
            costcentermaster = CostCenterMaster.objects.get(原価センタ=cost_center)
            cost_center_class_code = costcentermaster.原価属性コード
            erp_construction_data.account_code = AccountCodeDefinitionMaster.objects.get(原価属性コード=cost_center_class_code, 品目グループコード=item_group_code[0:2]).勘定コード
            erp_construction_data.account_code = erp_construction_data.account_code.replace(' ', '')

            erp_construction_data.cost_center = cost_center
            erp_construction_data.instruction_code = budget_no
            erp_construction_data.order_no = erp_construction_data.order_id
            erp_construction_data.relation_no = work_class + str(work_id)
            procurement_person_in_charge = ProSpecificationUnit.objects.get(budget_id=budget_id, construction_id=request.POST['work_id'], lost_flag=0).procurement_person_in_charge
            erp_construction_data.purchase_person = UserMaster.objects.get(ＮＴユーザー名=procurement_person_in_charge).担当別購買グループ
            # 個別契約書類作成時のみstatusを"0"に
            # if this_step == 241003001:
            #     erp_construction_data.status = 0
            erp_construction_data.budget_id = budget_id
            erp_construction_data.department = this_department
            erp_construction_data.division = this_division
            if created:
                erp_construction_data.entry_operator = operator
                erp_construction_data.entry_datetime = now
            else:
                erp_construction_data.update_datetime = now
                erp_construction_data.update_operator = operator

            # 注文分類が①「注文NO」のときERPにデータを転送(status=0)、②それ以外の時ERPにデータを転送しない(status=10)
            if this_step != next_step and this_step == 241003001:
                erp_construction_data.erp_errormsg = ""
                if request.POST["order_classification"] == '注文NO':
                    erp_construction_data.status = 0
                else:
                    erp_construction_data.status = 10

            erp_construction_data.save()

            # 新ERP刷新対応
            mcframe_data, created = MCFrame.objects.get_or_create(order_id=work_id)
            mcframe_data.detail_no = 1
            mcframe_data.order_amount = 1
            mcframe_data.base_unit_amount = 1
            mcframe_data.purchase_group_code = 'YA4'
            mcframe_data.currency_code = 'JPY'
            mcframe_data.ordering_unit = 'SK'
            mcframe_data.amount_per_base_unit = 'SK'
            mcframe_data.plant_code = 'ISKY'
            mcframe_data.storage_space_code = 'YA4'
            mcframe_data.purchase_trace_no = ''
            mcframe_data.rem = ''
            mcframe_data.vendor_code = vendor_code
            mcframe_data.account_class = account_class
            mcframe_data.item_code = item_code2
            mcframe_data.item_group_code = item_group_code
            mcframe_data.work_class = work_class
            mcframe_data.order_date = order_date
            mcframe_data.specification_person_in_charge = str(User.objects.get(username=prospecificationunit_data.specification_person_in_charge, lost_flag=0))
            mcframe_data.procurement_person_in_charge = str(User.objects.get(username=prospecificationunit_data.procurement_person_in_charge, lost_flag=0))
            mcframe_data.request_department = str(request_division) + '　' + str(request_department)
            mcframe_data.item_text = jaconv.z2h(work_name, kana=True, digit=True, ascii=True).replace("\t", " ")  # カタカナも半角変換対応
            mcframe_data.delivery_date = str_work_delivery_date  # 納入期日
            mcframe_data.order_person = request.POST["order_creator"]
            mcframe_data.storage_space_rem = storage_space_rem.replace("\t", " ")  # 納入場所
            mcframe_data.item_detail_text = item_detail_text
            mcframe_data.construction_start_date = str_work_start_date  # 決定工期FROM
            mcframe_data.consumption_tax_code = request.POST["tax_kbn"]
            # 候補業者検索機能対応
            mcframe_data.total_price = proestimate_data.confirmed_last_estimated_amount
            # mcframe_data.discount_price = proestimate_data.confirmed_last_estimated_amount - proestimate_data.confirmed_estimated_amount_af_nego
            discount_price = proestimate_data.confirmed_last_estimated_amount - proestimate_data.confirmed_estimated_amount_af_nego
            if discount_price == 0:
                mcframe_data.discount_price = None
            else:
                mcframe_data.discount_price = discount_price
            # 勘定CD取得
            if account_class == 'F':
                mcframe_data.account_code = AccountCodeDefinitionMaster.objects.get(原価属性コード=cost_center_class_code, 品目グループコード=item_group_code[0:2]).勘定コード
                mcframe_data.account_code = mcframe_data.account_code.replace(' ', '')
            elif account_class == '':
                mcframe_data.account_code = ''
            mcframe_data.cost_center = cost_center
            mcframe_data.instruction_code = budget_no
            mcframe_data.relation_no = work_class + str(work_id)
            mcframe_data.purchase_person = UserMaster.objects.get(ＮＴユーザー名=procurement_person_in_charge).担当別購買グループ
            mcframe_data.budget_id = budget_id
            mcframe_data.department = this_department
            mcframe_data.division = this_division

            mcframe_data.order_no = request.POST["order_no"] if request.POST["order_no"] is not '' else None
            if request.POST['construction_classification'] == 'その他':
                mcframe_data.order_type_classification = 11
            elif request.POST['vendor_code'] == 'X0315500':
                mcframe_data.order_type_classification = 10
            else:
                mcframe_data.order_type_classification = 9
            numbering = MCFrame.objects.filter(budget_id=budget_id).count()
            mcframe_data.numbering = numbering
            mcframe_data.year = int('20' + budget_no[2:4])

            if created:
                mcframe_data.entry_operator = operator
                mcframe_data.entry_datetime = now
            else:
                mcframe_data.update_datetime = now
                mcframe_data.update_operator = operator
            # 注文分類が①「注文NO」のときERPにデータを転送(status=0)、②それ以外の時ERPにデータを転送しない(status=10)
            if this_step != next_step and this_step == 241003001:
                mcframe_data.erp_errormsg = ""
                if request.POST["order_classification"] == '注文NO':
                    mcframe_data.status = 0
                else:
                    mcframe_data.status = 10
            mcframe_data.save()
            # 新ERP刷新対応

        # ログより差戻を可能とするためtarget='prospecificationunit'とする
        Log(target='prospecificationunit', target_id=construction_id, action=action, operator=operator, operation_datetime=now, step=this_step, comment=comment, operator_department=this_department, operator_division=this_division, budget_id=this_budget_id).save()

        # 進捗状況を対象(prospecificationunit)と工事idで抽出･･･あれば呼び出し、なければ新規登録
        progress_data, created = Progress.objects.get_or_create(target="prospecificationunit", target_id=construction_id)
        # 各項目を設定
        progress_data.present_step = next_step
        progress_data.present_operator = next_person
        progress_data.present_department = next_department
        department_data = DepartmentMaster.objects.get(department_cd=next_department)
        progress_data.present_division = department_data.division_cd

        # 今のstepと次のstepが違う場合の処理･･･追加で項目(最終工程、最終作業者、最終処理日時)に値を設定
        if this_step != next_step:
            progress_data.last_operation_step = this_step
            progress_data.last_operator = operator
            progress_data.last_operation_datetime = now

        # 進捗状況のレコードを保存
        progress_data.save()

        # 進捗通知機能
        if this_step != next_step:
            step_notice(progress_data)

        ary = {
            'msg': msg,
            'flag': '1',
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

# 候補業者検索機能
@require_POST
def confirmed_vendor_change(request):
    try:
        vendormaster = SupplierMaster.objects.filter(supplier_name__icontains=request.POST['confirmed_vendor'], lost_flag=0)
        data = ''
        for vendormaster in vendormaster:
            data += '<option value="' + vendormaster.supplier_cd + '">' + vendormaster.supplier_cd + ':' + vendormaster.supplier_name + '</option>'

        ary = {
            'data': data,
        }
        return JsonResponse(ary)
    except Exception:
        output_log_exception(request, traceback.format_exc())
        raise

