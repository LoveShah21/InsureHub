"""
Serializers for Insurance Applications module.
"""

from rest_framework import serializers
from django.utils import timezone

from .models import InsuranceApplication, ApplicationDocument


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationDocument."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = ApplicationDocument
        fields = [
            'id', 'document_type', 'document_name', 'document_file',
            'file_size', 'mime_type', 'verification_status',
            'verification_notes', 'verified_by_name', 'verified_at',
            'uploaded_by_name', 'upload_date'
        ]
        read_only_fields = [
            'id', 'file_size', 'verification_status', 'verification_notes',
            'verified_by_name', 'verified_at', 'uploaded_by_name', 'upload_date'
        ]


class ApplicationDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading documents."""
    
    class Meta:
        model = ApplicationDocument
        fields = ['document_type', 'document_name', 'document_file']
    
    def create(self, validated_data):
        request = self.context.get('request')
        application = self.context.get('application')
        
        document = ApplicationDocument.objects.create(
            application=application,
            uploaded_by=request.user,
            **validated_data
        )
        
        # Set file size
        if document.document_file:
            document.file_size = document.document_file.size
            document.save(update_fields=['file_size'])
        
        return document


class InsuranceApplicationSerializer(serializers.ModelSerializer):
    """Serializer for InsuranceApplication."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InsuranceApplication
        fields = [
            'id', 'application_number', 'customer', 'customer_name', 'customer_email',
            'insurance_type', 'insurance_type_name', 'status', 'rejection_reason',
            'application_data', 'requested_coverage_amount', 'policy_tenure_months',
            'budget_min', 'budget_max',
            'submission_date', 'review_start_date', 'approval_date',
            'documents', 'documents_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'application_number', 'customer', 'status', 'rejection_reason',
            'submission_date', 'review_start_date', 'approval_date',
            'created_at', 'updated_at'
        ]
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class InsuranceApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications."""
    
    class Meta:
        model = InsuranceApplication
        fields = [
            'id', 'application_number', 'insurance_type', 'application_data',
            'requested_coverage_amount', 'policy_tenure_months',
            'budget_min', 'budget_max'
        ]
        read_only_fields = ['id', 'application_number']
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Get or create customer profile
        from apps.customers.models import CustomerProfile
        customer, _ = CustomerProfile.objects.get_or_create(user=request.user)
        
        application = InsuranceApplication.objects.create(
            customer=customer,
            **validated_data
        )
        return application


class InsuranceApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating draft applications."""
    
    class Meta:
        model = InsuranceApplication
        fields = [
            'application_data', 'requested_coverage_amount',
            'policy_tenure_months', 'budget_min', 'budget_max'
        ]
    
    def validate(self, attrs):
        if self.instance.status != 'DRAFT':
            raise serializers.ValidationError(
                "Only draft applications can be updated."
            )
        return attrs


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for status updates by Backoffice."""
    action = serializers.ChoiceField(choices=['start_review', 'approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        action = attrs.get('action')
        reason = attrs.get('reason', '')
        
        if action == 'reject' and not reason:
            raise serializers.ValidationError({
                'reason': 'Rejection reason is required.'
            })
        
        return attrs


class InsuranceApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing applications."""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    insurance_type_name = serializers.CharField(source='insurance_type.type_name', read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InsuranceApplication
        fields = [
            'id', 'application_number', 'customer_name',
            'insurance_type_name', 'status',
            'submission_date', 'documents_count', 'created_at'
        ]
    
    def get_documents_count(self, obj):
        return obj.documents.count()
