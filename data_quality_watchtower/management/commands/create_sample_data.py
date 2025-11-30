import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from apps.datasets.models import Dataset
from apps.rules.models import Rule

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create test user if it doesn't exist
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            self.stdout.write(self.style.SUCCESS('Created test user (username: testuser, password: testpass123)'))
        else:
            self.stdout.write('Test user already exists')

        # Create test CSV file if it doesn't exist
        test_csv_path = os.path.join(settings.MEDIA_ROOT, 'datasets', 'test_data.csv')
        os.makedirs(os.path.dirname(test_csv_path), exist_ok=True)
        
        if not os.path.exists(test_csv_path):
            # Create sample data
            data = {
                'id': range(1, 51),
                'product_name': [f'Product {i}' for i in range(1, 51)],
                'price': [10.0 + (i * 2.5) for i in range(1, 51)],  # Prices from $10 to $135
                'category': ['Electronics', 'Clothing', 'Books', 'Home'] * 12 + ['Electronics', 'Clothing', 'Books']
            }
            
            df = pd.DataFrame(data)
            df.to_csv(test_csv_path, index=False)
            self.stdout.write(self.style.SUCCESS(f'Created test CSV file at {test_csv_path}'))
        else:
            self.stdout.write('Test CSV file already exists')

        # Create test dataset if it doesn't exist
        if not Dataset.objects.filter(name='Test Product Data').exists():
            test_user = User.objects.get(username='testuser')
            dataset = Dataset.objects.create(
                name='Test Product Data',
                source_type='CSV',
                owner=test_user,
                is_active=True
            )
            # Attach the file to the dataset
            dataset.file.name = 'datasets/test_data.csv'
            dataset.row_count = 50
            dataset.column_count = 4
            dataset.save()
            self.stdout.write(self.style.SUCCESS('Created test dataset'))
        else:
            self.stdout.write('Test dataset already exists')

        # Create test rules if they don't exist
        test_dataset = Dataset.objects.filter(name='Test Product Data').first()
        if test_dataset:
            rules_data = [
                {
                    'name': 'Price Not Null Check',
                    'rule_type': 'NOT_NULL',
                    'dsl_expression': 'NOT_NULL("price")',
                    'description': 'Check that prices are not null'
                },
                {
                    'name': 'Unique ID Check',
                    'rule_type': 'UNIQUE',
                    'dsl_expression': 'UNIQUE("id")',
                    'description': 'Check that IDs are unique'
                },
                {
                    'name': 'Valid Price Range',
                    'rule_type': 'IN_RANGE',
                    'dsl_expression': 'IN_RANGE("price", 5.0, 200.0)',
                    'description': 'Check that prices are within valid range'
                }
            ]
            
            for rule_data in rules_data:
                if not Rule.objects.filter(name=rule_data['name'], dataset=test_dataset).exists():
                    Rule.objects.create(
                        dataset=test_dataset,
                        owner=test_user,
                        **rule_data
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created rule: {rule_data['name']}"))
                else:
                    self.stdout.write(f"Rule already exists: {rule_data['name']}")

        self.stdout.write(self.style.SUCCESS('Sample data creation completed successfully!'))
