from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
import json


def public_home(request):
    """Public home page that doesn't require authentication"""
    if request.user.is_authenticated:
        return redirect('dashboard:enhanced_dashboard')
    return render(request, 'public_home.html')

def enhanced_dashboard(request):
    """Enhanced dashboard with modern UI and dynamic charts"""
    return render(request, 'dashboard/home_enhanced.html')


@login_required
def dashboard_home(request):
    # Get stats
    dataset_count = Dataset.objects.filter(is_active=True).count()
    rule_count = Rule.objects.filter(is_active=True).count()
    incident_count = Incident.objects.filter(status='OPEN').count()
    
    # Get recent incidents
    recent_incidents = Incident.objects.select_related('rule', 'dataset').order_by('-created_at')[:5]
    
    # Get incidents by severity
    incidents_by_severity = list(Incident.objects.values('severity').annotate(count=Count('severity')))
    
    # Get rule run statistics
    total_runs = RuleRun.objects.count()
    passed_runs = RuleRun.objects.filter(failed_count=0).count()
    failed_runs = RuleRun.objects.exclude(failed_count=0).count()
    
    # Calculate pass rate
    if total_runs > 0:
        pass_rate = (passed_runs / total_runs) * 100
    else:
        pass_rate = 0
    
    # Get recent rule runs (last 10)
    recent_runs = RuleRun.objects.select_related('rule', 'rule__dataset').order_by('-started_at')[:10]
    
    context = {
        'dataset_count': dataset_count,
        'rule_count': rule_count,
        'incident_count': incident_count,
        'recent_incidents': recent_incidents,
        'incidents_by_severity': incidents_by_severity,
        'total_runs': total_runs,
        'passed_runs': passed_runs,
        'failed_runs': failed_runs,
        'pass_rate': round(pass_rate, 2),
        'recent_runs': recent_runs,
    }
    
    return render(request, 'dashboard/home.html', context)


def _get_dataset_quality_scores():
    """
    Calculate quality scores for all active datasets
    """
    datasets = Dataset.objects.filter(is_active=True)
    quality_scores = []
    
    for dataset in datasets:
        # Get all rule runs for this dataset
        rule_runs = RuleRun.objects.filter(rule__dataset=dataset)
        total_runs = rule_runs.count()
        
        if total_runs == 0:
            quality_scores.append({
                'name': dataset.name,
                'quality_score': 0
            })
            continue
        
        passed_runs = rule_runs.filter(failed_count=0).count()
        quality_score = (passed_runs / total_runs) * 100
        
        quality_scores.append({
            'name': dataset.name,
            'quality_score': round(quality_score, 2)
        })
    
    return quality_scores


def _get_rules_run_frequency():
    """
    Get frequency data for how many times each rule has been run
    """
    # Get rules with their run counts (count of RuleRun objects), ordered by run count descending
    rules_with_counts = Rule.objects.annotate(
        run_count=Count('runs')
    ).filter(run_count__gt=0).order_by('-run_count')[:10]  # Top 10 rules
    
    frequency_data = []
    for rule in rules_with_counts:
        frequency_data.append({
            'name': rule.name,
            'run_count': rule.run_count
        })
    
    return frequency_data