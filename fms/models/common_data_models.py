from django.db import models


# 進捗状況
from fms.models.master_models import CheckItemMaster
from .common_master_models import DepartmentMaster


class Progress(models.Model):
    target = models.CharField('対象', max_length=20, blank=True, null=True)
    target_id = models.IntegerField('対象id', blank=True, null=True)
    present_step = models.IntegerField('工程', blank=True, null=True)
    present_department = models.CharField('作業部署', max_length=20, blank=True, null=True)
    present_division = models.CharField('作業部門', max_length=20, blank=True, null=True)
    present_operator = models.CharField('次作業者', max_length=20, blank=True, null=True)
    last_operation_step = models.IntegerField('前作業', blank=True, null=True)
    last_operator = models.CharField('前作業者', max_length=20, blank=True, null=True)
    last_operation_datetime = models.DateTimeField('前作業日時', blank=True, null=True)


# ログ
class Log(models.Model):
    target = models.CharField('対象', max_length=40, blank=True, null=True)
    target_id = models.IntegerField('対象id', blank=True, null=True)
    action = models.CharField('実行内容', max_length=20, blank=True, null=True)
    step = models.IntegerField('工程', blank=True, null=True)
    operator = models.CharField('作業者', max_length=20, blank=True, null=True)
    operator_department = models.CharField('作業者部署', max_length=20, blank=True, null=True)
    operator_division = models.CharField('作業者部門', max_length=20, blank=True, null=True)
    operation_datetime = models.DateTimeField('作業日時', blank=True, null=True)
    comment = models.CharField('コメント', max_length=800, blank=True, null=True)
    budget_id = models.IntegerField('予算id', blank=True, null=True)


# 進捗工程表示項目
class StepDisplayItem(models.Model):
    step = models.IntegerField('工程', blank=True, null=True)
    page = models.IntegerField('ページNO', blank=True, null=True)
    div_id_name = models.CharField('div_id名', max_length=40, blank=True, null=True)
    item_name = models.CharField('item名', max_length=40, blank=True, null=True)
    action_pb_flag = models.IntegerField('ボタン表示FL', blank=True, null=True)
    default_page = models.IntegerField('初期ページ', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 添付ファイル保存テーブル
class AdditionalDocuments(models.Model):
    budget_id = models.IntegerField('予算ID', blank=True, null=True)
    work_id = models.IntegerField('工事ID', blank=True, null=True)
    file_no = models.IntegerField('ファイルNo', blank=True, null=True)
    file_name = models.TextField('ファイル名', max_length=100, blank=True, null=True)
    file = models.BinaryField('ファイルデータ', blank=True, null=True)
    entry_time = models.DateTimeField('登録日時', blank=True, null=True)
    entry_user = models.TextField('登録者', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('削除フラグ', blank=True, null=True)


# 添付ファイル保存テーブル
class AttachmentDocuments(models.Model):
    folder = models.CharField('保存先', max_length=100, blank=True, null=True)
    data = models.CharField('データ', max_length=100, blank=True, null=True)
    file_name = models.CharField('ファイル名', max_length=100, blank=True, null=True)
    entry_time = models.DateTimeField('登録日時', blank=True, null=True)
    entry_user = models.CharField('登録者', max_length=20, blank=True, null=True)
    lost_flag = models.IntegerField('削除フラグ', blank=True, null=True)
    div_id_name = models.CharField('タブ名', max_length=100, blank=True, null=True)


# チェックリスト
class CheckList(models.Model):
    function_cd = models.CharField('機能コード', max_length=40, blank=True, null=True)
    target = models.CharField('対象', max_length=20, blank=True, null=True)
    target_id = models.IntegerField('対象id', blank=True, null=True)
    check_items = models.ManyToManyField(CheckItemMaster, verbose_name='チェック項目', through="CheckListItemRelation")
    check_departments = models.ManyToManyField(DepartmentMaster, verbose_name='所管部署', through="CheckListDepartmentRelation")
    lost_flag = models.IntegerField('削除フラグ', blank=True, null=True)


# チェックリスト項目
class CheckListItemRelation(models.Model):
    check_list = models.ForeignKey(CheckList, verbose_name='チェックリスト', on_delete=models.PROTECT)
    check_item = models.ForeignKey(CheckItemMaster, verbose_name='チェック項目', on_delete=models.PROTECT)
    check_status = models.IntegerField('チェック状態', blank=True, null=True)
    input_text = models.CharField('入力テキスト', max_length=100, blank=True, null=True)


# チェックリスト所管部署
class CheckListDepartmentRelation(models.Model):
    check_list = models.ForeignKey(CheckList, verbose_name='チェックリスト', on_delete=models.PROTECT)
    department = models.ForeignKey(DepartmentMaster, verbose_name='所管部署', on_delete=models.PROTECT)
    comment = models.TextField('所管部署コメント', max_length=1000, blank=True, null=True)
