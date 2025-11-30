from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q
import csv
from .models import AuditLog
from apps.audit.utils import create_audit_log


@login_required
def audit_log_list(request):
    """Display list of audit logs with filtering and search"""
    # Get all audit logs, ordered by timestamp (newest first)
    audit_logs = AuditLog.objects.select_related('actor').all().order_by('-timestamp')
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        audit_logs = audit_logs.filter(
            Q(actor__username__icontains=search_query) |
            Q(action_type__icontains=search_query) |
            Q(target_type__icontains=search_query) |
            Q(before__icontains=search_query) |
            Q(after__icontains=search_query)
        )
    
    # Filter by action type
    action_filter = request.GET.get('action')
    if action_filter:
        audit_logs = audit_logs.filter(action_type=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user')
    if user_filter:
        audit_logs = audit_logs.filter(actor__username=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        audit_logs = audit_logs.filter(timestamp__gte=date_from)
    if date_to:
        audit_logs = audit_logs.filter(timestamp__lte=date_to + ' 23:59:59')
    
    # Get unique users for filter dropdown
    users = AuditLog.objects.values_list('actor__username', flat=True).distinct().order_by('actor__username')
    
    # Pagination
    paginator = Paginator(audit_logs, 25)  # Show 25 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': users,
        'search_query': search_query,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'audit/list.html', context)


@login_required
def export_audit_logs_csv(request):
    """Export audit logs as CSV"""
    # Create audit log for the export action
    create_audit_log(
        actor=request.user,
        action_type='EXPORT',
        target_type='AuditLogs',
        target_id=0,
        after={
            'format': 'CSV'
        },
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Get all audit logs
    audit_logs = AuditLog.objects.select_related('actor').all().order_by('-timestamp')
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        audit_logs = audit_logs.filter(
            Q(actor__username__icontains=search_query) |
            Q(action_type__icontains=search_query) |
            Q(target_type__icontains=search_query) |
            Q(before__icontains=search_query) |
            Q(after__icontains=search_query)
        )
    
    # Filter by action type
    action_filter = request.GET.get('action')
    if action_filter:
        audit_logs = audit_logs.filter(action_type=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user')
    if user_filter:
        audit_logs = audit_logs.filter(actor__username=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        audit_logs = audit_logs.filter(timestamp__gte=date_from)
    if date_to:
        audit_logs = audit_logs.filter(timestamp__lte=date_to + ' 23:59:59')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Timestamp', 
        'User', 
        'Action', 
        'Target Type', 
        'Target ID', 
        'IP Address',
        'Before Data',
        'After Data'
    ])
    
    # Write data rows
    for log in audit_logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.actor.username,
            log.get_action_type_display(),
            log.target_type,
            log.target_id,
            log.ip_address or '',
            str(log.before) if log.before else '',
            str(log.after) if log.after else ''
        ])
    
    return response