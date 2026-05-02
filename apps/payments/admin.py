from django.contrib import admin
from apps.payments.models import Payment, StripePayment, ChapaPayment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'currency', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['transaction_id', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'payment_gateway_response']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'user', 'borrow_record', 'transaction_id')
        }),
        ('Amount Details', {
            'fields': ('amount', 'currency', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'payment_gateway_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    list_display = ['payment', 'stripe_payment_intent_id', 'stripe_charge_id']
    search_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'payment__transaction_id']
    readonly_fields = ['payment', 'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id']


@admin.register(ChapaPayment)
class ChapaPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment', 'chapa_tx_ref', 'payment_method_type']
    search_fields = ['chapa_tx_ref', 'payment__transaction_id']
    readonly_fields = ['payment', 'chapa_tx_ref', 'chapa_checkout_url']
    list_filter = ['payment_method_type']

