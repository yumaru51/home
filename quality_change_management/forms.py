from django import forms
from quality_change_management.models import TargetMaster, StepMaster, StepDisplayItem, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User


class RequestForm(forms.ModelForm):
    # list用意
    division_list = [('', '')]
    department_list = [('', '')]
    user_list = [('', '')]
    method_list = [
        ('方法', '方法'),
        ('設備', '設備'),
        ('原料/副原料', '原料/副原料'),
        ('人', '人'),
    ]

    # 外部参照でlist作成('value', 'text')形式
    for division_master in DivisionMaster.objects.values_list('division_cd', 'division_name'):
        division_list.append(division_master)
    division = forms.ChoiceField(label='部門名', choices=division_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')

    for department_master in DepartmentMaster.objects.values_list('department_cd', 'department_name'):
        department_list.append(department_master)
    department = forms.ChoiceField(label='部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')

    for user_master in User.objects.filter(lost_flag=0).values_list('username', 'last_name'):
        user_list.append(user_master)
    user = forms.ChoiceField(label='申請者', choices=user_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')

    method = forms.ChoiceField(label='変更対象', choices=method_list, widget=forms.RadioSelect(attrs={}))
    # title = forms.CharField(label='変更管理名称', widget=forms.TextInput(attrs={'class': 'form-control'}))
    # delivery_date = forms.DateField(label='変更希望日', widget=forms.DateInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Request
        fields = ['title', 'division', 'department', 'user', 'method', 'delivery_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', }),
        }

    def __init__(self, edit, **kwargs):
        super(RequestForm, self).__init__(**kwargs)
        if edit == 'off':
            self.fields['title'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['title'].widget.attrs['tabindex'] = '-1'
            self.fields['division'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['division'].widget.attrs['tabindex'] = '-1'
            self.fields['department'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['department'].widget.attrs['tabindex'] = '-1'
            self.fields['user'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['user'].widget.attrs['tabindex'] = '-1'
            self.fields['method'].widget.attrs['onclick'] = 'return false'
            self.fields['delivery_date'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['delivery_date'].widget.attrs['tabindex'] = '-1'


class ProgressForm(forms.ModelForm):
    # list用意
    step_list = [('', '')]
    department_list = [('', '')]
    user_list = [('', '')]
    # 外部参照でlist作成('value', 'text')形式

    for step_master in StepMaster.objects.values_list('step', 'step_name'):
        step_list.append(step_master)
    present_step_id = forms.ChoiceField(label='進捗名', choices=step_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    for department_master in DepartmentMaster.objects.values_list('department_cd', 'department_name'):
        department_list.append(department_master)
    present_department = forms.ChoiceField(label='部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    for user_master in User.objects.filter(lost_flag=0).values_list('username', 'last_name'):
        user_list.append(user_master)
    present_operator = forms.ChoiceField(label='申請者', choices=user_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)

    class Meta:
        model = Progress
        # fields = ['request_id', 'present_step_id', 'present_department', 'present_operator']
        fields = ['present_department', 'present_operator', 'present_step_id']
        widgets = {
            # 'request_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LogForm(forms.ModelForm):
    test_list = [
        ('one', 'item 1'),
        ('two', 'item 2'),
        ('three', 'item 3'),
    ]
    target = forms.CharField(label='対象', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    target_table_id = forms.CharField(label='対象ID', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    step = forms.CharField(label='工程ID', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    action = forms.CharField(label='作業CD', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    operation_datetime = forms.CharField(label='作業日時', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    operator = forms.CharField(label='作業者', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    operator_division = forms.CharField(label='作業者部門', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')
    operator_department = forms.CharField(label='作業者部署', widget=forms.TextInput(attrs={'class': 'form-control'}), initial='')

    class Meta:
        model = Log
        # fields = ['target', 'target_table_id', 'step', 'action', 'operation_datetime', 'operator', 'operator_division', 'operator_department', 'comment']
        fields = ['comment']
        widgets = {
            'comment': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TestForm(forms.Form):
    data = [
        ('one', 'item 1'),
        ('two', 'item 2'),
        ('three', 'item 3'),
    ]
    name = forms.CharField(label='name', widget=forms.TextInput(
        attrs={'class': 'form-control', 'style': 'background-color:#ffff00;', 'list': 'list', 'autocomplete': 'off', 'type': 'search', 'autofocus': ''}), initial='y-kawauchi')
    # widget=forms.TextInput(attrs={'disabled': '', 'placeholder': 'test', 'maxlength': '10', 'size': '100'}))
    mail = forms.CharField(label='mail', widget=forms.TextInput(attrs={'class': 'form-control'}))
    age = forms.IntegerField(label='age', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    check = forms.BooleanField(label='Checkbox', required=False)
    user_type = forms.ChoiceField(label=u'会員タイプ', choices=[], widget=forms.RadioSelect())

    def __init__(self, gender, **kwargs):
        super(TestForm, self).__init__(**kwargs)
        if gender == 'male':
            self.fields['user_type'].choices = [('a', 'A'), ('b', 'B')]
        else:
            self.fields['user_type'].choices = [('c', 'C'), ('d', 'D'), ('e', 'E')]
            self.fields['mail_magazine'] = forms.BooleanField(label=u'メルマガ購読', widget=forms.CheckboxInput())
