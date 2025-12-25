"""
Serializers for Claim Lifecycle Management module.
"""

from rest_framework import serializers
from .models import Claim, ClaimDocument


class ClaimDocumentSerializer(serializers.ModelSerializer):
    """Serializer for ClaimDocument."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClaimDocument
        fields = [
            'id', 'document_type', 'document_name', 'document_file',
            'file_size', 'verification_status', 'verification_notes',
            'uploaded_by_name', 'upload_date'
        ]
        read_only_fields = [
            'file_size', 'verification_status', 'verification_notes', 'upload_date'
        ]


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claim."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    documents = ClaimDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'policy', 'policy_number',
            'customer', 'customer_name', 'customer_email',
            'claim_type', 'claim_description', 'incident_date', 'incident_location',
            'amount_requested', 'amount_approved', 'amount_settled',
            'status', 'rejection_reason',
            'submitted_at', 'review_started_at', 'approved_at',
            'rejected_at', 'settled_at', 'closed_at',
            'documents', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'claim_number', 'amount_approved', 'amount_settled', 'status',
            'rejection_reason', 'submitted_at', 'review_started_at',
            'approved_at', 'rejected_at', 'settled_at', 'closed_at',
            'created_at', 'updated_at'
        ]


class ClaimCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating claims."""
    
    class Meta:
        model = Claim
        fields = [
            'policy', 'claim_type', 'claim_description',
            'incident_date', 'incident_location', 'amount_requested'
        ]
    
    def validate_policy(self, value):
        """Validate that policy belongs to user and is active."""
        request = self.context.get('request')
        
        if value.customer.user != request.user:
            raise serializers.ValidationError("You can only claim on your own policies.")
        
        if not value.is_active:
            raise serializers.ValidationError("Claims can only be made on active policies.")
        
        return value
    
    def validate_amount_requested(self, value):
        """Validate claim amount."""
        if value <= 0:
            raise serializers.ValidationError("Claim amount must be positive.")
        return value
    
    def validate(self, attrs):
        """Validate claim amount doesn't exceed sum insured."""
        policy = attrs.get('policy')
        amount_requested = attrs.get('amount_requested')
        
        if amount_requested > policy.sum_insured:
            raise serializers.ValidationError({
                'amount_requested': f"Claim amount cannot exceed sum insured ({policy.sum_insured})."
            })
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        claim = Claim.objects.create(
            customer=validated_data['policy'].customer,
            submitted_by=request.user,
            **validated_data
        )
        return claim


class ClaimStatusUpdateSerializer(serializers.Serializer):
    """Serializer for claim status updates by Backoffice."""
    action = serializers.ChoiceField(choices=[
        'start_review', 'approve', 'reject', 'settle', 'close'
    ])
    approved_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False
    )
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        action = attrs.get('action')
        
        if action == 'approve' and not attrs.get('approved_amount'):
            raise serializers.ValidationError({
                'approved_amount': 'Approved amount is required for approval.'
            })
        
        if action == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required.'
            })
        
        return attrs


class ClaimListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing claims."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'policy_number', 'customer_name',
            'claim_type', 'amount_requested', 'status',
            'submitted_at', 'created_at'
        ]
