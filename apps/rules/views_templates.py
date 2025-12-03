from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import RuleTemplate, Rule
from apps.datasets.models import Dataset
from .forms import RuleFromTemplateForm

@login_required
def template_list(request):
    """Display list of available rule templates"""
    templates = RuleTemplate.objects.filter(is_active=True).order_by('template_type', 'name')
    
    # Group templates by type for better presentation
    template_groups = {}
    for template in templates:
        if template.template_type not in template_groups:
            template_groups[template.template_type] = []
        template_groups[template.template_type].append(template)
    
    return render(request, 'rules/template_list.html', {
        'template_groups': template_groups
    })

@login_required
def template_detail(request, template_id):
    """Display template details and form to create rule from template"""
    template = get_object_or_404(RuleTemplate, id=template_id, is_active=True)
    
    if request.method == 'POST':
        form = RuleFromTemplateForm(request.POST, template=template, user=request.user)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.owner = request.user
            rule.save()
            
            messages.success(request, f'Rule "{rule.name}" created successfully from template!')
            return redirect('rules:rule_detail', rule_id=rule.id)
    else:
        # Pre-populate form with template defaults
        initial_data = {
            'severity': template.severity,
            'description': template.description,
        }
        form = RuleFromTemplateForm(template=template, user=request.user, initial=initial_data)
    
    return render(request, 'rules/template_detail.html', {
        'template': template,
        'form': form
    })

@login_required
def get_template_dsl(request, template_id):
    """API endpoint to get DSL template for a given template"""
    template = get_object_or_404(RuleTemplate, id=template_id, is_active=True)
    
    return JsonResponse({
        'dsl_template': template.dsl_template,
        'description': template.description
    })