from django.contrib import admin
from .models import Rule, RuleRun

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'dataset', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active', 'created_at']
    search_fields = ['name', 'dataset__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RuleRun)
class RuleRunAdmin(admin.ModelAdmin):
    list_display = ['rule', 'run_id', 'started_at', 'finished_at', 'passed_count', 'failed_count']
    list_filter = ['started_at', 'finished_at']
    search_fields = ['rule__name', 'run_id']