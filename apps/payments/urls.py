"""
Payment URLs
URL patterns for payment-related views.
"""

from django.urls import path
from apps.payments import views

app_name = 'payments'

urlpatterns = [
    # Payment method selection
    path('select-method/<int:record_id>/', views.select_payment_method, name='select_method'),
    
    # Stripe routes
    path('stripe/create-intent/<int:record_id>/', views.create_stripe_payment_intent, name='stripe_create_intent'),
    path('stripe/success/', views.stripe_payment_success, name='stripe_success'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Chapa routes
    path('chapa/initialize/<int:record_id>/', views.initialize_chapa_payment, name='chapa_initialize'),
    path('chapa/callback/', views.chapa_payment_callback, name='chapa_callback'),
    path('chapa/webhook/', views.chapa_webhook, name='chapa_webhook'),
    
    # Payment history and receipt
    path('history/', views.payment_history, name='history'),
    path('receipt/<uuid:payment_id>/', views.payment_receipt, name='payment_receipt'),
    
    # Payment cancel
    path('cancel/', views.payment_cancel, name='cancel'),
]
