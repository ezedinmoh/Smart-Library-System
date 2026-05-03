from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_user_management import (
    user_deactivate, user_activate, user_delete,
    batch_deactivate_users, batch_activate_users, batch_delete_users
)
from .forms import CustomPasswordResetForm

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/change-password-ajax/', views.change_password_ajax, name='change_password_ajax'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<str:notification_key>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/delete/<str:notification_key>/', views.delete_notification_view, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications_view, name='clear_all_notifications'),
    path('list/', views.users_list, name='list'),
    path('create/', views.user_create, name='create'),
    path('<int:pk>/detail/', views.user_detail, name='detail'),
    path('<int:pk>/role-change/', views.user_role_change, name='role_change'),
    path('<int:pk>/update-borrow-limit/', views.update_borrow_limit, name='update_borrow_limit'),
    path('<int:pk>/deactivate/', user_deactivate, name='deactivate'),
    path('<int:pk>/activate/', user_activate, name='activate'),
    path('<int:pk>/delete/', user_delete, name='delete'),
    
    # Batch operations
    path('batch/deactivate/', batch_deactivate_users, name='batch_deactivate'),
    path('batch/activate/', batch_activate_users, name='batch_activate'),
    path('batch/delete/', batch_delete_users, name='batch_delete'),
    
    path('export/csv/', views.export_users_csv, name='export_csv'),
    path('export/excel/', views.export_users_excel, name='export_excel'),
    path('export/excel/', views.export_users_excel, name='export_excel'),
    
    # Email verification
    path('verify-email/<str:key>/', views.confirm_email, name='confirm_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # Bulk operations
    path('bulk-import/', views.bulk_import_users, name='bulk_import'),
    path('bulk-import/template/', views.download_user_import_template, name='import_template'),
    path('bulk-email/', views.bulk_email_users, name='bulk_email'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             html_email_template_name='users/password_reset_email_html.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/users/password-reset/done/',
             form_class=CustomPasswordResetForm  # Use custom form for inactive users
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/users/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
