from django.urls import path
from django.conf.urls import url
# 品質検討会資料
from .views import quality_study_meeting_materials
# 品質日報
from .views import quality_daily_report
# TEST
# from .views import kawauchi


app_name = 'reportoutput'
urlpatterns = [
    # 【チタン】品質検討会資料
    path('CL法/品質検討会資料/', quality_study_meeting_materials.quality_study_meeting_materials, name='quality_study_meeting_materials'),
    path('CL法/品質検討会資料/__select__brand/', quality_study_meeting_materials.__select__brand, name='__select__brand'),
    path('CL法/品質検討会資料/download/<brand>/<int:run_no1>/<int:run_no2>/<int:run_no3>/', quality_study_meeting_materials.trace_report, name='trace_report'),
    path('S法/品質検討会資料/', quality_study_meeting_materials.s_quality_study_meeting_materials, name='s_quality_study_meeting_materials'),
    path('S法/品質検討会資料/__select__brand/', quality_study_meeting_materials.s___select__brand, name='s___select__brand'),
    path('S法/品質検討会資料/download/<brand>/<int:run_no1>/<int:run_no2>/<int:run_no3>/', quality_study_meeting_materials.s_trace_report, name='s_trace_report'),
    # 【チタン】トレースNO採番
    path('品質検討会資料/トレースNO採番/', quality_study_meeting_materials.trace_no_numbering, name='trace_no_numbering'),

    # 【機能材】品質日報
    path('機能材/品質日報/', quality_daily_report.quality_daily_report1, name='quality_daily_report1'),
    path('機能材/品質日報/report/download/<startTime>/<endTime>/', quality_daily_report.quality_daily_report2, name='quality_daily_report2'),

    # TEST
    # path('川内/report/', kawauchi.report, name='report'),
    # path('川内/chatwindow/', kawauchi.chatwindow, name='chatwindow'),

]
