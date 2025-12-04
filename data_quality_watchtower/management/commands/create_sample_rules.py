from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
from apps.rules.models import Rule
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample rules for testing'

    def handle(self, *args, **options):
        # Get the first user as owner
        try:
            owner = User.objects.first()
            if not owner:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        # Get test dataset
        dataset = Dataset.objects.filter(name='Sample Sales Data').first()
        if not dataset:
            self.stdout.write(self.style.ERROR('Sample dataset not found. Please run create_sample_data first.'))
            return

        # Create sample rules
        rules_data = [
            {
                'name': 'Price Validation Rule',
                'description': 'Ensure all prices are positive',
                'rule_type': 'CUSTOM',
                'dsl_expression': 'COLUMN_GREATER_THAN("price", 0)',
                'is_active': True
            },
            {
                'name': 'Quantity Validation Rule',
                'description': 'Ensure all quantities are positive integers',
                'rule_type': 'CUSTOM',
                'dsl_expression': 'COLUMN_GREATER_THAN("quantity", 0)',
                'is_active': True
            },
            {
                'name': 'Product Name Completeness Rule',
                'description': 'Ensure product names are not null',
                'rule_type': 'CUSTOM',
                'dsl_expression': 'NOT_NULL("product")',
                'is_active': True
            }
        ]

        created_count = 0
        for rule_data in rules_data:
            if not Rule.objects.filter(name=rule_data['name'], dataset=dataset).exists():
                rule_data['dataset'] = dataset
                rule_data['owner'] = owner
                Rule.objects.create(**rule_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created rule: {rule_data["name"]}'))

        if created_count == 0:
            self.stdout.write('All sample rules already exist')
        else:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} sample rules'))