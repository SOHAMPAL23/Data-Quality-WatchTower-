from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import RuleRun
from apps.rules.models import Rule
from apps.datasets.models import Dataset
from django.db.models import Q
import json

@login_required
def rule_run_timeline(request):
    """Display a timeline of rule executions"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    dataset_filter = request.GET.get('dataset', '')
    rule_filter = request.GET.get('rule', '')
    status_filter = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # Start with all rule runs
    rule_runs = RuleRun.objects.select_related('rule', 'dataset').order_by('-started_at')
    
    # Apply filters
    if search_query:
        rule_runs = rule_runs.filter(
            Q(rule__name__icontains=search_query) |
            Q(dataset__name__icontains=search_query)
        )
    
    if dataset_filter:
        rule_runs = rule_runs.filter(dataset_id=dataset_filter)
    
    if rule_filter:
        rule_runs = rule_runs.filter(rule_id=rule_filter)
    
    if status_filter:
        rule_runs = rule_runs.filter(status=status_filter)
    
    # Paginate results
    paginator = Paginator(rule_runs, 20)  # Show 20 runs per page
    page_obj = paginator.get_page(page)
    
    # Get filter options
    datasets = Dataset.objects.filter(is_active=True).order_by('name')
    rules = Rule.objects.filter(is_active=True).order_by('name')
    statuses = RuleRun.objects.values_list('status', flat=True).distinct().order_by('status')
    
    return render(request, 'rules/timeline.html', {
        'page_obj': page_obj,
        'datasets': datasets,
        'rules': rules,
        'statuses': statuses,
        'search_query': search_query,
        'dataset_filter': dataset_filter,
        'rule_filter': rule_filter,
        'status_filter': status_filter,
    })

@login_required
def rule_run_timeline_api(request):
    """API endpoint for rule execution timeline data"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    dataset_filter = request.GET.get('dataset', '')
    rule_filter = request.GET.get('rule', '')
    status_filter = request.GET.get('status', '')
    limit = int(request.GET.get('limit', 50))
    
    # Start with all rule runs
    rule_runs = RuleRun.objects.select_related('rule', 'dataset').order_by('-started_at')
    
    # Apply filters
    if search_query:
        rule_runs = rule_runs.filter(
            Q(rule__name__icontains=search_query) |
            Q(dataset__name__icontains=search_query)
        )
    
    if dataset_filter:
        rule_runs = rule_runs.filter(dataset_id=dataset_filter)
    
    if rule_filter:
        rule_runs = rule_runs.filter(rule_id=rule_filter)
    
    if status_filter:
        rule_runs = rule_runs.filter(status=status_filter)
    
    # Limit results
    rule_runs = rule_runs[:limit]
    
    # Format data for timeline
    timeline_data = []
    for run in rule_runs:
        # Determine status color
        if run.status == 'SUCCESS':
            status_color = 'success'
        elif run.status == 'FAILURE':
            status_color = 'danger'
        elif run.status == 'RUNNING':
            status_color = 'warning'
        else:
            status_color = 'secondary'
        
        # Check if there's an associated incident
        incident = None
        if hasattr(run, 'incident') and run.incident:
            incident = {
                'id': run.incident.id,
                'title': run.incident.title,
            }
        
        timeline_data.append({
            'id': run.id,
            'rule_name': run.rule.name,
            'dataset_name': run.dataset.name if run.dataset else 'Unknown',
            'started_at': run.started_at.isoformat(),
            'finished_at': run.finished_at.isoformat() if run.finished_at else None,
            'duration': (run.finished_at - run.started_at).total_seconds() if run.finished_at else None,
            'status': run.status,
            'status_color': status_color,
            'total_rows': run.total_rows,
            'passed_count': run.passed_count,
            'failed_count': run.failed_count,
            'incident': incident,
        })
    
    return JsonResponse({
        'timeline_data': timeline_data,
        'count': len(timeline_data),
    })