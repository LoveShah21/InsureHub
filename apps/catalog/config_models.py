"""
Configuration Models for Insurance Catalog

This module contains configuration-driven business rules:
- PremiumSlab: Premium calculation slabs
- PolicyEligibilityRule: Eligibility conditions
- DiscountRule: Discount rules with conditions
- QuoteCalculationWeight: Quote scoring weights
- ClaimApprovalThreshold: Claim approval levels
- BusinessConfiguration: System-wide settings
- CompanyConfiguration: Per-company settings
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class PremiumSlab(models.Model):
    """
    Premium calculation slabs by insurance type and coverage amount.
    
    Used by quote engine to calculate base premium based on sum insured range.
    """
    insurance_type = models.ForeignKey(
        'InsuranceType', on_delete=models.CASCADE,
        related_name='premium_slabs'
    )
    slab_name = models.CharField(max_length=255)
    min_coverage_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    max_coverage_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('9999999999.99')
    )
    base_premium = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Base premium for this slab"
    )
    percentage_markup = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Additional percentage of coverage amount"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'premium_slabs'
        ordering = ['insurance_type', 'min_coverage_amount']
        unique_together = ['insurance_type', 'min_coverage_amount', 'max_coverage_amount']
    
    def __str__(self):
        return f"{self.slab_name} ({self.insurance_type.type_code})"
    
    def calculate_premium(self, coverage_amount):
        """Calculate premium for a given coverage amount."""
        base = self.base_premium
        markup = coverage_amount * (self.percentage_markup / 100)
        return base + markup


class PolicyEligibilityRule(models.Model):
    """
    Eligibility rules for policy issuance.
    
    Conditions stored as JSON for flexibility:
    Example: {"min_age": 18, "max_age": 65, "min_income": 300000}
    """
    insurance_type = models.ForeignKey(
        'InsuranceType', on_delete=models.CASCADE,
        related_name='eligibility_rules'
    )
    rule_name = models.CharField(max_length=255)
    rule_condition = models.JSONField(
        default=dict,
        help_text="JSON conditions: {min_age, max_age, min_income, etc.}"
    )
    rule_priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority rules evaluated first"
    )
    error_message = models.CharField(
        max_length=500, blank=True,
        help_text="Message to show when rule fails"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'policy_eligibility_rules'
        ordering = ['insurance_type', '-rule_priority']
    
    def __str__(self):
        return f"{self.rule_name} ({self.insurance_type.type_code})"


class DiscountRule(models.Model):
    """
    Discount rules with conditions and percentages.
    
    Conditions stored as JSON for flexibility:
    Example: {"min_fleet_size": 5, "max_claim_ratio": 0.2}
    """
    rule_name = models.CharField(max_length=255)
    rule_code = models.CharField(max_length=100, unique=True, db_index=True)
    insurance_type = models.ForeignKey(
        'InsuranceType', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='discount_rules',
        help_text="Null = applies to all insurance types"
    )
    rule_condition = models.JSONField(
        default=dict,
        help_text="JSON conditions for discount eligibility"
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_max_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Maximum discount amount cap"
    )
    rule_priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority evaluated first"
    )
    is_combinable = models.BooleanField(
        default=True,
        help_text="Can this discount combine with others?"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_discount_rules'
    )
    
    class Meta:
        db_table = 'discount_rules'
        ordering = ['-rule_priority', 'rule_name']
    
    def __str__(self):
        return f"{self.rule_name} ({self.discount_percentage}%)"
    
    def is_valid_for_date(self, check_date=None):
        """Check if discount is valid for a given date."""
        from datetime import date
        check_date = check_date or date.today()
        
        if self.effective_from and check_date < self.effective_from:
            return False
        if self.effective_to and check_date > self.effective_to:
            return False
        return True


class QuoteCalculationWeight(models.Model):
    """
    Weights for quote scoring algorithm.
    
    Score factors like: age_risk, medical_risk, driving_risk, claim_history
    """
    insurance_type = models.ForeignKey(
        'InsuranceType', on_delete=models.CASCADE,
        related_name='calculation_weights'
    )
    factor_name = models.CharField(
        max_length=255,
        help_text="E.g., age_risk_factor, medical_risk_factor"
    )
    factor_weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight between 0 and 1"
    )
    factor_calculation_formula = models.TextField(
        blank=True,
        help_text="Description of how factor is calculated"
    )
    min_weight_value = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    max_weight_value = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quote_calculation_weights'
        unique_together = ['insurance_type', 'factor_name']
        ordering = ['insurance_type', 'factor_name']
    
    def __str__(self):
        return f"{self.factor_name}: {self.factor_weight} ({self.insurance_type.type_code})"


class ClaimApprovalThreshold(models.Model):
    """
    Claim approval thresholds by amount.
    
    Determines which role can approve claims at different amounts.
    """
    APPROVAL_LEVEL_CHOICES = [
        ('AUTO_APPROVE', 'Auto Approve'),
        ('OFFICER_APPROVAL', 'Officer Approval'),
        ('MANAGER_APPROVAL', 'Manager Approval'),
        ('DIRECTOR_APPROVAL', 'Director Approval'),
    ]
    
    insurance_type = models.ForeignKey(
        'InsuranceType', on_delete=models.CASCADE,
        related_name='approval_thresholds'
    )
    approval_level = models.CharField(
        max_length=30, choices=APPROVAL_LEVEL_CHOICES
    )
    min_claim_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    max_claim_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('9999999999.99')
    )
    required_approver_role = models.ForeignKey(
        'accounts.Role', on_delete=models.RESTRICT,
        related_name='claim_thresholds'
    )
    max_processing_days = models.PositiveIntegerField(
        default=15,
        help_text="SLA for claim processing"
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claim_approval_thresholds'
        ordering = ['insurance_type', 'min_claim_amount']
    
    def __str__(self):
        return f"{self.approval_level} ({self.min_claim_amount}-{self.max_claim_amount})"


class BusinessConfiguration(models.Model):
    """
    System-wide configuration settings.
    
    Replaces hardcoded values like GST rate, SLA days, etc.
    """
    CONFIG_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('QUOTE', 'Quote Settings'),
        ('CLAIM', 'Claim Settings'),
        ('PAYMENT', 'Payment Settings'),
        ('SECURITY', 'Security Settings'),
        ('TAX', 'Tax Settings'),
    ]
    
    config_key = models.CharField(max_length=255, unique=True, db_index=True)
    config_value = models.TextField()
    config_type = models.CharField(
        max_length=20, choices=CONFIG_TYPE_CHOICES, default='GENERAL'
    )
    config_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    min_value = models.CharField(max_length=255, blank=True)
    max_value = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='updated_configs'
    )
    
    class Meta:
        db_table = 'business_configuration'
        ordering = ['config_type', 'config_key']
    
    def __str__(self):
        return f"{self.config_key}: {self.config_value}"
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get configuration value by key."""
        try:
            config = cls.objects.get(config_key=key, is_active=True)
            return config.config_value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def get_int(cls, key, default=0):
        """Get configuration value as integer."""
        value = cls.get_value(key)
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default
    
    @classmethod
    def get_decimal(cls, key, default=Decimal('0')):
        """Get configuration value as Decimal."""
        value = cls.get_value(key)
        try:
            return Decimal(value) if value else default
        except:
            return default
    
    @classmethod
    def get_default_configs(cls):
        """Return default system configurations for seeding."""
        return [
            {'config_key': 'GST_RATE', 'config_value': '18', 'config_type': 'TAX', 
             'config_description': 'GST rate percentage'},
            {'config_key': 'QUOTE_VALIDITY_DAYS', 'config_value': '30', 'config_type': 'QUOTE',
             'config_description': 'Days a quote remains valid'},
            {'config_key': 'CLAIM_SLA_DAYS', 'config_value': '15', 'config_type': 'CLAIM',
             'config_description': 'SLA for claim settlement in days'},
            {'config_key': 'MAX_PAYMENT_RETRIES', 'config_value': '3', 'config_type': 'PAYMENT',
             'config_description': 'Maximum payment retry attempts'},
            {'config_key': 'ACCOUNT_LOCK_THRESHOLD', 'config_value': '5', 'config_type': 'SECURITY',
             'config_description': 'Failed login attempts before lockout'},
            {'config_key': 'ACCOUNT_LOCK_DURATION', 'config_value': '30', 'config_type': 'SECURITY',
             'config_description': 'Account lockout duration in minutes'},
            {'config_key': 'SESSION_TIMEOUT', 'config_value': '30', 'config_type': 'SECURITY',
             'config_description': 'Session timeout in minutes'},
        ]


class CompanyConfiguration(models.Model):
    """
    Per-company configuration settings.
    
    Allows different settings for each insurance company.
    """
    insurance_company = models.ForeignKey(
        'InsuranceCompany', on_delete=models.CASCADE,
        related_name='configurations'
    )
    config_key = models.CharField(max_length=255)
    config_value = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_configuration'
        unique_together = ['insurance_company', 'config_key']
        ordering = ['insurance_company', 'config_key']
    
    def __str__(self):
        return f"{self.insurance_company.company_code}: {self.config_key}"
