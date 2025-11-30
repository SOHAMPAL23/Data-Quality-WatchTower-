from django.contrib import admin
from .models import Incident, IncidentComment

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'rule', 'dataset', 'status', 'severity', 'sla_status', 'created_at']
    list_filter = ['status', 'severity', 'sla_status', 'created_at']
    search_fields = ['title', 'description', 'rule__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(IncidentComment)
class IncidentCommentAdmin(admin.ModelAdmin):
    list_display = ['incident', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['incident__title', 'author__username', 'content']