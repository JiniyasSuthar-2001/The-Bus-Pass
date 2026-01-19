from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('payment/', views.payment_page, name='payment_page'),
    path('payment/success/', views.payment_success, name='payment_success'),
    
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-conductor/', views.create_conductor, name='create_conductor'),
    
    path('conductor-dashboard/', views.conductor_dashboard, name='conductor_dashboard'),
    
    path('verify/', views.verify_pass, name='verify_pass'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
