# 共通項目
from .common_views import index, level4_step_top, level5_step_top, action_button_display, get_log_lists, job_return, add_new_line
from .common_views import go_next_step, detail_template, change_department, top_page_detail, print_csv, push_task
from .common_views import hold_step, date_to_hyphen

from .select_views import select_division, input_select_division, select_department, input_select_department
from .select_views import input_select_division_without_div_add_name, select_vendor, select_person
from .select_views import input_select_equipment_list, input_select_condition_list, select_next_department
from .select_views import select_next_division, select_next_step_department, next_step_department_select
from .select_views import select_discovery_person, instruction_no_filter, cost_center_filter
from .select_views import select_filter_division, select_filter_department, select_work_step, select_budget_plan
from .file_loader_views import file_upload, file_upload_file_list
from .file_loader_views import file_upload, file_upload_file_list, file_download, file_delete, file_upload_other_type
from .file_loader_views import file_upload_file_list_other_type, attached_file_download, output_file_download
from .file_loader_views import input_file_upload
from .file_loader_views import server_file_download

# メール送信関連
from .notice_mail_views import mail_send_action

# イレギュラー処理関係
from .irregular_views import irregular_menu, level5_step_stop
from .irregular_views import stop_work_info, get_stop_execution_work_lists, stop_work_filter, stop_work_cause_entry
from .irregular_views import cs_forced_termination, stop_budget_progress
from .irregular_views import edit_supplier_master_page, edit_supplier_master_entry

# 一時的対応関係
from .temporary_response_views import temporary_response_menu, make_ordered_construction_excel_page
from .temporary_response_views import make_ordered_construction_excel
from .temporary_response_views import make_plantia_import_excel_page, make_plantia_import_excel
from .temporary_response_views import end_maintenance_order_filter, end_maintenance_order_list
from .temporary_response_views import make_hearing_document_page, make_hearing_document
from .temporary_response_views import make_budget_registration_list_page, make_budget_registration_list, import_budget_registration_list
from .temporary_response_views import make_carry_forward_document_page, make_carry_forward_document
from .temporary_response_views import go_next_budget_plan_page
# 進捗工程登録/更新
from .management_views import step_edit, get_step_list, step_detail, get_step_relation_list, get_step_action_list
from .management_views import get_step_display_item_list, get_data_entry_step_list, get_action_master_list
from .management_views import step_management, step_display_item_detail, step_action_detail, data_entry_step_detail
from .management_views import step_data_entry, step_data_delete, step_display_item_entry, step_display_item_delete
from .management_views import step_action_entry, step_action_delete, data_entry_step_master_entry
from .management_views import data_entry_step_master_delete, step_relation_entry, step_relation_delete
# 予算関係
from .budget_views import budget_detail, budget_data_info, get_budget_lists, budget_edit, budget_filter, budget_entry
from .budget_views import budget_copy, budget_copy_source, copy_budget_material_list_entry, copy_budget_law_list_entry
from .budget_views import copy_budget_equipment_list_entry, copy_required_spec_list_entry
from .budget_views import budget_change_department, set_budget_condition, set_relation_budget_condition
from .budget_views import budget_charge_person_info, budget_charge_person_entry
from .budget_views import budget_mplan_entry, go_next_budget_plan_list
from .budget_carry_forward_views import budget_carry_forward_start, budget_carry_forward_list, budget_carry_forward_info
from .budget_carry_forward_views import budget_carry_forward_entry, budget_carry_forward_register

