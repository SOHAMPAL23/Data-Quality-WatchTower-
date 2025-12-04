import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import uuid
from .models import Dataset
from apps.rules.models import Rule, RuleRun

logger = logging.getLogger(__name__)


@login_required
def enhanced_dataset_upload(request):
    """
    Render the enhanced dataset upload page
    """
    return render(request, 'datasets/upload_enhanced.html')


@csrf_exempt
def save_enhanced_dataset(request):
    """
    Save dataset and rules from client-side analysis
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parse the JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            
        dataset_name = data.get('dataset_name')
        profile = data.get('profile')
        rules = data.get('rules')
        quality_score = data.get('quality_score', 0)
        
        if not dataset_name or not profile or not rules:
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        # Check if dataset name already exists
        if Dataset.objects.filter(name=dataset_name, owner=request.user).exists():
            return JsonResponse({'error': 'Dataset with this name already exists. Please choose a different name.'}, status=400)
        
        # Create dataset record (without file since it was processed client-side)
        dataset = Dataset.objects.create(
            name=dataset_name,
            description=f"Dataset uploaded with enhanced profiling: {dataset_name}",
            source_type='CSV',
            owner=request.user,
            row_count=profile.get('rowCount', 0),
            column_count=profile.get('columnCount', 0),
            schema=profile.get('columns', {}),
            quality_score=quality_score,
            is_active=True
        )
        
        # Create rules
        created_rules = []
        for rule_data in rules:
            try:
                # Generate DSL expression based on rule type
                dsl_expression = generate_dsl_expression(rule_data)
                
                if dsl_expression:
                    rule = Rule.objects.create(
                        dataset=dataset,
                        owner=request.user,
                        name=f"{rule_data['type']} rule for {rule_data['column']}",
                        description=f"Auto-generated {rule_data['type']} rule for column {rule_data['column']}",
                        rule_type=rule_data['type'],
                        dsl_expression=dsl_expression,
                        severity=rule_data.get('severity', 'MEDIUM'),
                        is_active=True
                    )
                    created_rules.append({
                        'id': rule.id,
                        'name': rule.name,
                        'type': rule.rule_type
                    })
            except Exception as e:
                logger.error(f"Error creating rule: {str(e)}")
                continue
        
        # Create initial rule runs for dashboard visualization
        initial_rule_runs = []
        for rule in Rule.objects.filter(dataset=dataset):
            try:
                # Ensure unique run_id
                run_id = f"initial_run_{rule.id}_{uuid.uuid4().hex[:8]}"
                
                rule_run = RuleRun.objects.create(
                    rule=rule,
                    dataset=dataset,
                    run_id=run_id,
                    started_at=timezone.now(),
                    finished_at=timezone.now(),
                    status='COMPLETED',
                    total_rows=dataset.row_count or 0,
                    passed_count=dataset.row_count or 0,  # Initially assume all pass
                    failed_count=0,
                    sample_evidence=[]
                )
                initial_rule_runs.append(rule_run.id)
            except Exception as e:
                logger.error(f"Error creating initial rule run: {str(e)}")
                continue
        
        logger.info(f"Created dataset {dataset.id} with {len(created_rules)} rules and {len(initial_rule_runs)} runs")
        
        return JsonResponse({
            'success': True,
            'dataset_id': dataset.id,
            'rules_created': len(created_rules),
            'rules': created_rules
        })
        
    except Exception as e:
        logger.error(f"Error saving enhanced dataset: {str(e)}")
        return JsonResponse({'error': f'Error saving dataset: {str(e)}'}, status=500)


def generate_dsl_expression(rule_data):
    """
    Generate DSL expression from rule data
    """
    rule_type = rule_data['type']
    column = rule_data['column']
    
    if rule_type == 'NOT_NULL':
        return f'NOT_NULL("{column}")'
    elif rule_type == 'UNIQUE':
        return f'UNIQUE("{column}")'
    elif rule_type == 'IN_RANGE':
        params = rule_data.get('params', {})
        min_val = params.get('min')
        max_val = params.get('max')
        if min_val is not None and max_val is not None:
            return f'IN_RANGE("{column}", {min_val}, {max_val})'
    elif rule_type == 'REGEX':
        params = rule_data.get('params', {})
        pattern = params.get('pattern')
        if pattern:
            # Escape quotes in pattern
            escaped_pattern = pattern.replace('"', '\\"')
            return f'REGEX("{column}", "{escaped_pattern}")'
    elif rule_type == 'LENGTH_RANGE':
        params = rule_data.get('params', {})
        min_length = params.get('min_length')
        max_length = params.get('max_length')
        if min_length is not None and max_length is not None:
            return f'LENGTH_RANGE("{column}", {min_length}, {max_length})'
    
    return None