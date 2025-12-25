"""
Views for Insurance Product Catalog module.

Provides API endpoints for:
- Insurance types (CRUD for Admin, Read for all)
- Insurance companies (CRUD for Admin, Read for all)
- Coverage types (CRUD for Admin, Read for all)
- Add-ons/Riders (CRUD for Admin, Read for all)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin

from .models import InsuranceType, InsuranceCompany, CoverageType, RiderAddon
from .serializers import (
    InsuranceTypeSerializer,
    InsuranceTypeDetailSerializer,
    InsuranceCompanySerializer,
    InsuranceCompanyListSerializer,
    CoverageTypeSerializer,
    RiderAddonSerializer,
)


class InsuranceTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for insurance types.
    
    GET /api/v1/insurance-types/       - List all types (Public)
    POST /api/v1/insurance-types/      - Create type (Admin)
    GET /api/v1/insurance-types/{id}/  - Get type details (Public)
    PUT/PATCH /api/v1/insurance-types/{id}/ - Update type (Admin)
    DELETE /api/v1/insurance-types/{id}/    - Delete type (Admin)
    """
    queryset = InsuranceType.objects.prefetch_related('coverage_types', 'addons').all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InsuranceTypeDetailSerializer
        return InsuranceTypeSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Non-admin users only see active types
        if self.action in ['list', 'retrieve']:
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(is_active=True)
            elif not self.request.user.user_roles.filter(role__role_name='ADMIN').exists():
                queryset = queryset.filter(is_active=True)
        return queryset


class InsuranceCompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for insurance companies.
    
    GET /api/v1/companies/       - List all companies (Public)
    POST /api/v1/companies/      - Create company (Admin)
    GET /api/v1/companies/{id}/  - Get company details (Public)
    PUT/PATCH /api/v1/companies/{id}/ - Update company (Admin)
    DELETE /api/v1/companies/{id}/    - Delete company (Admin)
    """
    queryset = InsuranceCompany.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InsuranceCompanyListSerializer
        return InsuranceCompanySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(is_active=True)
            elif not self.request.user.user_roles.filter(role__role_name='ADMIN').exists():
                queryset = queryset.filter(is_active=True)
        return queryset


class CoverageTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for coverage types.
    
    GET /api/v1/coverages/       - List all coverages (Public)
    POST /api/v1/coverages/      - Create coverage (Admin)
    GET /api/v1/coverages/{id}/  - Get coverage details (Public)
    PUT/PATCH /api/v1/coverages/{id}/ - Update coverage (Admin)
    DELETE /api/v1/coverages/{id}/    - Delete coverage (Admin)
    """
    queryset = CoverageType.objects.select_related('insurance_type').all()
    serializer_class = CoverageTypeSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by insurance type if provided
        insurance_type_id = self.request.query_params.get('insurance_type')
        if insurance_type_id:
            queryset = queryset.filter(insurance_type_id=insurance_type_id)
        
        return queryset


class RiderAddonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for add-ons/riders.
    
    GET /api/v1/addons/       - List all addons (Public)
    POST /api/v1/addons/      - Create addon (Admin)
    GET /api/v1/addons/{id}/  - Get addon details (Public)
    PUT/PATCH /api/v1/addons/{id}/ - Update addon (Admin)
    DELETE /api/v1/addons/{id}/    - Delete addon (Admin)
    """
    queryset = RiderAddon.objects.select_related('insurance_type').all()
    serializer_class = RiderAddonSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by insurance type if provided
        insurance_type_id = self.request.query_params.get('insurance_type')
        if insurance_type_id:
            queryset = queryset.filter(insurance_type_id=insurance_type_id)
        
        return queryset
