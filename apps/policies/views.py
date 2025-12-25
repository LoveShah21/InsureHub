"""
Views for Policy and Payment modules.

Provides API endpoints for:
- Policy listing and details
- Payment order creation (Razorpay)
- Payment verification (Razorpay)
- Invoice viewing

CRITICAL: Payment verification is CSRF-exempt but signature-verified.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from datetime import date
import json

from apps.accounts.permissions import IsAdminOrBackoffice
from apps.quotes.models import Quote
from apps.notifications.service import notification_service

from .models import Policy, Payment, Invoice
from .serializers import (
    PolicySerializer,
    PolicyListSerializer,
    PaymentSerializer,
    InvoiceSerializer,
)
from .payment_gateway import razorpay_gateway


class PolicyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for policies.
    
    GET /api/v1/policies/      - List customer's policies
    GET /api/v1/policies/{id}/ - Get policy details
    GET /api/v1/policies/all/  - List all policies (Admin/Backoffice)
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Backoffice sees all
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            return Policy.objects.select_related(
                'customer__user', 'insurance_type', 'insurance_company'
            ).all()
        
        # Customers see only their own
        return Policy.objects.select_related(
            'customer__user', 'insurance_type', 'insurance_company'
        ).filter(customer__user=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PolicyListSerializer
        return PolicySerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrBackoffice])
    def all(self, request):
        """List all policies (Admin/Backoffice only)."""
        policies = Policy.objects.select_related(
            'customer__user', 'insurance_company'
        ).all()
        
        # Filter by status
        policy_status = request.query_params.get('status')
        if policy_status:
            policies = policies.filter(status=policy_status)
        
        page = self.paginate_queryset(policies)
        if page is not None:
            serializer = PolicyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PolicyListSerializer(policies, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    """
    Create a Razorpay order for payment.
    
    POST /api/v1/payments/create-order/
    Body: { "quote_id": 123 }
    
    Returns: { "order_id": "order_xxx", "amount": 15000, "currency": "INR" }
    """
    quote_id = request.data.get('quote_id')
    
    if not quote_id:
        return Response(
            {'error': 'quote_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        quote = Quote.objects.select_related('customer').get(id=quote_id)
    except Quote.DoesNotExist:
        return Response(
            {'error': 'Quote not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check ownership
    if quote.customer.user != request.user:
        return Response(
            {'error': 'You can only pay for your own quotes.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check quote status
    if quote.status != 'ACCEPTED':
        return Response(
            {'error': 'Quote must be accepted before payment.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already paid
    if hasattr(quote, 'policy'):
        return Response(
            {'error': 'This quote already has a policy.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check for existing pending payment
    existing_payment = Payment.objects.filter(
        quote=quote,
        status__in=['PENDING', 'INITIATED']
    ).first()
    
    if existing_payment and existing_payment.razorpay_order_id:
        # Return existing order
        return Response({
            'order_id': existing_payment.razorpay_order_id,
            'amount': int(existing_payment.payment_amount * 100),
            'currency': 'INR',
            'payment_id': existing_payment.id
        })
    
    # Create Razorpay order
    try:
        amount = float(quote.total_premium_with_gst)
        order = razorpay_gateway.create_order(
            amount=amount,
            receipt_id=quote.quote_number
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to create order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Create payment record
    payment = Payment.objects.create(
        quote=quote,
        customer=quote.customer,
        payment_amount=quote.total_premium_with_gst,
        payment_method='RAZORPAY',
        status='INITIATED',
        razorpay_order_id=order['id']
    )
    
    return Response({
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'payment_id': payment.id
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # CSRF exempt, but signature verified
def verify_razorpay_payment(request):
    """
    Verify Razorpay payment signature and issue policy.
    
    POST /api/v1/payments/verify/
    Body: {
        "razorpay_payment_id": "pay_xxx",
        "razorpay_order_id": "order_xxx",
        "razorpay_signature": "xxx"
    }
    
    SECURITY: This endpoint is CSRF-exempt because:
    1. Razorpay signature verification replaces CSRF
    2. Signature uses HMAC-SHA256 with server-side secret
    3. Only valid Razorpay callbacks succeed
    
    IDEMPOTENCY: If payment already processed, returns existing policy.
    """
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return Response(
            {'success': False, 'error': 'Missing payment details.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find payment record
    try:
        payment = Payment.objects.select_related(
            'quote__customer__user',
            'quote__insurance_type',
            'quote__insurance_company'
        ).get(razorpay_order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Payment record not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # IDEMPOTENCY CHECK: If already successful, return existing policy
    if payment.status == 'SUCCESS':
        policy = payment.policy
        return Response({
            'success': True,
            'message': 'Payment already processed.',
            'policy_number': policy.policy_number if policy else None
        })
    
    # Only process if in valid state
    if payment.status not in ['PENDING', 'INITIATED']:
        return Response(
            {'success': False, 'error': f'Invalid payment state: {payment.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify signature
    is_valid = razorpay_gateway.verify_payment(
        order_id=razorpay_order_id,
        payment_id=razorpay_payment_id,
        signature=razorpay_signature
    )
    
    if not is_valid:
        # Signature verification failed
        payment.status = 'FAILED'
        payment.failure_reason = 'Signature verification failed'
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.save()
        
        return Response({
            'success': False,
            'error': 'Payment verification failed.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Signature valid - process payment atomically
    with transaction.atomic():
        quote = payment.quote
        
        # Update payment
        payment.status = 'SUCCESS'
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.payment_date = timezone.now()
        payment.save()
        
        # Create policy
        start_date = date.today()
        tenure_months = quote.policy_tenure_months
        
        from dateutil.relativedelta import relativedelta
        end_date = start_date + relativedelta(months=tenure_months)
        
        policy = Policy.objects.create(
            quote=quote,
            customer=quote.customer,
            insurance_type=quote.insurance_type,
            insurance_company=quote.insurance_company,
            status='ACTIVE',
            policy_start_date=start_date,
            policy_end_date=end_date,
            policy_tenure_months=tenure_months,
            premium_amount=quote.final_premium,
            gst_amount=quote.gst_amount,
            total_premium_with_gst=quote.total_premium_with_gst,
            sum_insured=quote.sum_insured,
            issued_at=timezone.now(),
            next_renewal_date=end_date
        )
        
        # Link payment to policy
        payment.policy = policy
        payment.save()
        
        # Create invoice
        invoice = Invoice.objects.create(
            policy=policy,
            payment=payment,
            invoice_date=date.today(),
            invoice_amount=quote.final_premium,
            gst_amount=quote.gst_amount,
            total_invoice_amount=quote.total_premium_with_gst,
            status='PAID'
        )
        
        # Send notification
        try:
            notification_service.notify_policy_issued(policy)
        except Exception:
            pass  # Don't fail payment for notification errors
    
    return Response({
        'success': True,
        'message': 'Payment verified. Policy issued!',
        'policy_number': policy.policy_number,
        'invoice_number': invoice.invoice_number
    })


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing payments.
    
    GET /api/v1/payments/      - List customer's payments
    GET /api/v1/payments/{id}/ - Get payment details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            return Payment.objects.all()
        
        return Payment.objects.filter(customer__user=user)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for invoices.
    
    GET /api/v1/invoices/      - List customer's invoices
    GET /api/v1/invoices/{id}/ - Get invoice details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            return Invoice.objects.select_related('policy', 'payment').all()
        
        return Invoice.objects.select_related('policy', 'payment').filter(
            policy__customer__user=user
        )
