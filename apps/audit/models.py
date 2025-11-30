from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('READ', 'Read'),  # Add READ action type
        ('RUN', 'Run'),
        ('TRIAGE', 'Triage'),
        ('EXPORT', 'Export'),
    ]
    
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_type = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField()
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.actor.username} {self.action_type} {self.target_type} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['action_type', 'timestamp']),
        ]