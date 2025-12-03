from django import forms
from .models import NotificationPreference


class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_rule_failed',
            'email_incident_created',
            'email_incident_resolved',
            'email_dataset_uploaded',
            'in_app_rule_failed',
            'in_app_incident_created',
            'in_app_incident_resolved',
            'in_app_dataset_uploaded',
        ]
        widgets = {
            'email_rule_failed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_incident_created': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_incident_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_dataset_uploaded': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_rule_failed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_incident_created': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_incident_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_dataset_uploaded': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }