from rest_framework import serializers
from apps.books.models import Book, Category, BookReview
from apps.borrow.models import BorrowRecord
from apps.users.models import User, UserProfile


class CategorySerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'book_count']
    
    def get_book_count(self, obj):
        return obj.books.count()


class BookReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = BookReview
        fields = ['id', 'user', 'rating', 'review_text', 'created_at']


class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    reviews = BookReviewSerializer(many=True, read_only=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'isbn', 'title', 'author', 'description',
            'category', 'category_id', 'total_copies', 'available_copies',
            'publisher', 'publication_date', 'pages', 'language',
            'rating', 'times_borrowed', 'is_available', 'reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['times_borrowed', 'created_at', 'updated_at']
    
    def get_is_available(self, obj):
        return obj.is_available()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['max_books_allowed', 'currently_borrowed', 'total_fines']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'profile']
        read_only_fields = ['id']


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'role', 'profile', 'created_at'
        ]


class BorrowRecordSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        write_only=True
    )
    days_remaining = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = BorrowRecord
        fields = [
            'id', 'user', 'book', 'book_id', 'borrow_date',
            'due_date', 'return_date', 'status', 'fine_amount',
            'fine_paid', 'days_remaining', 'days_overdue'
        ]
        read_only_fields = ['id', 'borrow_date', 'status', 'fine_amount']
    
    def get_days_remaining(self, obj):
        return obj.get_days_remaining()
    
    def get_days_overdue(self, obj):
        return obj.get_days_overdue()
    
    def create(self, validated_data):
        """Create a new borrow record"""
        user = self.context['request'].user
        book = validated_data['book']
        
        # Check availability
        if not book.is_available():
            raise serializers.ValidationError('Book is not available for borrowing.')
        
        # Check borrow limit
        if not user.profile.can_borrow():
            raise serializers.ValidationError('You have reached the borrowing limit.')
        
        # Check if already borrowed
        if BorrowRecord.objects.filter(user=user, book=book, status='borrowed').exists():
            raise serializers.ValidationError('You have already borrowed this book.')
        
        borrow_record = BorrowRecord.objects.create(
            user=user,
            book=book,
            **{k: v for k, v in validated_data.items() if k != 'book'}
        )
        
        # Update availability
        book.borrow_book()
        user.profile.currently_borrowed += 1
        user.profile.save()
        
        return borrow_record
