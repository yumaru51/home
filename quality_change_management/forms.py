from django import forms
from quality_change_management.models import TargetMaster, StepMaster, StepPageEntryMaster, StepDisplayPage, StepChargeDepartment, StepRelation, ActionMaster, StepAction, \
    Log, Request, Quality, Safety, Progress
from fms.models import DivisionMaster, DepartmentMaster, User


# list用意　外部参照でlist作成('value', 'text')形式
step_list = [('', '')]
for step_master in StepMaster.objects.filter(lost_flag=0, hidden_flag=0).values_list('step', 'step_name'):
    step_list.append(step_master)
division_list = [('', '')]
for division_master in DivisionMaster.objects.filter(lost_flag=0).values_list('division_cd', 'division_name'):
    division_list.append(division_master)
department_list = [('', '')]
for department_master in DepartmentMaster.objects.filter(lost_flag=0).values_list('department_cd', 'department_name'):
    department_list.append(department_master)
test_list = []
user_list = [('', '')]
for user_master in User.objects.filter(lost_flag=0, first_name__isnull=False).values_list('username', 'last_name', 'first_name'):
    test_list = (user_master[0], user_master[1] + '　' + user_master[2])
    user_list.append(test_list)
    test_list = []

change_target_list = [
    ('method', '方法'),
    ('facility', '設備'),
    ('material', '原料/副原料'),
    ('man', '人'),
    ('other', 'その他')
]
level_list = [
    ('', ''),
    ('継続', '継続'),
    ('一過性', '一過性'),
]
aspect_list = [
    ('', ''),
    ('0', '0'),
    ('Ⅰ', 'Ⅰ'),
    ('Ⅱ', 'Ⅱ'),
    ('Ⅲ', 'Ⅲ'),
]
judgement_list = [
    ('', ''),
    ('許可', '許可'),
    ('条件付許可', '条件付許可'),
    ('不可', '不可'),
    ('不要', '不要'),
]
progress_class = [
    ('', ''),
    ('1', '登録'),
    ('2', '進行中'),
    ('3', '完了'),
]
work_class = [
    ('', ''),
    ('request', '原課'),
    ('engineering', '工務'),
    ('quality', '品質'),
    ('safety', '安全'),
]
display_class = [
    ('1', '完了表示'),
    ('2', '却下表示'),
]


