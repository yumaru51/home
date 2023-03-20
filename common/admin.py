from django.contrib import admin
from fms.models import UserAttribute, User, ProcessMaster, SubmissionDocumentMaster, SupplierMaster, Progress, \
    BudgetLaw, MaintenanceCostCenterMaster
from fms.models import Budget, CsManage, ProBudgetUnit, BudgetCondition, DepartmentMaster, Work, ProSpecificationUnit
from fms.models import FreeSpecDetail
from fms.models import StepMaster, StepRelation, StepAction, DataEntryStepMaster, StepDisplayItem, DivisionMaster
from fms.models import MaintenanceInstructionNoMaster, MaintenanceAccountCodeMaster, MaintenanceAccountCodeDefinitionMaster
from fms.models import InputNgCharacter, BusinessYearMaster, BudgetCarryForward, StopWorkCause, StepFunctionUserMaster

# master_models.py
from fms.models import MPlanBasisMaster, PlanClassMaster, CheckItemMaster, StopWorkCauseMaster, WorkManagementClassMaster, \
    PurposeClassMaster
# budget_data_
from fms.models import EvaluationCriteriaMaster, EvaluationPointMaster, EvaluationDecisionMaster
'''

from fms.models import BudgetConditionMaster, StepMaster, UserAttribute, DivisionMaster, DepartmentMaster, User

admin.site.register(BudgetConditionMaster)
admin.site.register(StepMaster)
admin.site.register(User)
'''


class UserAttributeAdmin(admin.ModelAdmin):
    list_display = ('username', 'department', 'division', 'authority', 'confirm_username', 'permit_username', 'lost_flag', 'display_order')
    list_filter = ['division', 'department']
    search_fields = ['username']


admin.site.register(UserAttribute, UserAttributeAdmin)


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'display_order', 'lost_flag')
    list_filter = ['last_name', 'first_name']
    search_fields = ['last_name', 'first_name']


admin.site.register(User, UserAdmin)


class ProcessMasterAdmin(admin.ModelAdmin):
    list_display = ('process_cd2', 'process_cd', 'process_name', 'department', 'display_order', 'lost_flag')
    list_filter = ['department']
    search_fields = ['process_cd2', 'process_cd', 'process_name', 'department']


admin.site.register(ProcessMaster, ProcessMasterAdmin)


class SubmissionDocumentMasterAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'default_submission_deadline', 'default_number_of_copies', 'display_order', 'lost_flag')
    list_filter = ['document_name']
    search_fields = ['document_name']


admin.site.register(SubmissionDocumentMaster, SubmissionDocumentMasterAdmin)


class SupplierMasterAdmin(admin.ModelAdmin):
    list_display = ('supplier_cd', 'supplier_name', 'lost_flag')
    list_filter = ['supplier_name']
    search_fields = ['supplier_cd', 'supplier_name']


admin.site.register(SupplierMaster, SupplierMasterAdmin)


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('target', 'target_id', 'present_step', 'present_department', 'present_division', 'present_operator', 'last_operation_step', 'last_operator', 'last_operation_datetime')
    list_filter = ['target']
    search_fields = ['target_id']


admin.site.register(Progress, ProgressAdmin)


class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'rev_no', 'budget_no', 'budget_name', 'business_year', 'budget_main_department', 'lost_flag')
    list_filter = ['business_year', 'budget_main_department']
    search_fields = ['budget_id']


admin.site.register(Budget, BudgetAdmin)


class ProBudgetUnitAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'rev_no', 'budget_name', 'department', 'division', 'jurisdiction_area', 'area_person_in_charge', 'lost_flag')
    list_filter = ['division', 'department', 'jurisdiction_area', 'area_person_in_charge']
    search_fields = ['budget_id']


admin.site.register(ProBudgetUnit, ProBudgetUnitAdmin)


class CsManageAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'cs_no', 'cs_rev_no', 'lost_flag')
    # list_filter = ['division', 'department', 'jurisdiction_area', 'area_person_in_charge']
    search_fields = ['budget_id']


admin.site.register(CsManage, CsManageAdmin)


class BudgetConditionAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'budget_condition')
    # list_filter = ['division', 'department', 'jurisdiction_area', 'area_person_in_charge']
    search_fields = ['budget_id']


admin.site.register(BudgetCondition, BudgetConditionAdmin)


class DepartmentMasterAdmin(admin.ModelAdmin):
    list_display = ('department_cd', 'department_name', 'division_cd', 'area_manager_id', 'display_order', 'lost_flag')
    list_filter = ['division_cd']
    search_fields = ['department_cd', 'department_name']


