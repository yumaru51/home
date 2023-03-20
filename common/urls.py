from django.conf.urls import url
from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'common'

urlpatterns = [
    path('', views.index, name='top_page'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cpexcel/', include('cpexcel.urls')),
    path('fms/', include('fms.urls')),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
