from django.db import models
from django.conf import settings
from apps.datasets.models import Dataset


class Rule(models.Model):
    RULE_TYPES = [
        ('NOT_NULL', 'NOT_NULL'),
        ('UNIQUE', 'UNIQUE'),
        ('IN_RANGE', 'IN_RANGE'),
        ('FOREIGN_KEY', 'FOREIGN_KEY'),
        ('REGEX', 'REGEX'),
        ('LENGTH_RANGE', 'LENGTH_RANGE'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='rules')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    dsl_expression = models.TextField(help_text="DSL expression like NOT_NULL('column_name')")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"
        
    def save(self, *args, **kwargs):
        # Ensure dataset is set
        if not self.dataset:
            raise ValueError("Rule must have a dataset")
        super().save(*args, **kwargs)


class RuleRun(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='runs')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='rule_runs', null=True, blank=True)
    run_id = models.CharField(max_length=100, unique=True, help_text="Unique identifier for this rule execution")
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    total_rows = models.IntegerField(default=0)
    passed_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    sample_evidence = models.JSONField(blank=True, null=True, help_text="Sample evidence rows that failed")
    
    def __str__(self):
        return f"{self.rule.name} run {self.run_id}"
    
    class Meta:
        ordering = ['-started_at']
        
    def save(self, *args, **kwargs):
        # Ensure dataset is set if not already
        if not self.dataset and self.rule:
            self.dataset = self.rule.dataset
        super().save(*args, **kwargs)
