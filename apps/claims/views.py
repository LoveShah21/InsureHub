"""
Views for Claim Lifecycle Management module.

Provides API endpoints for:
- Claim submission (Customer)
- Claim status updates (Backoffice)
- Document upload (Customer)
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.permissions import IsAdminOrBackoffice

from .models import Claim, ClaimDocument
from .serializers import (
    ClaimSerializer,
    ClaimCreateSerializer,
    ClaimListSerializer,
    ClaimStatusUpdateSerializer,
    ClaimDocumentSerializer,
)


class ClaimViewSet(viewsets.ModelViewSet):
    """
    API endpoint for claims.
    
    Customers can:
    - Create claims (POST /api/v1/claims/)
    - List their claims (GET /api/v1/claims/)
    - View claim details (GET /api/v1/claims/{id}/)
    - Upload documents (POST /api/v1/claims/{id}/upload-document/)
    
    Backoffice can:
    - List all claims (GET /api/v1/claims/all/)
    - Update status (POST /api/v1/claims/{id}/update-status/)
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Backoffice sees all
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            return Claim.objects.select_related(
                'customer__user', 'policy'
            ).prefetch_related('documents').all()
        
        # Customers see only their own
        return Claim.objects.select_related(
            'customer__user', 'policy'
        ).prefetch_related('documents').filter(customer__user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClaimCreateSerializer
        if self.action == 'list':
            return ClaimListSerializer
        return ClaimSerializer
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update claim status (Backoffice only)."""
        # Check permission
        if not request.user.user_roles.filter(
            role__role_name__in=['ADMIN', 'BACKOFFICE']
        ).exists():
            return Response(
                {'error': 'Backoffice access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        serializer = ClaimStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_name = serializer.validated_data['action']
        
        try:
            if action_name == 'start_review':
                claim.start_review(request.user)
            elif action_name == 'approve':
                claim.approve(
                    request.user,
                    serializer.validated_data['approved_amount']
                )
            elif action_name == 'reject':
                claim.reject(
                    request.user,
                    serializer.validated_data['rejection_reason']
                )
            elif action_name == 'settle':
                claim.settle(request.user)
            elif action_name == 'close':
                claim.close(request.user)
            
            return Response({
                'message': f'Claim {action_name} successful.',
                'claim': ClaimSerializer(claim).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """Upload a document for a claim."""
        claim = self.get_object()
        
        # Check ownership
        if claim.customer.user != request.user:
            return Response(
                {'error': 'You can only upload documents to your own claims.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow uploads for non-closed claims
        if claim.status in ['SETTLED', 'CLOSED']:
            return Response(
                {'error': 'Cannot upload documents to settled or closed claims.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document_type = request.data.get('document_type')
        document_name = request.data.get('document_name')
        document_file = request.FILES.get('document_file')
        
        if not all([document_type, document_name, document_file]):
            return Response(
                {'error': 'document_type, document_name, and document_file are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document = ClaimDocument.objects.create(
            claim=claim,
            document_type=document_type,
            document_name=document_name,
            document_file=document_file,
            file_size=document_file.size,
            uploaded_by=request.user
        )
        
        return Response({
            'message': 'Document uploaded successfully.',
            'document': ClaimDocumentSerializer(document).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """List documents for a claim."""
        claim = self.get_object()
        documents = claim.documents.all()
        serializer = ClaimDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrBackoffice])
    def all(self, request):
        """List all claims (Admin/Backoffice only)."""
        claims = Claim.objects.select_related('customer__user', 'policy').all()
        
        # Filter by status
        claim_status = request.query_params.get('status')
        if claim_status:
            claims = claims.filter(status=claim_status)
        
        page = self.paginate_queryset(claims)
        if page is not None:
            serializer = ClaimListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
