from django.urls import path
from . import views
from . import views_enhanced
from . import views_profiling

app_name = 'datasets'

urlpatterns = [
    path('', views.dataset_list, name='dataset_list'),
    path('create/', views.dataset_create, name='dataset_create'),
    path('create-enhanced/', views_enhanced.enhanced_dataset_upload, name='enhanced_dataset_upload'),
    path('save-enhanced/', views_enhanced.save_enhanced_dataset, name='save_enhanced_dataset'),
    path('<int:pk>/', views.dataset_detail, name='dataset_detail'),
    # Removed the non-existent dataset_edit path
    path('<int:pk>/delete/', views.dataset_delete, name='dataset_delete'),
    path('<int:pk>/run-rules/', views.dataset_run_rules, name='dataset_run_rules'),
    path('<int:pk>/recommendations/', views.get_rule_recommendations, name='get_rule_recommendations'),
    # Profiling URLs
    path('<int:dataset_id>/profile/', views_profiling.dataset_profile, name='dataset_profile'),
    path('<int:dataset_id>/profile/api/', views_profiling.dataset_profile_api, name='dataset_profile_api'),
    path('<int:dataset_id>/profile/refresh/', views_profiling.refresh_dataset_profile, name='refresh_dataset_profile'),
    path('<int:dataset_id>/quality-report/', views_profiling.dataset_quality_report, name='dataset_quality_report'),
]