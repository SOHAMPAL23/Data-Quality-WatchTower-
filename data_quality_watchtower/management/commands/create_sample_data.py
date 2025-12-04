import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.datasets.models import Dataset
from apps.rules.models import Rule

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create test user if it doesn't exist
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Created test user (username: testuser, password: testpass123)'))
        else:
            self.stdout.write('Test user already exists')

        # Create sample dataset
        test_user = User.objects.get(username='testuser')
        
        # Sample sales data
        data = {
            'date': pd.date_range('2023-01-01', periods=50, freq='D'),
            'product': [f'Product {i%5+1}' for i in range(1, 51)],
            'quantity': [i for i in range(1, 51)],
            'price': [10.0 + (i * 2.5) for i in range(1, 51)],  # Prices from $10 to $135
        }
        
        df = pd.DataFrame(data)
        csv_path = os.path.join(settings.MEDIA_ROOT, 'sample_sales_data.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        # Create dataset record
        if not Dataset.objects.filter(name='Sample Sales Data').exists():
            dataset = Dataset.objects.create(
                name='Sample Sales Data',
                description='Sample sales data for testing',
                source_type='CSV',
                file=csv_path,
                owner=test_user,
                row_count=len(df),
                column_count=len(df.columns),
                schema={col: str(dtype) for col, dtype in df.dtypes.items()},
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created dataset: {dataset.name}'))
        else:
            self.stdout.write('Sample dataset already exists')

        # Create test rules if they don't exist
        test_dataset = Dataset.objects.filter(name='Sample Sales Data').first()
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