admin.site.register(DepartmentMaster, DepartmentMasterAdmin)


class DivisionMasterAdmin(admin.ModelAdmin):
    list_display = ('division_cd', 'division_name', 'display_order', 'lost_flag')
    list_filter = ['division_cd']
    search_fields = ['division_cd', 'division_name']


admin.site.register(DivisionMaster,  DivisionMasterAdmin)


class WorkAdmin(admin.ModelAdmin):
    list_display = ('work_budget_id', 'work_id', 'work_rev_no', 'work_name', 'work_order_department', 'work_charge_process', 'lost_flag')
    list_filter = ['work_budget_id']
    search_fields = ['work_id', 'work_name']


admin.site.register(Work, WorkAdmin)


class ProSpecificationUnitAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'construction_id', 'rev_no', 'work_name', 'department', 'specification_person_in_charge', 'lost_flag')
    list_filter = ['budget_id']
    search_fields = ['construction_id', 'work_name']


admin.site.register(ProSpecificationUnit, ProSpecificationUnitAdmin)


class BudgetLawAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'rev_no', 'law_name', 'lost_flag', 'entry_on_progress_flag')
    # list_filter = ['division', 'department', 'jurisdiction_area', 'area_person_in_charge']
    search_fields = ['budget_id']


admin.site.register(BudgetLaw, BudgetLawAdmin)


class FreeSpecDetailAdmin(admin.ModelAdmin):
    list_display = ('work_id', 'sub_no', 'rev_no', 'entry_class', 'lost_flag', 'entry_on_progress_flag')
    search_fields = ['work_id']


admin.site.register(FreeSpecDetail, FreeSpecDetailAdmin)
'''
admin.site.register(DivisionMaster)
admin.site.register(DepartmentMaster)
'''


class StepMasterAdmin(admin.ModelAdmin):
    list_display = ('step_id', 'step_name', 'charge_department_class', 'step_level', 'lost_flag', 'display_order')
    list_filter = ['step_level', 'charge_department_class']
    search_fields = ['step_id']


admin.site.register(StepMaster,  StepMasterAdmin)


class StepRelationAdmin(admin.ModelAdmin):
    list_display = ('step_id', 'next_step', 'display_order', 'lost_flag')
    list_filter = ['next_step']
    search_fields = ['step_id']


admin.site.register(StepRelation,  StepRelationAdmin)


class StepDisplayItemAdmin(admin.ModelAdmin):
    list_display = ('step', 'page', 'div_id_name', 'item_name', 'action_pb_flag', 'default_page', 'lost_flag')
    list_filter = ['default_page', 'action_pb_flag', 'item_name']
    search_fields = ['step']


admin.site.register(StepDisplayItem,  StepDisplayItemAdmin)


class StepActionAdmin(admin.ModelAdmin):
    list_display = ('step_id', 'action_cd', 'next_step', 'display_order', 'lost_flag', 'target')
    list_filter = ['action_cd', 'target']
    search_fields = ['step_id']


admin.site.register(StepAction,  StepActionAdmin)


class DataEntryStepMasterAdmin(admin.ModelAdmin):
    list_display = ('step_id', 'target_table', 'lost_flag')
    list_filter = ['target_table']
    search_fields = ['step_id']


admin.site.register(DataEntryStepMaster,  DataEntryStepMasterAdmin)


class MaintenanceInstructionNoMasterAdmin(admin.ModelAdmin):
    list_display = ('instruction_code', 'instruction_code_textcontent', 'instruction_type', 'instruction_type_name', 'cost_center', 'instruction_status')
    list_filter = ['instruction_type', 'cost_center']
    search_fields = ['instruction_code']


admin.site.register(MaintenanceInstructionNoMaster,  MaintenanceInstructionNoMasterAdmin)


class MaintenanceAccountCodeMasterAdmin(admin.ModelAdmin):
    list_display = ('account_code', 'account_code_name')
    # list_filter = ['account_code_name']
    search_fields = ['account_code']


admin.site.register(MaintenanceAccountCodeMaster,  MaintenanceAccountCodeMasterAdmin)


class MaintenanceAccountCodeDefinitionMasterAdmin(admin.ModelAdmin):
    list_display = ('item_group_code', 'cost_center_class_code', 'account_code')
    # list_filter = ['account_code_name']
    search_fields = ['account_code']


admin.site.register(MaintenanceAccountCodeDefinitionMaster,  MaintenanceAccountCodeDefinitionMasterAdmin)


