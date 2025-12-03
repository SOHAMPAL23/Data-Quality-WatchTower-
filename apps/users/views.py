from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from apps.audit.utils import log_user_login, log_user_logout


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            messages.success(request, f'Account created for {username}!')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    # Use the modern template
    return render(request, 'users/register_modern.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Log user login activity
                log_user_login(user, request.META.get('REMOTE_ADDR'))
                
                return redirect('dashboard:enhanced_dashboard')  # Redirect to enhanced dashboard
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = CustomAuthenticationForm()
    # Use the modern template
    return render(request, 'users/login_modern.html', {'form': form})


# Remove the viewer_login function as it's not needed

@login_required
def user_logout(request):
    # Log user logout activity before logout
    log_user_logout(request.user, request.META.get('REMOTE_ADDR'))
    
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard:public_home')


@login_required
def profile(request):
    """User profile page"""
    return render(request, 'users/profile.html', {'user': request.user})