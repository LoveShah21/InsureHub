"""
Insurance Product & Policy Catalog Models

This module contains models for:
- InsuranceType: Types of insurance (Motor, Health, Travel, etc.)
- InsuranceCompany: Insurance providers
- CoverageType: Coverage options for each insurance type
- RiderAddon: Optional add-ons/riders

These are master data tables managed by Admin.
Customers can only view (read-only access).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class InsuranceType(models.Model):
    """
    Types of insurance products.
    
    Examples:
    - Motor Insurance
    - Health Insurance
    - Travel Insurance
    - Workers Compensation
    - Commercial Property Management
    """
    type_name = models.CharField(max_length=100, unique=True)
    type_code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_types'
        ordering = ['type_name']
    
    def __str__(self):
        return f"{self.type_name} ({self.type_code})"
    
    @classmethod
    def get_default_types(cls):
        """Return default insurance types for seeding."""
        return [
            {'type_name': 'Motor Insurance', 'type_code': 'MOTOR', 'description': 'Vehicle/Auto Insurance'},
            {'type_name': 'Health Insurance', 'type_code': 'HEALTH', 'description': 'Medical and Health Coverage'},
            {'type_name': 'Travel Insurance', 'type_code': 'TRAVEL', 'description': 'Travel and Trip Insurance'},
            {'type_name': 'Workers Compensation', 'type_code': 'WC', 'description': 'Employee Injury/Compensation'},
            {'type_name': 'Commercial Property', 'type_code': 'CPM', 'description': 'Business Property Insurance'},
        ]


class InsuranceCompany(models.Model):
    """
    Insurance providers/companies.
    
    Each company can offer multiple insurance types.
    """
    company_name = models.CharField(max_length=255, unique=True)
    company_code = models.CharField(max_length=50, unique=True, db_index=True)
    registration_number = models.CharField(max_length=100, blank=True)
    headquarters_address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    
    # Service quality metrics (used in quote scoring)
    claim_settlement_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=Decimal('0.90'),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Claim settlement ratio (0-1)"
    )
    service_rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=Decimal('4.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Service rating out of 5"
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_companies'
        verbose_name_plural = 'Insurance companies'
        ordering = ['company_name']
    
    def __str__(self):
        return f"{self.company_name} ({self.company_code})"
    
    @classmethod
    def get_default_companies(cls):
        """Return default insurance companies for seeding."""
        return [
            {'company_name': 'SafeGuard Insurance', 'company_code': 'SAFEGUARD', 'claim_settlement_ratio': Decimal('0.95'), 'service_rating': Decimal('4.5')},
            {'company_name': 'TrustShield Insurance', 'company_code': 'TRUSTSHIELD', 'claim_settlement_ratio': Decimal('0.92'), 'service_rating': Decimal('4.2')},
            {'company_name': 'SecureLife Insurance', 'company_code': 'SECURELIFE', 'claim_settlement_ratio': Decimal('0.88'), 'service_rating': Decimal('4.0')},
            {'company_name': 'PremiumCare Insurance', 'company_code': 'PREMIUMCARE', 'claim_settlement_ratio': Decimal('0.90'), 'service_rating': Decimal('4.3')},
            {'company_name': 'ValueFirst Insurance', 'company_code': 'VALUEFIRST', 'claim_settlement_ratio': Decimal('0.85'), 'service_rating': Decimal('3.8')},
        ]


class CoverageType(models.Model):
    """
    Coverage options available for each insurance type.
    
    Examples for Motor Insurance:
    - Third Party Liability
    - Own Damage
    - Personal Accident
    """
    coverage_name = models.CharField(max_length=255)
    coverage_code = models.CharField(max_length=50, db_index=True)
    insurance_type = models.ForeignKey(
        InsuranceType, on_delete=models.RESTRICT,
        related_name='coverage_types'
    )
    description = models.TextField(blank=True)
    
    is_mandatory = models.BooleanField(default=False)
    base_premium_per_unit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Base premium per coverage unit"
    )
    unit_of_measurement = models.CharField(max_length=50, blank=True, default='per policy')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coverage_types'
        unique_together = ['insurance_type', 'coverage_code']
        ordering = ['insurance_type', 'coverage_name']
    
    def __str__(self):
        return f"{self.coverage_name} ({self.insurance_type.type_code})"


class RiderAddon(models.Model):
    """
    Optional add-ons/riders for insurance policies.
    
    Examples for Motor Insurance:
    - Zero Depreciation
    - Roadside Assistance
    - Engine Protection
    """
    addon_name = models.CharField(max_length=255)
    addon_code = models.CharField(max_length=50, db_index=True)
    insurance_type = models.ForeignKey(
        InsuranceType, on_delete=models.RESTRICT,
        related_name='addons'
    )
    description = models.TextField(blank=True)
    
    premium_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Premium as percentage of base premium"
    )
    is_optional = models.BooleanField(default=True)
    max_coverage_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Maximum coverage amount for this add-on"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'riders_addons'
        unique_together = ['insurance_type', 'addon_code']
        ordering = ['insurance_type', 'addon_name']
    
    def __str__(self):
        return f"{self.addon_name} ({self.insurance_type.type_code})"
