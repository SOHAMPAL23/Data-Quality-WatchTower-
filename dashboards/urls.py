from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('api/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('dataset/<int:dataset_id>/api/stats/', views.dataset_stats, name='dataset_stats'),
    path('dataset/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
]