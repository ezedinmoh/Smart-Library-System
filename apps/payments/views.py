"""
Payment Views
Handles payment selection, processing, callbacks, and payment history.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.conf import settings
from apps.borrow.models import BorrowRecord
from apps.payments.models import Payment, StripePayment, ChapaPayment
from apps.payments.stripe_handler import StripePaymentHandler, REUSABLE_PAYMENT_INTENT_STATUSES
from apps.payments.chapa_handler import ChapaPaymentHandler
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def select_payment_method(request, record_id):
    """
    Display payment method selection page (Stripe or Chapa)
    """
    borrow_record = get_object_or_404(BorrowRecord, id=record_id, user=request.user)
    
    # Check if fine exists and is not paid
    if borrow_record.fine_amount <= 0:
        messages.info(request, "No fine to pay for this record.")
        return redirect('borrow:my_books')
    
    if borrow_record.fine_paid:
        messages.info(request, "Fine has already been paid.")
        return redirect('borrow:my_books')
    
    # Get exchange rate from system settings
    from apps.dashboard.models import SystemSettings
    from decimal import Decimal
    system_settings = SystemSettings.get_settings()
    
    # Calculate USD equivalent for display
    amount_usd = float(borrow_record.fine_amount) * float(system_settings.etb_to_usd_rate)
    
    # Calculate processing fee if needed for Stripe
    from decimal import Decimal
    stripe_minimum = 0.50
    processing_fee = 0
    total_usd = amount_usd
    
    if amount_usd < stripe_minimum:
        processing_fee = stripe_minimum - amount_usd
        total_usd = stripe_minimum
    
    context = {
        'borrow_record': borrow_record,
        'amount_etb': borrow_record.fine_amount,
        'amount_usd': round(amount_usd, 2),
        'processing_fee_usd': round(processing_fee, 2),
        'total_usd': round(total_usd, 2),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'stripe_return_url': request.build_absolute_uri(reverse('payments:stripe_success')),
        'debug': (
            settings.STRIPE_PUBLIC_KEY.startswith('pk_test_') or
            getattr(settings, 'CHAPA_SECRET_KEY', '').startswith('CHASECK_TEST-')
        ),  # Show test info when using test keys (works on both local and Render)
    }
    
    return render(request, 'payments/select_method.html', context)


@login_required
@require_http_methods(["POST"])
def create_stripe_payment_intent(request, record_id):
    """
    Create a Stripe Payment Intent and return client secret
    """
    try:
        borrow_record = get_object_or_404(BorrowRecord, id=record_id, user=request.user)
        
        # Validate fine
        if borrow_record.fine_amount <= 0 or borrow_record.fine_paid:
            return JsonResponse({
                'success': False,
                'error': 'No fine to pay or already paid'
            }, status=400)

        # Reuse an open pending Stripe intent to avoid duplicate Payment rows
        existing_payment = Payment.objects.filter(
            borrow_record=borrow_record,
            user=request.user,
            payment_method='stripe',
            status='pending',
        ).order_by('-created_at').first()

        if existing_payment:
            try:
                stripe_payment = existing_payment.stripe_details
                intent = StripePaymentHandler.retrieve_payment_intent(
                    stripe_payment.stripe_payment_intent_id
                )
                if intent and intent.status in REUSABLE_PAYMENT_INTENT_STATUSES:
                    amount_usd = intent.amount / 100
                    processing_fee_usd = float(
                        intent.metadata.get('processing_fee_usd', 0) or 0
                    )
                    return JsonResponse({
                        'success': True,
                        'client_secret': intent.client_secret,
                        'payment_id': str(existing_payment.id),
                        'amount_usd': amount_usd,
                        'processing_fee_usd': processing_fee_usd,
                        'reused': True,
                    })
            except StripePayment.DoesNotExist:
                pass
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            borrow_record=borrow_record,
            amount=borrow_record.fine_amount,
            currency='ETB',
            payment_method='stripe',
            transaction_id=f"STRIPE-{borrow_record.id}-{Payment.objects.count() + 1}",
            status='pending',
        )
        
        # Log payment initiation
        from apps.dashboard.utils import log_activity
        log_activity(
            request.user,
            'payment_initiated',
            f'Stripe payment initiated: ETB {borrow_record.fine_amount} for book "{borrow_record.book.title}"',
            request
        )
        
        # Create Stripe payment intent
        result = StripePaymentHandler.create_payment_intent(payment)
        
        if result['success']:
            # Create Stripe payment details
            StripePayment.objects.create(
                payment=payment,
                stripe_payment_intent_id=result['payment_intent_id'],
            )
            
            return JsonResponse({
                'success': True,
                'client_secret': result['client_secret'],
                'payment_id': str(payment.id),
                'amount_usd': result['amount_usd'],
                'processing_fee_usd': result.get('processing_fee_usd', 0),
            })
        else:
            payment.status = 'failed'
            payment.save()
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to create payment intent')
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error creating Stripe payment intent: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def stripe_payment_success(request):
    """
    Handle successful Stripe payment redirect
    """
    payment_intent_id = request.GET.get('payment_intent')
    redirect_status = request.GET.get('redirect_status')

    if redirect_status == 'failed':
        messages.error(request, "Payment was not completed. Please try again.")
        return redirect('borrow:my_books')
    
    if not payment_intent_id:
        messages.error(request, "Invalid payment session.")
        return redirect('borrow:my_books')
    
    try:
        # Find payment by Stripe payment intent ID
        stripe_payment = StripePayment.objects.select_related('payment').get(
            stripe_payment_intent_id=payment_intent_id
        )
        payment = stripe_payment.payment

        # Verify the returning user owns this payment
        if payment.user_id != request.user.id:
            messages.error(request, "Unauthorized access.")
            return redirect('borrow:my_books')

        # Already completed (e.g. webhook ran before redirect)
        if payment.status == 'completed':
            messages.success(request, f"Payment of ETB {payment.amount} completed successfully!")
            return redirect('payments:payment_receipt', payment_id=payment.id)
        
        # Confirm payment
        if StripePaymentHandler.confirm_payment(payment, payment_intent_id):
            messages.success(request, f"Payment of ETB {payment.amount} completed successfully!")
            
            # Send success email to student + notify staff
            from apps.users.notifications import notify_payment_success, notify_admins_fine_paid
            notify_payment_success(payment)
            notify_admins_fine_paid(payment)
            
            return redirect('payments:payment_receipt', payment_id=payment.id)
        else:
            messages.error(request, "Payment verification failed. Please contact support.")
            return redirect('borrow:my_books')
            
    except StripePayment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('borrow:my_books')
    except Exception as e:
        logger.error(f"Error processing Stripe success: {str(e)}")
        messages.error(request, "An error occurred processing your payment.")
        return redirect('borrow:my_books')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    result = StripePaymentHandler.handle_webhook(payload, sig_header)
    
    if result['success']:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


@login_required
@require_http_methods(["POST"])
def initialize_chapa_payment(request, record_id):
    """
    Initialize Chapa payment and redirect to checkout
    """
    try:
        borrow_record = get_object_or_404(BorrowRecord, id=record_id, user=request.user)
        
        # Validate fine
        if borrow_record.fine_amount <= 0 or borrow_record.fine_paid:
            messages.error(request, "No fine to pay or already paid.")
            return redirect('borrow:my_books')
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            borrow_record=borrow_record,
            amount=borrow_record.fine_amount,
            currency='ETB',
            payment_method='chapa',
            transaction_id=f"CHAPA-{borrow_record.id}-{Payment.objects.count() + 1}",
            status='pending',
        )
        
        # Log payment initiation
        from apps.dashboard.utils import log_activity
        log_activity(
            request.user,
            'payment_initiated',
            f'Chapa payment initiated: ETB {borrow_record.fine_amount} for book "{borrow_record.book.title}"',
            request
        )
        
        # Prepare URLs
        callback_url = request.build_absolute_uri(reverse('payments:chapa_webhook'))
        return_url = request.build_absolute_uri(reverse('payments:chapa_callback'))
        
        # Initialize Chapa payment
        result = ChapaPaymentHandler.initialize_payment(payment, callback_url, return_url)
        
        if result['success']:
            # Create Chapa payment details
            ChapaPayment.objects.create(
                payment=payment,
                chapa_tx_ref=result['tx_ref'],
                chapa_checkout_url=result['checkout_url'],
            )
            
            # Redirect to Chapa checkout
            return redirect(result['checkout_url'])
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f"Payment initialization failed: {result.get('error', 'Unknown error')}")
            return redirect('payments:select_method', record_id=record_id)
            
    except Exception as e:
        logger.error(f"Error initializing Chapa payment: {str(e)}")
        messages.error(request, "An unexpected error occurred.")
        return redirect('borrow:my_books')


@login_required
def chapa_payment_callback(request):
    """
    Handle Chapa payment callback (user redirect after payment)
    
    Note: In test mode, Chapa may process the webhook before redirecting the user.
    We need to check if the payment was already confirmed by the webhook.
    """
    # Log all callback parameters for debugging
    logger.info(f"Chapa callback received with GET params: {dict(request.GET)}")
    logger.info(f"Chapa callback received with POST params: {dict(request.POST)}")
    
    # Chapa may send different parameter names, check all possibilities
    tx_ref = (request.GET.get('tx_ref') or 
              request.GET.get('trx_ref') or 
              request.GET.get('transaction_ref') or
              request.POST.get('tx_ref') or
              request.POST.get('trx_ref'))
    
    status = request.GET.get('status') or request.POST.get('status')
    
    # If no tx_ref in URL, check if user has a recent pending Chapa payment
    if not tx_ref:
        logger.info("No tx_ref in callback, checking for recent pending payments")
        try:
            # Find the most recent pending or completed Chapa payment for this user
            recent_payment = Payment.objects.filter(
                user=request.user,
                payment_method='chapa',
                status__in=['pending', 'completed']
            ).order_by('-created_at').first()
            
            if recent_payment:
                logger.info(f"Found recent payment {recent_payment.id} with status {recent_payment.status}")
                
                # If already completed (by webhook), show success
                if recent_payment.status == 'completed':
                    messages.success(request, f"Payment of ETB {recent_payment.amount} completed successfully!")
                    return redirect('payments:payment_receipt', payment_id=recent_payment.id)
                
                # If still pending, try to get tx_ref from ChapaPayment
                try:
                    chapa_payment = ChapaPayment.objects.get(payment=recent_payment)
                    tx_ref = chapa_payment.chapa_tx_ref
                    status = 'success'  # Assume success if we're in callback
                    logger.info(f"Retrieved tx_ref from database: {tx_ref}")
                except ChapaPayment.DoesNotExist:
                    pass
        except Exception as e:
            logger.error(f"Error checking recent payments: {str(e)}")
    
    if not tx_ref:
        logger.error(f"No tx_ref found in callback. GET: {dict(request.GET)}, POST: {dict(request.POST)}")
        messages.error(request, "Invalid payment session.")
        return redirect('borrow:my_books')
    
    try:
        # Find payment by tx_ref
        chapa_payment = ChapaPayment.objects.select_related('payment').get(chapa_tx_ref=tx_ref)
        payment = chapa_payment.payment
        
        # Verify payment status is for current user
        if payment.user != request.user:
            messages.error(request, "Unauthorized access.")
            return redirect('borrow:my_books')
        
        # Check if already completed (by webhook)
        if payment.status == 'completed':
            messages.success(request, f"Payment of ETB {payment.amount} completed successfully!")
            return redirect('payments:payment_receipt', payment_id=payment.id)
        
        # If status is success or not provided, try to confirm payment
        if status == 'success' or not status:
            # Confirm payment
            if ChapaPaymentHandler.confirm_payment(payment, tx_ref):
                messages.success(request, f"Payment of ETB {payment.amount} completed successfully!")
                
                # Send success email to student + notify staff
                from apps.users.notifications import notify_payment_success, notify_admins_fine_paid
                notify_payment_success(payment)
                notify_admins_fine_paid(payment)
                
                return redirect('payments:payment_receipt', payment_id=payment.id)
            else:
                messages.error(request, "Payment verification failed. Please contact support.")
                return redirect('borrow:my_books')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Payment was not completed. Please try again.")
            return redirect('payments:select_method', record_id=payment.borrow_record.id)
            
    except ChapaPayment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('borrow:my_books')
    except Exception as e:
        logger.error(f"Error processing Chapa callback: {str(e)}")
        messages.error(request, "An error occurred processing your payment.")
        return redirect('borrow:my_books')


@csrf_exempt
def chapa_webhook(request):
    """
    Handle Chapa webhook events
    
    Note: Chapa may send webhooks as GET or POST requests.
    In test mode, Chapa often sends GET requests with query parameters.
    """
    try:
        logger.info(f"Chapa webhook received - Method: {request.method}")
        logger.info(f"GET params: {dict(request.GET)}")
        logger.info(f"POST body: {request.body.decode('utf-8') if request.body else 'empty'}")
        
        # Handle GET request (common in Chapa test mode)
        if request.method == 'GET':
            tx_ref = request.GET.get('trx_ref') or request.GET.get('tx_ref')
            status = request.GET.get('status')
            
            if tx_ref and status == 'success':
                # Process the payment
                try:
                    from apps.payments.models import ChapaPayment
                    chapa_payment = ChapaPayment.objects.select_related('payment').get(chapa_tx_ref=tx_ref)
                    payment = chapa_payment.payment
                    
                    # Verify and confirm payment
                    if ChapaPaymentHandler.confirm_payment(payment, tx_ref):
                        logger.info(f"Payment {payment.id} confirmed via GET webhook")
                        return HttpResponse(status=200)
                    else:
                        logger.error(f"Payment confirmation failed for {tx_ref}")
                        return HttpResponse(status=400)
                        
                except ChapaPayment.DoesNotExist:
                    logger.error(f"Payment not found for tx_ref: {tx_ref}")
                    return HttpResponse(status=404)
            
            # If not a success status, just acknowledge
            return HttpResponse(status=200)
        
        # Handle POST request (standard webhook)
        elif request.method == 'POST':
            payload = json.loads(request.body)
            result = ChapaPaymentHandler.handle_webhook(payload)
            
            if result['success']:
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=400)
        
        return HttpResponse(status=405)  # Method not allowed
        
    except Exception as e:
        logger.error(f"Error processing Chapa webhook: {str(e)}")
        return HttpResponse(status=400)


@login_required
def payment_history(request):
    """
    Display user's payment history
    """
    payments = Payment.objects.filter(user=request.user).select_related(
        'borrow_record', 'borrow_record__book'
    ).order_by('-created_at')
    
    context = {
        'payments': payments,
    }
    
    return render(request, 'payments/history.html', context)


@login_required
def payment_receipt(request, payment_id):
    """
    Display payment receipt
    """
    payment = get_object_or_404(
        Payment.objects.select_related('borrow_record', 'borrow_record__book', 'user'),
        id=payment_id,
        user=request.user
    )
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/receipt.html', context)


@login_required
def payment_cancel(request):
    """
    Handle payment cancellation
    """
    messages.info(request, "Payment was cancelled.")
    return redirect('borrow:my_books')
