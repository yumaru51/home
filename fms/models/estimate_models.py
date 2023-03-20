from django.db import models


# 見積
class Estimate(models.Model):
    work_id = models.IntegerField('工事id', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    vendor = models.CharField('業者名', max_length=50, blank=True, null=True)
    estimate_price = models.IntegerField('見積金額', blank=True, null=True)
    prospect_price = models.IntegerField('見込金額', blank=True, null=True)
    entry_class = models.CharField('登録区分', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    adoption_flag = models.IntegerField('採用FL', blank=True, null=True)
    price_after_discount = models.IntegerField('値引後金額', blank=True, null=True)
    discount_num = models.IntegerField('値引回数', blank=True, null=True)
    start_date = models.DateField('着工日', blank=True, null=True)
    end_date = models.DateField('完工日', blank=True, null=True)
    management_class = models.CharField('区分', max_length=1, blank=True, null=True)
    rem = models.CharField('備考', max_length=400, blank=True, null=True)


# 値引
class Discount(models.Model):
    estimate_id = models.IntegerField('見積id', blank=True, null=True)
    discount_no = models.IntegerField('値引回数', blank=True, null=True)
    discount_price = models.IntegerField('値引額', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_on_progress_flag = models.IntegerField('登録中FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
    vendor_person = models.CharField('業者担当者', max_length=20, blank=True, null=True)
    rem = models.TextField('備考', max_length=500, blank=True, null=True)