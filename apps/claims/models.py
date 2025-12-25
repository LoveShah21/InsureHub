"""
Claim Lifecycle Management Models

This module handles the complete claim lifecycle:
- Claim: Main claim entity with status workflow
- ClaimDocument: Supporting documents for claims

Claim Status Flow:
SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED → SETTLED

Business Rules:
- amount_approved must be ≤ amount_requested
- amount_approved is set by Backoffice during APPROVED transition
- Settlement occurs only after APPROVED status
- Customers cannot modify amount_requested after submission
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


def generate_claim_number():
    """Generate unique claim number."""
    return f"CLM-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


class Claim(models.Model):
    """
    Insurance claim submitted against a policy.
    
    Status Flow:
    - SUBMITTED: Customer has submitted the claim
    - UNDER_REVIEW: Backoffice is reviewing
    - APPROVED: Claim approved (amount_approved set)
    - REJECTED: Claim rejected
    - SETTLED: Claim amount has been settled/paid
    - CLOSED: Claim is closed
    """
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SETTLED', 'Settled'),
        ('CLOSED', 'Closed'),
    ]
    
    CLAIM_TYPE_CHOICES = [
        ('ACCIDENT', 'Accident'),
        ('THEFT', 'Theft'),
        ('NATURAL_DISASTER', 'Natural Disaster'),
        ('MEDICAL', 'Medical'),
        ('DEATH', 'Death'),
        ('DAMAGE', 'Property Damage'),
        ('LIABILITY', 'Third Party Liability'),
        ('OTHER', 'Other'),
    ]
    
    # Core references
    claim_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_claim_number
    )
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.RESTRICT,
        related_name='claims'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='claims'
    )
    
    # Claim details
    claim_type = models.CharField(max_length=30, choices=CLAIM_TYPE_CHOICES)
    claim_description = models.TextField()
    incident_date = models.DateField()
    incident_location = models.TextField(blank=True)
    
    # Financial
    amount_requested = models.DecimalField(
        max_digits=15, decimal_places=2,
        help_text="Amount claimed by customer"
    )
    amount_approved = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Amount approved by Backoffice (must be ≤ amount_requested)"
    )
    amount_settled = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Amount actually settled"
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='SUBMITTED', db_index=True
    )
    rejection_reason = models.TextField(blank=True)
    
    # Workflow timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    review_started_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Workflow actors
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='submitted_claims'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_claims'
    )
    settled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='settled_claims'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claims'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['policy']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.claim_number} - {self.status}"
    
    def start_review(self, user):
        """Start reviewing the claim."""
        if self.status != 'SUBMITTED':
            raise ValueError("Only submitted claims can be reviewed.")
        
        self.status = 'UNDER_REVIEW'
        self.review_started_at = timezone.now()
        self.reviewed_by = user
        self.save()
    
    def approve(self, user, approved_amount):
        """
        Approve the claim.
        
        Business Rule: approved_amount must be ≤ amount_requested
        """
        if self.status not in ['SUBMITTED', 'UNDER_REVIEW']:
            raise ValueError("Cannot approve claim in this status.")
        
        if approved_amount > self.amount_requested:
            raise ValueError("Approved amount cannot exceed requested amount.")
        
        self.status = 'APPROVED'
        self.amount_approved = approved_amount
        self.approved_at = timezone.now()
        self.reviewed_by = user
        self.save()
    
    def reject(self, user, reason):
        """Reject the claim."""
        if self.status not in ['SUBMITTED', 'UNDER_REVIEW']:
            raise ValueError("Cannot reject claim in this status.")
        
        if not reason:
            raise ValueError("Rejection reason is required.")
        
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.rejected_at = timezone.now()
        self.reviewed_by = user
        self.save()
    
    def settle(self, user, settled_amount=None):
        """
        Settle the approved claim.
        
        Settlement only allowed after approval.
        """
        if self.status != 'APPROVED':
            raise ValueError("Only approved claims can be settled.")
        
        if not self.amount_approved:
            raise ValueError("Approved amount must be set before settlement.")
        
        self.status = 'SETTLED'
        self.amount_settled = settled_amount or self.amount_approved
        self.settled_at = timezone.now()
        self.settled_by = user
        self.save()
    
    def close(self, user):
        """Close the claim."""
        if self.status not in ['SETTLED', 'REJECTED']:
            raise ValueError("Only settled or rejected claims can be closed.")
        
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.save()


class ClaimDocument(models.Model):
    """
    Documents uploaded with insurance claims.
    
    Examples:
    - FIR copy
    - Medical reports
    - Repair bills
    - Photos of damage
    """
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('FIR_COPY', 'FIR Copy'),
        ('MEDICAL_REPORT', 'Medical Report'),
        ('HOSPITAL_BILL', 'Hospital Bill'),
        ('REPAIR_ESTIMATE', 'Repair Estimate'),
        ('REPAIR_BILL', 'Repair Bill'),
        ('DAMAGE_PHOTO', 'Damage Photos'),
        ('POLICE_REPORT', 'Police Report'),
        ('WITNESS_STATEMENT', 'Witness Statement'),
        ('ID_PROOF', 'Identity Proof'),
        ('OTHER', 'Other'),
    ]
    
    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE,
        related_name='documents'
    )
    
    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_TYPE_CHOICES, db_index=True
    )
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='claim_documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Verification
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS_CHOICES,
        default='PENDING', db_index=True
    )
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_claim_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_claim_documents'
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claim_documents'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.document_type} - {self.claim.claim_number}"
