from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Incident
from apps.rules.models import Rule
from apps.datasets.models import Dataset

User = get_user_model()


@login_required
def incident_list(request):
    incidents = Incident.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        incidents = incidents.filter(status=status_filter)
    
    # Filter by severity
    severity_filter = request.GET.get('severity')
    if severity_filter:
        incidents = incidents.filter(severity=severity_filter)
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        incidents = incidents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(rule__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(incidents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'incidents/list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'search_query': search_query,
    })


@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    
    # Capture the state before update for audit logging
    before_state = {
        'status': incident.status,
        'severity': incident.severity,
        'assigned_to': incident.assigned_to.username if incident.assigned_to else None
    }
    
    # Get comments
    comments = incident.comments.all()
    
    if request.method == 'POST':
        if 'update_incident' in request.POST:
            form = IncidentUpdateForm(request.POST, instance=incident)
            if form.is_valid():
                old_status = incident.status
                incident = form.save(commit=False)
                
                # Handle status changes
                if old_status != incident.status:
                    if incident.status == 'RESOLVED' and not incident.resolved_at:
                        incident.resolved_at = timezone.now()
                    elif incident.status == 'ACKNOWLEDGED' and not incident.acknowledged_at:
                        incident.acknowledged_at = timezone.now()
                
                incident.save()
                
                # Log incident update activity
                after_state = {
                    'status': incident.status,
                    'severity': incident.severity,
                    'assigned_to': incident.assigned_to.username if incident.assigned_to else None
                }
                
                log_incident_update(
                    user=request.user,
                    incident=incident,
                    before_state=before_state,
                    after_state=after_state,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, 'Incident updated successfully!')
                return redirect('incidents:incident_detail', pk=incident.pk)
        elif 'add_comment' in request.POST:
            comment_form = IncidentCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.incident = incident
                comment.author = request.user
                comment.save()
                messages.success(request, 'Comment added successfully!')
                return redirect('incidents:incident_detail', pk=incident.pk)
    else:
        form = IncidentUpdateForm(instance=incident)
        comment_form = IncidentCommentForm()
    
    return render(request, 'incidents/detail.html', {
        'incident': incident,
        'form': form,
        'comment_form': comment_form,
        'comments': comments,
    })


@login_required
def incident_bulk_update(request):
    if request.method == 'POST':
        incident_ids = request.POST.getlist('incident_ids')
        status = request.POST.get('status')
        assigned_to_id = request.POST.get('assigned_to')
        
        if incident_ids:
            incidents = Incident.objects.filter(id__in=incident_ids)
            
            # Log updates for each incident
            for incident in incidents:
                before_state = {
                    'status': incident.status,
                    'assigned_to': incident.assigned_to.username if incident.assigned_to else None
                }
                
                if status:
                    incident.status = status
                
                if assigned_to_id:
                    assigned_to = User.objects.get(id=assigned_to_id)
                    incident.assigned_to = assigned_to
                
                incident.save()
                
                after_state = {
                    'status': incident.status,
                    'assigned_to': incident.assigned_to.username if incident.assigned_to else None
                }
                
                log_incident_update(
                    user=request.user,
                    incident=incident,
                    before_state=before_state,
                    after_state=after_state,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            
            messages.success(request, f'Updated {incidents.count()} incidents.')
        else:
            messages.warning(request, 'No incidents selected.')
    
    return redirect('incidents:incident_list')


@login_required
def incident_evidence(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    
    # Parse evidence JSON
    import json
    evidence_data = []
    if incident.evidence:
        try:
            evidence_data = json.loads(incident.evidence)
        except json.JSONDecodeError:
            pass
    
    return render(request, 'incidents/evidence.html', {
        'incident': incident,
        'evidence_data': evidence_data,
    })