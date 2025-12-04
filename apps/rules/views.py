from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Rule, RuleRun
from .forms import RuleForm
from apps.datasets.models import Dataset
from apps.audit.utils import log_rule_update


@login_required
def rule_list(request):
    rules = Rule.objects.filter(owner=request.user)
    
    # Filter by dataset
    dataset_id = request.GET.get('dataset')
    if dataset_id:
        rules = rules.filter(dataset_id=dataset_id)
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        rules = rules.filter(name__icontains=search_query)
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        rules = rules.filter(is_active=True)
    elif active_filter == 'false':
        rules = rules.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(rules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get datasets for filter dropdown
    datasets = Dataset.objects.filter(owner=request.user)
    
    return render(request, 'rules/list.html', {
        'page_obj': page_obj,
        'datasets': datasets,
        'search_query': search_query,
        'dataset_filter': dataset_id,
        'active_filter': active_filter,
    })


@login_required
def rule_run_list(request):
    # Get all rule runs with related rule and dataset info
    rule_runs = RuleRun.objects.select_related('rule', 'rule__dataset').all()
    
    # Filter by rule name
    rule_name_filter = request.GET.get('rule_name')
    if rule_name_filter:
        rule_runs = rule_runs.filter(rule__name__icontains=rule_name_filter)
    
    # Filter by status (based on failed count)
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'passed':
            rule_runs = rule_runs.filter(failed_count=0)
        elif status_filter == 'failed':
            rule_runs = rule_runs.exclude(failed_count=0)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        rule_runs = rule_runs.filter(started_at__date__gte=date_from)
    if date_to:
        rule_runs = rule_runs.filter(started_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(rule_runs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'rules/runs_list.html', {
        'page_obj': page_obj,
        'rule_name_filter': rule_name_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def rule_create(request):
    if request.method == 'POST':
        form = RuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.owner = request.user
            rule.save()
            messages.success(request, f'Rule "{rule.name}" created successfully!')
            return redirect('rules:rule_list')
    else:
        form = RuleForm()
    
    return render(request, 'rules/create.html', {'form': form})


@login_required
def rule_detail(request, pk):
    rule = get_object_or_404(Rule, pk=pk, owner=request.user)
    
    # Get recent rule runs
    rule_runs = rule.runs.all()[:10]
    
    return render(request, 'rules/detail.html', {
        'rule': rule,
        'rule_runs': rule_runs,
    })


@login_required
def rule_edit(request, pk):
    rule = get_object_or_404(Rule, pk=pk, owner=request.user)
    
    # Capture the state before update for audit logging
    before_state = {
        'name': rule.name,
        'description': rule.description,
        'rule_type': rule.rule_type,
        'dsl_expression': rule.dsl_expression,
        'severity': rule.severity,
        'is_active': rule.is_active
    }
    
    if request.method == 'POST':
        form = RuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save()
            
            # Log rule update activity
            after_state = {
                'name': rule.name,
                'description': rule.description,
                'rule_type': rule.rule_type,
                'dsl_expression': rule.dsl_expression,
                'severity': rule.severity,
                'is_active': rule.is_active
            }
            
            log_rule_update(
                user=request.user,
                rule=rule,
                before_state=before_state,
                after_state=after_state,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Rule "{rule.name}" updated successfully!')
            return redirect('rules:rule_detail', pk=rule.pk)
    else:
        form = RuleForm(instance=rule)
    
    return render(request, 'rules/edit.html', {'form': form, 'rule': rule})


@login_required
def rule_delete(request, pk):
    rule = get_object_or_404(Rule, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        rule_name = rule.name
        rule.delete()
        messages.success(request, f'Rule "{rule_name}" deleted successfully!')
        return redirect('rules:rule_list')
    
    return render(request, 'rules/delete.html', {'rule': rule})


@login_required
def rule_toggle_active(request, pk):
    rule = get_object_or_404(Rule, pk=pk, owner=request.user)
    
    # Capture the state before update for audit logging
    before_state = {
        'is_active': rule.is_active
    }
    
    rule.is_active = not rule.is_active
    rule.save()
    
    # Log rule update activity
    after_state = {
        'is_active': rule.is_active
    }
    
    log_rule_update(
        user=request.user,
        rule=rule,
        before_state=before_state,
        after_state=after_state,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    status = "activated" if rule.is_active else "deactivated"
    messages.success(request, f'Rule "{rule.name}" {status} successfully!')
    return redirect('rules:rule_list')


@login_required
def rule_run(request, pk):
    rule = get_object_or_404(Rule, pk=pk, owner=request.user)
    
    # Trigger Celery task to run this rule
    from .tasks import run_single_rule_task
    task = run_single_rule_task.delay(rule.id)
    
    messages.success(request, f'Rule "{rule.name}" execution started. Check back later for results.')
    return redirect('rules:rule_detail', pk=rule.pk)


@login_required
def create_rule_from_recommendation(request):
    """
    Create a rule from a recommendation
    """
    if request.method == 'POST':
        dataset_id = request.POST.get('dataset_id')
        rule_type = request.POST.get('rule_type')
        column = request.POST.get('column')
        
        # Get dataset
        dataset = get_object_or_404(Dataset, pk=dataset_id, owner=request.user)
        
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
            dsl_expression = f'IN_RANGE("{column}", 0, 1000000)'  # Default range
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
            owner=request.user,
            is_active=True
        )
        
        messages.success(request, f'Rule "{rule.name}" created successfully!')
        return redirect('datasets:dataset_list')
    
    return redirect('dashboard:dashboard_home')