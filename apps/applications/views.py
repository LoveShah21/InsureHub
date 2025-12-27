"""
Views for Insurance Applications module.

Provides API endpoints for:
- Application CRUD (Customer)
- Application submission (Customer)
- Document upload (Customer)
- Application review (Backoffice)
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.permissions import IsAdminOrBackoffice, IsOwnerOrAdmin

from .models import InsuranceApplication, ApplicationDocument
from .serializers import (
    InsuranceApplicationSerializer,
    InsuranceApplicationCreateSerializer,
    InsuranceApplicationUpdateSerializer,
    InsuranceApplicationListSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationDocumentSerializer,
    ApplicationDocumentUploadSerializer,
)


class InsuranceApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for insurance applications.
    
    Customers can:
    - Create applications (POST /api/v1/applications/)
    - List their applications (GET /api/v1/applications/)
    - View application details (GET /api/v1/applications/{id}/)
    - Update draft applications (PUT/PATCH /api/v1/applications/{id}/)
    - Submit applications (POST /api/v1/applications/{id}/submit/)
    - Upload documents (POST /api/v1/applications/{id}/documents/)
    
    Backoffice can:
    - List all applications (GET /api/v1/applications/all/)
    - Update status (POST /api/v1/applications/{id}/update-status/)
    - Verify documents (POST /api/v1/applications/{id}/documents/{doc_id}/verify/)
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Backoffice sees all applications
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            queryset = InsuranceApplication.objects.select_related(
                'customer__user', 'insurance_type'
            ).prefetch_related('documents').all()
        else:
            # Customers see only their own
            queryset = InsuranceApplication.objects.select_related(
                'customer__user', 'insurance_type'
            ).prefetch_related('documents').filter(customer__user=user)
        
        # Search functionality
        from django.db.models import Q
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(application_number__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)
        
        # Filter by insurance type
        insurance_type = self.request.query_params.get('insurance_type')
        if insurance_type:
            queryset = queryset.filter(insurance_type_id=insurance_type)
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InsuranceApplicationCreateSerializer
        if self.action in ['update', 'partial_update']:
            return InsuranceApplicationUpdateSerializer
        if self.action == 'list':
            return InsuranceApplicationListSerializer
        return InsuranceApplicationSerializer
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit an application for review."""
        application = self.get_object()
        
        # Check ownership
        if application.customer.user != request.user:
            return Response(
                {'error': 'You can only submit your own applications.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            application.submit(request.user)
            return Response({
                'message': 'Application submitted successfully.',
                'application': InsuranceApplicationSerializer(application).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update application status (Backoffice only)."""
        # Check permission
        if not request.user.user_roles.filter(
            role__role_name__in=['ADMIN', 'BACKOFFICE']
        ).exists():
            return Response(
                {'error': 'Backoffice access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_name = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        old_status = application.status
        
        try:
            if action_name == 'start_review':
                application.start_review(request.user)
            elif action_name == 'approve':
                application.approve(request.user)
            elif action_name == 'reject':
                application.reject(request.user, reason)
            
            # Send email notification if status changed
            if application.status != old_status:
                from apps.notifications.email_service import send_application_status_email
                send_application_status_email(application, old_status)
            
            return Response({
                'message': f'Application {action_name} successful.',
                'application': InsuranceApplicationSerializer(application).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """Upload a document for an application."""
        application = self.get_object()
        
        # Check ownership
        if application.customer.user != request.user:
            return Response(
                {'error': 'You can only upload documents to your own applications.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationDocumentUploadSerializer(
            data=request.data,
            context={'request': request, 'application': application}
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        return Response({
            'message': 'Document uploaded successfully.',
            'document': ApplicationDocumentSerializer(document).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """List documents for an application."""
        application = self.get_object()
        documents = application.documents.all()
        serializer = ApplicationDocumentSerializer(documents, many=True)
        return Response(serializer.data)


class ApplicationDocumentVerifyView(generics.GenericAPIView):
    """
    API endpoint for document verification (Backoffice only).
    
    POST /api/v1/applications/{app_id}/documents/{doc_id}/verify/
    """
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
    
    def post(self, request, application_id, document_id):
        try:
            document = ApplicationDocument.objects.get(
                id=document_id,
                application_id=application_id
            )
        except ApplicationDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action == 'verify':
            document.verify(request.user, notes)
            message = 'Document verified successfully.'
        elif action == 'reject':
            if not notes:
                return Response(
                    {'error': 'Rejection notes are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            document.reject(request.user, notes)
            message = 'Document rejected.'
        else:
            return Response(
                {'error': 'Invalid action. Use "verify" or "reject".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'document': ApplicationDocumentSerializer(document).data
        })
