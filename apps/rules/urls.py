from django.urls import path
from . import views
from . import views_templates
from . import views_timeline

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
    path('timeline/', views_timeline.rule_run_timeline, name='rule_run_timeline'),
    path('timeline/api/', views_timeline.rule_run_timeline_api, name='rule_run_timeline_api'),
    path('create-from-recommendation/', views.create_rule_from_recommendation, name='create_rule_from_recommendation'),
    # Rule templates URLs
    path('templates/', views_templates.template_list, name='template_list'),
    path('templates/<int:template_id>/', views_templates.template_detail, name='template_detail'),
    path('templates/<int:template_id>/dsl/', views_templates.get_template_dsl, name='get_template_dsl'),
]