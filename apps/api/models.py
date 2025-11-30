from django.db import models

# The API app might not need models as it's primarily for exposing data
# But we can create some models for API keys or access logs if needed

class APIKey(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class APILog(models.Model):
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, blank=True, null=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    response_status = models.IntegerField()
    response_time = models.FloatField()  # in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_status}"

    class Meta:
        ordering = ['-created_at']