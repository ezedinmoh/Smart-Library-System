from django.urls import path
from . import views

app_name = 'borrow'

urlpatterns = [
    # Student actions
    path('request-list/', views.request_list, name='request_list'),
    path('request/<int:book_pk>/', views.request_book, name='request_book'),
    path('request/<int:request_pk>/cancel/', views.cancel_request, name='cancel_request'),
    path('request/<int:request_pk>/delete/', views.delete_request, name='delete_request'),
    path('requests/clear-rejected/', views.clear_rejected_requests, name='clear_rejected'),
    path('requests/clear-cancelled/', views.clear_cancelled_requests, name='clear_cancelled'),
    path('my-books/', views.my_borrowed_books, name='my_books'),
    path('history/', views.borrow_history, name='history'),
    path('record/<int:record_pk>/student-return/', views.student_return_book, name='student_return'),
    
    # Librarian/Admin actions
    path('pending-requests/', views.pending_requests, name='pending_requests'),
    path('approve-request/<int:request_pk>/', views.approve_request, name='approve_request'),
    path('reject-request/<int:request_pk>/', views.reject_request, name='reject_request'),
    path('issue-return/', views.issue_return, name='issue_return'),
    path('issue/<int:book_pk>/<int:user_pk>/', views.issue_book, name='issue_book'),
    path('record/<int:record_pk>/return/', views.return_book, name='return_book'),
    path('all-records/', views.all_borrow_records, name='all_records'),
    
    # Admin only
    path('overdue/', views.overdue_management, name='overdue'),
    path('export/csv/', views.export_borrow_records_csv, name='export_csv'),
    path('export/excel/', views.export_borrow_records_excel, name='export_excel'),
    path('export/excel/', views.export_borrow_records_excel, name='export_excel'),
    
    # Legacy (for backward compatibility)
    path('book/<int:book_pk>/', views.borrow_book, name='borrow_book'),
]
