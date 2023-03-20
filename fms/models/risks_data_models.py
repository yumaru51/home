from django.db import models


# リスク評価結果
class BudgetRisks(models.Model):
    business_year = models.IntegerField('年度', blank=True, null=True)
    risks = models.CharField('リスク評価結果', max_length=2400, blank=True, null=True)
    note = models.CharField('備考', max_length=400, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)