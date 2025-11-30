import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from apps.datasets.models import Dataset
from apps.rules.models import Rule

class Command(BaseCommand):
    help = 'Generate sample rules for testing all rule types'

    def handle(self, *args, **options):
        # Get the demo dataset
        demo_dataset = Dataset.objects.filter(name='Demo Employee Data').first()
        if not demo_dataset:
            self.stdout.write(self.style.ERROR('Demo dataset not found. Please run seed_demo_data first.'))
            return

        # Get demo user
        demo_user = User.objects.filter(username='demo').first()
        if not demo_user:
            self.stdout.write(self.style.ERROR('Demo user not found. Please run seed_demo_data first.'))
            return

        # Create sample rules for all types
        rules_data = [
            {
                'name': 'Email Not Null Check',
                'rule_type': 'NOT_NULL',
                'dsl_expression': 'NOT_NULL("email")',
                'description': 'Check that email addresses are not null'
            },
            {
                'name': 'Unique ID Check',
                'rule_type': 'UNIQUE',
                'dsl_expression': 'UNIQUE("id")',
                'description': 'Check that IDs are unique'
            },
            {
                'name': 'Valid Age Range',
                'rule_type': 'IN_RANGE',
                'dsl_expression': 'IN_RANGE("age", 18, 65)',
                'description': 'Check that ages are within valid range (18-65)'
            },
            {
                'name': 'Valid Email Format',
                'rule_type': 'REGEX',
                'dsl_expression': 'REGEX("email", "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")',
                'description': 'Check that email addresses match valid format'
            }
        ]
        
        created_count = 0
        for rule_data in rules_data:
            if not Rule.objects.filter(name=rule_data['name'], dataset=demo_dataset).exists():
                Rule.objects.create(
                    dataset=demo_dataset,
                    owner=demo_user,
                    **rule_data
                )
                self.stdout.write(self.style.SUCCESS(f"Created rule: {rule_data['name']}"))
                created_count += 1
            else:
                self.stdout.write(f"Rule already exists: {rule_data['name']}")

        self.stdout.write(self.style.SUCCESS(f'Generated {created_count} new sample rules successfully!'))