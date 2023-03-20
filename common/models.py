from django.db import models


# ユーザー属性
class UserAttribute(models.Model):
    username = models.CharField('ユーザー名', max_length=150, blank=True, null=True)
    department = models.CharField('部署', max_length=10, blank=True, null=True)
    division = models.CharField('部門', max_length=10, blank=True, null=True)
    authority = models.CharField('権限', max_length=10, blank=True, null=True)
    confirm_username = models.CharField('確認者', max_length=150, blank=True, null=True)
    permit_username = models.CharField('承認者', max_length=150, blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)


# 年度マスタ
class BusinessYearMaster(models.Model):
    business_year = models.IntegerField('年度', primary_key=True)
    display_flag = models.IntegerField('表示FL', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.business_year)


# 部門マスタ
class DivisionMaster(models.Model):
    division_cd = models.CharField('部門CD', max_length=10, primary_key=True)
    division_name = models.CharField('部門名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.division_name)


# 部署マスタ
class DepartmentMaster(models.Model):
    department_cd = models.CharField('部署CD', max_length=10, primary_key=True)
    department_name = models.CharField('部署名', max_length=20, blank=True, null=True)
    division_cd = models.CharField('部門CD', max_length=10, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.department_name)


# 期マスタ
class PeriodClassMaster(models.Model):
    period_class_cd = models.IntegerField('期CD', primary_key=True)
    period_class_name = models.CharField('期区分名', max_length=20, blank=True, null=True)
    display_order = models.IntegerField('表示順', blank=True, null=True)
    lost_flag = models.IntegerField('無効FL', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.period_class_name)