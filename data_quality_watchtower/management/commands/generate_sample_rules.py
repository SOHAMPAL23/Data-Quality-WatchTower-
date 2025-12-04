import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.datasets.models import Dataset
from apps.rules.models import Rule

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample rules based on dataset schema'

    def handle(self, *args, **options):
        # Get demo user
        demo_user = User.objects.filter(username='demo').first()
        if not demo_user:
            self.stdout.write(self.style.ERROR('Demo user not found. Please run seed_demo_data first.'))
            return

        # Get sample dataset
        dataset = Dataset.objects.filter(name='Sample Customer Data').first()
        if not dataset:
            self.stdout.write(self.style.ERROR('Sample dataset not found. Please run seed_demo_data first.'))
            return

        # Generate rules based on schema
        rules_created = 0
        
        # Create rules for each column
        for column, dtype in dataset.schema.items():
            rule_name = f'{column.title()} Validation'
            
            # Skip if rule already exists
            if Rule.objects.filter(name=rule_name, dataset=dataset).exists():
                continue
                
            # Generate appropriate DSL expression based on data type
            if 'int' in dtype.lower() or 'float' in dtype.lower():
                dsl_expression = f'COLUMN_GREATER_THAN("{column}", 0)'
                description = f'Ensure {column} values are positive'
            elif 'object' in dtype.lower() or 'str' in dtype.lower():
                dsl_expression = f'NOT_NULL("{column}")'
                description = f'Ensure {column} values are not null'
            else:
                # Default rule for other types
                dsl_expression = f'NOT_NULL("{column}")'
                description = f'Basic validation for {column}'
            
            # Create the rule
            Rule.objects.create(
                name=rule_name,
                description=description,
                dataset=dataset,
                rule_type='CUSTOM',
                dsl_expression=dsl_expression,
                owner=demo_user,
                is_active=True
            )
            
            rules_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule_name}'))
        
        if rules_created == 0:
            self.stdout.write('No new rules created - all sample rules already exist')
        else:
            self.stdout.write(self.style.SUCCESS(f'Created {rules_created} sample rules'))