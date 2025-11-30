import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Dataset
from .forms import DatasetForm
from .utils import analyze_dataset_for_rules
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident
import pandas as pd
import json
import uuid

# Configure logger
logger = logging.getLogger(__name__)


@login_required
def dataset_list(request):
    datasets = Dataset.objects.filter(owner=request.user)
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        datasets = datasets.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(datasets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'datasets/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@login_required
def dataset_create(request):
    if request.method == 'POST':
        form = DatasetForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.owner = request.user
            
            # Save the dataset first to ensure file is properly handled
            dataset.save()
            
            # Process CSV file if provided
            if dataset.source_type == 'CSV' and dataset.file:
                try:
                    # Read CSV file to get stats
                    # Try multiple encodings to handle different file types
                    encodings = ['utf-8', 'latin1', 'cp1252']
                    df = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(dataset.file.path, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if df is None:
                        raise Exception('Unable to read CSV file with supported encodings')
                    
                    dataset.row_count = len(df)
                    dataset.column_count = len(df.columns)
                    dataset.schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
                    
                    # Get sample statistics for the first few rows
                    sample_df = df.head()
                    
                    # Handle special float values that can't be serialized to JSON
                    from numpy import nan, inf
                    cleaned_data = []
                    for row in sample_df.to_dict('records'):
                        cleaned_row = {}
                        for k, v in row.items():
                            if pd.isna(v):
                                cleaned_row[k] = None
                            elif isinstance(v, float) and (v == float('inf') or v == float('-inf')):
                                cleaned_row[k] = str(v)
                            else:
                                cleaned_row[k] = v
                        cleaned_data.append(cleaned_row)
                    
                    dataset.sample_stats = cleaned_data
                    
                    # Save dataset with updated fields
                    dataset.save(update_fields=['row_count', 'column_count', 'schema', 'sample_stats'])
                    
                    # Generate rule recommendations
                    recommendations = analyze_dataset_for_rules(df)
                    
                    # Automatically create rules based on recommendations
                    created_rules = _create_rules_from_recommendations(dataset, recommendations, request.user)
                    
                    messages.success(request, f'Dataset "{dataset.name}" created successfully with {len(created_rules)} auto-generated rules!')
                    return redirect('datasets:dataset_detail', pk=dataset.pk)
                except Exception as e:
                    messages.error(request, f'Error processing CSV file: {str(e)}')
                    # Delete the dataset if processing failed
                    dataset.delete()
                    return redirect('datasets:dataset_create')
            else:
                messages.success(request, f'Dataset "{dataset.name}" created successfully!')
                return redirect('datasets:dataset_list')
    else:
        form = DatasetForm()
    
    return render(request, 'datasets/create.html', {'form': form})


def _create_rules_from_recommendations(dataset, recommendations, user):
    """
    Create rules automatically from recommendations
    """
    created_rules = []
    
    try:
        for rec in recommendations:
            rule_type = rec.get('type')
            column = rec.get('column')
            
            if not rule_type or not column:
                continue
                
            # Generate rule name and DSL expression based on type
            if rule_type == 'NOT_NULL':
                rule_name = f'{column} Not Null Check'
                dsl_expression = f'NOT_NULL("{column}")'
                description = f'Check that {column} values are not null'
            elif rule_type == 'UNIQUE':
                rule_name = f'{column} Unique Check'
                dsl_expression = f'UNIQUE("{column}")'
                description = f'Check that {column} values are unique'
            elif rule_type == 'IN_RANGE':
                rule_name = f'{column} Range Check'
                # Use default range values, can be adjusted later
                dsl_expression = f'IN_RANGE("{column}", 0, 1000000)'
                description = f'Check that {column} values are within range'
            elif rule_type == 'REGEX':
                rule_name = f'{column} Email Format Check'
                dsl_expression = f'REGEX("{column}", "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$")'
                description = f'Check that {column} values match email format'
            else:
                rule_name = f'{column} {rule_type} Check'
                dsl_expression = f'{rule_type}("{column}")'
                description = f'Auto-generated {rule_type} rule for {column}'
            
            # Create the rule
            rule = Rule.objects.create(
                name=rule_name,
                description=description,
                dataset=dataset,
                rule_type=rule_type,
                dsl_expression=dsl_expression,
                owner=user,
                is_active=True
            )
            
            created_rules.append(rule)
            
            # Create initial rule run for dashboard visualization
            rule_run = RuleRun.objects.create(
                rule=rule,
                dataset=dataset,
                run_id=f"initial_run_{rule.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
                started_at=timezone.now(),
                finished_at=timezone.now(),
                status='COMPLETED',
                total_rows=dataset.row_count or 0,
                passed_count=dataset.row_count or 0,  # Initially assume all pass
                failed_count=0,
                sample_evidence=[]
            )
            
    except Exception as e:
        logger.error(f"Error creating rules from recommendations: {str(e)}")
    
    return created_rules


@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    
    # Check if this is a request for fresh data
    if request.GET.get('fresh_data') == 'true':
        # Return JSON response with fresh data
        quality_metrics = _get_dataset_quality_metrics(dataset)
        quality_trend_data = dataset.quality_trend_data or []
        rule_pass_rates = dataset.rule_pass_rates or []
        
        response_data = {
            'quality_metrics': quality_metrics,
            'quality_trend_data': quality_trend_data,
            'rule_pass_rates': rule_pass_rates
        }
        
        print(f"Sending fresh data for dataset {dataset.id}: {response_data}")  # Debug log
        return JsonResponse(response_data)
    
    # Get dataset preview for CSV files
    preview_data = None
    if dataset.source_type == 'CSV' and dataset.file:
        try:
            # Try multiple encodings to handle different file types
            encodings = ['utf-8', 'latin1', 'cp1252']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(dataset.file.path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is not None:
                preview_data = {
                    'columns': df.columns.tolist(),
                    'data': df.head(10).to_dict('records')
                }
            else:
                messages.error(request, 'Unable to read CSV file with supported encodings')
        except Exception as e:
            messages.error(request, f'Error loading dataset preview: {str(e)}')
    
    # Get quality metrics for the dataset
    quality_metrics = _get_dataset_quality_metrics(dataset)
    
    # Get rule execution history for this dataset
    rule_runs = RuleRun.objects.filter(rule__dataset=dataset).select_related('rule').order_by('-started_at')[:10]
    
    # Get incidents for this dataset
    incidents = Incident.objects.filter(dataset=dataset).order_by('-created_at')[:5]
    
    # Get quality trend data from dataset
    quality_trend_data = dataset.quality_trend_data or []
    
    context = {
        'dataset': dataset,
        'preview_data': preview_data,
        'quality_metrics': quality_metrics,
        'rule_runs': rule_runs,
        'incidents': incidents,
        'quality_trend_data': json.dumps(quality_trend_data),
    }
    
    print(f"Rendering dataset detail page for dataset {dataset.id}")  # Debug log
    return render(request, 'datasets/detail.html', context)


def _get_dataset_quality_metrics(dataset):
    """
    Calculate quality metrics for a dataset based on rule runs
    """
    # Get all rule runs for this dataset
    rule_runs = RuleRun.objects.filter(rule__dataset=dataset)
    
    total_runs = rule_runs.count()
    print(f"Dataset {dataset.id} has {total_runs} rule runs")  # Debug log
    
    if total_runs == 0:
        # If no rule runs exist, return default values
        default_metrics = {
            'overall_quality_score': 0,
            'passed_runs': 0,
            'failed_runs': 0,
            'total_violations': 0,
            'latest_run_date': None,
            'rules_executed': 0,
        }
        print(f"Dataset {dataset.id} has no rule runs, returning default metrics: {default_metrics}")  # Debug log
        return default_metrics
    
    passed_runs = rule_runs.filter(failed_count=0).count()
    failed_runs = total_runs - passed_runs
    
    # Calculate total violations
    total_violations = sum(run.failed_count for run in rule_runs)
    
    # Calculate overall quality score (percentage of passed runs)
    quality_score = (passed_runs / total_runs) * 100 if total_runs > 0 else 0
    
    # Get latest run date
    latest_run = rule_runs.order_by('-started_at').first()
    latest_run_date = latest_run.started_at if latest_run else None
    
    # Get number of rules executed
    rules_executed = rule_runs.values('rule').distinct().count()
    
    metrics = {
        'overall_quality_score': round(quality_score, 2),
        'passed_runs': passed_runs,
        'failed_runs': failed_runs,
        'total_violations': total_violations,
        'latest_run_date': latest_run_date,
        'rules_executed': rules_executed,
    }
    
    print(f"Dataset {dataset.id} metrics: {metrics}")  # Debug log
    return metrics


@login_required
def dataset_edit(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = DatasetForm(request.POST, request.FILES, instance=dataset)
        if form.is_valid():
            dataset = form.save()
            
            # Re-process CSV file if a new one was uploaded
            if dataset.source_type == 'CSV' and dataset.file:
                try:
                    # Try multiple encodings to handle different file types
                    encodings = ['utf-8', 'latin1', 'cp1252']
                    df = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(dataset.file.path, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if df is None:
                        raise Exception('Unable to read CSV file with supported encodings')
                    
                    dataset.row_count = len(df)
                    dataset.column_count = len(df.columns)
                    dataset.schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
                    
                    # Handle special float values that can't be serialized to JSON
                    from numpy import nan, inf
                    cleaned_data = []
                    for row in df.head().to_dict('records'):
                        cleaned_row = {}
                        for k, v in row.items():
                            if pd.isna(v):
                                cleaned_row[k] = None
                            elif isinstance(v, float) and (v == float('inf') or v == float('-inf')):
                                cleaned_row[k] = str(v)
                            else:
                                cleaned_row[k] = v
                        cleaned_data.append(cleaned_row)
                    
                    dataset.sample_stats = cleaned_data
                    
                    # Save dataset with updated fields
                    dataset.save(update_fields=['row_count', 'column_count', 'schema', 'sample_stats'])
                except Exception as e:
                    messages.error(request, f'Error processing CSV file: {str(e)}')
            
            messages.success(request, f'Dataset "{dataset.name}" updated successfully!')
            return redirect('datasets:dataset_detail', pk=dataset.pk)
    else:
        form = DatasetForm(instance=dataset)
    
    return render(request, 'datasets/edit.html', {'form': form, 'dataset': dataset})


@login_required
def dataset_delete(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        dataset_name = dataset.name
        dataset.delete()
        messages.success(request, f'Dataset "{dataset_name}" deleted successfully!')
        return redirect('datasets:dataset_list')
    
    return render(request, 'datasets/delete.html', {'dataset': dataset})


@login_required
def dataset_run_rules(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    
    # Trigger Celery task to run all rules for this dataset
    from apps.rules.tasks import run_dataset_rules_task
    task = run_dataset_rules_task.delay(dataset.id)
    
    messages.success(request, f'Rules execution started for dataset "{dataset.name}". Results will be available shortly.')
    # Redirect back to dataset detail with a flag indicating rules were just run
    return redirect('datasets:dataset_detail', pk=dataset.pk)


@login_required
def get_rule_recommendations(request, pk):
    """
    Get rule recommendations for a dataset
    """
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    
    # Check if dataset has a file
    if not dataset.file or not dataset.file.path:
        return JsonResponse({'error': 'Dataset has no file'}, status=400)
    
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
        return JsonResponse({'error': f'Error analyzing dataset: {str(e)}'}, status=500)