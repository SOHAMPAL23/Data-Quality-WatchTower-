from django.db import models
from django.conf import settings
from django.utils import timezone


class Dataset(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('CSV', 'CSV File'),
        ('DB', 'Database Table'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPE_CHOICES)
    file = models.FileField(upload_to='datasets/', blank=True, null=True)
    db_connection = models.JSONField(blank=True, null=True, help_text="Database connection details")
    table_name = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Overall quality score (0-100)")
    sample_stats = models.JSONField(blank=True, null=True, help_text="Sample statistics for the dataset")
    schema = models.JSONField(blank=True, null=True, help_text="Dataset schema information")
    # Graph data
    quality_trend_data = models.JSONField(blank=True, null=True, help_text="Quality trend data for charts")
    rule_pass_rates = models.JSONField(blank=True, null=True, help_text="Rule-level pass rates for charts")
    # Heatmap data
    heatmap_data = models.JSONField(blank=True, null=True, help_text="Per-dataset heatmap data for visualization")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['source_type']),
        ]
        
    def save(self, *args, **kwargs):
        # Ensure row_count and column_count are set if not already
        if self.row_count is None:
            self.row_count = 0
        if self.column_count is None:
            self.column_count = 0
        super().save(*args, **kwargs)