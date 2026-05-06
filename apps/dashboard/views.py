from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
from ..books.models import Book, Category
from ..borrow.models import BorrowRecord, BookRequest
from ..users.models import User
from ..users.permissions import admin_required, librarian_or_admin_required, student_required
from .utils import _send_notification_email

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    # Basic counts
    total_books = Book.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # User role breakdown
    admin_count = User.objects.filter(role='admin').count()
    librarian_count = User.objects.filter(role='librarian').count()
    student_count = User.objects.filter(role='student').count()
    
    # Book statistics
    available_books = Book.objects.filter(available_copies__gt=0).count()
    unavailable_books = Book.objects.filter(available_copies=0).count()
    total_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
    
    # Borrow statistics
    total_borrows = BorrowRecord.objects.count()
    active_borrows = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    overdue_books = BorrowRecord.objects.filter(status='overdue').count()
    returned_books = BorrowRecord.objects.filter(status='returned').count()
    
    # Pending requests
    pending_requests = BookRequest.objects.filter(status='pending').count()
    
    # Financial data
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(
        total=Sum('fine_amount'))['total'] or 0
    unpaid_fines = BorrowRecord.objects.filter(
        fine_amount__gt=0, fine_paid=False
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    # Recent activity
    recent_borrows = BorrowRecord.objects.select_related('user', 'book').order_by('-borrow_date')[:10]
    recent_returns = BorrowRecord.objects.filter(status='returned').select_related('user', 'book').order_by('-return_date')[:10]
    
    # Most popular books
    most_borrowed = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]
    
    # Monthly statistics for charts
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    monthly_borrows = BorrowRecord.objects.filter(
        borrow_date__gte=last_30_days
    ).extra(
        select={'day': 'date(borrow_date)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    context = {
        # Basic stats
        'total_books': total_books,
        'total_categories': total_categories,
        'total_users': total_users,
        'active_users': active_users,
        
        # User breakdown
        'admin_count': admin_count,
        'librarian_count': librarian_count,
        'student_count': student_count,
        
        # Book stats
        'available_books': available_books,
        'unavailable_books': unavailable_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        
        # Borrow stats
        'total_borrows': total_borrows,
        'active_borrows': active_borrows,
        'overdue_books': overdue_books,
        'returned_books': returned_books,
        'pending_requests': pending_requests,
        
        # Financial
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        
        # Recent activity
        'recent_borrows': recent_borrows,
        'recent_returns': recent_returns,
        'most_borrowed': most_borrowed,
        
        # Chart data
        'monthly_borrows': list(monthly_borrows),
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


def home(request):
    """Home/Landing page - accessible to everyone, but redirect authenticated users to their dashboard"""
    # Redirect authenticated users to their role-specific dashboard
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('dashboard:admin')
        elif request.user.is_librarian:
            return redirect('dashboard:librarian')
        elif request.user.is_student:
            return redirect('dashboard:student')
    
    # Get statistics for landing page
    from django.db.models import Count, Sum
    from datetime import timedelta
    
    total_books = Book.objects.count()
    total_users = User.objects.filter(is_active=True).count()
    
    # Calculate daily borrows (average or today's count)
    today = timezone.now().date()
    daily_borrows = BorrowRecord.objects.filter(borrow_date__date=today).count()
    
    # If no borrows today, show average from last 30 days
    if daily_borrows == 0:
        last_30_days = today - timedelta(days=30)
        total_borrows_30_days = BorrowRecord.objects.filter(borrow_date__date__gte=last_30_days).count()
        daily_borrows = total_borrows_30_days // 30 if total_borrows_30_days > 0 else 0
    
    # Get category statistics
    categories_stats = Category.objects.annotate(
        book_count=Count('books')
    ).order_by('-book_count')[:6]
    
    # Get featured books for the landing page (for non-authenticated users)
    featured_books = Book.objects.filter(
        available_copies__gt=0
    ).select_related('category').order_by('-times_borrowed', '-rating')[:6]
    
    # Get 3 books for hero floating animation (top 3 most popular)
    hero_books = Book.objects.select_related('category').order_by('-times_borrowed', '-rating')[:3]
    
    context = {
        'total_books': total_books,
        'total_users': total_users,
        'daily_borrows': daily_borrows,
        'categories_stats': categories_stats,
        'featured_books': featured_books,
        'hero_books': hero_books,
        'borrowed_books': [],
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
@librarian_or_admin_required
def librarian_dashboard(request):
    """Librarian dashboard with operational statistics"""
    # Book management stats
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available_copies__gt=0).count()
    low_stock_books = Book.objects.filter(available_copies__lte=2, available_copies__gt=0)
    out_of_stock_books = Book.objects.filter(available_copies=0).count()
    
    # Borrow management stats
    active_borrows = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    overdue_books = BorrowRecord.objects.filter(status='overdue').count()
    pending_requests = BookRequest.objects.filter(status='pending').count()
    approved_requests = BookRequest.objects.filter(status='approved').count()
    
    # Today's activity
    today = timezone.now().date()
    todays_borrows = BorrowRecord.objects.filter(borrow_date__date=today).count()
    todays_returns = BorrowRecord.objects.filter(return_date=today).count()
    todays_requests = BookRequest.objects.filter(request_date__date=today).count()
    
    # Recent activity for librarian attention
    recent_borrows = BorrowRecord.objects.select_related('user', 'book').order_by('-borrow_date')[:10]
    recent_requests = BookRequest.objects.filter(status='pending').select_related('user', 'book').order_by('-request_date')[:10]
    overdue_records = BorrowRecord.objects.filter(status='overdue').select_related('user', 'book').order_by('due_date')[:10]
    
    # Books needing attention
    popular_books = Book.objects.filter(available_copies__lte=2).order_by('-times_borrowed')[:5]
    
    # Fine collection
    total_fines_pending = BorrowRecord.objects.filter(
        fine_amount__gt=0, fine_paid=False
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    context = {
        # Book stats
        'total_books': total_books,
        'available_books': available_books,
        'low_stock_books': low_stock_books,
        'out_of_stock_books': out_of_stock_books,
        'low_stock_count': low_stock_books.count(),
        
        # Borrow stats
        'active_borrows': active_borrows,
        'overdue_books': overdue_books,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        
        # Today's activity
        'todays_borrows': todays_borrows,
        'todays_returns': todays_returns,
        'todays_requests': todays_requests,
        
        # Recent activity
        'recent_borrows': recent_borrows,
        'recent_requests': recent_requests,
        'overdue_records': overdue_records,
        'popular_books': popular_books,
        
        # Financial
        'total_fines_pending': total_fines_pending,
    }
    
    return render(request, 'dashboard/librarian_dashboard.html', context)


@login_required
@student_required
def student_dashboard(request):
    """Student dashboard with personal library information"""
    user = request.user
    
    # Personal borrow statistics
    borrowed_books = BorrowRecord.objects.filter(user=user, status__in=['borrowed', 'overdue']).select_related('book')
    borrow_history = BorrowRecord.objects.filter(user=user).select_related('book').order_by('-borrow_date')
    overdue_books = BorrowRecord.objects.filter(user=user, status='overdue').select_related('book')
    
    # Request statistics
    pending_requests = BookRequest.objects.filter(user=user, status='pending').select_related('book')
    approved_requests = BookRequest.objects.filter(user=user, status='approved').select_related('book')
    
    # Personal stats
    total_books_borrowed = borrow_history.count()
    books_returned = BorrowRecord.objects.filter(user=user, status='returned').count()
    current_borrowed_count = borrowed_books.count()
    
    # Fine information
    total_fines = BorrowRecord.objects.filter(user=user, fine_amount__gt=0).aggregate(
        total=Sum('fine_amount'))['total'] or 0
    unpaid_fines = BorrowRecord.objects.filter(
        user=user, fine_amount__gt=0, fine_paid=False
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    # Recommendations based on user's reading history
    user_categories = borrow_history.values_list('book__category', flat=True).distinct()
    recommended_books = Book.objects.filter(
        category__in=user_categories,
        available_copies__gt=0
    ).exclude(
        id__in=borrowed_books.values_list('book_id', flat=True)
    ).order_by('-times_borrowed')[:6]
    
    # If no history-based recommendations, show popular books
    if not recommended_books.exists():
        recommended_books = Book.objects.filter(
            available_copies__gt=0
        ).order_by('-times_borrowed')[:6]
    
    # Due dates and alerts
    books_due_soon = borrowed_books.filter(
        due_date__lte=timezone.now().date() + timedelta(days=3)
    ).order_by('due_date')
    
    # Reading progress (books borrowed this month)
    this_month = timezone.now().replace(day=1).date()
    books_this_month = BorrowRecord.objects.filter(
        user=user, 
        borrow_date__gte=this_month
    ).count()
    
    context = {
        # Current status
        'borrowed_books': borrowed_books,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'overdue_books': overdue_books,
        'books_due_soon': books_due_soon,
        
        # Statistics
        'total_books_borrowed': total_books_borrowed,
        'books_returned': books_returned,
        'current_borrowed_count': current_borrowed_count,
        'books_this_month': books_this_month,
        'max_limit': request.user.profile.max_books_allowed,
        'remaining_slots': request.user.profile.max_books_allowed - current_borrowed_count,
        
        # Financial
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        
        # Recommendations
        'recommended_books': recommended_books,
        'borrow_history': borrow_history[:10],  # Recent 10
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
@admin_required
def analytics(request):
    """Analytics view for admin with real chart data"""
    from django.db.models import Count, Sum
    from datetime import timedelta

    today = timezone.now().date()

    # Last 12 months borrow trend
    monthly_labels = []
    monthly_data = []
    for i in range(11, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30 * i))
        month_start = month_start.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        count = BorrowRecord.objects.filter(
            borrow_date__date__gte=month_start,
            borrow_date__date__lt=month_end
        ).count()
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_data.append(count)

    # Category distribution
    category_stats = list(Category.objects.annotate(
        book_count=Count('books'),
        borrow_count=Count('books__borrow_records')
    ).values('name', 'book_count', 'borrow_count').order_by('-borrow_count'))

    # User role distribution
    role_stats = {
        'admin': User.objects.filter(role='admin').count(),
        'librarian': User.objects.filter(role='librarian').count(),
        'student': User.objects.filter(role='student').count(),
    }

    # Book availability
    available_books = Book.objects.filter(available_copies__gt=0).count()
    unavailable_books = Book.objects.filter(available_copies=0).count()

    # Last 7 days daily activity
    daily_labels = []
    daily_borrows = []
    daily_returns = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%a %d'))
        daily_borrows.append(BorrowRecord.objects.filter(borrow_date__date=day).count())
        daily_returns.append(BorrowRecord.objects.filter(return_date=day).count())

    # Top 10 most borrowed books
    top_books = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]

    # Summary stats
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(t=Sum('fine_amount'))['t'] or 0
    unpaid_fines = BorrowRecord.objects.filter(fine_amount__gt=0, fine_paid=False).aggregate(t=Sum('fine_amount'))['t'] or 0

    import json
    context = {
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_data_json': json.dumps(monthly_data),
        'category_stats': category_stats,
        'role_stats': role_stats,
        'available_books': available_books,
        'unavailable_books': unavailable_books,
        'daily_labels_json': json.dumps(daily_labels),
        'daily_borrows_json': json.dumps(daily_borrows),
        'daily_returns_json': json.dumps(daily_returns),
        'top_books': top_books,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
@admin_required
def reports(request):
    """Reports view for admin"""
    from django.db.models import Sum, Count
    from datetime import timedelta

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    # This month stats
    this_month_borrows = BorrowRecord.objects.filter(borrow_date__date__gte=this_month_start).count()
    this_month_returns = BorrowRecord.objects.filter(return_date__gte=this_month_start).count()
    this_month_requests = BookRequest.objects.filter(request_date__date__gte=this_month_start).count()
    this_month_fines = BorrowRecord.objects.filter(
        fine_amount__gt=0, borrow_date__date__gte=this_month_start
    ).aggregate(t=Sum('fine_amount'))['t'] or 0

    # Last month stats
    last_month_borrows = BorrowRecord.objects.filter(
        borrow_date__date__gte=last_month_start,
        borrow_date__date__lt=this_month_start
    ).count()

    # Overall stats
    total_borrows = BorrowRecord.objects.count()
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(t=Sum('fine_amount'))['t'] or 0
    unpaid_fines = BorrowRecord.objects.filter(fine_amount__gt=0, fine_paid=False).aggregate(t=Sum('fine_amount'))['t'] or 0
    total_users = User.objects.count()
    total_books = Book.objects.count()

    # Top borrowed books (all time)
    top_books = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]

    # Most active students
    top_students = User.objects.filter(role='student').annotate(
        borrow_count=Count('borrow_records')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:10]

    # Overdue summary
    overdue_count = BorrowRecord.objects.filter(status='overdue').count()
    overdue_fines = BorrowRecord.objects.filter(
        status='overdue', fine_amount__gt=0
    ).aggregate(t=Sum('fine_amount'))['t'] or 0

    context = {
        'this_month_borrows': this_month_borrows,
        'this_month_returns': this_month_returns,
        'this_month_requests': this_month_requests,
        'this_month_fines': this_month_fines,
        'last_month_borrows': last_month_borrows,
        'total_borrows': total_borrows,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        'total_users': total_users,
        'total_books': total_books,
        'top_books': top_books,
        'top_students': top_students,
        'overdue_count': overdue_count,
        'overdue_fines': overdue_fines,
        'this_month': this_month_start,
    }
    return render(request, 'dashboard/reports.html', context)


@login_required
def calendar_view(request):
    """Calendar view showing due dates and library events"""
    from django.utils import timezone
    import json
    
    # Get borrow records with due dates
    if request.user.is_student:
        # Students see only their own due dates
        records = BorrowRecord.objects.filter(
            user=request.user,
            status__in=['borrowed', 'overdue']
        ).select_related('book')
    else:
        # Staff see all due dates
        records = BorrowRecord.objects.filter(
            status__in=['borrowed', 'overdue']
        ).select_related('user', 'book')
    
    # Prepare calendar events
    events = []
    for record in records:
        color = '#dc3545' if record.status == 'overdue' else '#28a745'  # Red for overdue, green for normal
        
        if request.user.is_student:
            title = f"Return: {record.book.title}"
        else:
            title = f"{record.user.username}: {record.book.title}"
        
        events.append({
            'title': title,
            'start': record.due_date.isoformat(),
            'color': color,
            'url': f'/books/{record.book.pk}/',
            'extendedProps': {
                'user': record.user.username,
                'book': record.book.title,
                'status': record.status,
                'fine': float(record.fine_amount) if record.fine_amount else 0
            }
        })
    
    context = {
        'events_json': json.dumps(events),
        'events': events
    }
    
    return render(request, 'dashboard/calendar.html', context)

@login_required
@admin_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics (for charts)"""
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Basic stats
    stats = {
        'total_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'active_borrows': BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count(),
        'overdue_books': BorrowRecord.objects.filter(status='overdue').count(),
    }
    
    # Monthly borrow trends (last 12 months)
    today = timezone.now().date()
    twelve_months_ago = today - timedelta(days=365)
    
    monthly_borrows = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = BorrowRecord.objects.filter(
            borrow_date__date__gte=month_start,
            borrow_date__date__lte=month_end
        ).count()
        
        monthly_borrows.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_borrows.reverse()  # Show oldest to newest
    
    # Category distribution
    category_stats = Category.objects.annotate(
        book_count=Count('books')
    ).values('name', 'book_count')
    
    # User role distribution
    role_stats = User.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')
    
    # Book status distribution
    available_books = Book.objects.filter(available_copies__gt=0).count()
    unavailable_books = Book.objects.filter(available_copies=0).count()
    
    # Recent activity (last 7 days)
    week_ago = today - timedelta(days=7)
    daily_activity = []
    
    for i in range(7):
        day = week_ago + timedelta(days=i)
        borrows = BorrowRecord.objects.filter(borrow_date__date=day).count()
        returns = BorrowRecord.objects.filter(return_date=day).count()
        
        daily_activity.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%a'),
            'borrows': borrows,
            'returns': returns
        })
    
    return JsonResponse({
        'stats': stats,
        'monthly_borrows': monthly_borrows,
        'category_stats': list(category_stats),
        'role_stats': list(role_stats),
        'book_status': {
            'available': available_books,
            'unavailable': unavailable_books
        },
        'daily_activity': daily_activity
    })
    

@login_required
def generate_library_card_view(request, user_id):
    """Generate and download library card for a user"""
    from django.http import HttpResponse
    from .utils import generate_library_card
    from ..users.models import User
    
    user = get_object_or_404(User, pk=user_id)
    
    # Allow users to download their own card, or admins to download any card
    if not (request.user.id == user_id or request.user.is_admin):
        messages.error(request, 'You can only download your own library card.')
        return redirect('users:profile')
    
    # Generate card
    card_image = generate_library_card(user)
    
    # Save to response
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="library_card_{user.username}.png"'
    card_image.save(response, 'PNG')
    
    # Log activity
    from .utils import log_activity
    log_activity(request.user, 'other', f'Downloaded library card for {user.username}', request)
    
    return response


@login_required
def view_library_card(request, user_id):
    """View library card as image (not download)"""
    from django.http import HttpResponse
    from .utils import generate_library_card
    from ..users.models import User
    
    user = get_object_or_404(User, pk=user_id)
    
    # Allow users to view their own card, or admins to view any card
    if not (request.user.id == user_id or request.user.is_admin):
        messages.error(request, 'You can only view your own library card.')
        return redirect('users:profile')
    
    # Generate card
    card_image = generate_library_card(user)
    
    # Return as inline image (not download)
    response = HttpResponse(content_type='image/png')
    card_image.save(response, 'PNG')
    
    return response


@login_required
@admin_required
def download_qr_code(request, book_id):
    """Download QR code for a book"""
    from django.http import HttpResponse, Http404, HttpResponseRedirect
    from ..books.models import Book

    book = get_object_or_404(Book, pk=book_id)

    if not book.qr_code:
        # Generate QR code if it doesn't exist
        book.generate_qr_code()
        book.save()

    if book.qr_code:
        storage = book.qr_code.storage
        is_cloudinary = 'cloudinary' in type(storage).__module__.lower()

        if is_cloudinary:
            # On Cloudinary: redirect to the remote URL — browser downloads it
            return HttpResponseRedirect(book.qr_code.url)
        else:
            # Local storage: read and serve from disk
            response = HttpResponse(book.qr_code.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="qr_code_{book.isbn}.png"'
            return response
    else:
        raise Http404("QR code not available")


@login_required
@admin_required
def export_overdue_csv(request):
    """Export overdue books to CSV"""
    from django.http import HttpResponse
    from ..borrow.models import BorrowRecord
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="overdue_books.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Email', 'Book', 'ISBN', 'Due Date', 'Days Overdue', 'Fine (ETB)', 'Fine Paid'])
    
    records = BorrowRecord.objects.filter(status='overdue').select_related('user', 'book')
    
    for record in records:
        writer.writerow([
            record.user.get_full_name() or record.user.username,
            record.user.email,
            record.book.title,
            record.book.isbn,
            record.due_date.strftime('%Y-%m-%d'),
            record.get_days_overdue(),
            f"{record.fine_amount:.2f}",
            'Yes' if record.fine_paid else 'No'
        ])
    
    return response


@login_required
@admin_required
def export_overdue_pdf(request):
    """Export overdue books to PDF"""
    from django.http import HttpResponse
    from .utils import generate_overdue_report_pdf
    
    pdf_buffer = generate_overdue_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="overdue_report.pdf"'
    
    return response


@login_required
@admin_required
def export_fine_report_pdf(request):
    """Export fine report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_fine_report_pdf
    
    pdf_buffer = generate_fine_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fine_report.pdf"'
    
    return response


@login_required
@admin_required
def export_top_books_pdf(request):
    """Export top 10 books report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_top_books_report_pdf
    
    pdf_buffer = generate_top_books_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="top_books_report.pdf"'
    
    return response


@login_required
@admin_required
def export_top_members_pdf(request):
    """Export top 10 members report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_top_members_report_pdf
    
    pdf_buffer = generate_top_members_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="top_members_report.pdf"'
    
    return response


@login_required
@admin_required
def create_backup(request):
    """
    Create a database backup and stream it directly to the browser.
    Works on Render (PostgreSQL/Supabase) — no local disk storage needed.
    """
    from django.contrib import messages
    from django.http import HttpResponse
    from .utils import create_database_backup, log_activity

    try:
        buffer, fmt = create_database_backup()
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        if fmt == 'sql':
            filename = f'db_backup_{timestamp}.sql'
            content_type = 'application/sql'
        else:
            filename = f'db_backup_{timestamp}.json'
            content_type = 'application/json'

        response = HttpResponse(buffer.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        log_activity(request.user, 'backup_created', f'Database backup downloaded: {filename}', request)
        return response

    except Exception as e:
        messages.error(request, f'Failed to create backup: {str(e)}')
        return redirect('dashboard:system_admin')


@login_required
@admin_required
def restore_backup(request):
    """
    Restore database from an uploaded JSON or SQL backup file.
    Works on Render (PostgreSQL/Supabase) — no local disk storage.
    """
    from django.contrib import messages
    from .utils import log_activity

    if request.method == 'POST':
        uploaded_file = request.FILES.get('backup_file')

        if not uploaded_file:
            messages.error(request, 'Please upload a backup file (.json or .sql).')
            return redirect('dashboard:system_admin')

        filename = uploaded_file.name.lower()

        if filename.endswith('.json'):
            # Django dumpdata JSON format — use loaddata
            try:
                import tempfile, os
                from django.core.management import call_command

                # Write to a temp file (loaddata needs a file path)
                with tempfile.NamedTemporaryFile(
                    mode='wb', suffix='.json', delete=False
                ) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                call_command('loaddata', tmp_path, verbosity=0)
                os.unlink(tmp_path)

                messages.success(request, 'Database restored successfully from JSON backup.')
                log_activity(request.user, 'backup_restored', f'Database restored from JSON: {uploaded_file.name}', request)

            except Exception as e:
                messages.error(request, f'Failed to restore from JSON: {str(e)}')

        elif filename.endswith('.sql'):
            # PostgreSQL SQL dump — use psql
            try:
                import subprocess, os, tempfile
                from django.conf import settings

                db = settings.DATABASES['default']
                database_url = os.environ.get('DATABASE_URL')

                with tempfile.NamedTemporaryFile(
                    mode='wb', suffix='.sql', delete=False
                ) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                env = os.environ.copy()

                if database_url:
                    cmd = ['psql', database_url, '-f', tmp_path]
                else:
                    env['PGPASSWORD'] = db.get('PASSWORD', '')
                    cmd = [
                        'psql',
                        '-h', db.get('HOST', 'localhost'),
                        '-p', str(db.get('PORT', '5432')),
                        '-U', db.get('USER', ''),
                        '-d', db.get('NAME', ''),
                        '-f', tmp_path,
                    ]

                result = subprocess.run(cmd, env=env, capture_output=True, timeout=120)
                os.unlink(tmp_path)

                if result.returncode == 0:
                    messages.success(request, 'Database restored successfully from SQL backup.')
                    log_activity(request.user, 'backup_restored', f'Database restored from SQL: {uploaded_file.name}', request)
                else:
                    messages.error(request, f'psql restore failed: {result.stderr.decode()[:500]}')

            except FileNotFoundError:
                messages.error(request, 'psql command not found. Use JSON backup format instead.')
            except Exception as e:
                messages.error(request, f'Failed to restore from SQL: {str(e)}')

        else:
            messages.error(request, 'Invalid file type. Please upload a .json or .sql backup file.')

    return redirect('dashboard:system_admin')


@login_required
@admin_required
def download_backup(request, backup_file):
    """
    Download backup is now handled by create_backup which streams directly.
    This endpoint is kept for URL compatibility but redirects to create_backup.
    """
    messages.info(request, 'Use the "Download Backup" button to generate and download a fresh backup.')
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def upload_backup(request):
    """
    Upload a backup file and restore it immediately.
    Accepts .json (Django dumpdata) or .sql (pg_dump) files.
    No local storage — file is processed in memory and discarded.
    """
    from django.contrib import messages

    if request.method == 'POST':
        # Delegate to restore_backup which handles the actual restore
        return restore_backup(request)

    return redirect('dashboard:system_admin')


@login_required
@admin_required
def delete_backup(request, backup_file):
    """
    Backup files are no longer stored on disk (ephemeral on Render).
    This endpoint is kept for URL compatibility.
    """
    messages.info(request, 'Backups are downloaded directly — no stored backups to delete.')
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def send_due_reminders(request):
    """Send due date reminder emails"""
    from django.contrib import messages
    from .utils import send_due_reminder_emails, log_activity
    
    try:
        sent_count = send_due_reminder_emails()
        messages.success(request, f'Sent {sent_count} reminder email(s) successfully.')
        log_activity(request.user, 'reminder_sent', f'Sent {sent_count} due date reminder emails', request)
    except Exception as e:
        messages.error(request, f'Failed to send reminders: {str(e)}')
    
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def send_overdue_notifications(request):
    """Send overdue notification emails"""
    from django.contrib import messages
    from .utils import send_overdue_notification_emails, log_activity
    
    try:
        sent_count = send_overdue_notification_emails()
        messages.success(request, f'Sent {sent_count} overdue notification(s) successfully.')
        log_activity(request.user, 'reminder_sent', f'Sent {sent_count} overdue notifications', request)
    except Exception as e:
        messages.error(request, f'Failed to send notifications: {str(e)}')
    
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def activity_log_view(request):
    """View full activity log"""
    from django.core.paginator import Paginator
    from ..users.models import ActivityLog
    
    # Get all activity logs
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filter by action type
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get action choices for filter
    from ..users.models import ActivityLog as AL
    action_choices = AL.ACTION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': action_choices,
        'total_count': logs.count(),
    }
    
    return render(request, 'dashboard/activity_log.html', context)


@login_required
@librarian_or_admin_required
def reservation_management(request):
    """Manage book reservations/requests"""
    from ..borrow.models import BookRequest
    from django.db.models import Q
    
    # Get all requests with filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests = BookRequest.objects.select_related('user', 'book', 'approved_by').all()
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if search:
        requests = requests.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(book__title__icontains=search)
        )
    
    # Get counts by status
    pending_count = BookRequest.objects.filter(status='pending').count()
    ready_count = BookRequest.objects.filter(status='ready').count()
    fulfilled_count = BookRequest.objects.filter(status='fulfilled').count()
    cancelled_count = BookRequest.objects.filter(status='cancelled').count()
    rejected_count = BookRequest.objects.filter(status='rejected').count()
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'search': search,
        'pending_count': pending_count,
        'ready_count': ready_count,
        'fulfilled_count': fulfilled_count,
        'cancelled_count': cancelled_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'dashboard/reservation_management.html', context)


@login_required
@admin_required
def system_administration(request):
    """System administration panel"""
    from ..users.models import ActivityLog
    from ..borrow.models import BorrowRecord
    from .models import SystemSettings
    from django.db.models import Sum
    import os
    
    # Get system settings
    system_settings = SystemSettings.get_settings()
    
    # Get system statistics
    total_logs = ActivityLog.objects.count()
    recent_logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Backup info — on Render backups are generated on-demand, not stored on disk
    backups = []  # No stored backups — use "Download Backup" to get a fresh one
    
    # Get email statistics
    books_due_soon = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lte=timezone.now().date() + timedelta(days=3),
        due_date__gte=timezone.now().date()
    ).count()
    
    overdue_books = BorrowRecord.objects.filter(status='overdue').count()
    
    context = {
        'system_settings': system_settings,
        'total_logs': total_logs,
        'recent_logs': recent_logs,
        'backups': backups,
        'books_due_soon': books_due_soon,
        'overdue_books': overdue_books,
    }
    
    return render(request, 'dashboard/system_administration.html', context)


