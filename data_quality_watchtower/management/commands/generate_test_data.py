import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident


class Command(BaseCommand):
    help = 'Generate test data for charts and dashboards'
    
    def handle(self, *args, **options):
        # Get or create test users
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin12345'
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            admin_user = User.objects.get(username='admin')
        
        # Get existing datasets
        datasets = Dataset.objects.all()
        rules = Rule.objects.all()
        
        if not datasets.exists() or not rules.exists():
            self.stdout.write(self.style.ERROR('No datasets or rules found. Please run create_sample_data first.'))
            return
        
        # Generate test rule runs for the last 30 days
        for i in range(30):
            run_date = timezone.now() - timezone.timedelta(days=i)
            
            # Create 2-5 rule runs per day
            for j in range(2 + (i % 4)):
                rule = rules.order_by('?').first()
                dataset = rule.dataset if rule.dataset else datasets.first()
                
                # Random passed/failed counts
                total_rows = 1000 + (i * 50)
                failed_rows = (i * 10) % 200  # Some variation
                passed_rows = total_rows - failed_rows
                
                RuleRun.objects.create(
                    rule=rule,
                    dataset=dataset,
                    run_id=f'test_run_{i}_{j}',
                    started_at=run_date,
                    finished_at=run_date + timezone.timedelta(minutes=5),
                    status='COMPLETED',
                    total_rows=total_rows,
                    passed_rows=passed_rows,
                    failed_rows=failed_rows
                )
        
        # Generate test incidents
        severities = ['LOW', 'MEDIUM', 'HIGH']
        for i in range(20):
            rule = rules.order_by('?').first()
            dataset = rule.dataset if rule.dataset else datasets.first()
            rule_run = RuleRun.objects.order_by('?').first()
            
            Incident.objects.create(
                rule=rule,
                rule_run=rule_run,
                dataset=dataset,
                status='OPEN' if i % 3 == 0 else 'ACKNOWLEDGED' if i % 3 == 1 else 'RESOLVED',
                severity=severities[i % 3],
                title=f'Test incident {i}',
                description=f'Test incident {i} description',
                created_at=timezone.now() - timezone.timedelta(days=i),
                updated_at=timezone.now() - timezone.timedelta(days=i//2)
            )
        
        self.stdout.write(self.style.SUCCESS('Test data generated successfully!'))