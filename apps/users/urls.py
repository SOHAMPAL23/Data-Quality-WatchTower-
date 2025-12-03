from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    # Remove viewer login path as it's not needed
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]