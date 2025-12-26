"""
Customer Profiling Models

This module contains the CustomerProfile model which extends
User with additional demographic and contact information.

Note: PAN/Aadhaar fields are stored for academic simulation only.
Production systems require field-level encryption and compliance.
"""

from django.db import models
from django.conf import settings


class CustomerProfile(models.Model):
    """
    Customer profile extending User with additional details.
    
    One-to-one relationship with User.
    Only users with Customer role should have profiles.
    
    Note: Sensitive fields (pan_number, aadhar_number) are masked
    in API responses for security.
    """
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
    ]
    
    OCCUPATION_CHOICES = [
        ('SALARIED', 'Salaried Employee'),
        ('SELF_EMPLOYED', 'Self Employed'),
        ('BUSINESS', 'Business Owner'),
        ('PROFESSIONAL', 'Professional'),
        ('RETIRED', 'Retired'),
        ('STUDENT', 'Student'),
        ('HOMEMAKER', 'Homemaker'),
        ('OTHER', 'Other'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    
    # Demographics
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    nationality = models.CharField(max_length=100, default='Indian')
    
    # Identity Documents (Academic simulation only - requires encryption in production)
    pan_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    aadhar_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Residential Address
    residential_address = models.TextField(blank=True)
    residential_city = models.CharField(max_length=100, blank=True)
    residential_state = models.CharField(max_length=100, blank=True)
    residential_country = models.CharField(max_length=100, default='India')
    residential_pincode = models.CharField(max_length=10, blank=True)
    
    # Professional Details
    occupation_type = models.CharField(max_length=50, choices=OCCUPATION_CHOICES, blank=True)
    employer_name = models.CharField(max_length=255, blank=True)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_profiles'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='updated_profiles'
    )
    
    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
    
    def __str__(self):
        return f"Profile: {self.user.email}"
    
    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [
            self.residential_address,
            self.residential_city,
            self.residential_state,
            self.residential_country,
            self.residential_pincode
        ]
        return ', '.join(filter(None, parts))
    
    @property
    def masked_pan(self):
        """Return masked PAN number (show only last 4 digits)."""
        if self.pan_number and len(self.pan_number) >= 4:
            return f"XXXX-XXXX-{self.pan_number[-4:]}"
        return None
    
    @property
    def masked_aadhar(self):
        """Return masked Aadhaar number (show only last 4 digits)."""
        if self.aadhar_number and len(self.aadhar_number) >= 4:
            return f"XXXX-XXXX-{self.aadhar_number[-4:]}"
        return None
    
    @property
    def age(self):
        """Calculate age from date of birth."""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class CustomerMedicalDisclosure(models.Model):
    """
    Medical history disclosure for health insurance.
    
    Used for risk assessment and premium calculation.
    """
    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE,
        related_name='medical_disclosures'
    )
    disclosure_date = models.DateField(auto_now_add=True)
    
    # Medical conditions
    medical_condition = models.CharField(max_length=255, blank=True)
    diagnosis_date = models.DateField(null=True, blank=True)
    is_chronic = models.BooleanField(default=False)
    medication_list = models.TextField(
        blank=True,
        help_text="List of current medications"
    )
    hospital_visits_last_year = models.PositiveIntegerField(default=0)
    
    # Pre-existing conditions
    has_diabetes = models.BooleanField(default=False)
    has_hypertension = models.BooleanField(default=False)
    has_heart_disease = models.BooleanField(default=False)
    has_cancer_history = models.BooleanField(default=False)
    smoker = models.BooleanField(default=False)
    alcohol_consumption = models.CharField(
        max_length=20, blank=True,
        choices=[
            ('NONE', 'None'),
            ('OCCASIONAL', 'Occasional'),
            ('REGULAR', 'Regular'),
        ]
    )
    
    is_disclosed = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_medical_disclosures'
        ordering = ['-disclosure_date']
    
    def __str__(self):
        return f"Medical Disclosure: {self.customer.user.email} ({self.disclosure_date})"


