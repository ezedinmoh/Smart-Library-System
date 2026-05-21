"""
Stripe Payment Handler
Handles all Stripe payment operations including payment intent creation,
confirmation, and webhook processing.
"""

import stripe
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Payment intents in these states can be reused (e.g. user re-opens Stripe form)
REUSABLE_PAYMENT_INTENT_STATUSES = frozenset({
    'requires_payment_method',
    'requires_confirmation',
    'requires_action',
})

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentHandler:
    """Handler for Stripe payment operations"""
    
    @staticmethod
    def create_payment_intent(payment):
        """
        Create a Stripe Payment Intent
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict: Payment intent data including client_secret
        """
        try:
            # Get exchange rate from system settings
            from apps.dashboard.models import SystemSettings
            system_settings = SystemSettings.get_settings()
            
            # Convert ETB to USD if needed
            amount_usd = payment.amount
            processing_fee_usd = Decimal('0')
            
            if payment.currency == 'ETB':
                amount_usd = Decimal(str(payment.amount)) * Decimal(str(system_settings.etb_to_usd_rate))
                amount_usd = amount_usd.quantize(Decimal('0.01'))
                
                # Stripe minimum amount is $0.50 USD
                STRIPE_MINIMUM_USD = Decimal('0.50')
                if amount_usd < STRIPE_MINIMUM_USD:
                    # Add processing fee to meet minimum
                    processing_fee_usd = STRIPE_MINIMUM_USD - amount_usd
                    amount_usd = STRIPE_MINIMUM_USD
                    logger.info(f"Added processing fee of ${processing_fee_usd} to meet Stripe minimum")
            
            # Stripe requires amount in cents
            amount_cents = int(amount_usd * 100)
            
            # Payment Element + Express Checkout (cards, wallets, BNPL, bank redirects, etc.)
            intent_params = {
                'amount': amount_cents,
                'currency': 'usd',
                'automatic_payment_methods': {
                    'enabled': True,
                    'allow_redirects': 'always',
                },
                'metadata': {
                    'payment_id': str(payment.id),
                    'user_id': str(payment.user.id),
                    'borrow_record_id': str(payment.borrow_record.id),
                    'original_amount': str(payment.amount),
                    'original_currency': payment.currency,
                    'processing_fee_usd': str(processing_fee_usd),
                },
                'description': f"Library Fine Payment - {payment.borrow_record.book.title}",
            }
            if payment.user.email:
                intent_params['receipt_email'] = payment.user.email

            intent = stripe.PaymentIntent.create(**intent_params)
            
            logger.info(f"Stripe Payment Intent created: {intent.id} for payment {payment.id}")
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount_usd': float(amount_usd),
                'processing_fee_usd': float(processing_fee_usd),
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Error creating Stripe payment intent: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
            }
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Retrieve a Stripe Payment Intent
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            PaymentIntent object or None
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent {payment_intent_id}: {str(e)}")
            return None
    
    @staticmethod
    def confirm_payment(payment, payment_intent_id):
        """
        Confirm a payment after successful Stripe payment
        
        Args:
            payment: Payment model instance
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            bool: Success status
        """
        try:
            from apps.payments.models import StripePayment

            # Retrieve payment intent to verify status
            intent = StripePaymentHandler.retrieve_payment_intent(payment_intent_id)
            
            if not intent:
                logger.error(f"Could not retrieve payment intent {payment_intent_id}")
                return False
            
            if intent.status == 'succeeded':
                if payment.status == 'completed':
                    logger.info(f"Payment {payment.id} already completed, skipping confirm")
                    return True

                # Update payment status
                payment.status = 'completed'
                payment.payment_gateway_response = {
                    'payment_intent_id': intent.id,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                }
                payment.save()

                # Persist Stripe-specific IDs for support and receipts
                charge_id = intent.latest_charge
                if isinstance(charge_id, str):
                    charge_id_str = charge_id
                elif charge_id:
                    charge_id_str = str(charge_id)
                else:
                    charge_id_str = ''

                StripePayment.objects.update_or_create(
                    payment=payment,
                    defaults={
                        'stripe_payment_intent_id': intent.id,
                        'stripe_charge_id': charge_id_str,
                        'stripe_payment_method_id': intent.payment_method or '',
                    },
                )
                
                # Mark fine as paid in borrow record (use update to bypass validation)
                from apps.borrow.models import BorrowRecord
                BorrowRecord.objects.filter(id=payment.borrow_record.id).update(fine_paid=True)
                
                # Log payment activity
                from apps.dashboard.utils import log_activity
                log_activity(
                    payment.user,
                    'payment_completed',
                    f'Stripe payment completed: ETB {payment.amount} for book "{payment.borrow_record.book.title}" (Transaction: {payment.transaction_id})',
                    None
                )
                
                logger.info(f"Payment {payment.id} confirmed successfully")
                return True
            else:
                logger.warning(f"Payment intent {payment_intent_id} status is {intent.status}")
                return False
                
        except Exception as e:
            logger.error(f"Error confirming payment {payment.id}: {str(e)}")
            return False
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        """
        Handle Stripe webhook events
        
        Args:
            payload: Raw request body
            sig_header: Stripe signature header
            
        Returns:
            dict: Response data
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(f"Stripe webhook received: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                StripePaymentHandler._handle_payment_success(payment_intent)
                
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                StripePaymentHandler._handle_payment_failure(payment_intent)
            
            return {'success': True}
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _handle_payment_success(payment_intent):
        """Handle successful payment webhook"""
        from apps.payments.models import Payment, StripePayment
        
        try:
            payment_id = payment_intent['metadata'].get('payment_id')
            if not payment_id:
                logger.error("No payment_id in webhook metadata")
                return
            
            payment = Payment.objects.get(id=payment_id)

            if payment.status == 'completed':
                logger.info(f"Payment {payment.id} already completed via webhook, skipping")
                return
            
            # Update payment status
            payment.status = 'completed'
            payment.payment_gateway_response = {
                'payment_intent_id': payment_intent['id'],
                'status': payment_intent['status'],
                'amount': payment_intent['amount'],
                'currency': payment_intent['currency'],
            }
            payment.save()
            
            charge_id = payment_intent.get('latest_charge', '')
            if not charge_id:
                charges = payment_intent.get('charges', {}).get('data', [])
                charge_id = charges[0].get('id', '') if charges else ''

            # Update or create Stripe payment details
            StripePayment.objects.update_or_create(
                payment=payment,
                defaults={
                    'stripe_payment_intent_id': payment_intent['id'],
                    'stripe_charge_id': charge_id or '',
                    'stripe_payment_method_id': payment_intent.get('payment_method', '') or '',
                }
            )
            
            # Mark fine as paid
            payment.borrow_record.fine_paid = True
            payment.borrow_record.save()
            
            # Send success email
            from apps.users.notifications import notify_payment_success
            notify_payment_success(payment)
            
            logger.info(f"Payment {payment.id} marked as completed via webhook")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for webhook: {payment_intent['metadata'].get('payment_id')}")
        except Exception as e:
            logger.error(f"Error handling payment success webhook: {str(e)}")
    
    @staticmethod
    def _handle_payment_failure(payment_intent):
        """Handle failed payment webhook"""
        from apps.payments.models import Payment
        
        try:
            payment_id = payment_intent['metadata'].get('payment_id')
            if not payment_id:
                logger.error("No payment_id in webhook metadata")
                return
            
            payment = Payment.objects.get(id=payment_id)
            payment.status = 'failed'
            payment.payment_gateway_response = {
                'payment_intent_id': payment_intent['id'],
                'status': payment_intent['status'],
                'error': payment_intent.get('last_payment_error', {}).get('message', 'Payment failed'),
            }
            payment.save()
            
            # Send failure email
            from apps.users.notifications import notify_payment_failure
            notify_payment_failure(payment)
            
            logger.info(f"Payment {payment.id} marked as failed via webhook")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for webhook: {payment_intent['metadata'].get('payment_id')}")
        except Exception as e:
            logger.error(f"Error handling payment failure webhook: {str(e)}")
