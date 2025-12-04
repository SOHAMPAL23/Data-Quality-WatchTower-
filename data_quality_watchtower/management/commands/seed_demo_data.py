import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.datasets.models import Dataset
from apps.rules.models import Rule

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def handle(self, *args, **options):
        # Create demo user if it doesn't exist
        if not User.objects.filter(username='demo').exists():
            User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo12345',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Created demo user (username: demo, password: demo12345)'))
        else:
            self.stdout.write('Demo user already exists')

        # Create sample customer dataset
        demo_user = User.objects.get(username='demo')
        
        # Sample customer data
        data = {
            'customer_id': range(1, 101),
            'name': [f'User {i}' for i in range(1, 101)],
            'email': [f'user{i}@example.com' for i in range(1, 101)],
            'age': [25 + (i % 40) for i in range(1, 101)],  # Ages from 25 to 64
            'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'] * 20,
            'salary': [30000 + (i * 1000) for i in range(1, 101)],  # Salaries from 30k to 130k
            'join_date': pd.date_range('2020-01-01', periods=100, freq='D').tolist(),
            'is_premium': [True if i % 3 == 0 else False for i in range(1, 101)]  # Every 3rd customer is premium
        }
        
        df = pd.DataFrame(data)
        csv_path = os.path.join(settings.MEDIA_ROOT, 'demo_customer_data.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        # Create dataset record
        if not Dataset.objects.filter(name='Sample Customer Data').exists():
            dataset = Dataset.objects.create(
                name='Sample Customer Data',
                description='Sample customer data for demonstration',
                source_type='CSV',
                file=csv_path,
                owner=demo_user,
                row_count=len(df),
                column_count=len(df.columns),
                schema={col: str(dtype) for col, dtype in df.dtypes.items()},
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created dataset: {dataset.name}'))
        else:
            self.stdout.write('Sample customer dataset already exists')

        self.stdout.write(self.style.SUCCESS('Demo data seeding completed successfully!'))