class RequestForm(forms.ModelForm):
    division = forms.ChoiceField(label='部門名', choices=division_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    department = forms.ChoiceField(label='部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    user = forms.ChoiceField(label='申請者', choices=user_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    change_target = forms.MultipleChoiceField(label='変更対象', choices=change_target_list, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline_change_target', 'required': 'True'}), required=True)
    others = forms.CharField(label='その他', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    title = forms.CharField(label='変更管理名称', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    outline = forms.CharField(label='変更内容概略', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'cols': 60}), required=True)
    level = forms.ChoiceField(label='継続/一過性', choices=level_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    treatment = forms.CharField(label='リスク低減処置', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    safety_aspect = forms.ChoiceField(label='安全面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    quality_aspect = forms.ChoiceField(label='品質面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')
    delivery_date = forms.DateField(label='変更希望日', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=True)

    class Meta:
        model = Request
        fields = ['division', 'department', 'user', 'change_target', 'others', 'title', 'outline', 'level', 'treatment', 'safety_aspect', 'quality_aspect', 'delivery_date']
        widgets = {}

    def __init__(self, edit, step, **kwargs):
        super(RequestForm, self).__init__(**kwargs)
        if edit == 'off' or step != 1102:  # editが「off」なら入力不可。
            self.fields['division'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['division'].widget.attrs['tabindex'] = '-1'
            self.fields['department'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['department'].widget.attrs['tabindex'] = '-1'
            self.fields['user'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['user'].widget.attrs['tabindex'] = '-1'
            self.fields['others'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['others'].widget.attrs['tabindex'] = '-1'
            self.fields['title'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['title'].widget.attrs['tabindex'] = '-1'
            self.fields['outline'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['outline'].widget.attrs['tabindex'] = '-1'
            self.fields['level'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['level'].widget.attrs['tabindex'] = '-1'
            self.fields['treatment'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['treatment'].widget.attrs['tabindex'] = '-1'
            self.fields['safety_aspect'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['safety_aspect'].widget.attrs['tabindex'] = '-1'
            self.fields['quality_aspect'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['quality_aspect'].widget.attrs['tabindex'] = '-1'
            self.fields['delivery_date'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['delivery_date'].widget.attrs['tabindex'] = '-1'
            self.fields['change_target'].widget.attrs['onclick'] = 'return false'


class Request2Form(forms.ModelForm):
    delivery_date_start = forms.DateField(label='変更日開始', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=True)    # 原課変更実施
    delivery_date_end = forms.DateField(label='変更日終了', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=True)      # 原課変更実施
    level2 = forms.ChoiceField(label='継続/一過性', choices=level_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='')      # 原課変更実施
    others2 = forms.CharField(label='その他', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)                                   # 原課変更実施

    class Meta:
        model = Request
        fields = ['delivery_date_start', 'delivery_date_end', 'level2', 'others2']
        widgets = {}

    def __init__(self, edit, step, **kwargs):
        super(Request2Form, self).__init__(**kwargs)
        if edit == 'off' or step != 1401:  # editが「off」なら入力不可。
            self.fields['delivery_date_start'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['delivery_date_start'].widget.attrs['tabindex'] = '-1'
            self.fields['delivery_date_end'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['delivery_date_end'].widget.attrs['tabindex'] = '-1'
            self.fields['level2'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['level2'].widget.attrs['tabindex'] = '-1'
            self.fields['others2'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['others2'].widget.attrs['tabindex'] = '-1'


class Request3Form(forms.ModelForm):
    education_management_system_id = forms.CharField(label='教育管理システムID', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)  # 評価確認

    class Meta:
        model = Request
        fields = ['education_management_system_id', ]
        widgets = {}

    def __init__(self, edit, step, **kwargs):
        super(Request3Form, self).__init__(**kwargs)
        if edit == 'off' or step != 1601:  # editが「off」なら入力不可。
            self.fields['education_management_system_id'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['education_management_system_id'].widget.attrs['tabindex'] = '-1'


class QualityForm(forms.ModelForm):
    quality_aspect = forms.ChoiceField(label='所管評価レベル', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    judgement = forms.ChoiceField(label='判定', choices=judgement_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    results = forms.CharField(label='対策検討結果', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'cols': 60}), initial='', required=False)

    class Meta:
        model = Quality
        fields = ['quality_aspect', 'judgement', 'results']
        widgets = {
        }

    def __init__(self, edit, step, **kwargs):
        super(QualityForm, self).__init__(**kwargs)
        if edit == 'off' or step != 1301:  # editが「off」なら入力不可。
            self.fields['quality_aspect'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['quality_aspect'].widget.attrs['tabindex'] = '-1'
            self.fields['judgement'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['judgement'].widget.attrs['tabindex'] = '-1'
            self.fields['results'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['results'].widget.attrs['tabindex'] = '-1'


class SafetyForm(forms.ModelForm):
    safety_aspect = forms.ChoiceField(label='所管評価レベル', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    judgement = forms.ChoiceField(label='判定', choices=judgement_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    results = forms.CharField(label='対策検討結果', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'cols': 60}), initial='', required=False)

    class Meta:
        model = Safety
        fields = ['safety_aspect', 'judgement', 'results']
        widgets = {
        }

    def __init__(self, edit, step, **kwargs):
        super(SafetyForm, self).__init__(**kwargs)
        if edit == 'off' or step != 1301:  # editが「off」なら入力不可。
            self.fields['safety_aspect'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['safety_aspect'].widget.attrs['tabindex'] = '-1'
            self.fields['judgement'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['judgement'].widget.attrs['tabindex'] = '-1'
            self.fields['results'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['results'].widget.attrs['tabindex'] = '-1'


class Quality2Form(forms.ModelForm):
    evaluation = forms.CharField(label='変更結果評価', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'cols': 60}), initial='', required=False)

    class Meta:
        model = Quality
        fields = ['evaluation']
        widgets = {
        }

    def __init__(self, edit, step, **kwargs):
        super(Quality2Form, self).__init__(**kwargs)
        if edit == 'off' or step != 1501:  # editが「off」なら入力不可。
            self.fields['evaluation'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['evaluation'].widget.attrs['tabindex'] = '-1'


class Safety2Form(forms.ModelForm):
    evaluation = forms.CharField(label='変更結果評価', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'cols': 60}), initial='', required=False)

    class Meta:
        model = Safety
        fields = ['evaluation']
        widgets = {
        }

    def __init__(self, edit, step, **kwargs):
        super(Safety2Form, self).__init__(**kwargs)
        if edit == 'off' or step != 1501:  # editが「off」なら入力不可。
            self.fields['evaluation'].widget.attrs['style'] = 'pointer-events: none; '
            self.fields['evaluation'].widget.attrs['tabindex'] = '-1'


class LogForm(forms.ModelForm):
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
        fields = ['comment']
        widgets = {
            'comment': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProgressForm(forms.Form):
    present_department = forms.ChoiceField(label='部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    present_step_id = forms.ChoiceField(label='進捗状況', choices=step_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    title = forms.CharField(label='変更管理名称', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    work_class = forms.ChoiceField(label='作業区分', choices=work_class, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    delivery_date_from = forms.DateField(label='変更日_FROM', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    delivery_date_to = forms.DateField(label='変更日_TO', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    safety_aspect = forms.ChoiceField(label='安全面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    quality_aspect = forms.ChoiceField(label='品質面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    # next_department = forms.ChoiceField(label='次作業者部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select', 'onchange': 'change_user(this.value);'}), initial='', required=False)
    next_department = forms.ChoiceField(label='次作業者部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    next_user = forms.ChoiceField(label='次作業者', choices=user_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    display_class = forms.MultipleChoiceField(label='　', choices=display_class, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline_display_class'}), required=False)


class ReportForm(forms.Form):
    progress_class = forms.ChoiceField(label='進捗区分', choices=progress_class, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)

    present_department = forms.ChoiceField(label='部署名', choices=department_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    present_step_id = forms.ChoiceField(label='進捗状況', choices=step_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    title = forms.CharField(label='変更管理名称', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    work_class = forms.ChoiceField(label='作業区分', choices=work_class, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    completion_date_from = forms.DateField(label='完了日_FROM', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    completion_date_to = forms.DateField(label='完了日_TO', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    safety_aspect = forms.ChoiceField(label='安全面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    quality_aspect = forms.ChoiceField(label='品質面', choices=aspect_list, widget=forms.Select(attrs={'size': 1, 'class': 'form-select'}), initial='', required=False)
    display_class = forms.MultipleChoiceField(label='　', choices=display_class, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline_display_class'}), required=False)
    # test = forms.MultipleChoiceField(label='変更対象', choices=display_class, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline_display_class'}), required=False)


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