@login_required
@admin_required
def update_system_settings(request):
    """Update system-wide settings"""
    from .models import SystemSettings
    from django.contrib import messages
    
    if request.method == 'POST':
        settings_obj = SystemSettings.get_settings()
        
        try:
            # Get form data
            default_borrow_limit = int(request.POST.get('default_borrow_limit', 5))
            fine_per_day = float(request.POST.get('fine_per_day', 2.00))
            max_borrow_days = int(request.POST.get('max_borrow_days', 14))
            apply_to_all = request.POST.get('apply_to_all') == 'on'
            
            # Validate
            if not (1 <= default_borrow_limit <= 20):
                messages.error(request, 'Borrow limit must be between 1 and 20.')
                return redirect('dashboard:system_admin')
            
            if fine_per_day < 0:
                messages.error(request, 'Fine per day cannot be negative.')
                return redirect('dashboard:system_admin')
            
            if not (1 <= max_borrow_days <= 90):
                messages.error(request, 'Max borrow days must be between 1 and 90.')
                return redirect('dashboard:system_admin')
            
            # Update settings
            settings_obj.default_borrow_limit = default_borrow_limit
            settings_obj.fine_per_day = fine_per_day
            settings_obj.max_borrow_days = max_borrow_days
            settings_obj.updated_by = request.user
            settings_obj.save()
            
            # Apply to all users if requested
            if apply_to_all:
                from ..users.models import UserProfile
                updated_count = UserProfile.objects.all().update(max_books_allowed=default_borrow_limit)
                messages.success(request, f'System settings updated! Borrow limit of {default_borrow_limit} books applied to {updated_count} users.')
            else:
                messages.success(request, f'System settings updated! New users will have a borrow limit of {default_borrow_limit} books.')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {str(e)}')
    
    return redirect('dashboard:system_admin')



