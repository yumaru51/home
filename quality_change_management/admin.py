from django.contrib import admin
from .models import TargetMaster, PageMaster, ActionMaster, StepMaster, StepPageEntryMaster, \
    StepDisplayPage, StepChargeDepartment, StepRelation, StepAction, Log, Request, Quality, Safety, Progress


class TargetMasterAdmin(admin.ModelAdmin):
    list_display = ('target', 'target_name', 'lost_flag')
    list_filter = ['target', 'target_name', 'lost_flag']
    search_fields = ['target', 'target_name', 'lost_flag']


admin.site.register(TargetMaster, TargetMasterAdmin)


class PageMasterAdmin(admin.ModelAdmin):
    list_display = ('page', 'page_name', 'lost_flag')
    list_filter = ['page', 'page_name', 'lost_flag']
    search_fields = ['page', 'page_name', 'lost_flag']


admin.site.register(PageMaster, PageMasterAdmin)


class ActionMasterAdmin(admin.ModelAdmin):
    list_display = ('action', 'action_name', 'action_class', 'action_authority', 'progress_transition', 'lost_flag')
    list_filter = ['action', 'action_name', 'action_class', 'action_authority', 'progress_transition', 'lost_flag']
    search_fields = ['action', 'action_name', 'action_class', 'action_authority', 'progress_transition', 'lost_flag']


admin.site.register(ActionMaster, ActionMasterAdmin)


class StepMasterAdmin(admin.ModelAdmin):
    list_display = ('step', 'step_name', 'hidden_flag', 'lost_flag')
    list_filter = ['step', 'step_name', 'hidden_flag', 'lost_flag']
    search_fields = ['step', 'step_name', 'hidden_flag', 'lost_flag']


admin.site.register(StepMaster, StepMasterAdmin)


class StepPageEntryMasterAdmin(admin.ModelAdmin):
    list_display = ('step', 'page', 'target', 'lost_flag')
    list_filter = ['step', 'page', 'target', 'lost_flag']
    search_fields = ['step', 'page', 'target', 'lost_flag']


admin.site.register(StepPageEntryMaster, StepPageEntryMasterAdmin)


class StepDisplayPageAdmin(admin.ModelAdmin):
    list_display = ('step', 'page_no', 'page', 'default_page', 'lost_flag')
    list_filter = ['step', 'page_no', 'page', 'default_page', 'lost_flag']
    search_fields = ['step', 'page_no', 'page', 'default_page', 'lost_flag']


admin.site.register(StepDisplayPage, StepDisplayPageAdmin)


class StepChargeDepartmentAdmin(admin.ModelAdmin):
    list_display = ('step', 'target', 'charge_department', 'display_order', 'lost_flag')
    list_filter = ['step', 'target', 'charge_department', 'display_order', 'lost_flag']
    search_fields = ['step', 'target', 'charge_department', 'display_order', 'lost_flag']


admin.site.register(StepChargeDepartment, StepChargeDepartmentAdmin)


class StepRelationAdmin(admin.ModelAdmin):
    list_display = ('present_step', 'next_step', 'type', 'display_order', 'lost_flag')
    list_filter = ['present_step', 'next_step', 'type', 'display_order', 'lost_flag']
    search_fields = ['present_step', 'next_step', 'type', 'display_order', 'lost_flag']


admin.site.register(StepRelation, StepRelationAdmin)


class StepActionAdmin(admin.ModelAdmin):
    list_display = ('step', 'action_class', 'action', 'display_order', 'lost_flag')
    list_filter = ['step', 'action_class', 'action', 'display_order', 'lost_flag']
    search_fields = ['step', 'action_class', 'action', 'display_order', 'lost_flag']


admin.site.register(StepAction, StepActionAdmin)


class LogAdmin(admin.ModelAdmin):
    list_display = ('target', 'target_table_id', 'step', 'action', 'operation_datetime', 'operator', 'operator_department', 'comment')
    list_filter = ['target', 'target_table_id', 'step', 'action', 'operation_datetime', 'operator', 'operator_department', 'comment']
    search_fields = ['target', 'target_table_id', 'step', 'action', 'operation_datetime', 'operator', 'operator_department', 'comment']


admin.site.register(Log, LogAdmin)


class RequestAdmin(admin.ModelAdmin):
    list_display = ('division', 'department', 'user', 'change_target', 'others', 'title', 'outline', 'level',
                    'treatment', 'safety_aspect', 'quality_aspect', 'delivery_date', 'delivery_date_start',
                    'delivery_date_end', 'level2', 'others2', 'completion_date', 'application_date',
                    'education_management_system_id')
    list_filter = ['division', 'department', 'user', 'change_target', 'others', 'title', 'outline', 'level',
                   'treatment', 'safety_aspect', 'quality_aspect', 'delivery_date', 'delivery_date_start',
                   'delivery_date_end', 'level2', 'others2', 'completion_date', 'application_date',
                   'education_management_system_id']
    search_fields = ['division', 'department', 'user', 'change_target', 'others', 'title', 'outline', 'level',
                     'treatment', 'safety_aspect', 'quality_aspect', 'delivery_date', 'delivery_date_start',
                     'delivery_date_end', 'level2', 'others2', 'completion_date', 'application_date',
                     'education_management_system_id']


admin.site.register(Request, RequestAdmin)


class QualityAdmin(admin.ModelAdmin):
    list_display = ('request', 'quality_aspect', 'judgement', 'results', 'evaluation')
    list_filter = ['request', 'quality_aspect', 'judgement', 'results', 'evaluation']
    search_fields = ['request', 'quality_aspect', 'judgement', 'results', 'evaluation']


admin.site.register(Quality, QualityAdmin)


class SafetyAdmin(admin.ModelAdmin):
    list_display = ('request', 'safety_aspect', 'judgement', 'results', 'evaluation')
    list_filter = ['request', 'safety_aspect', 'judgement', 'results', 'evaluation']
    search_fields = ['request', 'safety_aspect', 'judgement', 'results', 'evaluation']


admin.site.register(Safety, SafetyAdmin)


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('request', 'target', 'present_step', 'present_division', 'present_department', 'present_operator',
                    'last_step')
    list_filter = ['request', 'target', 'present_step', 'present_division', 'present_department', 'present_operator',
                   'last_step']
    search_fields = ['request', 'target', 'present_step', 'present_division', 'present_department', 'present_operator',
                     'last_step']


admin.site.register(Progress, ProgressAdmin)


