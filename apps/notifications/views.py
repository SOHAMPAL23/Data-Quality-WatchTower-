from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Notification, NotificationPreference
from .forms import NotificationPreferencesForm
from django.core.paginator import Paginator


@login_required
def notification_list(request):
    """Display list of notifications for the logged-in user"""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Filter by read/unread
    read_filter = request.GET.get('read')
    if read_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif read_filter == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications/list.html', {
        'page_obj': page_obj,
        'read_filter': read_filter
    })


@login_required
def mark_as_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications:list')


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read for the logged-in user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'All notifications marked as read.'})
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
def notification_preferences(request):
    """Manage notification preferences"""
    preference, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully.')
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferencesForm(instance=preference)
    
    return render(request, 'notifications/preferences.html', {'form': form})