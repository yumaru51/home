from django.db import models
from fms.models import DivisionMaster, DepartmentMaster, User, UserAttribute
import datetime


# 対象マスタ
class TargetMaster(models.Model):
    target = models.CharField('対象', max_length=20, primary_key=True)
    target_name = models.CharField('対象名', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    # def __str__(self):
    #     return u'%s' % (self.target_name)

    class Meta:
        db_table = 'm_target'


# 入力テーブルマスタ
# class EntryMaster(models.Model):
#     target = models.CharField('対象', max_length=20, blank=True, null=True)
#     item = models.CharField('項目', max_length=40, blank=True, null=True)
#     item_type = models.CharField('項目種類', max_length=40, blank=True, null=True)
#     lost_flag = models.IntegerField('無効FL', blank=True, null=True)
#
#     class Meta:
#         db_table = 'm_entry'


# 詳細画面のタブを管理
class PageMaster(models.Model):
    page = models.CharField('ページID', max_length=20, primary_key=True)
    page_name = models.CharField('ページ名', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.page_name)

    class Meta:
        db_table = 'm_page'


# ボタン機能を管理
class ActionMaster(models.Model):
    action = models.CharField('作業CD', max_length=20, primary_key=True)
    action_name = models.CharField('作業名', max_length=20, blank=True, null=True)
    action_class = models.CharField('作業属性', max_length=20, blank=True, null=True)
    action_authority = models.IntegerField('作業権限', blank=True, null=True)
    progress_transition = models.IntegerField('進捗遷移', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.action_name)

    class Meta:
        db_table = 'm_action'


# ワークフローのステップを管理
class StepMaster(models.Model):
    step = models.IntegerField('工程ID', primary_key=True)
    # target = models.ForeignKey(TargetMaster, verbose_name='対象', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    step_name = models.CharField('工程名', max_length=20, blank=True, null=True)
    hidden_flag = models.IntegerField('無効FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    # def __str__(self):
    #     return u'%s' % (self.step_name)

    class Meta:
        db_table = 'm_step'


# ステップ＆ページのエントリー制御を管理
class StepPageEntryMaster(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT)
    page = models.ForeignKey(PageMaster, verbose_name='ページID', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    target = models.ForeignKey(TargetMaster, verbose_name='対象', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    # item = models.CharField('項目', max_length=40, blank=True, null=True)
    # entry = models.IntegerField('入力FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    class Meta:
        db_table = 'm_step_page_entry'


# ステップ毎の表示タブを管理
class StepDisplayPage(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT)
    page_no = models.IntegerField('ページNO', blank=True, null=True)
    page = models.ForeignKey(PageMaster, verbose_name='ページID', blank=False, null=False, on_delete=models.PROTECT)
    default_page = models.IntegerField('初期ページ', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    class Meta:
        db_table = 'm_step_display_page'


# ステップ毎の担当部門管理
class StepChargeDepartment(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT)
    target = models.ForeignKey(TargetMaster, verbose_name='対象', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    charge_department = models.CharField('担当部署', max_length=20, blank=True, null=True)
    # department = models.ForeignKey(DepartmentMaster, verbose_name='担当部署', related_name='charge_department', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    class Meta:
        db_table = 'm_step_charge_department'


# ステップ毎の遷移先を管理
class StepRelation(models.Model):
    present_step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT, related_name='steprelation_present_step')
    next_step = models.ForeignKey(StepMaster, verbose_name='次工程ID', blank=False, null=False, on_delete=models.PROTECT, related_name='steprelation_next_step')
    type = models.CharField('進行方向', max_length=10, blank=True, null=True)  # next or return
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    class Meta:
        db_table = 'm_step_relation'


# 各ステップのボタン管理
class StepAction(models.Model):
    step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT)
    # target = models.ForeignKey(TargetMaster, verbose_name='対象', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    action_class = models.CharField('作業属性', max_length=20, blank=True, null=True)
    action = models.ForeignKey(ActionMaster, verbose_name='作業CD', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    class Meta:
        db_table = 'm_step_action'


# ログトランザクション
class Log(models.Model):
    target = models.ForeignKey(TargetMaster, verbose_name='対象', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    target_table_id = models.IntegerField('対象ID', blank=True, null=True)
    step = models.ForeignKey(StepMaster, verbose_name='工程ID', blank=False, null=False, on_delete=models.PROTECT)
    action = models.ForeignKey(ActionMaster, verbose_name='作業CD', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    operation_datetime = models.DateTimeField('作業日時', blank=True, null=True)
    operator = models.CharField('作業者', max_length=20, blank=True, null=True)
    # username = models.ForeignKey(User, verbose_name='作業者', related_name='operator', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    # operator_division = models.CharField('作業者部門', max_length=20, blank=True, null=True)
    operator_department = models.CharField('作業者部署', max_length=20, blank=True, null=True)
    # department = models.ForeignKey(DepartmentMaster, verbose_name='作業者部署', related_name='operator_department', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    comment = models.CharField('コメント', max_length=800, blank=True, null=True)

    # def __str__(self):
    #     user = User.objects.get(username=self.operator)
    #     return u'%s　%s' % (user.last_name, user.first_name)

    class Meta:
        db_table = 't_log'


# 依頼トランザクション
class Request(models.Model):
    division = models.CharField('部門名', max_length=40, blank=True, null=True)
    # division = models.ForeignKey(DivisionMaster, verbose_name='部門名', max_length=40, blank=True, null=True, on_delete=models.PROTECT)
    department = models.CharField('部署名', max_length=40, blank=True, null=True)
    # department = models.ForeignKey(DepartmentMaster, verbose_name='部署名', related_name='department', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    user = models.CharField('申請者', max_length=40, blank=True, null=True)
    # username = models.ForeignKey(User, verbose_name='申請者', related_name='user', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    change_target = models.CharField('変更対象', max_length=100, blank=True, null=True)
    others = models.CharField('その他', max_length=40, blank=True, null=True)
    title = models.CharField('変更管理名称', max_length=50, blank=True, null=True)
    outline = models.CharField('変更内容概略', max_length=1000, blank=True, null=True)
    level = models.CharField('継続/一過性', max_length=40, blank=True, null=True)
    treatment = models.CharField('リスク低減処置', max_length=40, blank=True, null=True)
    safety_aspect = models.CharField('評価レベル_安全面', max_length=40, blank=True, null=True)
    quality_aspect = models.CharField('評価レベル_品質面', max_length=40, blank=True, null=True)
    delivery_date = models.DateField('変更希望日', blank=True, null=True)

    delivery_date_start = models.DateField('変更日開始', blank=True, null=True)                  # 原課変更実施
    delivery_date_end = models.DateField('変更日終了', blank=True, null=True)                    # 原課変更実施
    level2 = models.CharField('継続/一過性', max_length=40, blank=True, null=True)               # 原課変更実施
    others2 = models.CharField('その他', max_length=40, blank=True, null=True)                   # 原課変更実施

    completion_date = models.DateField('完了日', blank=True, null=True)
    application_date = models.DateField('申請日', blank=True, null=True, default=datetime.datetime.today())
    education_management_system_id = models.CharField('教育管理システムID', max_length=40, blank=True, null=True)

    class Meta:
        db_table = 't_request'


# 品質トランザクション
class Quality(models.Model):
    request = models.ForeignKey(Request, verbose_name='依頼ID', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    quality_aspect = models.CharField('所管評価レベル', max_length=40, blank=True, null=True)
    judgement = models.CharField('判定', max_length=40, blank=True, null=True)
    results = models.CharField('対策検討結果', max_length=1000, blank=True, null=True)
    evaluation = models.CharField('変更結果評価', max_length=1000, blank=True, null=True)

    class Meta:
        db_table = 't_quality'


# 安全トランザクション
class Safety(models.Model):
    request = models.ForeignKey(Request, verbose_name='依頼ID', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    safety_aspect = models.CharField('所管評価レベル', max_length=40, blank=True, null=True)
    judgement = models.CharField('判定', max_length=40, blank=True, null=True)
    results = models.CharField('対策検討結果', max_length=1000, blank=True, null=True)
    evaluation = models.CharField('変更結果評価', max_length=1000, blank=True, null=True)

    class Meta:
        db_table = 't_safety'


# 各案件の進捗管理
class Progress(models.Model):
    request = models.ForeignKey(Request, verbose_name='依頼ID', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    target = models.CharField('対象', max_length=20, blank=True, null=True)
    present_step = models.ForeignKey(StepMaster, verbose_name='現工程ID', blank=True, null=True, on_delete=models.PROTECT, related_name='progress_present_step')
    present_division = models.CharField('現作業部門', max_length=20, blank=True, null=True)  # 遷移時、次の作業部門は画面から選択
    present_department = models.CharField('現作業部署', max_length=20, blank=True, null=True)  # 遷移時、次の作業部署は画面から選択
    # department = models.ForeignKey(DepartmentMaster, verbose_name='現作業部署', related_name='present_department', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    present_operator = models.CharField('現作業者', max_length=20, blank=True, null=True)  # 遷移時、次の作業者は画面から選択
    # username = models.ForeignKey(User, verbose_name='現作業者', related_name='present_operator', max_length=20, blank=False, null=False, on_delete=models.PROTECT)
    last_step = models.ForeignKey(StepMaster, verbose_name='前工程ID', blank=True, null=True, on_delete=models.PROTECT, related_name='progress_last_step')
    # last_operator = models.CharField('前作業者', max_length=20, blank=True, null=True)  # 前の作業者はログから取得
    # last_operation_datetime = models.DateTimeField('前作業日時', blank=True, null=True)  # 前の作業日時はログから取得

    class Meta:
        db_table = 't_progress'

