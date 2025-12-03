from django.urls import path
from . import views
from . import views_enhanced

app_name = 'incidents'

urlpatterns = [
    path('', views.incident_list, name='incident_list'),
    path('dashboard/', views_enhanced.incident_dashboard, name='incident_dashboard'),
    path('create/', views_enhanced.create_incident, name='incident_create'),
    path('<int:pk>/', views.incident_detail, name='incident_detail'),
    path('<int:pk>/evidence/', views.incident_evidence, name='incident_evidence'),
    path('bulk-update/', views.incident_bulk_update, name='incident_bulk_update'),
    path('bulk-assign/', views_enhanced.incident_bulk_assign, name='incident_bulk_assign'),
    path('bulk-resolve/', views_enhanced.incident_bulk_resolve, name='incident_bulk_resolve'),
    path('api/stats/', views_enhanced.incident_api_stats, name='incident_api_stats'),
]