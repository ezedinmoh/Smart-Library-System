from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.books.models import Book, Category
from apps.borrow.models import BorrowRecord
from apps.users.models import User
from apps.users.permissions import IsAdmin, IsLibrarianOrAdmin, IsStudent, IsOwnerOrLibrarianOrAdmin
from .serializers import (
    BookSerializer, CategorySerializer, BorrowRecordSerializer,
    UserSerializer, UserDetailSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for book categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class BookViewSet(viewsets.ModelViewSet):
    """
    API endpoint for books with search and filtering.
    """
    queryset = Book.objects.select_related('category').prefetch_related('reviews')
    serializer_class = BookSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['category', 'language']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'author', 'times_borrowed', 'rating', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only librarians and admins can modify books
            permission_classes = [IsLibrarianOrAdmin]
        else:
            # All authenticated users can view books
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter based on user permissions"""
        return self.queryset
    
    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        """Borrow a book"""
        book = self.get_object()
        serializer = BorrowRecordSerializer(
            data={'book_id': book.id},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available books"""
        queryset = self.get_queryset().filter(available_copies__gt=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BorrowRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for borrow records.
    """
    serializer_class = BorrowRecordSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['status', 'user']
    search_fields = ['book__title', 'user__username']
    ordering_fields = ['borrow_date', 'due_date', 'status']
    ordering = ['-borrow_date']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create']:
            # Students can create borrow records (request books)
            permission_classes = [IsStudent]
        elif self.action in ['update', 'partial_update', 'destroy', 'return_book']:
            # Only librarians and admins can modify borrow records
            permission_classes = [IsLibrarianOrAdmin]
        else:
            # All authenticated users can view (filtered by get_queryset)
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Return records based on user role"""
        user = self.request.user
        if user.is_admin or user.is_librarian:
            return BorrowRecord.objects.all().select_related('user', 'book')
        return BorrowRecord.objects.filter(user=user).select_related('user', 'book')
    
    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """Return a borrowed book"""
        record = self.get_object()
        
        if record.status != 'borrowed':
            return Response(
                {'error': 'This book has already been returned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        record.return_book()
        serializer = self.get_serializer(record)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue books"""
        if not request.user.is_admin and not request.user.is_librarian:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(status='overdue')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_borrows(self, request):
        """Get user's borrow records"""
        queryset = BorrowRecord.objects.filter(user=request.user).select_related('book')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new borrow record"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for users. Admin and Librarian only.
    """
    queryset = User.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'created_at']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            # Only admins and librarians can view user lists
            permission_classes = [IsLibrarianOrAdmin]
        else:
            # All authenticated users can access 'me' endpoint
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Return all users for admin/librarian, only self for students"""
        user = self.request.user
        if user.is_admin or user.is_librarian:
            return self.queryset
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
