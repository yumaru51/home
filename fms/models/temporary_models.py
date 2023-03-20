from django.db import models
from .common_master_models import User


# PLANTIAインポートファイル出力
class TemporaryMakePlantiaImport(models.Model):
    user = models.ForeignKey(User, verbose_name=' ユーザーid', null=True, on_delete=models.PROTECT)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 工事
class DailyConstruction(models.Model):
    scheduled_construction_id = models.IntegerField('計画工事id', blank=True, null=True)
    small_construction_id = models.IntegerField('小口工事id', blank=True, null=True)
    construction_class = models.IntegerField('工事区分', blank=True, null=True)
    construction_name = models.CharField('工事名', max_length=70, blank=True, null=True)
    fires_flag = models.BooleanField('火気使用FL', blank=True, null=True)
    drilling_flag = models.BooleanField('掘削FL', blank=True, null=True)
    blockage_flag = models.BooleanField('交通遮断FL', blank=True, null=True)
    notification_flag = models.BooleanField('届出FL', blank=True, null=True)
    high_place_flag = models.BooleanField('高所作業FL', blank=True, null=True)
    entering_the_tank_flag = models.BooleanField('入槽作業FL', blank=True, null=True)
    heavy_equipment_flag = models.BooleanField('重機使用FL', blank=True, null=True)
    brake_off_flag = models.BooleanField('縁切FL', blank=True, null=True)
    contamination_flag = models.BooleanField('異物FL', blank=True, null=True)
    construction_date = models.DateField('工事日', blank=True, null=True)
    charge_person = models.CharField('担当者', max_length=30, blank=True, null=True)
    constructor = models.CharField('業者', max_length=30, blank=True, null=True)
    detail = models.CharField('作業詳細', max_length=300, blank=True, null=True)
    rem = models.CharField('備考', max_length=300, blank=True, null=True)
    position_x = models.IntegerField('x座標', blank=True, null=True)
    position_y = models.IntegerField('y座標', blank=True, null=True)
    blockage_position_x = models.IntegerField('交通遮断x座標', blank=True, null=True)
    blockage_position_y = models.IntegerField('交通遮断y座標', blank=True, null=True)
    display_number = models.IntegerField('表示NO', blank=True, null=True)
    lost_flag = models.BooleanField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)

