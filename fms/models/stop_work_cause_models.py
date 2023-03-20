from django.db import models


# 工事中止理由
class StopWorkCause(models.Model):
    budget_id = models.IntegerField('予算ID', blank=True, null=True)
    construction_id = models.IntegerField('工事ID', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    stop_work_cause_name = models.CharField('中止原因', max_length=20, blank=True, null=True)
    stop_work_reason = models.CharField('中止理由', max_length=200, blank=True, null=True)
    stop_work_risk = models.CharField('リスク', max_length=200, blank=True, null=True)
    approval_no = models.CharField('決裁No', max_length=15, blank=True, null=True)
    target = models.CharField('中止対象', max_length=20, blank=True, null=True)
    present_step = models.IntegerField('中止時のステップ', blank=True, null=True)
    present_operator = models.CharField('中止時の作業担当者', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
