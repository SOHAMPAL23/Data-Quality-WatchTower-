import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from apps.datasets.models import Dataset
from apps.rules.models import Rule

class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def handle(self, *args, **options):
        # Create demo user if it doesn't exist
        if not User.objects.filter(username='demo').exists():
            User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo12345'
            )
            self.stdout.write(self.style.SUCCESS('Created demo user (username: demo, password: demo12345)'))
        else:
            self.stdout.write('Demo user already exists')

        # Create demo CSV file if it doesn't exist
        demo_csv_path = os.path.join(settings.MEDIA_ROOT, 'datasets', 'demo_data.csv')
        os.makedirs(os.path.dirname(demo_csv_path), exist_ok=True)
        
        if not os.path.exists(demo_csv_path):
            # Create sample data
            data = {
                'id': range(1, 101),
                'name': [f'User {i}' for i in range(1, 101)],
                'email': [f'user{i}@example.com' for i in range(1, 101)],
                'age': [20 + (i % 50) for i in range(1, 101)],  # Ages between 20-69
                'salary': [30000 + (i * 1000) for i in range(1, 101)],  # Salaries from 30k to 130k
                'department': ['IT', 'HR', 'Finance', 'Marketing', 'Operations'] * 20
            }
            
            df = pd.DataFrame(data)
            df.to_csv(demo_csv_path, index=False)
            self.stdout.write(self.style.SUCCESS(f'Created demo CSV file at {demo_csv_path}'))
        else:
            self.stdout.write('Demo CSV file already exists')

        # Create demo dataset if it doesn't exist
        if not Dataset.objects.filter(name='Demo Employee Data').exists():
            demo_user = User.objects.get(username='demo')
            dataset = Dataset.objects.create(
                name='Demo Employee Data',
                source_type='CSV',
                owner=demo_user,
                is_active=True
            )
            # Attach the file to the dataset
            dataset.file.name = 'datasets/demo_data.csv'
            dataset.row_count = 100
            dataset.column_count = 6
            dataset.save()
            self.stdout.write(self.style.SUCCESS('Created demo dataset'))
        else:
            self.stdout.write('Demo dataset already exists')

        # Create demo rules if they don't exist
        demo_dataset = Dataset.objects.filter(name='Demo Employee Data').first()
        if demo_dataset:
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
                    'description': 'Check that ages are within valid range'
                }
            ]
            
            for rule_data in rules_data:
                if not Rule.objects.filter(name=rule_data['name'], dataset=demo_dataset).exists():
                    Rule.objects.create(
                        dataset=demo_dataset,
                        owner=demo_user,
                        **rule_data
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created rule: {rule_data['name']}"))
                else:
                    self.stdout.write(f"Rule already exists: {rule_data['name']}")

        self.stdout.write(self.style.SUCCESS('Demo data seeding completed successfully!'))