@login_required
@admin_required
def system_settings_view(request):
    """View and edit system settings - Admin only"""
    from apps.dashboard.models import SystemSettings
    from django.contrib import messages
    
    settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update settings from form
            settings.default_borrow_limit = int(request.POST.get('default_borrow_limit', 5))
            settings.fine_per_day = float(request.POST.get('fine_per_day', 2.00))
            settings.etb_to_usd_rate = float(request.POST.get('etb_to_usd_rate', 0.0180))
            settings.max_borrow_days = int(request.POST.get('max_borrow_days', 14))
            settings.updated_by = request.user
            settings.save()
            
            messages.success(request, 'System settings updated successfully!')
            
            # Log activity
            from .utils import log_activity
            log_activity(request.user, 'settings_updated', 'System settings updated', request)
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'dashboard/system_settings.html', context)


@login_required
def test_email(request):
    """
    Admin-only: send a test email via Brevo HTTP API (no SMTP ports needed).
    Returns JSON with result + diagnostics.
    """
    import logging
    import os
    from django.conf import settings as django_settings
    from allauth.account.models import EmailAddress

    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)

    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'message': 'Admin access required.'}, status=403)

    to_email = request.user.email
    if not to_email:
        return JsonResponse({'success': False, 'message': 'Your account has no email address.'})

    is_verified = EmailAddress.objects.filter(
        email__iexact=to_email, verified=True
    ).exists()

    brevo_api_key = os.environ.get('BREVO_API_KEY', '')
    resend_key    = os.environ.get('RESEND_API_KEY', '')

    diag = {
        'to': to_email,
        'from': django_settings.DEFAULT_FROM_EMAIL,
        'backend_setting': django_settings.EMAIL_BACKEND,
        'brevo_api_key_set': bool(brevo_api_key),
        'brevo_api_key_preview': brevo_api_key[:12] + '...' if brevo_api_key else '(not set)',
        'resend_api_key_set': bool(resend_key),
        'allauth_verified': is_verified,
    }

    if not brevo_api_key:
        return JsonResponse({
            'success': False,
            'message': (
                'BREVO_API_KEY not found in environment. '
                'Add it in Render dashboard -> Environment -> BREVO_API_KEY '
                '(get it from brevo.com -> SMTP & API -> API Keys tab).'
            ),
            'diagnostics': diag,
        })

    try:
        # Use Brevo HTTP API directly — no SMTP ports, works on Render free tier
        from django.conf import settings as s
        if not hasattr(s, 'ANYMAIL'):
            s.ANYMAIL = {}
        s.ANYMAIL['BREVO_API_KEY'] = brevo_api_key

        from anymail.backends.brevo import EmailBackend as BrevoBackend
        from django.core.mail import EmailMessage

        backend = BrevoBackend(fail_silently=False)
        msg = EmailMessage(
            subject='[SmartLibrary] Test Email',
            body=(
                f'This is a test email from Smart Library.\n\n'
                f'Brevo HTTP API is working correctly.\n\n'
                f'Sent to: {to_email}\n'
                f'From: {django_settings.DEFAULT_FROM_EMAIL}\n'
            ),
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            connection=backend,
        )
        msg.send(fail_silently=False)
        logger.info(f'Test email sent to {to_email} via Brevo API')
        return JsonResponse({
            'success': True,
            'message': f'Test email sent to {to_email} via Brevo API. Check your inbox (and spam folder).',
            'diagnostics': diag,
        })

    except Exception as e:
        logger.error(f'Test email FAILED to {to_email}: {type(e).__name__}: {e}')
        return JsonResponse({
            'success': False,
            'message': f'{type(e).__name__}: {e}',
            'diagnostics': diag,
        })

