from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from .views import main, info, action, ajax

app_name = 'quality_change_management'
# todo urlパラメーターで「admin」「accounts」に送れない。。。
urlpatterns = [
    path('', main.top_page, name='top_page'),
    # path('accounts/', include('django.contrib.auth.urls'), name='accounts'),
    # path('admin/', admin.site.urls, name='admin'),
    path('detail/<int:present_step>/<str:target>/<int:request_id>/', main.detail, name='detail'),
    path('report/<int:export>', main.report, name='report'),
    # entry処理
    path('action/<function_name>/', action.action, name='action'),
    # ajax処理
    path('ajax_next_step/', ajax.ajax_next_step, name='ajax_next_step'),
    path('ajax_department/', ajax.ajax_department, name='ajax_department'),
    path('ajax_user/', ajax.ajax_user, name='ajax_user'),
    path('ajax_file_upload/', ajax.ajax_file_upload, name='ajax_file_upload'),
    path('ajax_file_list/', ajax.ajax_file_list, name='ajax_file_list'),
    path('ajax_file_list/<data_id>/<file_name>/', ajax.ajax_file_download, name='ajax_file_download'),
    # path('ajax_file_delete/', ajax.ajax_file_delete, name='ajax_file_delete'),
    path('ajax_file_delete/<file_name>/', ajax.ajax_file_delete, name='ajax_file_delete'),
]
