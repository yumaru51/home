from django.contrib import admin
from .models import User, DepartmentMaster, DivisionMaster, UserAttribute


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'display_order', 'lost_flag')
    list_filter = ['lost_flag']
    search_fields = ['username', 'first_name', 'last_name', 'display_order', 'lost_flag']


admin.site.register(User, UserAdmin)


class DepartmentMasterAdmin(admin.ModelAdmin):
    list_display = ('department_cd', 'department_name', 'division_cd', 'area_manager', 'jurisdiction_area',
                    'display_order', 'lost_flag')
    list_filter = ['department_cd', 'department_name', 'division_cd', 'area_manager', 'jurisdiction_area',
                   'display_order', 'lost_flag']
    search_fields = ['department_cd', 'department_name', 'division_cd', 'area_manager', 'jurisdiction_area',
                     'display_order', 'lost_flag']


admin.site.register(DepartmentMaster, DepartmentMasterAdmin)


class DivisionMasterAdmin(admin.ModelAdmin):
    list_display = ('division_cd', 'division_name', 'display_order', 'lost_flag')
    list_filter = ['division_cd', 'division_name', 'display_order', 'lost_flag']
    search_fields = ['division_cd', 'division_name', 'display_order', 'lost_flag']


admin.site.register(DivisionMaster, DivisionMasterAdmin)


class UserAttributeAdmin(admin.ModelAdmin):
    list_display = ('username', 'department', 'division', 'authority', 'confirm_username', 'permit_username',
                    'department_charge_flag', 'display_order', 'user_order', 'lost_flag')
    list_filter = ['username', 'department', 'division', 'authority', 'confirm_username', 'permit_username',
                   'department_charge_flag', 'display_order', 'user_order', 'lost_flag']
    search_fields = ['username', 'department', 'division', 'authority', 'confirm_username', 'permit_username',
                     'department_charge_flag', 'display_order', 'user_order', 'lost_flag']


admin.site.register(UserAttribute, UserAttributeAdmin)
