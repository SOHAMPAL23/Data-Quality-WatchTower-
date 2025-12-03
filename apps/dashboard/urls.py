from django.urls import path
from . import views
from . import api_views
from . import views_search
from .api import dashboard_api
from .api.views import DashboardStatsAPIView, DashboardFiltersAPIView

app_name = 'dashboard'

urlpatterns = [
    path('', views.public_home, name='public_home'),
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/enhanced/', views.enhanced_dashboard, name='enhanced_dashboard'),
    path('dashboard/search/', views_search.global_search, name='global_search'),
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
    # Enhanced dashboard API endpoints
    path('api/dashboard/stats/', DashboardStatsAPIView.as_view(), name='dashboard_stats_api'),
    path('api/dashboard/filters/', DashboardFiltersAPIView.as_view(), name='dashboard_filters_api'),
    path('api/dashboard/enhanced-stats/', dashboard_api.enhanced_dashboard_stats_api, name='enhanced_dashboard_stats_api'),
]