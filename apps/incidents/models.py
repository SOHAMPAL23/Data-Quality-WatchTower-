from django.db import models
from django.conf import settings
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun


class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('MUTED', 'Muted'),
    ]
    
    SLA_STATUS_CHOICES = [
        ('OK', 'OK'),
        ('WARNING', 'Warning'),
        ('BREACHED', 'Breached'),
    ]
    
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    rule_run = models.ForeignKey(RuleRun, on_delete=models.CASCADE, null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    sla_status = models.CharField(max_length=10, choices=SLA_STATUS_CHOICES, default='OK')
    
    evidence = models.TextField(blank=True, help_text="JSON formatted evidence data")
    evidence_file = models.FileField(upload_to='incident_evidence/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['assigned_to']),
        ]


class IncidentComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.incident.title}"
    
    class Meta:
        ordering = ['created_at']