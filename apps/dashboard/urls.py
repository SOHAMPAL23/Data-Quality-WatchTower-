from django.urls import path
from . import views
from . import api_views
from .api import dashboard_api

app_name = 'dashboard'

urlpatterns = [
    path('', views.public_home, name='public_home'),
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/api/dataset-quality/', api_views.dataset_quality_api, name='dataset_quality_api'),
    path('dashboard/api/rule-frequency/', api_views.rule_frequency_api, name='rule_frequency_api'),
    path('dashboard/api/rules-per-dataset/', api_views.rules_per_dataset_api, name='rules_per_dataset_api'),
    path('dashboard/api/recent-rule-executions/', api_views.recent_rule_executions_api, name='recent_rule_executions_api'),
    # New dashboard API endpoints
    path('api/dashboard/active-datasets/', dashboard_api.active_datasets_api, name='active_datasets_api'),
    path('api/dashboard/active-rules/', dashboard_api.active_rules_api, name='active_rules_api'),
    path('api/dashboard/open-incidents/', dashboard_api.open_incidents_api, name='open_incidents_api'),
    path('api/dashboard/pass-rate/', dashboard_api.pass_rate_api, name='pass_rate_api'),
    path('api/dashboard/rule-execution-trend/', dashboard_api.rule_execution_trend_api, name='rule_execution_trend_api'),
    path('api/dashboard/incidents-severity/', dashboard_api.incidents_severity_api, name='incidents_severity_api'),
]