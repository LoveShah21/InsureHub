"""
Claims Workflow Service

This module provides business logic for claims processing:
- Status history recording
- Approval threshold checking
- Settlement generation
"""

from decimal import Decimal
from datetime import date
from django.utils import timezone
from django.db import transaction

from apps.claims.models import (
    Claim, ClaimStatusHistory, ClaimAssessment, ClaimSettlement
)
from apps.catalog.models import ClaimApprovalThreshold


class ClaimsWorkflowService:
    """
    Service for managing claim workflow and business logic.
    
    Implements:
    - Status transition validation
    - Status history recording
    - Approval threshold checking
    - Settlement creation
    """
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        'SUBMITTED': ['UNDER_REVIEW'],
        'UNDER_REVIEW': ['APPROVED', 'REJECTED', 'SURVEYOR_ASSIGNED'],
        'SURVEYOR_ASSIGNED': ['UNDER_INVESTIGATION'],
        'UNDER_INVESTIGATION': ['ASSESSED'],
        'ASSESSED': ['APPROVED', 'REJECTED'],
        'APPROVED': ['SETTLED'],
        'SETTLED': ['CLOSED'],
        'REJECTED': ['CLOSED'],
        'CLOSED': [],
    }
    
    def __init__(self, claim: Claim):
        self.claim = claim
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new status is valid."""
        current = self.claim.status
        return new_status in self.VALID_TRANSITIONS.get(current, [])
    
    def record_status_change(
        self,
        old_status: str,
        new_status: str,
        user,
        reason: str = '',
        request=None
    ):
        """Record a status change in history."""
        ip_address = None
        user_agent = ''
        
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return ClaimStatusHistory.objects.create(
            claim=self.claim,
            old_status=old_status,
            new_status=new_status,
            status_change_reason=reason,
            changed_by=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_approval_threshold(self) -> ClaimApprovalThreshold:
        """
        Get the approval threshold for this claim's amount.
        
        Returns the threshold that determines who can approve this claim.
        """
        amount = self.claim.amount_requested
        insurance_type = self.claim.policy.quote.application.insurance_type
        
        threshold = ClaimApprovalThreshold.objects.filter(
            insurance_type=insurance_type,
            min_claim_amount__lte=amount,
            max_claim_amount__gte=amount,
            is_active=True
        ).first()
        
        return threshold
    
    def can_user_approve(self, user) -> bool:
        """
        Check if user has authority to approve this claim.
        
        Compares user's role against required approval level.
        """
        threshold = self.get_approval_threshold()
        if not threshold:
            # No threshold defined - default to needing ADMIN
            return user.user_roles.filter(role__role_name='ADMIN').exists()
        
        required_role = threshold.required_approver_role
        return user.user_roles.filter(role=required_role).exists()
    
    @transaction.atomic
    def transition_status(
        self,
        new_status: str,
        user,
        reason: str = '',
        approved_amount: Decimal = None,
        request=None
    ):
        """
        Transition claim to new status with validation.
        
        Records history and performs status-specific actions.
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.claim.status} to {new_status}"
            )
        
        old_status = self.claim.status
        
        # Status-specific logic
        if new_status == 'UNDER_REVIEW':
            self.claim.review_started_at = timezone.now()
            self.claim.reviewed_by = user
        
        elif new_status == 'APPROVED':
            if not self.can_user_approve(user):
                raise ValueError("You don't have authority to approve this claim amount.")
            
            if approved_amount is None:
                raise ValueError("Approved amount is required.")
            if approved_amount > self.claim.amount_requested:
                raise ValueError("Approved amount cannot exceed requested amount.")
            
            self.claim.amount_approved = approved_amount
            self.claim.approved_at = timezone.now()
            self.claim.reviewed_by = user
        
        elif new_status == 'REJECTED':
            if not reason:
                raise ValueError("Rejection reason is required.")
            self.claim.rejection_reason = reason
            self.claim.rejected_at = timezone.now()
            self.claim.reviewed_by = user
        
        elif new_status == 'SETTLED':
            if not self.claim.amount_approved:
                raise ValueError("Claim must be approved before settlement.")
            self.claim.amount_settled = self.claim.amount_approved
            self.claim.settled_at = timezone.now()
            self.claim.settled_by = user
        
        elif new_status == 'CLOSED':
            self.claim.closed_at = timezone.now()
        
        self.claim.status = new_status
        self.claim.save()
        
        # Record history
        self.record_status_change(old_status, new_status, user, reason, request)
        
        return self.claim
    
    @transaction.atomic
    def assign_surveyor(self, surveyor_user, assessment_date: date = None):
        """
        Assign a surveyor and create assessment record.
        
        Creates a pending ClaimAssessment.
        """
        if self.claim.status != 'UNDER_REVIEW':
            raise ValueError("Surveyor can only be assigned to claims under review.")
        
        assessment_date = assessment_date or date.today()
        
        # Create assessment record
        assessment = ClaimAssessment.objects.create(
            claim=self.claim,
            surveyor=surveyor_user,
            assessment_date=assessment_date,
            damage_assessment='',
            assessment_status='PENDING'
        )
        
        # Update claim status
        old_status = self.claim.status
        self.claim.status = 'SURVEYOR_ASSIGNED'
        self.claim.save()
        
        self.record_status_change(
            old_status, 'SURVEYOR_ASSIGNED', surveyor_user,
            f"Surveyor assigned: {surveyor_user.email}"
        )
        
        return assessment
    
    @transaction.atomic
    def record_assessment(
        self,
        assessment: ClaimAssessment,
        damage_desc: str,
        loss_amount: Decimal,
        deductible: Decimal = None,
        findings: dict = None
    ):
        """
        Record surveyor's assessment findings.
        """
        deductible = deductible or Decimal('0.00')
        findings = findings or {}
        
        assessment.damage_assessment = damage_desc
        assessment.loss_amount_assessed = loss_amount
        assessment.deductible_applicable = deductible
        assessment.assessment_findings = findings
        assessment.assessment_status = 'COMPLETED'
        assessment.calculate_net_amount()
        
        # Update claim status
        if self.claim.status == 'UNDER_INVESTIGATION':
            old_status = self.claim.status
            self.claim.status = 'ASSESSED'
            self.claim.save()
            
            self.record_status_change(
                old_status, 'ASSESSED', assessment.surveyor,
                f"Assessment completed. Net amount: {assessment.net_claim_amount}"
            )
        
        return assessment
    
    @transaction.atomic
    def create_settlement(
        self,
        user,
        settlement_method: str = 'BANK_TRANSFER',
        bank_details: dict = None
    ) -> ClaimSettlement:
        """
        Create settlement record for approved claim.
        
        Must be called after claim is approved.
        """
        if self.claim.status != 'APPROVED':
            raise ValueError("Settlement can only be created for approved claims.")
        
        if not self.claim.amount_approved:
            raise ValueError("Approved amount is required.")
        
        bank_details = bank_details or {}
        
        settlement = ClaimSettlement.objects.create(
            claim=self.claim,
            settlement_amount=self.claim.amount_approved,
            settlement_method=settlement_method,
            bank_account_number=bank_details.get('account_number', ''),
            bank_name=bank_details.get('bank_name', ''),
            bank_ifsc_code=bank_details.get('ifsc_code', ''),
            account_holder_name=bank_details.get('holder_name', ''),
            settlement_approved_by=user,
            settlement_status='PENDING'
        )
        
        return settlement
    
    def get_sla_status(self) -> dict:
        """
        Check if claim is within SLA.
        
        Returns SLA status and days remaining/overdue.
        """
        from apps.catalog.models import BusinessConfiguration
        
        sla_days = BusinessConfiguration.get_int('CLAIM_SLA_DAYS', 15)
        
        if self.claim.status in ['SETTLED', 'CLOSED', 'REJECTED']:
            # Claim is complete
            if self.claim.settled_at:
                processing_days = (self.claim.settled_at.date() - self.claim.submitted_at.date()).days
            elif self.claim.rejected_at:
                processing_days = (self.claim.rejected_at.date() - self.claim.submitted_at.date()).days
            else:
                processing_days = 0
            
            return {
                'status': 'COMPLETED',
                'processing_days': processing_days,
                'within_sla': processing_days <= sla_days
            }
        
        # Claim is still in progress
        days_elapsed = (date.today() - self.claim.submitted_at.date()).days
        days_remaining = sla_days - days_elapsed
        
        return {
            'status': 'IN_PROGRESS',
            'days_elapsed': days_elapsed,
            'days_remaining': max(0, days_remaining),
            'within_sla': days_remaining >= 0,
            'sla_days': sla_days
        }
