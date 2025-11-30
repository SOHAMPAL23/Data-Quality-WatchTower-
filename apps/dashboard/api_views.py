from django.http import JsonResponse
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.dashboard.models import DashboardGraph
from django.db.models import Count, Avg, F, Case, When, IntegerField, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

def dataset_quality_api(request):
    """
    API endpoint for dataset quality scores
    Returns: [{"dataset": "Dataset Name", "quality": 87}, ...]
    """
    try:
        # Calculate quality score as percentage of passed rule runs
        datasets_with_quality = Dataset.objects.annotate(
            total_runs=Count('rule_runs'),
            passed_runs=Count('rule_runs', filter=Q(rule_runs__failed_count=0)),
            quality_score=Case(
                When(total_runs=0, then=0),
                default=(F('passed_runs') * 100.0 / F('total_runs')),
                output_field=IntegerField()
            )
        ).filter(
            total_runs__gt=0
        ).values(
            'name', 
            'quality_score'
        ).order_by('-quality_score')
        
        # Format data for frontend
        data = [
            {
                'dataset': dataset['name'],
                'quality': round(dataset['quality_score'], 2)
            }
            for dataset in datasets_with_quality
        ]
        
        # Save to DashboardGraph for persistence
        DashboardGraph.objects.create(
            graph_type='DATASET_QUALITY',
            data=data
        )
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def rule_frequency_api(request):
    """
    API endpoint for rule run frequency
    Returns: [{"rule": "Rule Name", "frequency": 4}, ...]
    """
    try:
        # Count how many times each rule has been run
        rules_with_frequency = Rule.objects.annotate(
            run_count=Count('runs')
        ).filter(
            run_count__gt=0
        ).values(
            'name',
            'run_count'
        ).order_by('-run_count')
        
        # Format data for frontend
        data = [
            {
                'rule': rule['name'],
                'frequency': rule['run_count']
            }
            for rule in rules_with_frequency
        ]
        
        # Save to DashboardGraph for persistence
        DashboardGraph.objects.create(
            graph_type='RULE_FREQUENCY',
            data=data
        )
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def rules_per_dataset_api(request):
    """
    API endpoint for rules per dataset
    Returns: [{"dataset": "Dataset Name", "rules": 10}, ...]
    """
    try:
        # Count rules per dataset
        datasets_with_rule_counts = Dataset.objects.annotate(
            rule_count=Count('rules')
        ).filter(
            rule_count__gt=0
        ).values(
            'name',
            'rule_count'
        ).order_by('-rule_count')
        
        # Format data for frontend
        data = [
            {
                'dataset': dataset['name'],
                'rules': dataset['rule_count']
            }
            for dataset in datasets_with_rule_counts
        ]
        
        # Save to DashboardGraph for persistence
        DashboardGraph.objects.create(
            graph_type='RULES_PER_DATASET',
            data=data
        )
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def recent_rule_executions_api(request):
    """
    API endpoint for recent rule executions (last 7 days)
    Returns: [{"date": "2023-01-01", "executions": 5}, ...]
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Get executions for last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        daily_executions = RuleRun.objects.filter(
            started_at__gte=week_ago
        ).annotate(
            date=TruncDate('started_at')
        ).values(
            'date'
        ).annotate(
            executions=Count('id')
        ).order_by('date')
        
        # Format data for frontend
        data = [
            {
                'date': execution['date'].strftime('%Y-%m-%d'),
                'executions': execution['executions']
            }
            for execution in daily_executions
        ]
        
        # Save to DashboardGraph for persistence
        DashboardGraph.objects.create(
            graph_type='RECENT_EXECUTIONS',
            data=data
        )
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)