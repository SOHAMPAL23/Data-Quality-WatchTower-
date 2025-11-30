from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import json
import pandas as pd
from apps.datasets.models import Dataset
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
from apps.datasets.utils import analyze_dataset_for_rules


@method_decorator(csrf_exempt, name='dispatch')
class DashboardStatsView(View):
    """
    API endpoint to return dashboard statistics as JSON
    """
    
    def get(self, request):
        # Prepare data for trend chart (last 7 days)
        today = timezone.now().date()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        
        # Get rule run stats for each day
        labels = []
        pass_counts = []
        fail_counts = []
        
        for date_str in dates:
            date_obj = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            next_date = date_obj + timedelta(days=1)
            
            runs = RuleRun.objects.filter(
                started_at__date__gte=date_obj,
                started_at__date__lt=next_date
            )
            
            passed = sum(run.passed_count for run in runs)
            failed = sum(run.failed_count for run in runs)
            
            labels.append(date_str)
            pass_counts.append(passed)
            fail_counts.append(failed)
        
        # Get data for heatmap (per dataset)
        datasets = Dataset.objects.filter(is_active=True)
        table_stats = []
        
        for dataset in datasets:
            runs = RuleRun.objects.filter(rule__dataset=dataset)
            total_runs = runs.count()
            failed_runs = runs.filter(failed_count__gt=0).count()
            
            success_rate = 0
            if total_runs > 0:
                success_rate = (total_runs - failed_runs) / total_runs * 100
            
            table_stats.append({
                'name': dataset.name,
                'total_runs': total_runs,
                'failed_runs': failed_runs,
                'success_rate': success_rate
            })
        
        # Get incidents by severity
        incidents_by_severity = list(Incident.objects.values('severity').annotate(count=Count('severity')))
        
        # Get dataset quality scores
        dataset_quality_scores = self._get_dataset_quality_scores()
        
        payload = {
            'labels': labels,
            'pass_counts': pass_counts,
            'fail_counts': fail_counts,
            'table_stats': table_stats,
            'incidents_by_severity': incidents_by_severity,
            'dataset_quality_scores': dataset_quality_scores
        }
        
        return JsonResponse(payload)
    
    def _get_dataset_quality_scores(self):
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


