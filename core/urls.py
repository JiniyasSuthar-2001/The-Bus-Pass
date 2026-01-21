from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Authentication & Home ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    # path('login/', auth_views.LoginView.as_view(), name='login'), # Replaced by custom_login
    path('login/', views.custom_login, name='login'),
    path('google-login/', views.google_login, name='google_login'),
    path('google-callback/', views.google_callback, name='google_callback'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # --- Password Reset Flows (Standard Django) ---
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    
    # --- User Dashboard & Payments ---
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('payment/', views.payment_page, name='payment_page'),
    path('recharge-wallet/', views.recharge_wallet, name='recharge_wallet'),
    
    # --- Admin ---
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-city/', views.add_city, name='add_city'),
    path('delete-city/<int:city_id>/', views.delete_city, name='delete_city'),
    path('add-route/', views.add_route, name='add_route'),
    path('delete-route/<int:route_id>/', views.delete_route, name='delete_route'),
    path('api/routes/', views.get_routes, name='get_routes'),
    path('create-conductor/', views.create_conductor, name='create_conductor'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # --- Conductor & Scanner ---
    path('conductor/login/', views.conductor_login, name='conductor_login'),
    path('conductor-dashboard/', views.conductor_dashboard, name='conductor_dashboard'),
    path('issue-ticket/', views.issue_ticket, name='issue_ticket'),
    path('verify/', views.verify_pass, name='verify_pass'), # Alias for Admin
]
