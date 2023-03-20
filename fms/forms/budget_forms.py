from django.forms import ModelForm
import bootstrap_datepicker_plus as datetimepicker
from fms.models import Budget, BudgetCondition


class BudgetEditFormLeft(ModelForm):
    class Meta:
        model = Budget
        fields = [
            'budget_id',
            'budget_no',
            'budget_name',
            'relation_budget_id',
            'decision_no',
            'business_year',
            'application_class',
            'budget_class',
            'period_class',
            'application_price',
            'budget_price',
            'budget_main_department',
            'budget_department_charge_person',
            'facility_process',
            'start_date',
            'end_date',
            'order_date',
            'delivery_date',
            'pre_order_flag',
            'asdm_flag'
        ]

        widgets = {
            'start_date': datetimepicker.DatePickerInput(
                format='%Y年%m月%d日',
                options={
                    'locale': 'ja',
                    'dayViewHeaderFormat': 'YYYY年 MMMM',
                }
            ),
            'end_date': datetimepicker.DatePickerInput(
                format='%Y年%m月%d日',
                options={
                    'locale': 'ja',
                    'dayViewHeaderFormat': 'YYYY年 MMMM',
                }
            ),
            'order_date': datetimepicker.DatePickerInput(
                format='%Y-%m-%d',
                options={
                    'locale': 'ja',
                    'dayViewHeaderFormat': 'YYYY年 MMMM',
                }
            ),
            'delivery_date': datetimepicker.DatePickerInput(
                format='%Y-%m-%d',
                options={
                    'locale': 'ja',
                    'dayViewHeaderFormat': 'YYYY年 MMMM',
                }
            )
        }


class BudgetEditFormCenter(ModelForm):
    class Meta:
        model = Budget
        fields = [
            'purpose_class',
            'purpose',
            'detail',
            'effect',
        ]


class BudgetEditFormRight(ModelForm):
    class Meta:
        model = Budget
        fields = [
            'influence_for_operation',
            'influence_for_quality',
            'budget_rem'
        ]
