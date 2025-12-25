"""
Serializers for Customer Profiling module.

Note: PAN/Aadhaar are masked in responses for security.
"""

from rest_framework import serializers
from datetime import date

from .models import CustomerProfile


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomerProfile with masked sensitive fields.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Masked sensitive fields (read-only)
    masked_pan = serializers.CharField(read_only=True)
    masked_aadhar = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'date_of_birth', 'age', 'gender', 'marital_status', 'nationality',
            'masked_pan', 'masked_aadhar',  # Only masked versions exposed
            'residential_address', 'residential_city', 'residential_state',
            'residential_country', 'residential_pincode', 'full_address',
            'occupation_type', 'employer_name', 'annual_income',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'user_name', 'created_at', 'updated_at']


class CustomerProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating CustomerProfile.
    PAN/Aadhaar can only be set, not updated (for security).
    """
    class Meta:
        model = CustomerProfile
        fields = [
            'date_of_birth', 'gender', 'marital_status', 'nationality',
            'pan_number', 'aadhar_number',
            'residential_address', 'residential_city', 'residential_state',
            'residential_country', 'residential_pincode',
            'occupation_type', 'employer_name', 'annual_income'
        ]
    
    def validate_date_of_birth(self, value):
        """Validate age is between 18 and 100."""
        if value:
            today = date.today()
            age = today.year - value.year - (
                (today.month, today.day) < (value.month, value.day)
            )
            if age < 18:
                raise serializers.ValidationError("You must be at least 18 years old.")
            if age > 100:
                raise serializers.ValidationError("Please enter a valid date of birth.")
        return value
    
    def validate_pan_number(self, value):
        """Validate PAN format (basic check)."""
        if value:
            value = value.upper().strip()
            if len(value) != 10:
                raise serializers.ValidationError("PAN must be 10 characters.")
        return value
    
    def validate_aadhar_number(self, value):
        """Validate Aadhaar format (basic check)."""
        if value:
            value = value.strip().replace(' ', '')
            if len(value) != 12 or not value.isdigit():
                raise serializers.ValidationError("Aadhaar must be 12 digits.")
        return value
    
    def update(self, instance, validated_data):
        """Prevent updating PAN/Aadhaar once set."""
        if instance.pan_number and 'pan_number' in validated_data:
            validated_data.pop('pan_number')
        if instance.aadhar_number and 'aadhar_number' in validated_data:
            validated_data.pop('aadhar_number')
        return super().update(instance, validated_data)


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing customers (Admin/Backoffice view)."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user_email', 'user_name', 'date_of_birth', 'age',
            'gender', 'residential_city', 'residential_state',
            'occupation_type', 'created_at'
        ]
