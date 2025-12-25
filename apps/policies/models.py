"""
Policy Issuance & Payment Models

This module contains:
- Policy: Issued insurance policies
- Payment: Payment records (mock gateway)
- Invoice: Immutable invoice records

Payment uses a mock gateway for academic demonstration.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


def generate_policy_number():
    """Generate unique policy number."""
    return f"POL-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_payment_number():
    """Generate unique payment reference."""
    return f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def generate_invoice_number():
    """Generate unique invoice number."""
    return f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


class Policy(models.Model):
    """
    Issued insurance policy.
    
    Created after successful payment for an accepted quote.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('LAPSED', 'Lapsed'),
    ]
    
    # Core references
    policy_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_policy_number
    )
    quote = models.OneToOneField(
        'quotes.Quote', on_delete=models.RESTRICT,
        related_name='policy'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='policies'
    )
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.RESTRICT,
        related_name='policies'
    )
    insurance_company = models.ForeignKey(
        'catalog.InsuranceCompany', on_delete=models.RESTRICT,
        related_name='policies'
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True
    )
    
    # Policy details
    policy_start_date = models.DateField()
    policy_end_date = models.DateField()
    policy_tenure_months = models.PositiveIntegerField()
    
    # Financial
    premium_amount = models.DecimalField(max_digits=15, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_premium_with_gst = models.DecimalField(max_digits=15, decimal_places=2)
    sum_insured = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Versioning (for endorsements)
    policy_version = models.PositiveIntegerField(default=1)
    
    # Workflow
    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issued_policies'
    )
    
    # Renewal
    last_renewal_date = models.DateField(null=True, blank=True)
    next_renewal_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'policies'
        verbose_name_plural = 'Policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['policy_start_date']),
            models.Index(fields=['policy_end_date']),
        ]
    
    def __str__(self):
        return f"{self.policy_number} - {self.customer.user.email}"
    
    @property
    def is_active(self):
        """Check if policy is currently active."""
        today = timezone.now().date()
        return (
            self.status == 'ACTIVE' and
            self.policy_start_date <= today <= self.policy_end_date
        )
    
    @property
    def days_until_expiry(self):
        """Calculate days until policy expires."""
        today = timezone.now().date()
        if today > self.policy_end_date:
            return 0
        return (self.policy_end_date - today).days


class Payment(models.Model):
    """
    Payment records for policies.
    
    Integrated with Razorpay Sandbox for real payment processing.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    METHOD_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('UPI', 'UPI'),
    ]
    
    # References
    payment_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_payment_number
    )
    quote = models.ForeignKey(
        'quotes.Quote', on_delete=models.RESTRICT,
        related_name='payments'
    )
    policy = models.ForeignKey(
        'Policy', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='payments'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default='RAZORPAY'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True
    )
    
    # Razorpay-specific fields
    razorpay_order_id = models.CharField(
        max_length=100, unique=True, db_index=True, blank=True
    )
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    
    # Gateway response (stores full response for debugging)
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Failure handling
    failure_reason = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quote']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['razorpay_order_id']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - {self.status}"


class Invoice(models.Model):
    """
    Immutable invoice records.
    
    Generated after successful payment.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # References
    invoice_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_invoice_number
    )
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE,
        related_name='invoices'
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoice'
    )
    
    # Invoice details
    invoice_date = models.DateField()
    invoice_amount = models.DecimalField(max_digits=15, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_invoice_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT'
    )
    
    # PDF storage
    invoice_url = models.URLField(blank=True)
    
    # Workflow
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_invoices'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.policy.policy_number}"