class MaintenanceCostCenterMasterAdmin(admin.ModelAdmin):
    list_display = ('department', 'cost_center', 'instruction_no', 'account_code', 'year', 'lost_flag')
    list_filter = ['year', 'lost_flag']
    search_fields = ['department', 'cost_center', 'instruction_no', 'account_code']


admin.site.register(MaintenanceCostCenterMaster,  MaintenanceCostCenterMasterAdmin)


class InputNgCharacterAdmin(admin.ModelAdmin):
    list_display = ('ng_character', 'lost_flag')
    list_filter = ['lost_flag']
    search_fields = ['ng_character']


admin.site.register(InputNgCharacter,  InputNgCharacterAdmin)


class BusinessYearMasterAdmin(admin.ModelAdmin):
    list_display = ('business_year', 'display_flag', 'lost_flag')


admin.site.register(BusinessYearMaster,  BusinessYearMasterAdmin)


class BudgetCarryForwardAdmin(admin.ModelAdmin):
    list_display = ('budget_id', 'carry_forward_id', 'rev_no', 'carry_forward_price', 'end_date', 'order_complete_flag', 'carry_forward_reason', 'carry_forward_year_from', 'carry_forward_year_to', 'settlement_no', 'lost_flag')
    list_filter = ['lost_flag']
    search_fields = ['budget_id']


admin.site.register(BudgetCarryForward, BudgetCarryForwardAdmin)


class StopWorkCauseAdmin(admin.ModelAdmin):
    list_display = ('target', 'budget_id', 'construction_id', 'rev_no', 'present_step', 'present_operator', 'lost_flag', 'entry_datetime', 'entry_operator')
    list_filter = ['lost_flag', 'target']
    search_fields = ['budget_id', 'construction_id']


admin.site.register(StopWorkCause, StopWorkCauseAdmin)


class StepFunctionUserMasterAdmin(admin.ModelAdmin):
    list_display = ('department', 'step',  'user', 'user_order', 'lost_flag')
    list_filter = ['lost_flag', 'department']
    search_fields = ['department', 'step']


admin.site.register(StepFunctionUserMaster, StepFunctionUserMasterAdmin)


class MPlanBasisMasterAdmin(admin.ModelAdmin):
    list_display = ('basis_cd', 'name', 'detail', 'display_order', 'lost_flag')


admin.site.register(MPlanBasisMaster, MPlanBasisMasterAdmin)


class PlanClassMasterAdmin(admin.ModelAdmin):
    list_display = ('class_cd', 'name', 'lost_flag')


admin.site.register(PlanClassMaster, PlanClassMasterAdmin)


class CheckItemMasterAdmin(admin.ModelAdmin):
    list_display = ('check_cd', 'function_cd', 'check_name', 'text_input_flag', 'display_order', 'lost_flag')


admin.site.register(CheckItemMaster, CheckItemMasterAdmin)


class StopWorkCauseMasterAdmin(admin.ModelAdmin):
    list_display = ('stop_work_cause_name', 'target', 'display_order', 'lost_flag')


admin.site.register(StopWorkCauseMaster, StopWorkCauseMasterAdmin)


class WorkManagementClassMasterAdmin(admin.ModelAdmin):
    list_display = ('management_class_cd', 'management_class_name', 'lost_flag')


admin.site.register(WorkManagementClassMaster, WorkManagementClassMasterAdmin)


class EvaluationCriteriaMasterAdmin(admin.ModelAdmin):
    list_display = ('target', 'criteria_cd', 'criteria_detail', 'display_order', 'lost_flag')


admin.site.register(EvaluationCriteriaMaster, EvaluationCriteriaMasterAdmin)


class EvaluationPointMasterAdmin(admin.ModelAdmin):
    list_display = ('point', 'point_detail', 'display_order', 'lost_flag', 'criteria_id')


admin.site.register(EvaluationPointMaster, EvaluationPointMasterAdmin)


class EvaluationDecisionMasterAdmin(admin.ModelAdmin):
    list_display = ('target', 'evaluation_cd', 'evaluation_point', 'decision_rank', 'decision_rank_detail', 'lost_flag')


admin.site.register(EvaluationDecisionMaster, EvaluationDecisionMasterAdmin)


class PurposeClassMasterAdmin(admin.ModelAdmin):
    list_display = ('purpose_class_cd', 'purpose_class_name', 'display_order', 'lost_flag')


admin.site.register(PurposeClassMaster, PurposeClassMasterAdmin)

