"""
Serializers for Policy and Payment modules.
"""

from rest_framework import serializers
from .models import Policy, Payment, Invoice


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for Policy."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    company_name = serializers.CharField(source='insurance_company.company_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'quote', 'customer', 'customer_name',
            'customer_email', 'insurance_type', 'insurance_type_name',
            'insurance_company', 'company_name', 'status',
            'policy_start_date', 'policy_end_date', 'policy_tenure_months',
            'premium_amount', 'gst_amount', 'total_premium_with_gst',
            'sum_insured', 'policy_version', 'issued_at',
            'is_active', 'days_until_expiry', 'next_renewal_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'policy_number', 'issued_at', 'created_at', 'updated_at'
        ]


class PolicyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing policies."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    company_name = serializers.CharField(source='insurance_company.company_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'customer_name', 'company_name',
            'status', 'policy_start_date', 'policy_end_date',
            'total_premium_with_gst', 'is_active', 'created_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'quote', 'policy', 'customer',
            'customer_name', 'payment_amount', 'payment_method',
            'status', 'transaction_id', 'transaction_reference',
            'payment_date', 'retry_count', 'failed_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'payment_number', 'status', 'transaction_id',
            'transaction_reference', 'payment_date', 'created_at', 'updated_at'
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating payment."""
    quote_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=[
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('UPI', 'UPI'),
    ])


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice."""
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'policy', 'policy_number', 'payment',
            'invoice_date', 'invoice_amount', 'gst_amount',
            'total_invoice_amount', 'status', 'invoice_url',
            'generated_at', 'created_at'
        ]
        read_only_fields = [
            'invoice_number', 'generated_at', 'created_at'
        ]
