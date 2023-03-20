from django.db import models
from .master_models import ExchangeTypeMaster


# 対機能要求仕様表示項目
class DisplayItemForHeatExchange(models.Model):
    exchange_type = models.ForeignKey(ExchangeTypeMaster, verbose_name='型式', null=True, on_delete=models.PROTECT)
    display_exchange_area_flag = models.IntegerField('伝熱面積表示FL', blank=True, null=True)
    display_hot_fluid_flag = models.IntegerField('高温物質FL', blank=True, null=True)
    display_hot_design_temperature_flag = models.IntegerField('高温側設計温度表示FL', blank=True, null=True)
    display_hot_regular_use_temperature_flag = models.IntegerField('高温側常用温度表示FL', blank=True, null=True)
    display_hot_input_temperature_flag = models.IntegerField('高温側入口温度表示FL', blank=True, null=True)
    display_hot_output_temperature_flag = models.IntegerField('高温側出口温度表示FL', blank=True, null=True)
    display_hot_fluid_capacity_flag = models.IntegerField('高温物質流量表示FL', blank=True, null=True)
    display_hot_fluid_capacity_unit_flag = models.IntegerField('高温物質流量単位表示FL', blank=True, null=True)
    display_hot_design_pressure_flag = models.IntegerField('高温側設計圧力表示FL', blank=True, null=True)
    display_hot_regular_use_pressure_flag = models.IntegerField('高温側常用圧力表示FL', blank=True, null=True)
    display_hot_pressure_unit_flag = models.IntegerField('高温側圧力単位表示FL', blank=True, null=True)
    display_cool_fluid_flag = models.IntegerField('低温物質FL', blank=True, null=True)
    display_cool_design_temperature_flag = models.IntegerField('低温側設計温度表示FL', blank=True, null=True)
    display_cool_regular_use_temperature_flag = models.IntegerField('低温側常用温度表示FL', blank=True, null=True)
    display_cool_input_temperature_flag = models.IntegerField('低温側入口温度表示FL', blank=True, null=True)
    display_cool_output_temperature_flag = models.IntegerField('低温側出口温度表示FL', blank=True, null=True)
    display_cool_fluid_capacity_flag = models.IntegerField('低温物質流量表示FL', blank=True, null=True)
    display_cool_fluid_capacity_unit_flag = models.IntegerField('低温物質流量単位表示FL', blank=True, null=True)
    display_cool_design_pressure_flag = models.IntegerField('低温側設計圧力表示FL', blank=True, null=True)
    display_cool_regular_use_pressure_flag = models.IntegerField('低温側常用圧力表示FL', blank=True, null=True)
    display_cool_pressure_unit_flag = models.IntegerField('低温側圧力単位表示FL', blank=True, null=True)
    display_rem_flag = models.IntegerField('備考表示FL', blank=True, null=True)


# 詳細仕様_自由記入テンプレート
class FreeSpecTemplate(models.Model):
    template_id = models.IntegerField('テンプレートid', blank=True, null=True)
    template_name = models.CharField('テンプレート名', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)


# 詳細仕様_自由記入テンプレート(中身)
class FreeSpecDetailTemplate(models.Model):
    template_id = models.IntegerField('テンプレートid', blank=True, null=True)
    page = models.IntegerField('ページ', blank=True, null=True)
    rev_no = models.IntegerField('RevNo', blank=True, null=True)
    detail = models.TextField('詳細', max_length=4000, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_datetime = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_datetime = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('変更者', max_length=20, blank=True, null=True)
