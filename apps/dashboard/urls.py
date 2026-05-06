from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin'),
    path('librarian/', views.librarian_dashboard, name='librarian'),
    path('student/', views.student_dashboard, name='student'),
    path('analytics/', views.analytics, name='analytics'),
    path('reports/', views.reports, name='reports'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/stats/', views.dashboard_stats_api, name='stats_api'),
    
    # New URLs for enhanced features
    path('library-card/<int:user_id>/', views.generate_library_card_view, name='library_card'),
    path('library-card-view/<int:user_id>/', views.view_library_card, name='library_card_view'),
    path('qr-code/<int:book_id>/', views.download_qr_code, name='download_qr'),
    path('export/overdue/csv/', views.export_overdue_csv, name='export_overdue_csv'),
    path('export/overdue/pdf/', views.export_overdue_pdf, name='export_overdue_pdf'),
    path('export/fines/pdf/', views.export_fine_report_pdf, name='export_fine_pdf'),
    path('export/top-books/pdf/', views.export_top_books_pdf, name='export_top_books_pdf'),
    path('export/top-members/pdf/', views.export_top_members_pdf, name='export_top_members_pdf'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('backup/download/<str:backup_file>/', views.download_backup, name='download_backup'),
    path('backup/upload/', views.upload_backup, name='upload_backup'),
    path('backup/delete/<str:backup_file>/', views.delete_backup, name='delete_backup'),
    path('reminders/due/', views.send_due_reminders, name='send_due_reminders'),
    path('reminders/overdue/', views.send_overdue_notifications, name='send_overdue_notifications'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('reservations/', views.reservation_management, name='reservations'),
    path('system/', views.system_administration, name='system_admin'),
    path('system/update-settings/', views.update_system_settings, name='update_system_settings'),
    path('settings/', views.system_settings_view, name='settings'),
    path('test-email/', views.test_email, name='test_email'),
    path('notifications/', views.notification_center, name='notification_center'),
]
