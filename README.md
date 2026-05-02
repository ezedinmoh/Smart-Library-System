# Library Book Borrowing System

A comprehensive Django-based web application for managing library book inventory, user accounts, and borrowing operations with advanced features including role-based access control, analytics, and PDF reading.

## Features

### Core Features ✅
- **Book Management**: Full CRUD operations for books with cover images and PDF uploads
- **User Management**: Registration, user profiles, and account management
- **Borrowing System**: Borrow and return books with availability tracking
- **Database**: SQLite with proper relational models

### Intermediate Features
- **Authentication System**: Django's built-in auth with django-allauth integration
- **Role-Based Access Control**: Admin, Librarian, and Student roles with specific permissions
- **Borrow Tracking**: Complete tracking of who borrowed what and when
- **Categories**: Organize books by categories with filtering
- **Search & Filter**: Search by title/author and filter by category, language, and availability
- **Validation**: Required fields, unique ISBN, strong passwords, and borrow limit enforcement

### Advanced Features
- **Dashboard & Analytics**: Statistics on books, users, and borrowing activities
- **Overdue Management**: Track and manage overdue books with fine calculation
- **Export System**: Export data to CSV format
- **PDF Reader**: Upload and read PDF books in the browser
- **Recommendations**: Suggest books from the same category
- **Reports**: Detailed reports on borrowing trends and user activity

### Pro Features
- **REST API**: Django REST Framework endpoints for books and borrowing
- **Email Notifications**: Borrow confirmations and due date reminders
- **Calendar Integration**: View due dates in a calendar format
- **Dark Mode UI**: Theme toggle for comfortable browsing
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop

## Project Structure

```
library_system/
├── apps/
│   ├── users/           # User management and profiles
│   ├── books/           # Book inventory and categories
│   ├── borrow/          # Borrowing records and tracking
│   ├── dashboard/       # Analytics and reporting
│   └── api/             # REST API endpoints
├── templates/           # HTML templates
├── static/              # Static files (CSS, JS, images)
├── media/               # User uploads (covers, PDFs)
├── manage.py            # Django management script
└── README.md            # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip or uv (Python package manager)

### Step 1: Install Dependencies

Using uv:
```bash
uv add Django==4.2 djangorestframework django-allauth django-crispy-forms crispy-bootstrap5 django-filter PyJWT django-cors-headers openpyxl PyPDF2 python-decouple
```

Or with pip:
```bash
pip install -r requirements.txt
```

### Step 2: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 4: Start Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Usage Guide

### Admin Panel
Access the Django admin at `/admin/` with your superuser credentials to manage:
- Users and roles
- Books and categories
- Borrow records
- User profiles and fines

### For Students
1. Register an account at `/users/register/`
2. Browse books at `/books/`
3. Borrow books (limited to 3 books at a time)
4. View your borrowed books at `/borrow/my-books/`
5. Track fines and payment status

### For Librarians
- Manage book inventory
- View all borrow records
- Monitor overdue books
- Generate reports

### For Admins
- Full system control
- User role management
- Analytics dashboard
- Export data to CSV

## API Endpoints

The REST API provides the following endpoints:

### Books
- `GET /api/books/` - List all books
- `POST /api/books/` - Create a new book
- `GET /api/books/<id>/` - Get book details
- `PUT /api/books/<id>/` - Update a book
- `DELETE /api/books/<id>/` - Delete a book

### Borrowing
- `GET /api/borrows/` - List all borrow records
- `POST /api/borrows/` - Create a new borrow record
- `GET /api/borrows/<id>/` - Get borrow details
- `PUT /api/borrows/<id>/` - Update borrow status

## Models

### User
- Custom user model extending Django's AbstractUser
- Fields: username, email, password, phone, address, role
- Roles: Admin, Librarian, Student

### UserProfile
- OneToOne relationship with User
- Tracks: max books allowed, currently borrowed count, total fines, profile picture

### Book
- Fields: ISBN, title, author, category, copies, cover image, PDF file, publisher, publication date, language, rating
- Methods: is_available(), borrow_book(), return_book()

### Category
- Fields: name, description
- Relationship: One-to-Many with Books

### BorrowRecord
- Fields: user, book, borrow_date, due_date, return_date, status, fine_amount
- Status options: Borrowed, Returned, Overdue
- Automatic fine calculation (₹10 per day overdue)

### BookReview
- Fields: book, user, rating (1-5), review text
- Unique constraint: One review per user per book

## Configuration

Key settings in `library_system/settings.py`:

```python
# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Borrow Duration (days)
DEFAULT_BORROW_DAYS = 14

# Maximum Books Per User
MAX_BOOKS_PER_USER = 3

# Fine Amount (per day overdue)
FINE_PER_DAY = 10
```

## File Management

- **Book Covers**: Stored in `/media/covers/`
- **PDFs**: Stored in `/media/pdfs/`
- **Profile Pictures**: Stored in `/media/profiles/`

## Email Configuration

For email notifications, configure in settings:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-email-provider'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
```

### Database Issues
```bash
python manage.py migrate --run-syncdb
```

### Missing Migrations
```bash
python manage.py makemigrations --empty apps.users --name fix_model
```

## Documentation

This project includes comprehensive documentation to help you get started and deploy to production:

### Getting Started
- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation and setup guide
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - REST API reference and examples

### Production Deployment
- **[PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)** - Step-by-step production deployment guide
- **[DEPLOYMENT_SECURITY_CHECKLIST.md](DEPLOYMENT_SECURITY_CHECKLIST.md)** - 100+ security checks for production
- **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** - Complete environment variables reference (30+ variables)
- **[ENV_QUICK_REFERENCE.md](ENV_QUICK_REFERENCE.md)** - Quick reference cheat sheet

### Project Status
- **[ISSUES_FIXED_SUMMARY.md](ISSUES_FIXED_SUMMARY.md)** - Summary of all critical issues fixed and current project status

## Future Enhancements

- [ ] Mobile application
- [ ] Advanced recommendation engine using ML
- [ ] SMS notifications
- [ ] Book reservations
- [ ] Social features (book clubs, discussions)
- [ ] Advanced analytics dashboards

## License

This project is provided as-is for educational and library management purposes.

## Support

For issues, questions, or contributions, please refer to the documentation or contact the development team.
