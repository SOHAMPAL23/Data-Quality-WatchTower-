from django.http import JsonResponse
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
from django.db.models import Count, Q, Sum, Avg
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


def enhanced_dashboard_stats_api(request):
    """
    Enhanced API endpoint for comprehensive dashboard statistics with descriptive data
    Route: /api/dashboard/enhanced-stats/
    """
    try:
        # Get date range filter
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Basic stats
        dataset_count = Dataset.objects.filter(is_active=True).count()
        rule_count = Rule.objects.filter(is_active=True).count()
        
        # Rule runs stats
        rule_runs = RuleRun.objects.all()
        if days:
            rule_runs = rule_runs.filter(started_at__gte=start_date)
        
        total_runs = rule_runs.count()
        passed_runs = rule_runs.filter(failed_count=0).count()
        failed_runs = rule_runs.exclude(failed_count=0).count()
        
        # Incidents stats
        incidents = Incident.objects.all()
        if days:
            incidents = incidents.filter(created_at__gte=start_date)
        
        incident_count = incidents.count()
        
        # Trend data (last N days)
        trend_labels = []
        passed_counts = []
        failed_counts = []
        total_rows_processed = []
        
        for i in range(days, -1, -1):
            date = timezone.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            trend_labels.append(date_str)
            
            day_runs = rule_runs.filter(started_at__date=date.date())
            day_passed = day_runs.filter(failed_count=0).count()
            day_failed = day_runs.exclude(failed_count=0).count()
            
            # Calculate total rows processed
            day_total_rows = day_runs.aggregate(total=Sum('total_rows'))['total'] or 0
            
            passed_counts.append(day_passed)
            failed_counts.append(day_failed)
            total_rows_processed.append(day_total_rows)
        
        # Quality distribution with descriptive labels
        quality_distribution = []
        datasets = Dataset.objects.filter(is_active=True)
        
        for dataset in datasets:
            # Calculate quality score for this dataset
            dataset_runs = RuleRun.objects.filter(rule__dataset=dataset)
            total_dataset_runs = dataset_runs.count()
            
            if total_dataset_runs > 0:
                passed_dataset_runs = dataset_runs.filter(failed_count=0).count()
                quality_score = (passed_dataset_runs / total_dataset_runs) * 100
                
                # Categorize quality
                if quality_score >= 90:
                    category = "Excellent"
                    color = "#28a745"  # Green
                elif quality_score >= 70:
                    category = "Good"
                    color = "#ffc107"  # Yellow
                elif quality_score >= 50:
                    category = "Fair"
                    color = "#fd7e14"  # Orange
                else:
                    category = "Poor"
                    color = "#dc3545"  # Red
                
                quality_distribution.append({
                    'dataset': dataset.name,
                    'quality_score': round(quality_score, 2),
                    'category': category,
                    'color': color,
                    'rows': dataset.row_count
                })
        
        # Execution status with more details
        execution_details = {
            'success': {
                'count': passed_runs,
                'percentage': round((passed_runs / total_runs * 100), 2) if total_runs > 0 else 0,
                'description': 'Rules executed without failures'
            },
            'failure': {
                'count': failed_runs,
                'percentage': round((failed_runs / total_runs * 100), 2) if total_runs > 0 else 0,
                'description': 'Rules with validation failures'
            },
            'inProgress': {
                'count': 0,
                'percentage': 0,
                'description': 'Currently executing rules'
            }
        }
        
        # Incident severity distribution with descriptions
        severity_descriptions = {
            'CRITICAL': 'Immediate attention required - system impact',
            'HIGH': 'High priority - business impact',
            'MEDIUM': 'Medium priority - moderate impact',
            'LOW': 'Low priority - minor issues'
        }
        
        incident_severity_data = []
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = incidents.filter(severity=severity).count()
            incident_severity_data.append({
                'severity': severity,
                'count': count,
                'description': severity_descriptions.get(severity, ''),
                'percentage': round((count / incident_count * 100), 2) if incident_count > 0 else 0
            })
        
        # Additional insights
        avg_rows_per_run = 0
        if total_runs > 0:
            total_rows_sum = rule_runs.aggregate(total=Sum('total_rows'))['total'] or 0
            avg_rows_per_run = total_rows_sum / total_runs if total_rows_sum > 0 else 0
        
        # Enhanced descriptions with business context and tooltips
        stats_descriptions = {
            'datasets': {
                'count': dataset_count,
                'description': f'Total active datasets in the system ({dataset_count} datasets monitored for quality)',
                'tooltip': f'Monitoring {dataset_count} datasets for data quality issues. Each dataset is checked against multiple validation rules.'
            },
            'rules': {
                'count': rule_count,
                'description': f'Active data quality rules ({rule_count} rules validating data integrity)',
                'tooltip': f'Using {rule_count} active validation rules to ensure data quality standards are met across all datasets.'
            },
            'executed': {
                'count': total_runs,
                'description': f'Total rule executions in the last {days} days ({passed_runs} successful, {failed_runs} failed)',
                'tooltip': f'Processed {total_runs} rule executions in the last {days} days. Success rate: {round((passed_runs/total_runs*100), 1) if total_runs > 0 else 0}%.'
            },
            'incidents': {
                'count': incident_count,
                'description': f'Open data quality incidents requiring attention ({incident_count} active issues)',
                'tooltip': f'{incident_count} unresolved data quality issues that require immediate attention. Critical incidents: {len([i for i in incident_severity_data if i["severity"] == "CRITICAL"])}'
            }
        }
        
        # Enhanced trend analysis
        trend_analysis = ""
        trend_tooltip = ""
        if len(passed_counts) > 1:
            recent_pass_rate = (passed_counts[-1] / (passed_counts[-1] + failed_counts[-1]) * 100) if (passed_counts[-1] + failed_counts[-1]) > 0 else 0
            previous_pass_rate = (passed_counts[-2] / (passed_counts[-2] + failed_counts[-2]) * 100) if (passed_counts[-2] + failed_counts[-2]) > 0 else 0
            
            if recent_pass_rate > previous_pass_rate:
                trend_analysis = f"Quality improving: Pass rate increased from {previous_pass_rate:.1f}% to {recent_pass_rate:.1f}%"
                trend_tooltip = f"Positive trend detected. Data quality has improved over the last two days."
            elif recent_pass_rate < previous_pass_rate:
                trend_analysis = f"Quality declining: Pass rate decreased from {previous_pass_rate:.1f}% to {recent_pass_rate:.1f}%"
                trend_tooltip = f"Warning: Data quality has declined. Investigate recent data changes."
            else:
                trend_analysis = f"Stable quality: Pass rate maintained at {recent_pass_rate:.1f}%"
                trend_tooltip = f"Data quality remains stable with consistent pass rate."
        
        # Calculate incident severity counts for tooltip
        critical_count = len([i for i in incident_severity_data if i["severity"] == "CRITICAL"])
        high_count = len([i for i in incident_severity_data if i["severity"] == "HIGH"])
        medium_count = len([i for i in incident_severity_data if i["severity"] == "MEDIUM"])
        low_count = len([i for i in incident_severity_data if i["severity"] == "LOW"])
        
        data = {
            'stats': stats_descriptions,
            'trends': {
                'labels': trend_labels,
                'passed': passed_counts,
                'failed': failed_counts,
                'total_rows': total_rows_processed,
                'description': f'Daily rule execution trends over the last {days} days. {trend_analysis}',
                'insight': f'Average {round(avg_rows_per_run, 0):,} rows processed per execution',
                'tooltip': trend_tooltip
            },
            'quality': {
                'distribution': quality_distribution,
                'description': 'Dataset quality scores categorized by excellence level. Higher scores indicate better data quality.',
                'insight': f'{len([d for d in quality_distribution if d.get("category") in ["Excellent", "Good"]])} of {len(quality_distribution)} datasets have good/excellent quality',
                'tooltip': f'Data quality distribution: {len([d for d in quality_distribution if d.get("category") == "Excellent"])} excellent, {len([d for d in quality_distribution if d.get("category") == "Good"])} good, {len([d for d in quality_distribution if d.get("category") in ["Fair", "Poor"]])} needing attention'
            },
            'execution': {
                'details': execution_details,
                'avg_rows_per_run': round(avg_rows_per_run, 2),
                'description': 'Rule execution success/failure rates with detailed breakdown',
                'insight': f'{execution_details["success"]["percentage"]}% of rules passed validation',
                'tooltip': f'Execution performance: {execution_details["success"]["count"]} successful, {execution_details["failure"]["count"]} failed out of {total_runs} total executions'
            },
            'incidents': {
                'severity_data': incident_severity_data,
                'description': 'Incident distribution by severity level with business impact descriptions',
                'insight': f'{len([i for i in incident_severity_data if i["count"] > 0])} severity levels have active incidents',
                'tooltip': f'Incident severity breakdown: {critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low priority issues'
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)