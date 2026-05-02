"""
Production Settings for Library Management System

This file contains production-ready settings with all security features enabled.
It imports from the base settings.py and overrides settings for production.

USAGE:
    Set environment variable: DJANGO_SETTINGS_MODULE=library_system.settings_production
    Or use: python manage.py runserver --settings=library_system.settings_production

IMPORTANT:
    - Never use these settings in development
    - Always set proper environment variables in production
    - Generate a new SECRET_KEY for production
    - Use PostgreSQL instead of SQLite
    - Use Redis for Celery broker
"""

# Import all settings from base settings
from .settings import *
from decouple import config

# ============================================================================
# SECURITY SETTINGS - PRODUCTION ONLY
# ============================================================================

# CRITICAL: Generate a new secret key for production
# Run: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = config('SECRET_KEY')  # MUST be set in environment, no default

# Debug must be False in production
DEBUG = False

# Allowed hosts - must be configured for your domain
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# ============================================================================
# HTTPS & SECURITY HEADERS
# ============================================================================

# Redirect all HTTP requests to HTTPS (disable for local testing)
SECURE_SSL_REDIRECT = False  # Set to True in production with SSL certificate

# Use secure cookies (only transmitted over HTTPS)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTP Strict Transport Security (HSTS)
# Tells browsers to only use HTTPS for this site
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent browsers from guessing content type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Enable browser XSS protection
SECURE_BROWSER_XSS_FILTER = True

# X-Frame-Options: Keep as SAMEORIGIN for PDF reader functionality
# If you don't need PDF reader, change to 'DENY' for better security
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Secure proxy SSL header (if behind a proxy like Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================================================
# DATABASE - POSTGRESQL (PRODUCTION)
# ============================================================================

# Use PostgreSQL in production (much better than SQLite)
# Install: pip install psycopg2-binary
# Format: postgresql://user:password@host:port/database

import dj_database_url

# Render provides DATABASE_URL automatically
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback to individual settings (local PostgreSQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='library_db'),
            'USER': config('DB_USER', default='library_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }

# ============================================================================
# STATIC FILES - PRODUCTION
# ============================================================================

# Use WhiteNoise for serving static files efficiently
# Install: pip install whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files compression and caching (Django 6 compatible)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# Static files will be served from /static/
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Media files (user uploads)
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# ============================================================================
# CELERY - PRODUCTION (REDIS)
# ============================================================================

# Use Redis for Celery broker and result backend
# Install Redis: https://redis.io/download
# Format: redis://localhost:6379/0
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')

# Disable eager execution (run tasks asynchronously)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False

# Celery task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# ============================================================================
# EMAIL - PRODUCTION
# ============================================================================

# Use real SMTP backend in production
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@smartlibrary.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='noreply@smartlibrary.com')

# ============================================================================
# LOGGING - PRODUCTION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django_errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
import os
LOGS_DIR = BASE_DIR / 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# ============================================================================
# CORS - PRODUCTION
# ============================================================================

# Configure CORS for your production domain
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://yourdomain.com,https://www.yourdomain.com'
).split(',')

# ============================================================================
# PAYMENT GATEWAYS - PRODUCTION
# ============================================================================

# Use production keys in production
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

CHAPA_SECRET_KEY = config('CHAPA_SECRET_KEY', default='')
CHAPA_WEBHOOK_SECRET = config('CHAPA_WEBHOOK_SECRET', default='')

# ============================================================================
# SITE CONFIGURATION - PRODUCTION
# ============================================================================

SITE_NAME = config('SITE_NAME', default='Smart Library Management System')
SITE_URL = config('SITE_URL', default='https://smartlibrary.onrender.com')

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

# Admin email for error notifications
ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@smartlibrary.com')),
]

MANAGERS = ADMINS

# ============================================================================
# SESSION & COOKIE SETTINGS
# ============================================================================

# Session cookie settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF cookie settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Template caching - Remove APP_DIRS when using loaders
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# ============================================================================
# SECURITY CHECKLIST REMINDER
# ============================================================================

"""
BEFORE DEPLOYING TO PRODUCTION, ENSURE:

1. ✅ SECRET_KEY is set to a new random value (not the development key)
2. ✅ DEBUG is False
3. ✅ ALLOWED_HOSTS is configured with your domain
4. ✅ Database is PostgreSQL (not SQLite)
5. ✅ Redis is running for Celery
6. ✅ All environment variables are set in .env
7. ✅ SSL certificate is installed
8. ✅ Static files are collected: python manage.py collectstatic
9. ✅ Migrations are applied: python manage.py migrate
10. ✅ Celery worker is running as a service
11. ✅ Celery beat is running as a service
12. ✅ Nginx/Apache is configured
13. ✅ Firewall is configured
14. ✅ Backups are automated
15. ✅ Monitoring is set up

Run security check:
    python manage.py check --deploy --settings=library_system.settings_production
"""
