"""
Insurance Application Models

This module handles the insurance application lifecycle:
- InsuranceApplication: Main application entity
- ApplicationDocument: Supporting documents for applications

Application Status Flow:
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


def generate_application_number():
    """Generate unique application number."""
    return f"APP-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


class InsuranceApplication(models.Model):
    """
    Insurance application submitted by customers.
    
    Status Flow:
    - DRAFT: Initial state, customer is still filling
    - SUBMITTED: Customer has completed and submitted
    - UNDER_REVIEW: Backoffice is reviewing
    - APPROVED: Application approved, ready for quote generation
    - REJECTED: Application rejected
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Core fields
    application_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_application_number
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='applications'
    )
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.RESTRICT,
        related_name='applications'
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    rejection_reason = models.TextField(blank=True)
    
    # Application data (flexible JSON for dynamic forms)
    application_data = models.JSONField(
        default=dict, blank=True,
        help_text="Dynamic form data based on insurance type"
    )
    
    # Coverage requirements
    requested_coverage_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    policy_tenure_months = models.PositiveIntegerField(default=12)
    
    # Budget preference (for quote filtering)
    budget_min = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    budget_max = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    
    # Workflow timestamps
    submission_date = models.DateTimeField(null=True, blank=True)
    review_start_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    
    # Workflow actors
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='submitted_applications'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_applications'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['insurance_type']),
            models.Index(fields=['status']),
            models.Index(fields=['submission_date']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.customer.user.email}"
    
    def submit(self, user):
        """Submit the application for review."""
        if self.status != 'DRAFT':
            raise ValueError("Only draft applications can be submitted.")
        
        self.status = 'SUBMITTED'
        self.submission_date = timezone.now()
        self.submitted_by = user
        self.save()
    
    def start_review(self, user):
        """Start reviewing the application."""
        if self.status != 'SUBMITTED':
            raise ValueError("Only submitted applications can be reviewed.")
        
        self.status = 'UNDER_REVIEW'
        self.review_start_date = timezone.now()
        self.reviewed_by = user
        self.save()
    
    def approve(self, user):
        """Approve the application."""
        if self.status not in ['SUBMITTED', 'UNDER_REVIEW']:
            raise ValueError("Cannot approve application in this status.")
        
        self.status = 'APPROVED'
        self.approval_date = timezone.now()
        self.reviewed_by = user
        self.save()
    
    def reject(self, user, reason):
        """Reject the application."""
        if self.status not in ['SUBMITTED', 'UNDER_REVIEW']:
            raise ValueError("Cannot reject application in this status.")
        
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.reviewed_by = user
        self.save()


class ApplicationDocument(models.Model):
    """
    Documents uploaded with insurance applications.
    
    Examples:
    - Identity proof (PAN, Aadhaar)
    - Address proof
    - Previous policy documents
    - Vehicle RC (for motor insurance)
    - Medical reports (for health insurance)
    """
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('ID_PROOF', 'Identity Proof'),
        ('ADDRESS_PROOF', 'Address Proof'),
        ('PAN_CARD', 'PAN Card'),
        ('AADHAR_CARD', 'Aadhaar Card'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('VEHICLE_RC', 'Vehicle RC'),
        ('PREVIOUS_POLICY', 'Previous Policy'),
        ('MEDICAL_REPORT', 'Medical Report'),
        ('INCOME_PROOF', 'Income Proof'),
        ('OTHER', 'Other'),
    ]
    
    application = models.ForeignKey(
        InsuranceApplication, on_delete=models.CASCADE,
        related_name='documents'
    )
    
    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_TYPE_CHOICES, db_index=True
    )
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='application_documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Verification
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS_CHOICES,
        default='PENDING', db_index=True
    )
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_documents'
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'application_documents'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.document_type} - {self.application.application_number}"
    
    def verify(self, user, notes=''):
        """Mark document as verified."""
        self.verification_status = 'VERIFIED'
        self.verification_notes = notes
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
    
    def reject(self, user, notes):
        """Mark document as rejected."""
        self.verification_status = 'REJECTED'
        self.verification_notes = notes
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
