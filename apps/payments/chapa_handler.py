"""
Chapa Payment Handler
Handles all Chapa payment operations including payment initialization,
verification, and webhook processing.
"""

from chapa import Chapa
from django.conf import settings
import logging
import uuid
import requests

logger = logging.getLogger(__name__)

# Initialize Chapa
chapa = Chapa(settings.CHAPA_SECRET_KEY)


class ChapaPaymentHandler:
    """Handler for Chapa payment operations"""
    
    @staticmethod
    def initialize_payment(payment, callback_url, return_url):
        """
        Initialize a Chapa payment
        
        Args:
            payment: Payment model instance
            callback_url: URL for Chapa to send webhook
            return_url: URL to redirect user after payment
            
        Returns:
            dict: Payment initialization data including checkout_url
        """
        try:
            # Generate unique transaction reference
            tx_ref = f"LIB-{payment.id}-{uuid.uuid4().hex[:8]}"
            
            # Prepare payment data
            payment_data = {
                'amount': str(payment.amount),
                'currency': 'ETB',
                'email': payment.user.email,
                'first_name': payment.user.first_name or payment.user.username,
                'last_name': payment.user.last_name or '',
                'tx_ref': tx_ref,
                'callback_url': callback_url,
                'return_url': return_url,
                'customization': {
                    'title': 'Library Fine',  # Max 16 characters
                    'description': 'Fine payment',  # Simplified, no special chars
                }
            }
            
            # Initialize payment with Chapa
            response = chapa.initialize(**payment_data)
            
            if response['status'] == 'success':
                checkout_url = response['data']['checkout_url']
                
                logger.info(f"Chapa payment initialized: {tx_ref} for payment {payment.id}")
                
                return {
                    'success': True,
                    'checkout_url': checkout_url,
                    'tx_ref': tx_ref,
                }
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Chapa initialization failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                }
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error initializing Chapa payment: {error_str}")
            
            # Provide more helpful error messages
            if '401' in error_str or 'Unauthorized' in error_str:
                error_msg = "Invalid API Key or the business can't accept payments at the moment. Please verify your API key and ensure the account is active and able to process payments."
            elif '400' in error_str:
                error_msg = "Invalid payment data. Please contact support."
            elif 'connection' in error_str.lower() or 'timeout' in error_str.lower():
                error_msg = "Unable to connect to payment gateway. Please try again later."
            else:
                error_msg = "Payment service temporarily unavailable. Please try Stripe or contact support."
            
            return {
                'success': False,
                'error': error_msg,
            }
    
    @staticmethod
    def verify_payment(tx_ref):
        """
        Verify a Chapa payment
        
        Args:
            tx_ref: Transaction reference
            
        Returns:
            dict: Verification result
        """
        try:
            # Use direct API call instead of buggy library method
            import requests
            from django.conf import settings
            
            url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
            }
            
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            logger.info(f"Chapa verification response for {tx_ref}: {response_data}")
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                data = response_data.get('data', {})
                return {
                    'success': True,
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'tx_ref': data.get('tx_ref'),
                    'data': data,
                }
            else:
                error_msg = response_data.get('message', 'Verification failed')
                logger.error(f"Chapa verification failed for {tx_ref}: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                }
                
        except Exception as e:
            logger.error(f"Error verifying Chapa payment {tx_ref}: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
            }
    
    @staticmethod
    def confirm_payment(payment, tx_ref):
        """
        Confirm a payment after successful Chapa payment
        
        Args:
            payment: Payment model instance
            tx_ref: Transaction reference
            
        Returns:
            bool: Success status
        """
        try:
            # Verify payment with Chapa
            verification = ChapaPaymentHandler.verify_payment(tx_ref)
            
            if not verification['success']:
                logger.error(f"Could not verify payment {tx_ref}")
                return False
            
            if verification['status'] == 'success':
                # Update payment status
                payment.status = 'completed'
                payment.payment_gateway_response = verification['data']
                payment.save()
                
                # Mark fine as paid in borrow record (use update to bypass validation)
                from apps.borrow.models import BorrowRecord
                BorrowRecord.objects.filter(id=payment.borrow_record.id).update(fine_paid=True)
                
                # Log payment activity
                from apps.dashboard.utils import log_activity
                log_activity(
                    payment.user,
                    'payment_completed',
                    f'Chapa payment completed: ETB {payment.amount} for book "{payment.borrow_record.book.title}" (Transaction: {payment.transaction_id})',
                    None
                )
                
                logger.info(f"Payment {payment.id} confirmed successfully")
                return True
            else:
                logger.warning(f"Payment {tx_ref} status is {verification['status']}")
                payment.status = 'failed'
                payment.save()
                return False
                
        except Exception as e:
            logger.error(f"Error confirming payment {payment.id}: {str(e)}")
            return False
    
    @staticmethod
    def handle_webhook(payload):
        """
        Handle Chapa webhook events
        
        Args:
            payload: Webhook payload data
            
        Returns:
            dict: Response data
        """
        try:
            logger.info(f"Chapa webhook received: {payload.get('event')}")
            
            event_type = payload.get('event')
            
            if event_type == 'charge.success':
                ChapaPaymentHandler._handle_payment_success(payload)
            elif event_type == 'charge.failed':
                ChapaPaymentHandler._handle_payment_failure(payload)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error handling Chapa webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _handle_payment_success(payload):
        """Handle successful payment webhook"""
        from apps.payments.models import Payment, ChapaPayment
        
        try:
            tx_ref = payload.get('tx_ref')
            if not tx_ref:
                logger.error("No tx_ref in webhook payload")
                return
            
            # Find payment by tx_ref
            chapa_payment = ChapaPayment.objects.select_related('payment').get(chapa_tx_ref=tx_ref)
            payment = chapa_payment.payment
            
            # Update payment status
            payment.status = 'completed'
            payment.payment_gateway_response = payload
            payment.save()
            
            # Mark fine as paid (use update to bypass validation)
            from apps.borrow.models import BorrowRecord
            BorrowRecord.objects.filter(id=payment.borrow_record.id).update(fine_paid=True)
            
            # Send success email
            from apps.users.notifications import notify_payment_success
            notify_payment_success(payment)
            
            logger.info(f"Payment {payment.id} marked as completed via webhook")
            
        except ChapaPayment.DoesNotExist:
            logger.error(f"Payment not found for webhook tx_ref: {tx_ref}")
        except Exception as e:
            logger.error(f"Error handling payment success webhook: {str(e)}")
    
    @staticmethod
    def _handle_payment_failure(payload):
        """Handle failed payment webhook"""
        from apps.payments.models import Payment, ChapaPayment
        
        try:
            tx_ref = payload.get('tx_ref')
            if not tx_ref:
                logger.error("No tx_ref in webhook payload")
                return
            
            # Find payment by tx_ref
            chapa_payment = ChapaPayment.objects.select_related('payment').get(chapa_tx_ref=tx_ref)
            payment = chapa_payment.payment
            
            payment.status = 'failed'
            payment.payment_gateway_response = payload
            payment.save()
            
            # Send failure email
            from apps.users.notifications import notify_payment_failure
            notify_payment_failure(payment)
            
            logger.info(f"Payment {payment.id} marked as failed via webhook")
            
        except ChapaPayment.DoesNotExist:
            logger.error(f"Payment not found for webhook tx_ref: {tx_ref}")
        except Exception as e:
            logger.error(f"Error handling payment failure webhook: {str(e)}")
