from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    path('', views.incident_list, name='incident_list'),
    path('<int:pk>/', views.incident_detail, name='incident_detail'),
    path('<int:pk>/evidence/', views.incident_evidence, name='incident_evidence'),
    path('bulk-update/', views.incident_bulk_update, name='incident_bulk_update'),
]