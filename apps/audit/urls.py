from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_log_list, name='audit_log_list'),
    path('export/csv/', views.export_audit_logs_csv, name='export_audit_logs_csv'),
]