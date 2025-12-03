from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
import json

class DashboardStatsAPIView(View):
    """
    API endpoint for enhanced dashboard statistics
    """
    
    def get(self, request):
        try:
            # Get date range filter
            days = int(request.GET.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Get dataset type filter
            dataset_type = request.GET.get('dataset_type', '')
            
            # Get user filter
            user_filter = request.GET.get('user', '')
            
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
            
            # Trend data (last 30 days)
            trend_labels = []
            passed_counts = []
            failed_counts = []
            
            for i in range(30, -1, -1):
                date = timezone.now() - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                trend_labels.append(date_str)
                
                day_passed = rule_runs.filter(
                    started_at__date=date.date(),
                    failed_count=0
                ).count()
                
                day_failed = rule_runs.filter(
                    started_at__date=date.date()
                ).exclude(failed_count=0).count()
                
                passed_counts.append(day_passed)
                failed_counts.append(day_failed)
            
            # Quality distribution with enhanced descriptions
            quality_high = Dataset.objects.filter(quality_score__gte=90).count()
            quality_medium = Dataset.objects.filter(
                quality_score__gte=70, 
                quality_score__lt=90
            ).count()
            quality_low = Dataset.objects.filter(quality_score__lt=70).count()
            
            # Enhanced quality descriptions
            quality_insights = []
            if quality_high > 0:
                quality_insights.append(f"{quality_high} datasets with excellent quality (90%+ pass rate)")
            if quality_medium > 0:
                quality_insights.append(f"{quality_medium} datasets with good quality (70-89% pass rate)")
            if quality_low > 0:
                quality_insights.append(f"{quality_low} datasets with poor quality (<70% pass rate)")
            
            quality_description = "Overall data quality distribution: " + "; ".join(quality_insights) if quality_insights else "No quality data available"
            
            # Execution status with business context
            execution_success = passed_runs
            execution_failure = failed_runs
            execution_in_progress = 0  # Simplified for now
            
            # Business context for execution status
            success_rate = (execution_success / total_runs * 100) if total_runs > 0 else 0
            failure_rate = (execution_failure / total_runs * 100) if total_runs > 0 else 0
            
            execution_description = f"Rule execution performance: {success_rate:.1f}% success rate ({execution_success} successful out of {total_runs} total executions); {failure_rate:.1f}% failure rate ({execution_failure} failed)"
            
            # Incident severity distribution with business impact
            critical_incidents = incidents.filter(severity='CRITICAL').count()
            high_incidents = incidents.filter(severity='HIGH').count()
            medium_incidents = incidents.filter(severity='MEDIUM').count()
            low_incidents = incidents.filter(severity='LOW').count()
            
            # Business impact description
            incident_insights = []
            if critical_incidents > 0:
                incident_insights.append(f"{critical_incidents} critical incidents requiring immediate attention")
            if high_incidents > 0:
                incident_insights.append(f"{high_incidents} high-priority incidents affecting business operations")
            if medium_incidents > 0:
                incident_insights.append(f"{medium_incidents} medium-priority incidents to monitor")
            if low_incidents > 0:
                incident_insights.append(f"{low_incidents} low-priority incidents for awareness")
            
            incident_description = "Incident severity breakdown: " + "; ".join(incident_insights) if incident_insights else "No incidents reported"
            
            data = {
                'stats': {
                    'datasets': dataset_count,
                    'rules': rule_count,
                    'executed': total_runs,
                    'incidents': incident_count
                },
                'trends': {
                    'labels': trend_labels,
                    'passed': passed_counts,
                    'failed': failed_counts
                },
                'quality': {
                    'labels': ['High Quality (>90%)', 'Medium Quality (70-90%)', 'Low Quality (<70%)'],
                    'scores': [quality_high, quality_medium, quality_low],
                    'description': quality_description
                },
                'execution': {
                    'success': execution_success,
                    'failure': execution_failure,
                    'inProgress': execution_in_progress,
                    'description': execution_description
                },
                'incidents': {
                    'critical': critical_incidents,
                    'high': high_incidents,
                    'medium': medium_incidents,
                    'low': low_incidents,
                    'description': incident_description
                }
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class DashboardFiltersAPIView(View):
    """
    API endpoint for dashboard filters
    """
    
    def get(self, request):
        try:
            # Get unique dataset types
            dataset_types = Dataset.objects.filter(is_active=True).values_list(
                'data_type', flat=True
            ).distinct().order_by('data_type')
            
            # Get users who created rules/datasets
            users = []
            
            data = {
                'dataset_types': list(dataset_types),
                'users': users
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)