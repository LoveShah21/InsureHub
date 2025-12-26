"""
Analytics Models

This module contains models for system analytics:
- PolicyAnalytics: Policy metrics by date/type
- ClaimAnalytics: Claim metrics
- RevenueAnalytics: Revenue tracking
- CustomerRiskAnalytics: Risk distribution

These tables are populated by aggregation jobs/services.
"""

from django.db import models
from decimal import Decimal


class PolicyAnalytics(models.Model):
    """
    Aggregated policy metrics by date, type, and company.
    
    Tracks policies issued, active, expired, cancelled.
    """
    analytics_date = models.DateField(db_index=True)
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.CASCADE,
        related_name='policy_analytics'
    )
    insurance_company = models.ForeignKey(
        'catalog.InsuranceCompany', on_delete=models.CASCADE,
        null=True, blank=True, related_name='policy_analytics'
    )
    
    # Counts
    policies_issued = models.PositiveIntegerField(default=0)
    policies_active = models.PositiveIntegerField(default=0)
    policies_expired = models.PositiveIntegerField(default=0)
    policies_cancelled = models.PositiveIntegerField(default=0)
    policies_renewed = models.PositiveIntegerField(default=0)
    
    # Financial
    total_sum_insured = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_premium_collected = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    average_premium = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'policy_analytics'
        unique_together = ['analytics_date', 'insurance_type', 'insurance_company']
        ordering = ['-analytics_date']
    
    def __str__(self):
        return f"Policy Analytics: {self.analytics_date} - {self.insurance_type.type_code}"


class ClaimAnalytics(models.Model):
    """
    Aggregated claim metrics by date and type.
    
    Tracks claims submitted, approved, rejected, settled.
    """
    analytics_date = models.DateField(db_index=True)
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.CASCADE,
        related_name='claim_analytics'
    )
    
    # Counts
    claims_submitted = models.PositiveIntegerField(default=0)
    claims_approved = models.PositiveIntegerField(default=0)
    claims_rejected = models.PositiveIntegerField(default=0)
    claims_settled = models.PositiveIntegerField(default=0)
    claims_pending = models.PositiveIntegerField(default=0)
    
    # Financial
    total_claimed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_approved_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_settled_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    average_claim_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    # Ratios
    claim_approval_ratio = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.00')
    )
    claim_settlement_ratio = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.00')
    )
    
    # Processing time (days)
    average_processing_days = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claim_analytics'
        unique_together = ['analytics_date', 'insurance_type']
        ordering = ['-analytics_date']
    
    def __str__(self):
        return f"Claim Analytics: {self.analytics_date} - {self.insurance_type.type_code}"


class RevenueAnalytics(models.Model):
    """
    Revenue tracking by date.
    
    Aggregates premium, GST, and payment data.
    """
    analytics_date = models.DateField(unique=True, db_index=True)
    
    # Revenue
    gross_premium = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    gst_collected = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    net_premium = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    
    # Payments
    total_payments_received = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    payments_pending = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    payments_failed = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    
    # Claims payout
    claims_payout = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    
    # Counts
    transaction_count = models.PositiveIntegerField(default=0)
    successful_payments = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'revenue_analytics'
        ordering = ['-analytics_date']
    
    def __str__(self):
        return f"Revenue: {self.analytics_date} - ₹{self.gross_premium}"


class CustomerRiskAnalytics(models.Model):
    """
    Risk distribution analytics by date.
    
    Tracks customer risk profile distribution.
    """
    analytics_date = models.DateField(unique=True, db_index=True)
    
    # Risk distribution counts
    low_risk_count = models.PositiveIntegerField(default=0)
    medium_risk_count = models.PositiveIntegerField(default=0)
    high_risk_count = models.PositiveIntegerField(default=0)
    critical_risk_count = models.PositiveIntegerField(default=0)
    
    # Average scores
    average_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50.00')
    )
    
    # Risk-premium correlation
    low_risk_avg_premium = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    high_risk_avg_premium = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_risk_analytics'
        ordering = ['-analytics_date']
    
    def __str__(self):
        return f"Risk Analytics: {self.analytics_date}"
