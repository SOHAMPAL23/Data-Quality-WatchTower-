from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q, DateField
from django.db.models.functions import Cast, Extract
import json

from rules.models import Rule, RuleRun, Dataset
from incidents.models import Incident

@login_required
def dashboard_home(request):
    """Display the main dashboard with charts and metrics"""
    # Get recent rule runs
    recent_runs = RuleRun.objects.select_related('rule', 'dataset').order_by('-started_at')[:10]
    
    # Get open incidents
    open_incidents = Incident.objects.filter(state='OPEN').count()
    
    # Get datasets
    datasets = Dataset.objects.filter(is_active=True).count()
    
    # Get rules
    rules = Rule.objects.filter(is_active=True).count()
    
    context = {
        'recent_runs': recent_runs,
        'open_incidents': open_incidents,
        'datasets': datasets,
        'rules': rules,
    }
    
    return render(request, 'dashboards/home.html', context)

def dashboard_stats(request):
    """API endpoint to return dashboard statistics as JSON"""
    # Get data for trend chart (last 30 days)
    days = 30
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=days)
    
    # Get rule runs grouped by day
    rule_runs = RuleRun.objects.filter(
        started_at__gte=start_date,
        started_at__lte=end_date
    ).annotate(
        day=Cast('started_at', DateField())
    ).values('day').annotate(
        total=Count('id'),
        passed=Sum('passed_rows'),
        failed=Sum('failed_rows')
    ).order_by('day')
    
    # Prepare data for chart
    labels = []
    pass_counts = []
    fail_counts = []
    
    for run in rule_runs:
        labels.append(run['day'].strftime('%Y-%m-%d'))
        pass_counts.append(run['passed'] or 0)
        fail_counts.append(run['failed'] or 0)
    
    # Get data for heatmap (per dataset)
    dataset_stats = Dataset.objects.filter(is_active=True).annotate(
        total_runs=Count('rules__runs'),
        failed_runs=Count('rules__runs', filter=Q(rules__runs__failed_rows__gt=0)),
        total_failed_rows=Sum('rules__runs__failed_rows'),
        total_rows=Sum('rules__runs__total_rows')
    ).values('id', 'name', 'total_runs', 'failed_runs', 'total_failed_rows', 'total_rows')
    
    table_stats = []
    for dataset in dataset_stats:
        success_rate = 0
        if dataset['total_rows'] and dataset['total_rows'] > 0:
            # Calculate success rate based on total rows vs failed rows
            success_rate = ((dataset['total_rows'] - dataset['total_failed_rows']) / dataset['total_rows']) * 100
        elif dataset['total_runs'] > 0:
            # Fallback to run-based calculation
            success_rate = ((dataset['total_runs'] - dataset['failed_runs']) / dataset['total_runs']) * 100
            
        table_stats.append({
            'id': dataset['id'],
            'name': dataset['name'],
            'total_runs': dataset['total_runs'],
            'failed_runs': dataset['failed_runs'],
            'success_rate': success_rate
        })
    
    # Handle case where there's no data
    if not labels:
        # Provide default data for the last 7 days
        for i in range(6, -1, -1):
            date = timezone.now() - timezone.timedelta(days=i)
            labels.append(date.strftime('%Y-%m-%d'))
            pass_counts.append(0)
            fail_counts.append(0)
    
    payload = {
        'labels': labels,
        'pass_counts': pass_counts,
        'fail_counts': fail_counts,
        'table_stats': table_stats
    }
    
    return JsonResponse(payload)

@login_required
def dataset_detail(request, dataset_id):
    """Display detailed statistics for a specific dataset"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Get rules for this dataset
    rules = Rule.objects.filter(dataset=dataset, is_active=True)
    
    # Get recent rule runs for this dataset
    recent_runs = RuleRun.objects.filter(dataset=dataset).select_related('rule').order_by('-started_at')[:10]
    
    context = {
        'dataset': dataset,
        'rules': rules,
        'recent_runs': recent_runs,
    }
    
    return render(request, 'dashboards/dataset.html', context)

def dataset_stats(request, dataset_id):
    """API endpoint to return dataset statistics as JSON"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Get data for trend chart (last 30 days) for this dataset
    days = 30
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=days)
    
    # Get rule runs grouped by day for this dataset
    rule_runs = RuleRun.objects.filter(
        dataset=dataset,
        started_at__gte=start_date,
        started_at__lte=end_date
    ).annotate(
        day=Cast('started_at', DateField())
    ).values('day').annotate(
        total=Count('id'),
        passed=Sum('passed_rows'),
        failed=Sum('failed_rows')
    ).order_by('day')
    
    # Prepare data for chart
    labels = []
    pass_counts = []
    fail_counts = []
    
    for run in rule_runs:
        labels.append(run['day'].strftime('%Y-%m-%d'))
        pass_counts.append(run['passed'] or 0)
        fail_counts.append(run['failed'] or 0)
    
    # Get rule statistics for this dataset
    rule_stats = Rule.objects.filter(dataset=dataset, is_active=True).annotate(
        total_runs=Count('runs'),
        failed_runs=Count('runs', filter=Q(runs__failed_rows__gt=0)),
        total_failed_rows=Sum('runs__failed_rows'),
        total_rows=Sum('runs__total_rows')
    ).values('name', 'total_runs', 'failed_runs', 'total_failed_rows', 'total_rows')
    
    rule_data = []
    for rule in rule_stats:
        success_rate = 0
        if rule['total_rows'] and rule['total_rows'] > 0:
            # Calculate success rate based on total rows vs failed rows
            success_rate = ((rule['total_rows'] - rule['total_failed_rows']) / rule['total_rows']) * 100
        elif rule['total_runs'] > 0:
            # Fallback to run-based calculation
            success_rate = ((rule['total_runs'] - rule['failed_runs']) / rule['total_runs']) * 100
            
        rule_data.append({
            'name': rule['name'],
            'total_runs': rule['total_runs'],
            'failed_runs': rule['failed_runs'],
            'success_rate': success_rate
        })
    
    # Handle case where there's no data
    if not labels:
        # Provide default data for the last 7 days
        for i in range(6, -1, -1):
            date = timezone.now() - timezone.timedelta(days=i)
            labels.append(date.strftime('%Y-%m-%d'))
            pass_counts.append(0)
            fail_counts.append(0)
    
    payload = {
        'labels': labels,
        'pass_counts': pass_counts,
        'fail_counts': fail_counts,
        'rule_data': rule_data
    }
    
    return JsonResponse(payload)