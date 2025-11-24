from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rules.models import Rule, RuleRun, Dataset
from incidents.models import Incident
import random
from datetime import timedelta
from django.utils import timezone
import uuid

class Command(BaseCommand):
    help = 'Seed the database with demo data for dashboards'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get or create users
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='ADMIN',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        try:
            steward_user = User.objects.get(username='steward')
        except User.DoesNotExist:
            steward_user = User.objects.create_user(
                username='steward',
                email='steward@example.com',
                password='steward123',
                role='DATA_STEWARD'
            )
            self.stdout.write(self.style.SUCCESS('Created data steward user'))

        try:
            viewer_user = User.objects.get(username='viewer')
        except User.DoesNotExist:
            viewer_user = User.objects.create_user(
                username='viewer',
                email='viewer@example.com',
                password='viewer123',
                role='VIEWER'
            )
            self.stdout.write(self.style.SUCCESS('Created viewer user'))

        # Create datasets
        datasets_data = [
            {
                'name': 'Customer Data',
                'source_type': 'CSV',
                'owner': admin_user,
                'is_active': True
            },
            {
                'name': 'Order Data',
                'source_type': 'DB',
                'table_name': 'orders',
                'owner': steward_user,
                'is_active': True
            },
            {
                'name': 'Product Data',
                'source_type': 'CSV',
                'owner': steward_user,
                'is_active': True
            }
        ]

        datasets = []
        for data in datasets_data:
            dataset, created = Dataset.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            datasets.append(dataset)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created dataset: {dataset.name}'))

        # Create rules
        rules_data = [
            {
                'dataset': datasets[0],
                'name': 'Customer Email Not Null',
                'rule_type': 'NOT_NULL',
                'dsl_expression': 'NOT_NULL("email")',
                'severity': 'HIGH'
            },
            {
                'dataset': datasets[0],
                'name': 'Customer ID Unique',
                'rule_type': 'UNIQUE',
                'dsl_expression': 'UNIQUE("id")',
                'severity': 'CRITICAL'
            },
            {
                'dataset': datasets[0],
                'name': 'Customer Age Range',
                'rule_type': 'RANGE',
                'dsl_expression': 'RANGE("age", min=18, max=65)',
                'severity': 'MEDIUM',
                'range_min': 18,
                'range_max': 65
            },
            {
                'dataset': datasets[1],
                'name': 'Order Customer FK',
                'rule_type': 'FK',
                'dsl_expression': 'FK("customer_id", "customers.id")',
                'severity': 'HIGH',
                'fk_table': 'customers',
                'fk_column': 'id'
            },
            {
                'dataset': datasets[1],
                'name': 'Order Amount Not Null',
                'rule_type': 'NOT_NULL',
                'dsl_expression': 'NOT_NULL("amount")',
                'severity': 'MEDIUM'
            },
            {
                'dataset': datasets[1],
                'name': 'Order Status Valid',
                'rule_type': 'RANGE',
                'dsl_expression': 'RANGE("status", min="pending", max="completed")',
                'severity': 'LOW'
            },
            {
                'dataset': datasets[2],
                'name': 'Product Name Not Null',
                'rule_type': 'NOT_NULL',
                'dsl_expression': 'NOT_NULL("name")',
                'severity': 'HIGH'
            },
            {
                'dataset': datasets[2],
                'name': 'Product Price Range',
                'rule_type': 'RANGE',
                'dsl_expression': 'RANGE("price", min=0, max=10000)',
                'severity': 'MEDIUM',
                'range_min': 0,
                'range_max': 10000
            }
        ]

        rules = []
        for data in rules_data:
            rule, created = Rule.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            rules.append(rule)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created rule: {rule.name}'))

        # Create rule runs for the last 30 days
        for i in range(50):
            # Randomly select rule and dataset
            rule = random.choice(rules)
            dataset = rule.dataset
            
            # Create rule run
            rule_run = RuleRun.objects.create(
                rule=rule,
                dataset=dataset,
                run_id=uuid.uuid4(),
                status='COMPLETED',
                started_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                finished_at=timezone.now() - timedelta(days=random.randint(0, 30)) + timedelta(minutes=random.randint(1, 60)),
                total_rows=random.randint(100, 10000),
                failed_rows=random.randint(0, 100),
                passed_rows=random.randint(0, 10000)
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created rule run: {rule_run.rule.name}'))

        # Create incidents
        incident_states = ['OPEN', 'ACK', 'MUTED', 'RESOLVED']
        severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

        for i in range(15):
            # Randomly select rule and dataset
            rule = random.choice(rules)
            dataset = rule.dataset
            
            # Create incident
            incident = Incident.objects.create(
                rule=rule,
                dataset=dataset,
                owner=random.choice([admin_user, steward_user, None]),
                state=random.choice(incident_states),
                title=f'Issue with {rule.name} - #{i+1}',
                description=f'This incident was automatically generated for demo purposes. Rule {rule.name} failed on dataset {dataset.name}.',
                severity=random.choice(severity_levels),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                sla_breached=random.choice([True, False])
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created incident: {incident.title}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data for dashboards'))