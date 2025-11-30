from django.urls import path
from .views import DashboardStatsView, RunRulesView, IncidentListView, RuleRunStatsView, DatasetRuleRecommendationsView, DatasetQualityMetricsView

app_name = 'api'

urlpatterns = [
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('rules/run/', RunRulesView.as_view(), name='run_rules'),
    path('incidents/', IncidentListView.as_view(), name='incident_list'),
    path('rule-runs/stats/', RuleRunStatsView.as_view(), name='rule_run_stats'),
    path('datasets/<int:dataset_id>/recommendations/', DatasetRuleRecommendationsView.as_view(), name='dataset_rule_recommendations'),
    path('datasets/<int:dataset_id>/quality-metrics/', DatasetQualityMetricsView.as_view(), name='dataset_quality_metrics'),
]