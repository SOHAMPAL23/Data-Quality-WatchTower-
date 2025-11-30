from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from apps.audit.utils import create_audit_log


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Create audit log
            create_audit_log(
                actor=user,
                action_type='CREATE',
                target_type='User',
                target_id=user.id,
                after={
                    'username': username,
                    'email': user.email,
                    'role': user.role
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Account created for {username}!')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Create audit log
            create_audit_log(
                actor=user,
                action_type='RUN',
                target_type='UserLogin',
                target_id=user.id,
                after={
                    'username': username,
                    'role': user.role
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return redirect('dashboard:dashboard_home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/login.html')


def viewer_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user has viewer role
            if user.role == 'viewer':
                login(request, user)
                
                # Create audit log
                create_audit_log(
                    actor=user,
                    action_type='RUN',
                    target_type='UserLogin',
                    target_id=user.id,
                    after={
                        'username': username,
                        'role': user.role
                    },
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return redirect('dashboard:dashboard_home')
            else:
                messages.error(request, 'This login page is for viewers only. Please use the admin login.')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/viewer_login.html')


@login_required
def user_logout(request):
    # Create audit log before logout
    create_audit_log(
        actor=request.user,
        action_type='RUN',
        target_type='UserLogout',
        target_id=request.user.id,
        after={
            'username': request.user.username,
            'role': request.user.role
        },
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard:dashboard_home')


@login_required
def profile(request):
    """User profile page"""
    return render(request, 'users/profile.html', {'user': request.user})