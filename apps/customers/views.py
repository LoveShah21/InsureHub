"""
Views for Customer Profiling module.

Provides API endpoints for:
- Customer profile management (own profile for customers)
- Customer listing (Admin/Backoffice only)
"""

from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrBackoffice, IsOwnerOrAdmin
from apps.accounts.models import Role

from .models import CustomerProfile
from .serializers import (
    CustomerProfileSerializer,
    CustomerProfileCreateUpdateSerializer,
    CustomerProfileListSerializer,
)


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current customer's profile.
    
    GET /api/v1/profile/     - Get own profile
    PUT/PATCH /api/v1/profile/ - Update own profile
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get or create profile for current user."""
        profile, created = CustomerProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerProfileCreateUpdateSerializer
        return CustomerProfileSerializer
    
    def update(self, request, *args, **kwargs):
        """Update profile with updated_by tracking."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Track who updated
        instance.updated_by = request.user
        serializer.save()
        
        # Return full profile
        return Response(CustomerProfileSerializer(instance).data)


class CustomerListView(generics.ListAPIView):
    """
    API endpoint for listing all customers.
    
    GET /api/v1/customers/   - List all customers (Admin/Backoffice only)
    """
    queryset = CustomerProfile.objects.select_related('user').all()
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter options
        city = self.request.query_params.get('city')
        state = self.request.query_params.get('state')
        occupation = self.request.query_params.get('occupation')
        
        if city:
            queryset = queryset.filter(residential_city__icontains=city)
        if state:
            queryset = queryset.filter(residential_state__icontains=state)
        if occupation:
            queryset = queryset.filter(occupation_type=occupation)
        
        return queryset


class CustomerDetailView(generics.RetrieveAPIView):
    """
    API endpoint for viewing customer details.
    
    GET /api/v1/customers/{id}/ - Get customer details (Admin/Backoffice only)
    """
    queryset = CustomerProfile.objects.select_related('user').all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
