from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
from apps.rules.models import Rule
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create sample rules for testing'

    def handle(self, *args, **options):
        # Get the first user as owner
        try:
            owner = User.objects.first()
            if not owner:
                self.stdout.write(
                    self.style.ERROR('No users found. Please create a user first.')
                )
                return
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No users found. Please create a user first.')
            )
            return

        # Get the test dataset
        try:
            dataset = Dataset.objects.get(name='Test Dataset')
        except Dataset.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Test Dataset not found. Please create a dataset first.')
            )
            return

        # Create sample rules
        rules_data = [
            {
                'name': 'Email Validation',
                'description': 'Ensure all emails are valid',
                'dsl_expression': 'REGEX(email, "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")'
            },
            {
                'name': 'Age Range Check',
                'description': 'Ensure age is between 18 and 65',
                'dsl_expression': 'IN_RANGE(age, 18, 65)'
            },
            {
                'name': 'Name Not Null',
                'description': 'Ensure name field is not null',
                'dsl_expression': 'NOT_NULL(name)'
            },
            {
                'name': 'Unique Email',
                'description': 'Ensure email addresses are unique',
                'dsl_expression': 'UNIQUE(email)'
            },
            {
                'name': 'Salary Positive',
                'description': 'Ensure salary is positive',
                'dsl_expression': 'IN_RANGE(salary, 1, 1000000)'
            }
        ]

        created_count = 0
        for rule_data in rules_data:
            # Check if rule already exists
            if not Rule.objects.filter(name=rule_data['name'], dataset=dataset).exists():
                rule = Rule.objects.create(
                    name=rule_data['name'],
                    description=rule_data['description'],
                    dataset=dataset,
                    dsl_expression=rule_data['dsl_expression'],
                    owner=owner,
                    is_active=True
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created rule: {rule.name}')
                )

        if created_count == 0:
            self.stdout.write(
                self.style.WARNING('All sample rules already exist.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created {created_count} sample rules.')
            )