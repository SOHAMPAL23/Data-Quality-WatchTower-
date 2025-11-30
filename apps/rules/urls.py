from django.urls import path
from . import views

app_name = 'rules'

urlpatterns = [
    path('', views.rule_list, name='rule_list'),
    path('create/', views.rule_create, name='rule_create'),
    path('<int:pk>/', views.rule_detail, name='rule_detail'),
    path('<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('<int:pk>/delete/', views.rule_delete, name='rule_delete'),
    path('<int:pk>/toggle-active/', views.rule_toggle_active, name='rule_toggle_active'),
    path('<int:pk>/run/', views.rule_run, name='rule_run'),
    path('runs/', views.rule_run_list, name='rule_run_list'),
    path('create-from-recommendation/', views.create_rule_from_recommendation, name='create_rule_from_recommendation'),
]