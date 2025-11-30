import uuid
import pandas as pd
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Rule, RuleRun
from .utils.rule_executor import RuleExecutor
from apps.datasets.models import Dataset
from apps.incidents.models import Incident
import os
import json


@shared_task
def run_single_rule_task(rule_id):
    """
    Run a single rule and create evidence.
    """
    try:
        rule = Rule.objects.select_related('dataset').get(id=rule_id)
        
        if not rule.is_active:
            return f"Rule {rule.name} is inactive, skipping execution."
        
        # Load dataset
        dataset = rule.dataset
        if not dataset.file:
            return f"Dataset {dataset.name} has no file, skipping execution."
        
        # Check if file exists
        file_path = dataset.file.path
        if not os.path.exists(file_path):
            return f"Dataset file not found: {file_path}"
        
        # Execute rule using RuleExecutor
        executor = RuleExecutor(rule, dataset)
        rule_run = executor.execute()
        
        return f"Rule {rule.name} executed successfully. Passed: {rule_run.passed_count}, Failed: {rule_run.failed_count}"
    
    except Exception as e:
        error_msg = f"Error executing rule {rule_id}: {str(e)}"
        print(error_msg)  # Log to console for debugging
        return error_msg


@shared_task
def run_dataset_rules_task(dataset_id):
    """
    Run all active rules for a specific dataset.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        rules = Rule.objects.filter(dataset=dataset, is_active=True)
        
        results = []
        for rule in rules:
            result = run_single_rule_task(rule.id)
            results.append(f"Rule {rule.name}: {result}")
        
        return f"Executed {len(results)} rules for dataset {dataset.name}: {'; '.join(results)}"
    
    except Exception as e:
        error_msg = f"Error running dataset rules for dataset {dataset_id}: {str(e)}"
        print(error_msg)  # Log to console for debugging
        return error_msg


@shared_task
def run_all_rules_task():
    """
    Run all active rules across all datasets.
    """
    try:
        rules = Rule.objects.filter(is_active=True)
        
        results = []
        for rule in rules:
            result = run_single_rule_task(rule.id)
            results.append(f"Rule {rule.name}: {result}")
        
        return f"Executed {len(results)} rules: {'; '.join(results)}"
    
    except Exception as e:
        return f"Error running all rules: {str(e)}"


@shared_task
def check_sla_breaches():
    """
    Check for SLA breaches in open incidents.
    """
    try:
        # Define SLA thresholds (in hours)
        HIGH_SEVERITY_SLA = 2  # 2 hours
        MEDIUM_SEVERITY_SLA = 24  # 24 hours
        LOW_SEVERITY_SLA = 72  # 72 hours
        
        # Get open incidents
        open_incidents = Incident.objects.filter(status='OPEN')
        
        now = timezone.now()
        breached_incidents = []
        
        for incident in open_incidents:
            # Calculate age of incident
            age_hours = (now - incident.created_at).total_seconds() / 3600
            
            # Check if SLA is breached
            sla_breached = False
            if incident.severity == 'HIGH' and age_hours > HIGH_SEVERITY_SLA:
                sla_breached = True
            elif incident.severity == 'MEDIUM' and age_hours > MEDIUM_SEVERITY_SLA:
                sla_breached = True
            elif incident.severity == 'LOW' and age_hours > LOW_SEVERITY_SLA:
                sla_breached = True
            
            if sla_breached:
                incident.sla_status = 'BREACHED'
                incident.save()
                breached_incidents.append(incident.id)
        
        return f"Checked {open_incidents.count()} open incidents. SLA breached for {len(breached_incidents)} incidents."
    
    except Exception as e:
        return f"Error checking SLA breaches: {str(e)}"