@login_required
@librarian_or_admin_required
def notification_center(request):
    """Notification center — send due-soon, overdue, unpaid-fine, and custom emails"""

    today = timezone.now().date()

    # Querysets
    due_soon = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lte=today + timedelta(days=3),
        due_date__gte=today,
    ).select_related('user', 'book').order_by('due_date')

    overdue = BorrowRecord.objects.filter(
        status='overdue',
    ).select_related('user', 'book').order_by('due_date')

    unpaid_fines = BorrowRecord.objects.filter(
        fine_amount__gt=0,
        fine_paid=False,
    ).select_related('user', 'book').order_by('-fine_amount')

    total_due_soon = due_soon.count()
    total_overdue  = overdue.count()
    total_unpaid   = unpaid_fines.aggregate(total=Sum('fine_amount'))['total'] or 0
    unpaid_count   = unpaid_fines.count()

    # Handle POST
    if request.method == 'POST':
        from django.contrib import messages as dj_messages
        action = request.POST.get('action', '')

        # Bulk / single record emails
        if action in ('send_due_soon', 'send_overdue', 'send_unpaid'):
            # JS sends multiple inputs named 'record_ids'; empty list = send all
            ids = [int(i) for i in request.POST.getlist('record_ids') if i.strip().isdigit()]

            if ids:
                target_records = list(
                    BorrowRecord.objects.filter(pk__in=ids).select_related('user', 'book')
                )
            else:
                # No IDs = send to everyone in that section
                if action == 'send_due_soon':
                    target_records = list(due_soon)
                elif action == 'send_overdue':
                    target_records = list(overdue)
                else:
                    target_records = list(unpaid_fines)

            sent = skipped = errors = 0
            for rec in target_records:
                if not rec.user.email:
                    skipped += 1
                    continue
                try:
                    _send_notification_email(action, rec)
                    sent += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(
                        f"notification_center email failed for record {rec.pk}: {e}"
                    )
                    errors += 1

            if sent:
                dj_messages.success(request, f'✓ {sent} email(s) queued successfully.')
            if skipped:
                dj_messages.warning(request, f'{skipped} user(s) skipped — no email address.')
            if errors:
                dj_messages.error(request, f'{errors} email(s) failed — check server logs.')

        # Custom email
        elif action == 'send_custom':
            import logging
            logger = logging.getLogger(__name__)

            subject        = request.POST.get('subject', '').strip()
            body           = request.POST.get('body', '').strip()
            recipient_type = request.POST.get('recipient_type', 'all')
            selected_ids   = request.POST.getlist('selected_user_ids')

            if not subject or not body:
                dj_messages.error(request, 'Subject and message are required.')
                return redirect('dashboard:notification_center')

            if recipient_type == 'specific' and selected_ids:
                recipients = User.objects.filter(pk__in=selected_ids, is_active=True).exclude(email='')
            elif recipient_type == 'students':
                recipients = User.objects.filter(role='student', is_active=True).exclude(email='')
            elif recipient_type == 'librarians':
                recipients = User.objects.filter(role='librarian', is_active=True).exclude(email='')
            else:
                recipients = User.objects.filter(is_active=True).exclude(email='')

            sent = errors = 0
            for u in recipients:
                p_subject = subject.replace('{name}', u.get_full_name() or u.username).replace('{username}', u.username)
                p_body    = body.replace('{name}', u.get_full_name() or u.username).replace('{username}', u.username)
                try:
                    _send_notification_email('send_custom', None,
                                             custom_to=u.email,
                                             custom_subject=p_subject,
                                             custom_body=p_body)
                    sent += 1
                except Exception as e:
                    logger.error(f"Custom email failed for {u.email}: {e}")
                    errors += 1

            if sent:
                dj_messages.success(request, f'✓ {sent} custom email(s) queued.')
            if errors:
                dj_messages.error(request, f'{errors} email(s) failed — check server logs.')

        return redirect('dashboard:notification_center')

    # Context for GET
    all_users = User.objects.filter(is_active=True).exclude(email='').order_by('first_name', 'username')

    context = {
        'due_soon_records':    due_soon,
        'overdue_records':     overdue,
        'unpaid_records':      unpaid_fines,
        'due_soon_count':      total_due_soon,
        'overdue_count':       total_overdue,
        'unpaid_count':        unpaid_count,
        'total_unpaid_amount': total_unpaid,
        'today':               today,
        'all_users':           all_users,
        # legacy names kept for safety
        'due_soon':            due_soon,
        'overdue':             overdue,
        'unpaid_fines':        unpaid_fines,
        'total_due_soon':      total_due_soon,
        'total_overdue':       total_overdue,
        'total_unpaid':        total_unpaid,
    }

    return render(request, 'dashboard/notification_center.html', context)