@method_decorator(csrf_exempt, name='dispatch')
class RunRulesView(View):
    """
    API endpoint to trigger rule execution
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            rule_ids = data.get('rule_ids', [])
            
            if not rule_ids:
                return JsonResponse({'error': 'No rule IDs provided'}, status=400)
            
            # Trigger rule execution tasks
            from apps.rules.tasks import run_single_rule_task
            task_results = []
            
            for rule_id in rule_ids:
                try:
                    result = run_single_rule_task.delay(rule_id)
                    task_results.append({'rule_id': rule_id, 'task_id': result.id})
                except Exception as e:
                    task_results.append({'rule_id': rule_id, 'error': str(e)})
            
            return JsonResponse({
                'message': f'Started execution for {len(task_results)} rules',
                'results': task_results
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class IncidentListView(View):
    """
    API endpoint to list incidents
    """
    
    def get(self, request):
        incidents = Incident.objects.select_related('rule', 'dataset').all()
        
        incident_data = []
        for incident in incidents:
            incident_data.append({
                'id': incident.id,
                'title': incident.title,
                'description': incident.description,
                'severity': incident.severity,
                'status': incident.status,
                'dataset': incident.dataset.name,
                'rule': incident.rule.name,
                'created_at': incident.created_at.isoformat(),
                'updated_at': incident.updated_at.isoformat(),
            })
        
        return JsonResponse({'incidents': incident_data})


@method_decorator(csrf_exempt, name='dispatch')
class RuleRunStatsView(View):
    """
    API endpoint to get rule run statistics
    """
    
    def get(self, request):
        # Get total rule runs
        total_runs = RuleRun.objects.count()
        
        # Get successful vs failed runs
        passed_runs = RuleRun.objects.filter(failed_count=0).count()
        failed_runs = RuleRun.objects.exclude(failed_count=0).count()
        
        # Get average pass/fail rates
        if total_runs > 0:
            pass_rate = (passed_runs / total_runs) * 100
            fail_rate = (failed_runs / total_runs) * 100
        else:
            pass_rate = 0
            fail_rate = 0
        
        # Get recent runs (last 10)
        recent_runs = RuleRun.objects.select_related('rule', 'rule__dataset').order_by('-started_at')[:10]
        recent_runs_data = []
        for run in recent_runs:
            recent_runs_data.append({
                'id': run.id,
                'rule_name': run.rule.name,
                'dataset_name': run.rule.dataset.name,
                'run_id': run.run_id,
                'started_at': run.started_at.isoformat(),
                'passed_count': run.passed_count,
                'failed_count': run.failed_count,
                'status': 'Passed' if run.failed_count == 0 else 'Failed'
            })
        
        payload = {
            'total_runs': total_runs,
            'passed_runs': passed_runs,
            'failed_runs': failed_runs,
            'pass_rate': round(pass_rate, 2),
            'fail_rate': round(fail_rate, 2),
            'recent_runs': recent_runs_data
        }
        
        return JsonResponse(payload)


@method_decorator(csrf_exempt, name='dispatch')
class DatasetRuleRecommendationsView(View):
    """
    API endpoint to get rule recommendations for a dataset
    """
    
    def get(self, request, dataset_id):
        try:
            # Get dataset
            dataset = Dataset.objects.get(id=dataset_id)
            
            # Check if dataset has a file
            if not dataset.file or not dataset.file.path:
                return JsonResponse({'error': 'Dataset has no file'}, status=400)
            
            # Try to read the CSV file
            try:
                # Try multiple encodings
                encodings = ['utf-8', 'latin1', 'cp1252']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(dataset.file.path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    return JsonResponse({'error': 'Unable to read CSV file with supported encodings'}, status=400)
                
                # Analyze dataset for rule recommendations
                recommendations = analyze_dataset_for_rules(df)
                
                return JsonResponse({
                    'status': 'completed',
                    'recommendations': recommendations
                })
                
            except Exception as e:
                return JsonResponse({'error': f'Error reading dataset: {str(e)}'}, status=500)
                
        except Dataset.DoesNotExist:
            return JsonResponse({'error': 'Dataset not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DatasetQualityMetricsView(View):
    """
    API endpoint to get detailed quality metrics for a specific dataset
    """
    
    def get(self, request, dataset_id):
        try:
            # Get dataset
            dataset = Dataset.objects.get(id=dataset_id)
            
            # Get quality metrics for the dataset
            quality_metrics = self._get_dataset_quality_metrics(dataset)
            
            # Get rule execution history for this dataset
            rule_runs = RuleRun.objects.filter(rule__dataset=dataset).select_related('rule').order_by('-started_at')[:10]
            rule_runs_data = []
            for run in rule_runs:
                rule_runs_data.append({
                    'id': run.id,
                    'rule_name': run.rule.name,
                    'rule_type': run.rule.get_rule_type_display(),
                    'started_at': run.started_at.isoformat(),
                    'passed_count': run.passed_count,
                    'failed_count': run.failed_count,
                    'status': 'Passed' if run.failed_count == 0 else 'Failed'
                })
            
            # Get incidents for this dataset
            incidents = Incident.objects.filter(dataset=dataset).order_by('-created_at')[:5]
            incidents_data = []
            for incident in incidents:
                incidents_data.append({
                    'id': incident.id,
                    'title': incident.title,
                    'severity': incident.severity,
                    'status': incident.status,
                    'created_at': incident.created_at.isoformat(),
                })
            
            payload = {
                'dataset': {
                    'id': dataset.id,
                    'name': dataset.name,
                    'source_type': dataset.get_source_type_display(),
                    'row_count': dataset.row_count,
                    'column_count': dataset.column_count,
                    'created_at': dataset.created_at.isoformat(),
                },
                'quality_metrics': quality_metrics,
                'recent_rule_runs': rule_runs_data,
                'recent_incidents': incidents_data
            }
            
            return JsonResponse(payload)
            
        except Dataset.DoesNotExist:
            return JsonResponse({'error': 'Dataset not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_dataset_quality_metrics(self, dataset):
        """
        Calculate quality metrics for a dataset based on rule runs
        """
        # Get all rule runs for this dataset
        rule_runs = RuleRun.objects.filter(rule__dataset=dataset)
        
        total_runs = rule_runs.count()
        if total_runs == 0:
            return {
                'overall_quality_score': 0,
                'passed_runs': 0,
                'failed_runs': 0,
                'total_violations': 0,
                'latest_run_date': None,
                'rules_executed': 0,
            }
        
        passed_runs = rule_runs.filter(failed_count=0).count()
        failed_runs = total_runs - passed_runs
        
        # Calculate total violations
        total_violations = sum(run.failed_count for run in rule_runs)
        
        # Calculate overall quality score (percentage of passed runs)
        quality_score = (passed_runs / total_runs) * 100 if total_runs > 0 else 0
        
        # Get latest run date
        latest_run = rule_runs.order_by('-started_at').first()
        latest_run_date = latest_run.started_at.isoformat() if latest_run else None
        
        # Get number of rules executed
        rules_executed = rule_runs.values('rule').distinct().count()
        
        return {
            'overall_quality_score': round(quality_score, 2),
            'passed_runs': passed_runs,
            'failed_runs': failed_runs,
            'total_violations': total_violations,
            'latest_run_date': latest_run_date,
            'rules_executed': rules_executed,
        }