from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.models import NotificationPreference

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize notification preferences for all existing users'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            # Create notification preferences if they don't exist
            preference, created = NotificationPreference.objects.get_or_create(user=user)
            if created:
                created_count += 1
                
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized notification preferences for {created_count} users'
            )
        )