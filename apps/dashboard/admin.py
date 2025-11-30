from django.contrib import admin
from .models import DashboardGraph

@admin.register(DashboardGraph)
class DashboardGraphAdmin(admin.ModelAdmin):
    list_display = ['graph_type', 'created_at']
    list_filter = ['graph_type', 'created_at']
    readonly_fields = ['created_at', 'updated_at']