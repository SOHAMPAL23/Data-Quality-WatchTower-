from django.contrib import admin
from .models import APIKey, APILog

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'method', 'response_status', 'response_time', 'created_at']
    list_filter = ['method', 'response_status', 'created_at']
    search_fields = ['endpoint', 'ip_address']
    readonly_fields = ['created_at']