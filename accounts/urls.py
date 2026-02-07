from django.urls import path
from .views import register, user_login, user_logout, home, password_reset, user_dashboard, profile_settings
from .views import first_time_email, first_time_set_password
from .views import admin_dashboard, trainer_list, trainer_add, trainer_edit, trainer_delete, member_list, member_add, member_edit, member_delete
from .views import trainer_dashboard, admin_reports, admin_reports_pdf, pay_pending_payment, cancel_payment
from .views import track_progress, log_weight, delete_weight_log, weight_chart_data

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('password-reset', password_reset, name='password-reset'),
    path('first-time/email/', first_time_email, name='first-time-email'),
    path('first-time/set-password/', first_time_set_password, name='first-time-set-password'),
    path('', home, name='home'), 

    # User stuff
    path('user-dashboard/', user_dashboard, name='user-dashboard'),
    path('profile/', profile_settings, name='profile'),
    path('profile-settings/', profile_settings, name='profile-settings'),
    path('browse-plans/', user_dashboard, name='browse-plans'),
    path('payment/<int:payment_id>/pay/', pay_pending_payment, name='pay-pending'),
    path('payment/<int:payment_id>/cancel/', cancel_payment, name='cancel-payment'),
    
    # Weight Tracking
    path('track-progress/', track_progress, name='track-progress'),
    path('log-weight/', log_weight, name='log-weight'),
    path('weight-log/<int:log_id>/delete/', delete_weight_log, name='delete-weight-log'),
    path('api/weight-chart-data/', weight_chart_data, name='weight-chart-data'),

    
    # Admin stuff
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),


    # Admin's trainer management
    path('admin-dashboard/trainers/', trainer_list, name='admin-trainers'),
    path('admin-dashboard/trainers/add/', trainer_add, name='admin-trainer-add'),
    path('admin-dashboard/trainers/edit/<int:trainer_id>/', trainer_edit, name='trainer-edit'),
    path('admin-dashboard/trainers/delete/<int:trainer_id>/', trainer_delete, name='trainer-delete'),



    # path('admin-payments/', admin_dashboard, name='admin-payments'),
    path('admin-reports/', admin_reports, name='admin-reports'),
    path('admin-reports/pdf/', admin_reports_pdf, name='admin-reports-pdf'),

    # Admin's members management
    path('admin-dashboard/members/', member_list, name='admin-members'),
    path('admin-dashboard/members/add/', member_add, name='admin-members-add'),
    path('admin-dashboard/members/edit/<int:member_id>/', member_edit, name='admin-members-edit'),
    path('admin-dashboard/members/delete/<int:member_id>/', member_delete, name='admin-members-delete'),

    
    # Trainer stuff
    path('trainer-dashboard/', trainer_dashboard, name='trainer-dashboard'),
]
