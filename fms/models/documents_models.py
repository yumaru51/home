from django.db import models
# from .master_models import ExchangeTypeMaster


# 提出書類
class SubmissionDocument(models.Model):
    work_id = models.IntegerField('工事id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    document_name = models.CharField('書類名', max_length=50, blank=True, null=True)
    number_of_copies = models.IntegerField('部数', blank=True, null=True)
    submission_deadline = models.CharField('提出期限', max_length=50, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    entry_class = models.CharField('登録区分', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)

