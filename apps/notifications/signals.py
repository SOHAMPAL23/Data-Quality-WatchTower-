from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.incidents.models import Incident
from apps.rules.models import RuleRun
from apps.datasets.models import Dataset
from .models import Notification, NotificationPreference
from .utils import create_notification

User = get_user_model()


@receiver(post_save, sender=Incident)
def create_incident_notification(sender, instance, created, **kwargs):
    """
    Create notifications when incidents are created or resolved
    """
    if created:
        # Notify assigned user if exists, otherwise notify all admins
        recipients = []
        if instance.assigned_to:
            recipients.append(instance.assigned_to)
        else:
            # Notify all admins
            admins = User.objects.filter(role='admin')
            recipients.extend(admins)
        
        # Create notification for each recipient
        for recipient in recipients:
            create_notification(
                recipient=recipient,
                notification_type='INCIDENT_CREATED',
                title=f"New Incident: {instance.title}",
                message=f"A new incident '{instance.title}' has been created with {instance.severity} severity.",
                incident=instance,
                actor=None  # System-generated
            )
    else:
        # Check if incident was resolved
        if instance.status == 'RESOLVED' and instance.resolved_at:
            # Notify assigned user if exists
            if instance.assigned_to:
                create_notification(
                    recipient=instance.assigned_to,
                    notification_type='INCIDENT_RESOLVED',
                    title=f"Incident Resolved: {instance.title}",
                    message=f"The incident '{instance.title}' has been resolved.",
                    incident=instance,
                    actor=None  # System-generated
                )


@receiver(post_save, sender=RuleRun)
def create_rule_run_notification(sender, instance, created, **kwargs):
    """
    Create notifications when rule runs fail or complete
    """
    if not created and instance.status in ['FAILED', 'SUCCESS']:
        # Get the rule owner
        rule_owner = instance.rule.owner
        
        if instance.status == 'FAILED':
            create_notification(
                recipient=rule_owner,
                notification_type='RULE_FAILED',
                title=f"Rule Failed: {instance.rule.name}",
                message=f"The rule '{instance.rule.name}' failed to execute on dataset '{instance.dataset.name}'.",
                rule=instance.rule,
                rule_run=instance,
                actor=None  # System-generated
            )
        elif instance.status == 'SUCCESS':
            create_notification(
                recipient=rule_owner,
                notification_type='RULE_COMPLETED',
                title=f"Rule Completed: {instance.rule.name}",
                message=f"The rule '{instance.rule.name}' completed successfully on dataset '{instance.dataset.name}'.",
                rule=instance.rule,
                rule_run=instance,
                actor=None  # System-generated
            )


@receiver(post_save, sender=Dataset)
def create_dataset_notification(sender, instance, created, **kwargs):
    """
    Create notifications when datasets are uploaded
    """
    if created:
        # Notify all admins about new dataset upload
        admins = User.objects.filter(role='admin')
        for admin in admins:
            create_notification(
                recipient=admin,
                notification_type='DATASET_UPLOADED',
                title=f"New Dataset Uploaded: {instance.name}",
                message=f"A new dataset '{instance.name}' has been uploaded by {instance.owner.username}.",
                dataset=instance,
                actor=instance.owner
            )