# 予算関係法令/関係機器
from .budget_law_equipment_views import budget_law_equipment_data_info, get_budget_law_list, get_budget_equipment_list, get_work_equipment_list
from .budget_law_equipment_views import get_equipment_list, filter_equip_family, filter_equip_type, select_budget_law
from .budget_law_equipment_views import select_budget_equipment, budget_law_entry, budget_equipment_entry
from .budget_law_equipment_views import budget_law_detail, budget_equipment_detail, budget_law_delete, budget_equipment_delete
from .budget_law_equipment_views import work_equipment_data_info, work_equipment_entry, work_equipment_detail, work_equipment_delete, work_equipment_detail_info
from .budget_law_equipment_views import filter_facility_code, reset_equipment_list
# 取扱物質関係
from .handling_material_views import handling_material_data_info, handling_material_detail, handling_material_list
from .handling_material_views import handling_material_entry, handling_material_delete, handling_material_my_master_list
from .handling_material_views import handling_material_my_master_delete, handling_material_my_master_entry
from .handling_material_views import handling_material_master_list
# 要求仕様関係
from .required_spec_views import required_spec_data_info, required_spec_entry, required_spec_delete, required_spec_list
from .required_spec_views import required_spec_detail
# 工事方針概要関係
from .construction_policy_overview_views import policy_overview_data_info, policy_overview_entry, policy_overview_delete
from .construction_policy_overview_views import policy_overview_detail, policy_overview_list
# 要求機能関係
from .required_function_views import required_function_entry, required_function_delete, required_function_data_info
from .required_function_views import required_function_list, required_function_data_info_2
# 計画担当者関係:planning_charge_person_views
from .planning_charge_person_views import planning_charge_person_data_info, select_charge_person
from .planning_charge_person_views import planning_charge_person_entry, get_planning_charge_person_list, get_planning_charge_person_user_list
from .planning_charge_person_views import planning_charge_person_detail, planning_charge_person_delete

from .estimate_work_list import get_estimate_work_list, estimate_work_lists_display, budget_estimate_entry
from .estimate_work_list import estimate_send_back, budget_new_work_entry_complete, work_return
from .risks_views import risks_info, risks_entry, get_risks_list, risks_go_next_step

# 工事関係
from .work_views import work_detail, work_common_data_info, work_default_entry, work_common_entry, get_work_lists
from .work_views import work_filter, plan_work_copy, copy_free_spec_list_entry, copy_equipment_list_entry
# 詳細仕様関係
from .template_function_views import template_function_data_info
# 詳細仕様(熱交換)関係
from .heat_exchange_spec_views import heat_exchange_spec_entry, heat_exchange_data_info
# 詳細仕様（自由）関係
from .free_function_views import free_function_data_info, free_function_data_entry, select_free_spec_template
# 見積関係
from .estimate_views import estimate_data_info, discount_list_info, estimate_entry, price_value_update
# 提出書類関係
from .document_views import select_document, document_detail, document_data_info, get_document_list, document_entry
from .document_views import document_delete
# 適用法規/支給品関係
from .work_law_supplies_views import work_law_supplies_data_info, get_work_law_list, get_work_supplies_list
from .work_law_supplies_views import select_work_law, select_work_supplies, work_law_entry, work_law_delete
from .work_law_supplies_views import work_law_detail, work_supplies_entry, work_supplies_delete, work_supplies_detail
# 届出cs関係
from .cs_views import get_cs_lists, cs_filter, cs_budget_id_filter, cs_common_entry, cs_detail_template
from .cs_views import cs_related_laws_list_info, get_cs_related_laws_list, get_cs_related_laws_list_forcus
from .cs_views import cs_data_info, delete_cs_notification_progress, cs_entry, get_cs_lists_data
from .cs_views import cs_laws_progress_top_page, cs_laws_progress_filter, get_cs_laws_progress_list
from .cs_views import cs_laws_progress_date_entry
from .cs_views import cs_safety_health_data_info, cs_safety_health_entry
from .cs_views import cs_environment_data_info, cs_environment_entry
from .cs_views import cs_engineering_data_info, cs_engineering_entry
from .cs_views import cs_department_list_filter, cs_go_next_step, next_button_display, get_cs_complete_count
# 工事実行関係
from .execution_views import get_execution_budget_lists, execution_budget_filter, execution_detail_template
from .execution_views import get_execution_work_lists, execution_work_filter
from .execution_views import get_specification_person_in_charge_list
from .execution_views import execution_budget_data_info, execution_budget_entry
from .execution_views import execution_work_data_info, execution_work_entry
from .execution_views import execution_work_copy, execution_work_copy_source, copy_document_list_entry, copy_law_supplies_list_entry
from .execution_views import copy_uploadfile_list_entry, budget_information
from .execution_views import get_specification_progress_count, get_budget_complete_count, probudgetunit_detail_template
from .execution_provendorevaluation_views import execution_provendorevaluation_data_info, execution_provendorevaluation_entry
from .execution_proindividualcontractdoc_views import execution_proindividualcontractdoc_data_info, execution_proindividualcontractdoc_entry
from .execution_proinspectionresults_views import execution_proinspectionresults_data_info, execution_proinspectionresults_entry
from .execution_proindividualcontractdoc_views import execution_proindividualcontractdoc_data_info, execution_proindividualcontractdoc_entry, confirmed_vendor_change
from .execution_proinspectionresults_views import execution_proinspectionresults_data_info, execution_proinspectionresults_entry

