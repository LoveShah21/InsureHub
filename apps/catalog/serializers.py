"""
Serializers for Insurance Product Catalog module.
"""

from rest_framework import serializers
from .models import InsuranceType, InsuranceCompany, CoverageType, RiderAddon


class InsuranceTypeSerializer(serializers.ModelSerializer):
    """Serializer for InsuranceType model."""
    coverages_count = serializers.SerializerMethodField()
    addons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InsuranceType
        fields = [
            'id', 'type_name', 'type_code', 'description', 
            'is_active', 'coverages_count', 'addons_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_coverages_count(self, obj):
        return obj.coverage_types.count()
    
    def get_addons_count(self, obj):
        return obj.addons.count()


class InsuranceCompanySerializer(serializers.ModelSerializer):
    """Serializer for InsuranceCompany model."""
    
    class Meta:
        model = InsuranceCompany
        fields = [
            'id', 'company_name', 'company_code', 'registration_number',
            'headquarters_address', 'contact_email', 'contact_phone',
            'website', 'logo_url', 'claim_settlement_ratio', 'service_rating',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InsuranceCompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing companies."""
    
    class Meta:
        model = InsuranceCompany
        fields = [
            'id', 'company_name', 'company_code', 'logo_url',
            'claim_settlement_ratio', 'service_rating', 'is_active'
        ]


class CoverageTypeSerializer(serializers.ModelSerializer):
    """Serializer for CoverageType model."""
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    
    class Meta:
        model = CoverageType
        fields = [
            'id', 'coverage_name', 'coverage_code', 'insurance_type',
            'insurance_type_name', 'description', 'is_mandatory',
            'base_premium_per_unit', 'unit_of_measurement',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RiderAddonSerializer(serializers.ModelSerializer):
    """Serializer for RiderAddon model."""
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    
    class Meta:
        model = RiderAddon
        fields = [
            'id', 'addon_name', 'addon_code', 'insurance_type',
            'insurance_type_name', 'description', 'premium_percentage',
            'is_optional', 'max_coverage_limit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InsuranceTypeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for InsuranceType with nested coverages and addons."""
    coverage_types = CoverageTypeSerializer(many=True, read_only=True)
    addons = RiderAddonSerializer(many=True, read_only=True)
    
    class Meta:
        model = InsuranceType
        fields = [
            'id', 'type_name', 'type_code', 'description', 'is_active',
            'coverage_types', 'addons', 'created_at', 'updated_at'
        ]
