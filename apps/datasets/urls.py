from django.urls import path
from . import views
from . import views_enhanced

app_name = 'datasets'

urlpatterns = [
    path('', views.dataset_list, name='dataset_list'),
    path('create/', views.dataset_create, name='dataset_create'),
    path('create-enhanced/', views_enhanced.enhanced_dataset_upload, name='enhanced_dataset_upload'),
    path('save-enhanced/', views_enhanced.save_enhanced_dataset, name='save_enhanced_dataset'),
    path('<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('<int:pk>/delete/', views.dataset_delete, name='dataset_delete'),
    path('<int:pk>/run-rules/', views.dataset_run_rules, name='dataset_run_rules'),
]