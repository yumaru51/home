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


# 部署マスタ
class DepartmentMaster(models.Model):
    department_cd = models.CharField('部署CD', max_length=10, primary_key=True)
    department_name = models.CharField('部署名', max_length=20, blank=True, null=True)
    division_cd = models.CharField('部門CD', max_length=10, blank=True, null=True)
    area_manager = models.ForeignKey(User, verbose_name='エリア担当者', null=True, on_delete=models.PROTECT)
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

