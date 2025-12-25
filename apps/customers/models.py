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
