from django.http import JsonResponse
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

def active_datasets_api(request):
    """
    API endpoint for total active datasets
    Route: /api/dashboard/active-datasets/
    Response: { "count": 5 }
    """
    try:
        count = Dataset.objects.filter(is_active=True).count()
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def active_rules_api(request):
    """
    API endpoint for active data rules
    Route: /api/dashboard/active-rules/
    Response: { "count": 12 }
    """
    try:
        count = Rule.objects.filter(is_active=True).count()
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def open_incidents_api(request):
    """
    API endpoint for open incidents
    Route: /api/dashboard/open-incidents/
    Response: { "count": 3 }
    """
    try:
        count = Incident.objects.filter(status='OPEN').count()
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def pass_rate_api(request):
    """
    API endpoint for overall pass rate
    Pass rate = successful rule runs / total rule runs × 100
    Route: /api/dashboard/pass-rate/
    Response: { "rate": 87.5 }
    """
    try:
        total_runs = RuleRun.objects.count()
        passed_runs = RuleRun.objects.filter(failed_count=0).count()
        
        if total_runs > 0:
            rate = (passed_runs / total_runs) * 100
        else:
            rate = 0
            
        return JsonResponse({'rate': round(rate, 2)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def rule_execution_trend_api(request):
    """
    API endpoint for rule execution trend (last 7 days)
    Route: /api/dashboard/rule-execution-trend/
    Response:
    [
      { "date": "2025-11-25", "executions": 22 },
      { "date": "2025-11-26", "executions": 30 }
    ]
    """
    try:
        # Get executions for last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        daily_executions = RuleRun.objects.filter(
            started_at__gte=week_ago
        ).extra(
            select={'date': 'date(started_at)'}
        ).values(
            'date'
        ).annotate(
            executions=Count('id')
        ).order_by('date')
        
        # Format data for frontend
        data = [
            {
                'date': execution['date'].strftime('%Y-%m-%d') if hasattr(execution['date'], 'strftime') else str(execution['date']),
                'executions': execution['executions']
            }
            for execution in daily_executions
        ]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def incidents_severity_api(request):
    """
    API endpoint for incidents by severity
    Route: /api/dashboard/incidents-severity/
    Response:
    [
      { "severity": "Low", "count": 2 },
      { "severity": "Medium", "count": 4 },
      { "severity": "High", "count": 1 }
    ]
    """
    try:
        severity_counts = Incident.objects.values('severity').annotate(count=Count('severity'))
        
        # Format data for frontend
        data = [
            {
                'severity': item['severity'],
                'count': item['count']
            }
            for item in severity_counts
        ]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)