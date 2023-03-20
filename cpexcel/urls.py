from django.conf.urls import url
from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'cpexcel'

urlpatterns = [
    url(r'^$', views.index, name='cpexcel_top_page'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('entry/', views.entry, name='entry'),
    path('execute/', views.execute, name='execute'),
    path('parts/program_lists/', views.program_list, name='program_list'),
    path('parts/program_filter/', views.program_filter, name='program_filter'),
    path('parts/program_entry_page/', views.program_entry_page, name='program_entry_page'),
    path('action/program_entry/', views.program_entry, name='program_entry'),
    path('action/program_delete/', views.program_delete, name='program_delete'),
    path('parts/task_entry_page/', views.task_entry_page, name='task_entry_page'),
    path('parts/task_list/', views.task_list, name='task_list'),
    path('action/task_entry/', views.task_entry, name='task_entry'),
    path('action/task_delete/', views.task_delete, name='task_delete'),
    path('parts/program_detail/', views.program_detail, name='program_detail'),
    path('action/program_execute/', views.program_execute, name='program_execute'),
    path('file_change_check/', views.file_change_check_page, name='file_change_check_page'),
    path('action/file_check/', views.file_change_check, name='file_change_check'),
    path('action/file_download/', views.file_download, name='file_download'),
    path('action/file_upload/', views.file_upload, name='file_upload'),
    path('action/task_import_file_upload/', views.file_import, name='file_import'),
    path('action/task_import_file_download/', views.task_import_file_download, name='task_import_file_download'),
    path('demo_files/', views.demo_file_download_page, name='demo_file_download_page'),
    path('action/demo_file_download/', views.demo_file_download, name='demo_file_download'),
]