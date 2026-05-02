from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'borrows', views.BorrowRecordViewSet, basename='borrow')
router.register(r'users', views.UserViewSet, basename='user')

# Add router URLs
urlpatterns = [
    path('', include(router.urls)),
]
