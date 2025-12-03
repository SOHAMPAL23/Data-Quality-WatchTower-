from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Incident, IncidentComment
from .forms import IncidentUpdateForm, IncidentCommentForm
from apps.rules.models import Rule
from apps.datasets.models import Dataset
from django.contrib.auth.models import User
from django.http import JsonResponse


@login_required
def create_incident(request):
    """Create a new incident with enhanced features"""
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        severity = request.POST.get('severity')
        rule_id = request.POST.get('rule')
        dataset_id = request.POST.get('dataset')
        assigned_to_id = request.POST.get('assigned_to')
        
        # Validate required fields
        if not title or not description or not severity:
            messages.error(request, 'Title, description, and severity are required.')
            return render(request, 'incidents/create_enhanced.html', {
                'rules': Rule.objects.filter(is_active=True),
                'datasets': Dataset.objects.filter(is_active=True),
                'users': User.objects.all(),
            })
        
        # Create incident
        try:
            rule = Rule.objects.get(id=rule_id) if rule_id else None
            dataset = Dataset.objects.get(id=dataset_id) if dataset_id else None
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            incident = Incident.objects.create(
                title=title,
                description=description,
                severity=severity,
                rule=rule,
                dataset=dataset,
                assigned_to=assigned_to,
                status='OPEN',
            )
            
            messages.success(request, f'Incident "{incident.title}" created successfully!')
            return redirect('incidents:incident_detail', pk=incident.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating incident: {str(e)}')
            return render(request, 'incidents/create_enhanced.html', {
                'rules': Rule.objects.filter(is_active=True),
                'datasets': Dataset.objects.filter(is_active=True),
                'users': User.objects.all(),
            })
    
    return render(request, 'incidents/create_enhanced.html', {
        'rules': Rule.objects.filter(is_active=True),
        'datasets': Dataset.objects.filter(is_active=True),
        'users': User.objects.all(),
    })


@login_required
def incident_dashboard(request):
    """Dashboard view for incidents with summary statistics"""
    # Get filter parameters
    status_filter = request.GET.get('status')
    severity_filter = request.GET.get('severity')
    assigned_to_filter = request.GET.get('assigned_to')
    
    # Base queryset
    incidents = Incident.objects.all()
    
    # Apply filters
    if status_filter:
        incidents = incidents.filter(status=status_filter)
    if severity_filter:
        incidents = incidents.filter(severity=severity_filter)
    if assigned_to_filter:
        incidents = incidents.filter(assigned_to_id=assigned_to_filter)
    
    # Summary statistics
    total_incidents = incidents.count()
    open_incidents = incidents.filter(status='OPEN').count()
    resolved_incidents = incidents.filter(status='RESOLVED').count()
    critical_incidents = incidents.filter(severity='CRITICAL').count()
    
    # Recent incidents
    recent_incidents = Incident.objects.select_related('rule', 'dataset', 'assigned_to').order_by('-created_at')[:10]
    
    # Incidents by severity
    severity_counts = {
        'CRITICAL': Incident.objects.filter(severity='CRITICAL').count(),
        'HIGH': Incident.objects.filter(severity='HIGH').count(),
        'MEDIUM': Incident.objects.filter(severity='MEDIUM').count(),
        'LOW': Incident.objects.filter(severity='LOW').count(),
    }
    
    # Incidents by status
    status_counts = {
        'OPEN': Incident.objects.filter(status='OPEN').count(),
        'ACKNOWLEDGED': Incident.objects.filter(status='ACKNOWLEDGED').count(),
        'RESOLVED': Incident.objects.filter(status='RESOLVED').count(),
        'MUTED': Incident.objects.filter(status='MUTED').count(),
    }
    
    # Pagination
    paginator = Paginator(incidents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'incidents/dashboard.html', {
        'page_obj': page_obj,
        'total_incidents': total_incidents,
        'open_incidents': open_incidents,
        'resolved_incidents': resolved_incidents,
        'critical_incidents': critical_incidents,
        'recent_incidents': recent_incidents,
        'severity_counts': severity_counts,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'assigned_to_filter': assigned_to_filter,
        'users': User.objects.all(),
    })


@login_required
def incident_bulk_assign(request):
    """Bulk assign incidents to users"""
    if request.method == 'POST':
        incident_ids = request.POST.getlist('incident_ids')
        assigned_to_id = request.POST.get('assigned_to')
        
        if incident_ids and assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
                updated_count = Incident.objects.filter(id__in=incident_ids).update(
                    assigned_to=assigned_to,
                    updated_at=timezone.now()
                )
                messages.success(request, f'Assigned {updated_count} incidents to {assigned_to.username}.')
            except User.DoesNotExist:
                messages.error(request, 'Selected user does not exist.')
        else:
            messages.warning(request, 'Please select incidents and a user to assign.')
    
    return redirect('incidents:incident_list')


@login_required
def incident_bulk_resolve(request):
    """Bulk resolve incidents"""
    if request.method == 'POST':
        incident_ids = request.POST.getlist('incident_ids')
        
        if incident_ids:
            updated_count = Incident.objects.filter(id__in=incident_ids).update(
                status='RESOLVED',
                resolved_at=timezone.now(),
                updated_at=timezone.now()
            )
            messages.success(request, f'Resolved {updated_count} incidents.')
        else:
            messages.warning(request, 'Please select incidents to resolve.')
    
    return redirect('incidents:incident_list')


@login_required
def incident_api_stats(request):
    """API endpoint for incident statistics"""
    # Get statistics
    total_incidents = Incident.objects.count()
    open_incidents = Incident.objects.filter(status='OPEN').count()
    critical_incidents = Incident.objects.filter(severity='CRITICAL').count()
    
    # Incidents by severity
    severity_data = []
    for severity, _ in Incident.SEVERITY_CHOICES:
        count = Incident.objects.filter(severity=severity).count()
        severity_data.append({
            'severity': severity,
            'count': count
        })
    
    # Incidents by status
    status_data = []
    for status, _ in Incident.STATUS_CHOICES:
        count = Incident.objects.filter(status=status).count()
        status_data.append({
            'status': status,
            'count': count
        })
    
    return JsonResponse({
        'total_incidents': total_incidents,
        'open_incidents': open_incidents,
        'critical_incidents': critical_incidents,
        'severity_data': severity_data,
        'status_data': status_data,
    })