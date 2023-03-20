from django.db import models


# ユーザーマスタ
class User(models.Model):
    username = models.CharField('ユーザーid', max_length=150, primary_key=True)
    first_name = models.CharField('名', max_length=30, blank=True, null=True)
    last_name = models.CharField('姓', max_length=30, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s　%s' % (self.last_name, self.first_name)


# 年度マスタ
class BusinessYearMaster(models.Model):
    business_year = models.IntegerField('年度', primary_key=True)
    display_flag = models.IntegerField('表示FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.business_year)


# 部署マスタ
class DepartmentMaster(models.Model):
    department_cd = models.CharField('部署CD', max_length=10, primary_key=True)
    department_name = models.CharField('部署名', max_length=20, blank=True, null=True)
    division_cd = models.CharField('部門CD', max_length=10, blank=True, null=True)
    area_manager = models.ForeignKey(User, verbose_name='エリア管理者', null=True, on_delete=models.PROTECT)
    jurisdiction_area = models.CharField('所管エリア', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.department_name)


# 部門マスタ
class DivisionMaster(models.Model):
    division_cd = models.CharField('部門CD', max_length=10, primary_key=True)
    division_name = models.CharField('部門名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.division_name)


# 期マスタ
class PeriodClassMaster(models.Model):
    period_class_cd = models.IntegerField('期CD', primary_key=True)
    period_class_name = models.CharField('期区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.period_class_name)


# 仕入先マスタ
class SupplierMaster (models.Model):
    supplier_cd = models.CharField('仕入先コード', max_length=10, blank=False, null=False)
    supplier_name = models.CharField('仕入先名', max_length=40, blank=True, null=True)
    lost_flag = models. IntegerField('無効FL', blank=True, null=True)


# 税コードマスタ
class TaxMaster(models.Model):
    tax_cd = models.CharField('税コード', max_length=2, blank=False, null=False)
    text = models.CharField('テキスト', max_length=50, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# ユーザー属性
class UserAttribute(models.Model):
    username = models.CharField('ユーザー名', max_length=150, blank=True, null=True)
    department = models.CharField('部署', max_length=10, blank=True, null=True)
    division = models.CharField('部門', max_length=10, blank=True, null=True)
    authority = models.CharField('権限', max_length=10, blank=True, null=True)
    confirm_username = models.CharField('確認者', max_length=150, blank=True, null=True)
    permit_username = models.CharField('承認者', max_length=150, blank=True, null=True)
    department_charge_flag = models.CharField('部署担当フラグ', max_length=10, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    user_order = models.IntegerField('部署内表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# ユーザーアクセス権
class UserAccessPermission(models.Model):
    username = models.CharField('ユーザー名', max_length=150, blank=True, null=True)
    permission = models.CharField('アクセス許可', max_length=40, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)


# 入力禁止文字テーブル
class InputNgCharacter(models.Model):
    ng_character = models.CharField('禁止文字', max_length=10, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

