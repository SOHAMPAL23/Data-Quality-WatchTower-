from django.db import models
from django.utils import timezone

class DashboardGraph(models.Model):
    GRAPH_TYPES = [
        ('DATASET_QUALITY', 'Dataset Quality Scores'),
        ('RULE_FREQUENCY', 'Rule Run Frequency'),
        ('RULES_PER_DATASET', 'Rules per Dataset'),
        ('RECENT_EXECUTIONS', 'Recent Rule Executions'),
    ]
    
    graph_type = models.CharField(max_length=20, choices=GRAPH_TYPES)
    data = models.JSONField(help_text="Graph data in JSON format")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['graph_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_graph_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"