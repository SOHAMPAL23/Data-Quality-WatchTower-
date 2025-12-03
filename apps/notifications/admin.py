from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at', 'email_sent_at']
    list_per_page = 20


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_rule_failed', 'email_incident_created', 'email_incident_resolved', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']