from .execution_prodelivery_views import execution_prodelivery_data_info, execution_prodelivery_entry
from .execution_proinspection_acceptance_views import execution_proinspection_acceptance_data_info, execution_proinspection_acceptance_entry
from .execution_proconstructionprep_views import execution_proconstructionprep_data_info, execution_proconstructionprep_entry
from .execution_proconstructionqualityresults_views import execution_proconstructionqualityresults_data_info, execution_proconstructionqualityresults_entry

from .execution_handling_material_views import execution_handling_material_data_info, execution_handling_material_list
from .execution_required_function_views import execution_required_function_data_info,  execution_required_function_list, execution_required_function_data_info_2
from .execution_proestimates_views import execution_proestimates_data_info, execution_proestimates_entry
from .execution_output_application_views import execution_output_application, comparison_table_sheet_each_vendor_info_make, make_complete_report_file

# テスト用
from .work_views import additional_document_save, additional_document_read
from .temporary_views import get_cs_log_lists, daily_construction_display, construction_data_get, daily_construction_entry_page, construction_entry_data_get, position_data_entry, file_import

# urls.py側でview名を指定
# from .mainte_views import maint_detail, maint_data_info, get_maint_lists, maint_edit, maint_filter, maint_entry, maint_common_entry, maint_detail_template
# from .mainte_views import mainte_detail_template, get_mainte_lists, LaboratoryDiagnosis, Recoverycompleted, Specification, BudgetBasicInformation, MaterialInformation, Specifications, Confirmed
# from .mainte_views import ResponseRequest, __select__discoverer, __select__status, __select__equipment_no, __select__cost_center, __div__plantia
# from .mainte_views import ResponseRequest_entry

# from .mainte_views import TEST
# 故障対応関係
from .maintenance_views import maintenance_change_department
from .phenomenon_views import phenomenon_data_info, phenomenon_entry, get_phenomenon_lists, phenomenon_filter
from .phenomenon_views import phenomenon_equipment_delete, phenomenon_copy_source, phenomenon_copy, measure_copy
from .inspection_views import inspection_data_info, inspection_entry
from .measure_views import measure_data_info, measure_entry, measure_change_department
from .notification_check_views import notification_check_data_info, notification_check_entry, notification_check_filter,get_notification_check_lists
from .report_maintenance_g_views import target_equipment_history_report_data_info, target_equipment_history_report_data_entry, equipment_history_report_data_pre_entry
from . import maintenance_report_origin_g_views
from .maintenance_order_views import maintenance_order_data_info, maintenance_iep_mail_send, maintenance_order_entry
from .maintenance_order_vendor_views import maintenance_order_vendor_data_info, maintenance_order_vendor_entry, make_request_for_quotation
from .maintenance_order_estimates_views import maintenance_order_estimates_data_info, maintenance_order_estimates_entry
from .maintenance_order_estimates_views import make_request_estimate_maintenance_order
from .maintenance_inspection_acceptance_views import maintenance_inspection_acceptance_info, maintenance_inspection_acceptance_entry

