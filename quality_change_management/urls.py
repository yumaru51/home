from django.contrib import admin
from django.urls import include, path
from .views import main, info, entry, ajax

# todo urlパラメーターで「admin」「accounts」に送れない。。。
urlpatterns = [
    path('', main.top_page, name='top_page'),
    # path('accounts/', include('django.contrib.auth.urls'), name='accounts'),
    # path('admin/', admin.site.urls, name='admin'),
    path('detail/<int:request_id>/', main.detail, name='detail'),
    # entry処理
    path('action/<function_name>/', entry.entry, name='entry'),
    # ajax処理
    path('ajax_next_step/', ajax.ajax_next_step, name='ajax_next_step'),
    path('ajax_department/', ajax.ajax_department, name='ajax_department'),
    path('ajax_user/', ajax.ajax_user, name='ajax_user'),
]
