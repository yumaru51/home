from django.db import models


# プログラムデータ
class Programs(models.Model):
    program_name = models.CharField('プログラム名', max_length=30, blank=True, null=True)
    description = models.CharField('説明', max_length=300, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_date = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)


# ファイルデータ
class Files(models.Model):
    program_id = models.IntegerField('プログラムid', blank=True, null=True)
    source_file_path = models.CharField('ソースファイル保存パス', max_length=50, blank=True, null=True)
    source_file_name = models.CharField('ソースファイル名', max_length=30, blank=True, null=True)
    post_to_file_path = models.CharField('転記先ファイル保存パス', max_length=50, blank=True, null=True)
    post_to_file_name = models.CharField('転記先ファイル名', max_length=30, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 作業データ
class Tasks(models.Model):
    program_id = models.IntegerField('プログラムid', blank=True, null=True)
    source_sheet_name = models.CharField('ソースシート名', max_length=30, blank=True, null=True)
    source_cell_name = models.CharField('ソースセル名', max_length=10, blank=True, null=True)
    post_to_sheet_name = models.CharField('転記先シート名', max_length=30, blank=True, null=True)
    post_to_cell_name = models.CharField('転記先セル名', max_length=10, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_date = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)
    update_date = models.DateTimeField('更新日時', blank=True, null=True)
    update_operator = models.CharField('更新者', max_length=20, blank=True, null=True)
    test_flag = models.IntegerField('テストFL', blank=True, null=True)


# 実行ログデータ
class ExecuteLogs(models.Model):
    program_id = models.IntegerField('プログラムid', blank=True, null=True)
    operator = models.CharField('実行者', max_length=20, blank=True, null=True)
    start_datetime = models.DateTimeField('開始日時', blank=True, null=True)
    end_datetime = models.DateTimeField('終了日時', blank=True, null=True)


# プログラム登録ログデータ
class ProgramEntryLogs(models.Model):
    program_id = models.IntegerField('プログラムid', blank=True, null=True)
    program_name = models.CharField('プログラム名', max_length=30, blank=True, null=True)
    description = models.CharField('説明', max_length=300, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    source_file_path = models.CharField('ソースファイル保存パス', max_length=50, blank=True, null=True)
    source_file_name = models.CharField('ソースファイル名', max_length=30, blank=True, null=True)
    post_to_file_path = models.CharField('転記先ファイル保存パス', max_length=50, blank=True, null=True)
    post_to_file_name = models.CharField('転記先ファイル名', max_length=30, blank=True, null=True)
    entry_date = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)


# タスク登録ログデータ
class TaskEntryLogs(models.Model):
    task_id = models.IntegerField('タスクid', blank=True, null=True)
    source_sheet_name = models.CharField('ソースシート名', max_length=30, blank=True, null=True)
    source_cell_name = models.CharField('ソースセル名', max_length=10, blank=True, null=True)
    post_to_sheet_name = models.CharField('転記先シート名', max_length=30, blank=True, null=True)
    post_to_cell_name = models.CharField('転記先セル名', max_length=10, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    entry_date = models.DateTimeField('登録日時', blank=True, null=True)
    entry_operator = models.CharField('登録者', max_length=20, blank=True, null=True)