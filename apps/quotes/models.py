"""
Quote Generation & Decision Engine Models

This module contains models for:
- Quote: Generated insurance quotes
- QuoteCoverage: Coverage selections for quotes
- QuoteAddon: Add-on selections for quotes
- QuoteRecommendation: Top recommendations with scoring

Quote Scoring Formula (Rule-Based, documented in code):
score = (0.4 * affordability) + (0.3 * claim_ratio) + 
        (0.2 * coverage_score) + (0.1 * service_rating)
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


def generate_quote_number():
    """Generate unique quote number."""
    return f"QT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


class Quote(models.Model):
    """
    Insurance quote generated for an application.
    
    Multiple quotes can be generated per application (from different companies).
    """
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent to Customer'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Core references
    quote_number = models.CharField(
        max_length=100, unique=True, db_index=True,
        default=generate_quote_number
    )
    application = models.ForeignKey(
        'applications.InsuranceApplication', on_delete=models.CASCADE,
        related_name='quotes'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='quotes'
    )
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.RESTRICT,
        related_name='quotes'
    )
    insurance_company = models.ForeignKey(
        'catalog.InsuranceCompany', on_delete=models.RESTRICT,
        related_name='quotes'
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='GENERATED', db_index=True
    )
    
    # Premium calculation
    base_premium = models.DecimalField(max_digits=15, decimal_places=2)
    risk_adjustment_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    adjusted_premium = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Discounts
    fleet_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    fleet_discount_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    loyalty_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    loyalty_discount_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    other_discounts_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    # Final amounts
    final_premium = models.DecimalField(max_digits=15, decimal_places=2)
    gst_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('18.00')
    )
    gst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_premium_with_gst = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Coverage details
    sum_insured = models.DecimalField(max_digits=15, decimal_places=2)
    policy_tenure_months = models.PositiveIntegerField(default=12)
    
    # Validity
    validity_days = models.PositiveIntegerField(default=30)
    generated_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField()
    
    # Scoring (for comparison)
    overall_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Overall suitability score (0-100)"
    )
    
    # Workflow
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_quotes'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quotes'
        ordering = ['-overall_score', '-created_at']
        indexes = [
            models.Index(fields=['application']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_at']),
            models.Index(fields=['overall_score']),
        ]
    
    def __str__(self):
        return f"{self.quote_number} - {self.insurance_company.company_name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate expiry date
        if not self.expiry_at:
            self.expiry_at = timezone.now() + timezone.timedelta(days=self.validity_days)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expiry_at
    
    def accept(self):
        """Mark quote as accepted."""
        if self.status != 'GENERATED':
            raise ValueError("Only generated quotes can be accepted.")
        if self.is_expired:
            raise ValueError("This quote has expired.")
        
        self.status = 'ACCEPTED'
        self.accepted_at = timezone.now()
        self.save()


class QuoteCoverage(models.Model):
    """
    Coverage selections for a quote.
    """
    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name='coverages'
    )
    coverage_type = models.ForeignKey(
        'catalog.CoverageType', on_delete=models.RESTRICT
    )
    coverage_limit = models.DecimalField(max_digits=15, decimal_places=2)
    coverage_premium = models.DecimalField(max_digits=12, decimal_places=2)
    is_selected = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quote_coverage_selection'
        unique_together = ['quote', 'coverage_type']
    
    def __str__(self):
        return f"{self.quote.quote_number} - {self.coverage_type.coverage_name}"


class QuoteAddon(models.Model):
    """
    Add-on selections for a quote.
    """
    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name='addons'
    )
    addon = models.ForeignKey(
        'catalog.RiderAddon', on_delete=models.RESTRICT
    )
    addon_premium = models.DecimalField(max_digits=12, decimal_places=2)
    is_selected = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quote_addon_selection'
        unique_together = ['quote', 'addon']
    
    def __str__(self):
        return f"{self.quote.quote_number} - {self.addon.addon_name}"


class QuoteRecommendation(models.Model):
    """
    Ranked recommendations for an application.
    
    Stores the top 3 quotes with their scores.
    """
    application = models.ForeignKey(
        'applications.InsuranceApplication', on_delete=models.CASCADE,
        related_name='recommendations'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='recommendations'
    )
    insurance_type = models.ForeignKey(
        'catalog.InsuranceType', on_delete=models.RESTRICT
    )
    recommended_quote = models.ForeignKey(
        Quote, on_delete=models.SET_NULL, null=True,
        related_name='recommendations'
    )
    
    # Ranking
    recommendation_rank = models.PositiveIntegerField()
    recommendation_reason = models.TextField(blank=True)
    
    # Scoring breakdown (for transparency)
    suitability_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    affordability_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    coverage_match_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    company_rating_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quote_recommendations'
        ordering = ['recommendation_rank']
        unique_together = ['application', 'recommendation_rank']
    
    def __str__(self):
        return f"Rank {self.recommendation_rank}: {self.recommended_quote}"
