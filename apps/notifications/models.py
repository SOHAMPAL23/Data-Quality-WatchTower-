from django.db import models
from django.conf import settings
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
from apps.datasets.models import Dataset


class NotificationType(models.TextChoices):
    RULE_FAILED = 'RULE_FAILED', 'Rule Failed'
    INCIDENT_CREATED = 'INCIDENT_CREATED', 'Incident Created'
    INCIDENT_RESOLVED = 'INCIDENT_RESOLVED', 'Incident Resolved'
    DATASET_UPLOADED = 'DATASET_UPLOADED', 'Dataset Uploaded'
    RULE_COMPLETED = 'RULE_COMPLETED', 'Rule Completed'


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    
    # Related objects
    rule = models.ForeignKey(Rule, on_delete=models.SET_NULL, null=True, blank=True)
    rule_run = models.ForeignKey(RuleRun, on_delete=models.SET_NULL, null=True, blank=True)
    incident = models.ForeignKey(Incident, on_delete=models.SET_NULL, null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For email notifications
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.notification_type} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
        ]


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notification preferences
    email_rule_failed = models.BooleanField(default=True)
    email_incident_created = models.BooleanField(default=True)
    email_incident_resolved = models.BooleanField(default=True)
    email_dataset_uploaded = models.BooleanField(default=False)
    
    # In-app notification preferences
    in_app_rule_failed = models.BooleanField(default=True)
    in_app_incident_created = models.BooleanField(default=True)
    in_app_incident_resolved = models.BooleanField(default=True)
    in_app_dataset_uploaded = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"