class CustomerDrivingHistory(models.Model):
    """
    Driving history for motor insurance.
    
    Used for risk assessment based on driving record.
    """
    LICENSE_STATUS_CHOICES = [
        ('VALID', 'Valid'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('REVOKED', 'Revoked'),
    ]
    
    customer = models.OneToOneField(
        CustomerProfile, on_delete=models.CASCADE,
        related_name='driving_history'
    )
    
    # License details
    license_number = models.CharField(max_length=100, blank=True)
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    license_status = models.CharField(
        max_length=20, choices=LICENSE_STATUS_CHOICES, default='VALID'
    )
    
    # Driving experience
    total_years_experience = models.PositiveIntegerField(default=0)
    vehicle_types_driven = models.JSONField(
        default=list,
        help_text="List of vehicle types driven"
    )
    
    # Violations and accidents
    violations_count = models.PositiveIntegerField(default=0)
    accidents_count = models.PositiveIntegerField(default=0)
    dui_convictions = models.PositiveIntegerField(default=0)
    last_violation_date = models.DateField(null=True, blank=True)
    last_accident_date = models.DateField(null=True, blank=True)
    
    # Suspension history
    suspension_count = models.PositiveIntegerField(default=0)
    
    last_updated = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_driving_history'
    
    def __str__(self):
        return f"Driving History: {self.customer.user.email}"
    
    @property
    def is_clean_record(self):
        """Check if customer has a clean driving record."""
        return self.violations_count == 0 and self.accidents_count == 0


class ClaimHistory(models.Model):
    """
    Historical claims per customer per year.
    
    Used for calculating claim history risk factor.
    """
    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE,
        related_name='claim_histories'
    )
    claim_year = models.PositiveIntegerField(db_index=True)
    claim_count = models.PositiveIntegerField(default=0)
    claim_amount_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    claim_approved_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    claim_rejection_count = models.PositiveIntegerField(default=0)
    last_claim_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claim_history'
        unique_together = ['customer', 'claim_year']
        ordering = ['-claim_year']
    
    def __str__(self):
        return f"Claim History: {self.customer.user.email} ({self.claim_year})"
    
    @property
    def claim_rejection_rate(self):
        """Calculate claim rejection rate."""
        if self.claim_count > 0:
            return round(self.claim_rejection_count / self.claim_count * 100, 2)
        return 0


class CustomerRiskProfile(models.Model):
    """
    Calculated risk profile for a customer.
    
    Aggregates various risk factors into an overall score.
    Used for premium adjustment in quote generation.
    """
    RISK_CATEGORY_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]
    
    customer = models.OneToOneField(
        CustomerProfile, on_delete=models.CASCADE,
        related_name='risk_profile'
    )
    
    # Risk category
    risk_category = models.CharField(
        max_length=10, choices=RISK_CATEGORY_CHOICES, default='MEDIUM'
    )
    risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00,
        help_text="Risk score 0-100 (higher = riskier)"
    )
    
    # Individual risk factors (0-100 each)
    age_risk_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    medical_risk_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    driving_risk_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    claim_history_risk_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    employment_risk_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    
    # Overall percentage adjustment
    overall_risk_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Premium adjustment percentage based on risk"
    )
    
    # Validity
    calculated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_risk_profiles'
    
    def __str__(self):
        return f"Risk Profile: {self.customer.user.email} ({self.risk_category})"
    
    def calculate_overall_risk(self):
        """Calculate overall risk score from individual factors."""
        from decimal import Decimal
        
        # Weighted average of factors
        weights = {
            'age': Decimal('0.15'),
            'medical': Decimal('0.25'),
            'driving': Decimal('0.25'),
            'claim_history': Decimal('0.25'),
            'employment': Decimal('0.10'),
        }
        
        self.risk_score = (
            self.age_risk_factor * weights['age'] +
            self.medical_risk_factor * weights['medical'] +
            self.driving_risk_factor * weights['driving'] +
            self.claim_history_risk_factor * weights['claim_history'] +
            self.employment_risk_factor * weights['employment']
        )
        
        # Determine category
        if self.risk_score <= 25:
            self.risk_category = 'LOW'
            self.overall_risk_percentage = Decimal('-10')  # Discount
        elif self.risk_score <= 50:
            self.risk_category = 'MEDIUM'
            self.overall_risk_percentage = Decimal('0')
        elif self.risk_score <= 75:
            self.risk_category = 'HIGH'
            self.overall_risk_percentage = Decimal('15')  # Surcharge
        else:
            self.risk_category = 'CRITICAL'
            self.overall_risk_percentage = Decimal('30')  # High surcharge
        
        self.save()
        return self.risk_score


# Import fleet models for convenience
from .fleet_models import (
    Fleet,
    FleetVehicle,
    FleetClaimHistory,
    FleetRiskScore,
)

