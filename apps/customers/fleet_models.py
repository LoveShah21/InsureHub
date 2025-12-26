"""
Fleet Management Models (Minimal Scope)

This module contains fleet-related models for motor insurance:
- Fleet: Customer fleet definitions
- FleetVehicle: Vehicles in a fleet
- FleetClaimHistory: Fleet claim history by year (stub)
- FleetRiskScore: Fleet risk and discount calculation (simplified)

Note: Advanced fleet analytics are out of scope for this academic project.
Designed for extensibility.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class Fleet(models.Model):
    """
    Customer fleet definition.
    
    Fleets are groups of vehicles owned by a single customer.
    Used for fleet discounts in motor insurance.
    """
    FLEET_TYPE_CHOICES = [
        ('COMMERCIAL', 'Commercial'),
        ('PRIVATE', 'Private'),
        ('MIXED', 'Mixed'),
    ]
    
    customer = models.ForeignKey(
        'CustomerProfile', on_delete=models.CASCADE,
        related_name='fleets'
    )
    fleet_name = models.CharField(max_length=255)
    fleet_code = models.CharField(max_length=100, blank=True, db_index=True)
    fleet_type = models.CharField(
        max_length=20, choices=FLEET_TYPE_CHOICES, default='COMMERCIAL'
    )
    total_vehicles = models.PositiveIntegerField(default=0)
    fleet_ownership_date = models.DateField(null=True, blank=True)
    fleet_purpose = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_fleets'
    )
    
    class Meta:
        db_table = 'fleets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.fleet_name} ({self.total_vehicles} vehicles)"
    
    def update_vehicle_count(self):
        """Update total vehicle count from related vehicles."""
        self.total_vehicles = self.vehicles.filter(vehicle_status='ACTIVE').count()
        self.save(update_fields=['total_vehicles'])


class FleetVehicle(models.Model):
    """
    Vehicle in a fleet.
    
    Tracks individual vehicles for fleet management.
    """
    VEHICLE_TYPE_CHOICES = [
        ('CAR', 'Car'),
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('BUS', 'Bus'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('OTHER', 'Other'),
    ]
    
    FUEL_TYPE_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('CNG', 'CNG'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
    ]
    
    VEHICLE_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SOLD', 'Sold'),
        ('SCRAPPED', 'Scrapped'),
    ]
    
    fleet = models.ForeignKey(
        Fleet, on_delete=models.CASCADE,
        related_name='vehicles'
    )
    vehicle_registration_number = models.CharField(
        max_length=50, unique=True, db_index=True
    )
    vehicle_make = models.CharField(max_length=100, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_year = models.PositiveIntegerField(null=True, blank=True)
    vehicle_type = models.CharField(
        max_length=20, choices=VEHICLE_TYPE_CHOICES, default='CAR'
    )
    vehicle_fuel_type = models.CharField(
        max_length=20, choices=FUEL_TYPE_CHOICES, default='PETROL'
    )
    vehicle_seating_capacity = models.PositiveIntegerField(default=5)
    vehicle_current_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    vehicle_status = models.CharField(
        max_length=20, choices=VEHICLE_STATUS_CHOICES, default='ACTIVE'
    )
    added_at = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fleet_vehicles'
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.vehicle_registration_number} ({self.vehicle_make} {self.vehicle_model})"


class FleetClaimHistory(models.Model):
    """
    Fleet claim history by year (stub implementation).
    
    Tracks aggregate claim data for the fleet.
    """
    fleet = models.ForeignKey(
        Fleet, on_delete=models.CASCADE,
        related_name='claim_histories'
    )
    claim_year = models.PositiveIntegerField(db_index=True)
    total_claims = models.PositiveIntegerField(default=0)
    total_claim_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    approved_claim_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    claim_ratio = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0000'),
        help_text="Claims to premium ratio"
    )
    settled_claims = models.PositiveIntegerField(default=0)
    rejected_claims = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fleet_claim_history'
        unique_together = ['fleet', 'claim_year']
        ordering = ['-claim_year']
    
    def __str__(self):
        return f"Fleet Claims: {self.fleet.fleet_name} ({self.claim_year})"


class FleetRiskScore(models.Model):
    """
    Fleet risk and discount calculation (simplified).
    
    Calculates fleet discount based on size and claim history.
    Extensibility note: Full implementation would include more factors.
    """
    FLEET_RISK_CATEGORY_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]
    
    fleet = models.OneToOneField(
        Fleet, on_delete=models.CASCADE,
        related_name='risk_score'
    )
    fleet_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50.00')
    )
    vehicle_count_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    claim_ratio_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    fleet_risk_category = models.CharField(
        max_length=10, choices=FLEET_RISK_CATEGORY_CHOICES, default='MEDIUM'
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Discount percentage for fleet policies"
    )
    calculated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fleet_risk_scores'
    
    def __str__(self):
        return f"Fleet Risk: {self.fleet.fleet_name} ({self.fleet_risk_category})"
    
    def calculate_discount(self):
        """
        Calculate fleet discount (simplified algorithm).
        
        Discount tiers:
        - 5-9 vehicles: 5%
        - 10-19 vehicles: 10%
        - 20+ vehicles: 15%
        
        Adjusted by claim ratio.
        """
        vehicle_count = self.fleet.total_vehicles
        
        # Base discount by fleet size
        if vehicle_count >= 20:
            base_discount = Decimal('15.00')
        elif vehicle_count >= 10:
            base_discount = Decimal('10.00')
        elif vehicle_count >= 5:
            base_discount = Decimal('5.00')
        else:
            base_discount = Decimal('0.00')
        
        # Adjust by claim ratio (reduce discount if high claims)
        latest_claim_history = self.fleet.claim_histories.first()
        if latest_claim_history and latest_claim_history.claim_ratio > Decimal('0.20'):
            base_discount *= Decimal('0.5')  # Halve discount for high claim ratio
        
        self.discount_percentage = base_discount
        
        # Determine risk category
        if base_discount >= Decimal('10.00'):
            self.fleet_risk_category = 'LOW'
        elif base_discount >= Decimal('5.00'):
            self.fleet_risk_category = 'MEDIUM'
        else:
            self.fleet_risk_category = 'HIGH'
        
        self.save()
        return self.discount_percentage
