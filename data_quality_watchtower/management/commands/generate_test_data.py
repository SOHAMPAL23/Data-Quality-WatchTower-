import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate comprehensive test data for all models'

    def handle(self, *args, **options):
        # Get or create test users
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin'
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            admin_user = User.objects.get(username='admin')

        # Create sample dataset
        if not Dataset.objects.filter(name='Test Employee Data').exists():
            # Create sample CSV data
            data = {
                'id': range(1, 101),
                'name': [f'Employee {i}' for i in range(1, 101)],
                'email': [f'employee{i}@company.com' for i in range(1, 101)],
                'department': ['Engineering', 'Marketing', 'Sales', 'HR'] * 25,
                'salary': [50000 + (i * 1000) for i in range(1, 101)],  # Salaries from 50k to 150k
                'hire_date': pd.date_range('2020-01-01', periods=100, freq='D').tolist(),
                'is_active': [True] * 95 + [False] * 5  # 5 inactive employees
            }
            
            df = pd.DataFrame(data)
            csv_path = os.path.join(settings.MEDIA_ROOT, 'test_employee_data.csv')
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df.to_csv(csv_path, index=False)
            
            dataset = Dataset.objects.create(
                name='Test Employee Data',
                description='Comprehensive test employee data',
                source_type='CSV',
                file=csv_path,
                owner=admin_user,
                row_count=len(df),
                column_count=len(df.columns),
                schema={col: str(dtype) for col, dtype in df.dtypes.items()},
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created dataset: {dataset.name}'))
        else:
            dataset = Dataset.objects.get(name='Test Employee Data')

        # Create sample rules
        rules_data = [
            {
                'name': 'Email Format Validation',
                'description': 'Ensure all email addresses are properly formatted',
                'rule_type': 'REGEX',
                'dsl_expression': 'REGEX("email", "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")'
            },
            {
                'name': 'Salary Range Check',
                'description': 'Ensure salaries are within reasonable range',
                'rule_type': 'IN_RANGE',
                'dsl_expression': 'IN_RANGE("salary", 30000, 200000)'
            },
            {
                'name': 'Employee ID Uniqueness',
                'description': 'Ensure employee IDs are unique',
                'rule_type': 'UNIQUE',
                'dsl_expression': 'UNIQUE("id")'
            },
            {
                'name': 'Name Completeness Check',
                'description': 'Ensure employee names are not null',
                'rule_type': 'NOT_NULL',
                'dsl_expression': 'NOT_NULL("name")'
            }
        ]

        for rule_data in rules_data:
            if not Rule.objects.filter(name=rule_data['name'], dataset=dataset).exists():
                rule = Rule.objects.create(
                    dataset=dataset,
                    owner=admin_user,
                    is_active=True,
                    **rule_data
                )
                self.stdout.write(self.style.SUCCESS(f'Created rule: {rule.name}'))

        # Get the rules for creating rule runs
        rules = Rule.objects.filter(dataset=dataset)

        # Create sample rule runs
        for i, rule in enumerate(rules):
            # Create multiple runs for each rule
            for j in range(3):
                run_id = f"test_run_{rule.id}_{j}"
                if not RuleRun.objects.filter(run_id=run_id).exists():
                    # Simulate some failures for variety
                    failed_count = 0 if j == 0 else (2 if j == 1 else 5)
                    passed_count = 100 - failed_count
                    
                    rule_run = RuleRun.objects.create(
                        rule=rule,
                        dataset=dataset,
                        run_id=run_id,
                        started_at=timezone.now() - timezone.timedelta(days=30-j*10),
                        finished_at=timezone.now() - timezone.timedelta(days=30-j*10) + timezone.timedelta(minutes=5),
                        status='COMPLETED',
                        total_rows=100,
                        passed_count=passed_count,
                        failed_count=failed_count,
                        sample_evidence=[
                            {"row_id": k, "column": "email", "value": f"user{k}@invalid", "error": "Invalid email format"}
                            for k in range(1, min(failed_count + 1, 6))
                        ] if failed_count > 0 else []
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created rule run: {rule_run.run_id}'))

        # Create sample incidents
        if rules.exists():
            rule = rules.first()
            incident_data = [
                {
                    'title': 'Critical Email Format Issue',
                    'description': 'Multiple email addresses found with invalid formats',
                    'severity': 'CRITICAL',
                    'status': 'OPEN'
                },
                {
                    'title': 'Salary Data Anomaly',
                    'description': 'Unexpected salary values detected outside normal range',
                    'severity': 'HIGH',
                    'status': 'OPEN'
                },
                {
                    'title': 'Minor Data Inconsistency',
                    'description': 'Small number of records with missing department information',
                    'severity': 'LOW',
                    'status': 'RESOLVED'
                }
            ]

            for incident_datum in incident_data:
                if not Incident.objects.filter(title=incident_datum['title']).exists():
                    incident = Incident.objects.create(
                        dataset=dataset,
                        rule=rule,
                        assigned_to=admin_user,
                        evidence_file=None,  # No evidence file in test data
                        **incident_datum
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created incident: {incident.title}'))

        self.stdout.write(self.style.SUCCESS('Successfully generated comprehensive test data!'))