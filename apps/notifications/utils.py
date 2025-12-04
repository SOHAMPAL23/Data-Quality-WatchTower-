from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference

User = get_user_model()

def create_notification(recipient, notification_type, title, message, actor=None, 
                       rule=None, rule_run=None, incident=None, dataset=None):
    """
    Create a notification for a user
    
    Args:
        recipient: User object to receive the notification
        notification_type: Type of notification
        title: Title of the notification
        message: Message body
        actor: User who triggered the notification (optional)
        rule: Rule object related to notification (optional)
        rule_run: RuleRun object related to notification (optional)
        incident: Incident object related to notification (optional)
        dataset: Dataset object related to notification (optional)
        
    Returns:
        Notification object
    """
    # Create in-app notification
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        rule=rule,
        rule_run=rule_run,
        incident=incident,
        dataset=dataset
    )
    
    # Send email notification if enabled
    send_email_notification(notification)
    
    return notification


def send_email_notification(notification):
    """
    Send email notification based on user preferences
    """
    try:
        # Get user notification preferences
        prefs, created = NotificationPreference.objects.get_or_create(user=notification.recipient)
        
        # Check if email notification is enabled for this type
        should_send_email = False
        if notification.notification_type == 'RULE_FAILED':
            should_send_email = prefs.email_rule_failed
        elif notification.notification_type == 'INCIDENT_CREATED':
            should_send_email = prefs.email_incident_created
        elif notification.notification_type == 'INCIDENT_RESOLVED':
            should_send_email = prefs.email_incident_resolved
        elif notification.notification_type == 'DATASET_UPLOADED':
            should_send_email = prefs.email_dataset_uploaded
            
        # Send email if enabled
        if should_send_email and hasattr(notification.recipient, 'email') and notification.recipient.email:
            subject = f"[Data Quality Watchtower] {notification.title}"
            message = f"{notification.message}\n\nView all notifications: {settings.SITE_URL}/notifications/"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=True
            )
            
            # Mark email as sent
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
            
    except Exception as e:
        # Log error but don't fail the notification creation
        print(f"Failed to send email notification: {e}")


def get_unread_notifications_count(user):
    """
    Get count of unread notifications for a user
    """
    return Notification.objects.filter(recipient=user, is_read=False).count()


def get_recent_notifications(user, limit=5):
    """
    Get recent notifications for a user
    """
    return Notification.objects.filter(recipient=user).order_by('-created_at')[:limit]