import traceback
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from fms.models import ErpItemConstruction, Budget, Work, Estimate
from gcsystem.models import ItemGroupMaster, QuantityUnitMaster, InstructionNoMaster, CostCenterMaster, AccountCodeDefinitionMaster
from gcsystem.models import AccountCodeMaster, StorageSpaceMaster, VendorMaster
from fms.views.common_def_views import output_log_info, output_log_error, output_log_exception


# # 項目工事発注レコード作成
# @login_required
# @require_POST
# def item_construction_record_entry(request):
#     try:
#         t_username = request.user.username
#
#         vendor_code = request.POST['vendor_code']
#         work_id = int(request.POST['work_id'])
#         work_rev_no = int(request.POST['work_rev_no'])
#         order_amount = request.POST['order_amount']
#         ordering_unit = request.POST['ordering_unit']
#         order_person = request.POST['order_person']
#         storage_space_rem = request.POST['storage_space_rem']
#
#         work_data = Work.objects.get(work_id=work_id, work_rev_no=work_rev_no)
#         work_unique_id = work_data.id
#         work_order_department = work_data.work_data.department_cd
#
#         work_class = work_data.work_class
#         budget_id = work_data.work_budget_id
#         work_name = work_data.work_data
#         work_delivery_date = work_data.work_delivery_date
#         # consumption_tax_code = work_data.consumption_tax_code
#
#         str_year = str(work_delivery_date.year)
#         str_month = str(work_delivery_date.month)
#         str_day = str(work_delivery_date.day)
#         str_work_delivery_date = str_year + str_month + str_day
#
#         work_start_date = work_data.work_start_date
#
#         str_year = str(work_start_date.year)
#         str_month = str(work_start_date.month)
#         str_year = str(work_start_date.day)
#         str_work_start_date = str_year + str_month + str_day
#
#         budget_data = Budget.objects.get(budget_id=budget_id, lost_flag=0)
#         budget_no = budget_data.budget_data
#
#         erp_item_construction_data_num = ErpItemConstruction.objects.filter(budget_id=budget_id).count()
#         this_no = erp_item_construction_data_num + 1
#         str_this_no = '000' + this_no
#         str_this_no = str_this_no[-3:0]
#         item_code = ''
#
#         # 工事の処理
#         if work_class == '2':
#             account_class = '1'
#             item_code =''
#
#             if budget_no[0] == '1':
#                 item_group_code = '9X-108000'
#
#             elif budget_no[0] == '2':
#                 item_group_code = '9U-108000'
#
#             instruction_no_master_data = InstructionNoMaster.objects.get(指図書コード=budget_no)
#
#             cost_center = instruction_no_master_data.利益センター
#
#             cost_center_master_data = CostCenterMaster.objects.get(原価センタ=cost_center)
#
#             cost_center_class_code = cost_center_master_data.原価属性コード
#
#             account_code_definition_master_data = AccountCodeDefinitionMaster.objects.get(原価属性コード=cost_center_class_code, 品目グループコード=item_group_code)
#
#             account_code = account_code_definition_master_data.勘定コード
#
#         # 物品の処理
#         else:
#             account_class = ''
#             if budget_no[0] == '1':
#                 item_code = 'ZT-'
#             elif budget_no[0] == '2':
#                 item_code = 'ZR-'
#
#             item_code = item_code + budget_no + str_this_no
#             item_group_code = item_group_code = request.POST['item_group_code']
#
#             account_code = ''
#
#         estimate_data = Estimate.objects.get(work_id=work_id, rev_no=work_rev_no, adoption_flag=1)
#
#         erp_item_construction_data, created = ErpItemConstruction.objects.get_or_create(work_id=work_id, work_rev_no=work_rev_no)
#         erp_item_construction_data.detail_no = 1
#         erp_item_construction_data.vendor_code = vendor_code
#         erp_item_construction_data.purchase_group_code = 'YA2'
#         erp_item_construction_data.purchase_person = t_username
#         erp_item_construction_data.currency_code = 'JPY'
#         erp_item_construction_data.account_class = account_class
#         erp_item_construction_data.item_code = item_code
#         erp_item_construction_data.item_text = work_name
#         erp_item_construction_data.order_amount = order_amount
#         erp_item_construction_data.ordering_unit = ordering_unit
#         erp_item_construction_data.delivery_date = str_work_delivery_date
#         erp_item_construction_data.amount_per_base_unit = 1
#         erp_item_construction_data.base_unit_amount = 'sk'
#         erp_item_construction_data.item_group_code = item_group_code
#         erp_item_construction_data.plant_code = 'ISKY'
#         erp_item_construction_data.storage_space_code = 'YA2'
#         erp_item_construction_data.purchase_trace_no = ''
#         erp_item_construction_data.order_person = order_person
#         erp_item_construction_data.rem = ''
#         erp_item_construction_data.storage_space_rem = storage_space_rem
#         erp_item_construction_data.total_price = estimate_data.price_after_discount
#         erp_item_construction_data.discount_price = estimate_data.estimate_price - estimate_data.price_after_discount
#         erp_item_construction_data.account_code = account_code
#         erp_item_construction_data.cost_center = cost_center
#         erp_item_construction_data.instruction_code = budget_no
#         erp_item_construction_data.consumption_tax_code = consumption_tax_code
#         erp_item_construction_data.relation_no = work_unique_id
#         erp_item_construction_data.item_detail_text = ''
#         erp_item_construction_data.construction_start_date = str_work_start_date
#         erp_item_construction_data.budget_id = budget_id
#         erp_item_construction_data.status = 0
#
#         erp_item_construction_data.save()
#     except Exception:
#         output_log_exception(request, traceback.format_exc())
#         raise
