from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Incident, IncidentComment
from .forms import IncidentUpdateForm, IncidentCommentForm
from django.contrib.auth.models import User


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
    
    # Get comments
    comments = incident.comments.all()
    
    if request.method == 'POST':
        if 'update_incident' in request.POST:
            form = IncidentUpdateForm(request.POST, instance=incident)
            if form.is_valid():
                form.save()
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
            
            if status:
                incidents.update(status=status)
            
            if assigned_to_id:
                assigned_to = User.objects.get(id=assigned_to_id)
                incidents.update(assigned_to=assigned_to)
            
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