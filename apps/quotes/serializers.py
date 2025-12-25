"""
Serializers for Quote Generation module.
"""

from rest_framework import serializers
from decimal import Decimal

from .models import Quote, QuoteCoverage, QuoteAddon, QuoteRecommendation


class QuoteCoverageSerializer(serializers.ModelSerializer):
    """Serializer for QuoteCoverage."""
    coverage_name = serializers.CharField(source='coverage_type.coverage_name', read_only=True)
    
    class Meta:
        model = QuoteCoverage
        fields = [
            'id', 'coverage_type', 'coverage_name',
            'coverage_limit', 'coverage_premium', 'is_selected'
        ]


class QuoteAddonSerializer(serializers.ModelSerializer):
    """Serializer for QuoteAddon."""
    addon_name = serializers.CharField(source='addon.addon_name', read_only=True)
    
    class Meta:
        model = QuoteAddon
        fields = [
            'id', 'addon', 'addon_name',
            'addon_premium', 'is_selected'
        ]


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote with nested details."""
    company_name = serializers.CharField(source='insurance_company.company_name', read_only=True)
    company_logo = serializers.CharField(source='insurance_company.logo_url', read_only=True)
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    coverages = QuoteCoverageSerializer(many=True, read_only=True)
    addons = QuoteAddonSerializer(many=True, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'application', 'customer', 'customer_name',
            'insurance_type', 'insurance_type_name',
            'insurance_company', 'company_name', 'company_logo',
            'status', 'base_premium', 'risk_adjustment_percentage',
            'adjusted_premium', 'fleet_discount_percentage', 'fleet_discount_amount',
            'loyalty_discount_percentage', 'loyalty_discount_amount',
            'other_discounts_amount', 'final_premium', 'gst_percentage',
            'gst_amount', 'total_premium_with_gst', 'sum_insured',
            'policy_tenure_months', 'validity_days', 'generated_at',
            'expiry_at', 'is_expired', 'overall_score',
            'coverages', 'addons', 'created_at'
        ]
        read_only_fields = [
            'quote_number', 'status', 'generated_at', 'expiry_at',
            'created_at', 'is_expired'
        ]


class QuoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing quotes."""
    company_name = serializers.CharField(source='insurance_company.company_name', read_only=True)
    company_logo = serializers.CharField(source='insurance_company.logo_url', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'company_name', 'company_logo',
            'status', 'total_premium_with_gst', 'sum_insured',
            'overall_score', 'is_expired', 'expiry_at', 'created_at'
        ]


class QuoteGenerateSerializer(serializers.Serializer):
    """Serializer for quote generation request."""
    application_id = serializers.IntegerField()
    coverage_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    addon_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )


class QuoteRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for QuoteRecommendation."""
    quote = QuoteListSerializer(source='recommended_quote', read_only=True)
    
    class Meta:
        model = QuoteRecommendation
        fields = [
            'id', 'recommendation_rank', 'recommendation_reason',
            'suitability_score', 'affordability_score',
            'coverage_match_score', 'company_rating_score',
            'quote', 'created_at'
        ]


class QuoteComparisonSerializer(serializers.Serializer):
    """Serializer for quote comparison response."""
    application_id = serializers.IntegerField()
    total_quotes = serializers.IntegerField()
    recommendations = QuoteRecommendationSerializer(many=True)
    all_quotes = QuoteListSerializer(many=True)
