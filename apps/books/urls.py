from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.books_list, name='list'),
    path('<int:pk>/', views.book_detail, name='detail'),
    path('create/', views.book_create, name='create'),
    path('<int:pk>/edit/', views.book_edit, name='edit'),
    path('<int:pk>/delete/', views.book_delete, name='delete'),
    path('<int:book_pk>/review/', views.add_review, name='add_review'),
    path('review/<int:review_pk>/delete/', views.delete_review, name='delete_review'),
    path('<int:pk>/read/', views.read_pdf, name='read_pdf'),
    path('<int:pk>/pdf/', views.serve_pdf, name='serve_pdf'),
    path('<int:pk>/recommendations/', views.get_book_recommendations, name='recommendations'),
    path('recommendations/', views.book_recommendations, name='user_recommendations'),
    path('manage-stock/', views.manage_stock, name='manage_stock'),
    path('export/csv/', views.export_books_csv, name='export_csv'),
    
    path('categories/', views.categories_list, name='categories'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    
    # Bulk operations
    path('bulk-import/', views.bulk_import_books, name='bulk_import'),
    path('bulk-import/template/', views.download_import_template, name='import_template'),
]
