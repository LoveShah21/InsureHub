"""
Views for Insurance Product Catalog module.

Provides API endpoints for:
- Insurance types (CRUD for Admin, Read for all)
- Insurance companies (CRUD for Admin, Read for all)
- Coverage types (CRUD for Admin, Read for all)
- Add-ons/Riders (CRUD for Admin, Read for all)

All list endpoints support search via ?q= parameter.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q, Count

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
    
    Search params: ?q= (name, category, description)
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
        
        # Search functionality
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(type_name__icontains=search_query) |
                Q(type_code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by category (type_code)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(type_code__iexact=category)
        
        return queryset.distinct()


class InsuranceCompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for insurance companies.
    
    GET /api/v1/companies/       - List all companies (Public)
    POST /api/v1/companies/      - Create company (Admin)
    GET /api/v1/companies/{id}/  - Get company details (Public)
    PUT/PATCH /api/v1/companies/{id}/ - Update company (Admin)
    DELETE /api/v1/companies/{id}/    - Delete company (Admin)
    
    Search params: ?q= (name, code, registration), ?min_rating=, ?max_rating=
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
        
        # Search functionality
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(company_code__icontains=search_query) |
                Q(registration_number__icontains=search_query)
            )
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        max_rating = self.request.query_params.get('max_rating')
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)
        
        return queryset.distinct()


class CoverageTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for coverage types.
    
    GET /api/v1/coverages/       - List all coverages (Public)
    POST /api/v1/coverages/      - Create coverage (Admin)
    GET /api/v1/coverages/{id}/  - Get coverage details (Public)
    PUT/PATCH /api/v1/coverages/{id}/ - Update coverage (Admin)
    DELETE /api/v1/coverages/{id}/    - Delete coverage (Admin)
    
    Search params: ?q= (name, description), ?insurance_type=
    """
    queryset = CoverageType.objects.select_related('insurance_type').all()
    serializer_class = CoverageTypeSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(coverage_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        # Filter by insurance type
        insurance_type_id = self.request.query_params.get('insurance_type')
        if insurance_type_id:
            queryset = queryset.filter(insurance_type_id=insurance_type_id)
        
        return queryset.distinct()


class RiderAddonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for add-ons/riders.
    
    GET /api/v1/addons/       - List all addons (Public)
    POST /api/v1/addons/      - Create addon (Admin)
    GET /api/v1/addons/{id}/  - Get addon details (Public)
    PUT/PATCH /api/v1/addons/{id}/ - Update addon (Admin)
    DELETE /api/v1/addons/{id}/    - Delete addon (Admin)
    
    Search params: ?q= (name, description), ?insurance_type=
    """
    queryset = RiderAddon.objects.select_related('insurance_type').all()
    serializer_class = RiderAddonSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(addon_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        # Filter by insurance type
        insurance_type_id = self.request.query_params.get('insurance_type')
        if insurance_type_id:
            queryset = queryset.filter(insurance_type_id=insurance_type_id)
        
        return queryset.distinct()


from rest_framework.views import APIView
from apps.policies.models import Policy


class PolicyExploreView(APIView):
    """
    API endpoint for policy marketplace/discovery.
    
    GET /api/v1/policies/explore/
    
    This is a READ-ONLY marketplace endpoint for customers to browse
    available insurance products (NOT their purchased policies).
    
    Query params:
    - q: Search term (insurance type, company name)
    - insurance_type: Filter by insurance type ID
    - company: Filter by company ID
    - min_premium: Minimum premium range
    - max_premium: Maximum premium range
    - category: Filter by category (health, life, auto, etc.)
    - sort: Sorting option (premium_asc, premium_desc, popular, rating)
    - page: Page number for pagination
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get all active insurance types with their companies and coverages
        queryset = InsuranceType.objects.filter(
            is_active=True
        ).prefetch_related(
            'coverage_types',
            'addons'
        ).annotate(
            policy_count=Count('policies')
        )
        
        # Search functionality
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(type_name__icontains=search_query) |
                Q(type_code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by category (using type_code)
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(type_code__iexact=category)
        
        # Get active companies
        companies = InsuranceCompany.objects.filter(is_active=True)
        
        # Filter by company
        company_id = request.query_params.get('company')
        if company_id:
            companies = companies.filter(id=company_id)
        
        # Filter by rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            companies = companies.filter(rating__gte=min_rating)
        
        # Build product catalog
        products = []
        
        for ins_type in queryset:
            # Get coverages for this type (no is_active field in CoverageType)
            coverages = list(ins_type.coverage_types.all().values(
                'id', 'coverage_name', 'description', 'base_premium_per_unit', 'is_mandatory'
            ))
            
            # Calculate base premium range
            premium_values = [c['base_premium_per_unit'] for c in coverages if c['base_premium_per_unit']]
            min_base = min(premium_values) if premium_values else 0
            max_base = max(premium_values) if premium_values else 0
            
            # Filter by premium range
            min_premium = request.query_params.get('min_premium')
            max_premium = request.query_params.get('max_premium')
            
            if min_premium and max_base < float(min_premium):
                continue
            if max_premium and min_base > float(max_premium):
                continue
            
            # Determine badges based on rules
            badges = []
            
            # Get the type code as category proxy
            type_category = ins_type.type_code.upper()
            
            # Most Popular - based on policy count
            if ins_type.policy_count >= 5:
                badges.append({'type': 'popular', 'label': 'Most Popular'})
            
            # Best for Families - health with multiple coverages
            if 'HEALTH' in type_category and len(coverages) >= 3:
                badges.append({'type': 'family', 'label': 'Best for Families'})
            
            # Budget Friendly - lowest base premium
            if min_base and min_base <= 5000:
                badges.append({'type': 'budget', 'label': 'Budget Friendly'})
            
            # High Coverage - high sum insured options
            if max_base and max_base >= 50000:
                badges.append({'type': 'premium', 'label': 'Premium Protection'})
            
            # Get applicable companies
            applicable_companies = []
            for company in companies:
                applicable_companies.append({
                    'id': company.id,
                    'name': company.company_name,
                    'logo': company.logo_url if company.logo_url else None,
                    'rating': float(company.service_rating) if company.service_rating else None,
                    'claim_ratio': float(company.claim_settlement_ratio) if company.claim_settlement_ratio else None,
                })
            
            # Map type_code to icon names
            icon_map = {
                'MOTOR': 'car-front',
                'HEALTH': 'heart-pulse',
                'TRAVEL': 'airplane',
                'WC': 'briefcase',
                'CPM': 'building',
            }
            
            products.append({
                'id': ins_type.id,
                'name': ins_type.type_name,
                'category': ins_type.type_code,  # Use type_code as category
                'description': ins_type.description,
                'icon': icon_map.get(ins_type.type_code, 'shield'),
                'base_premium_range': {
                    'min': float(min_base) if min_base else 0,
                    'max': float(max_base) if max_base else 0,
                },
                'coverages': coverages[:5],  # Top 5 coverages
                'total_coverages': len(coverages),
                'badges': badges,
                'companies': applicable_companies,
                'policy_count': ins_type.policy_count,
            })
        
        # Sorting
        sort_by = request.query_params.get('sort', 'popular')
        if sort_by == 'premium_asc':
            products.sort(key=lambda x: x['base_premium_range']['min'])
        elif sort_by == 'premium_desc':
            products.sort(key=lambda x: x['base_premium_range']['max'], reverse=True)
        elif sort_by == 'popular':
            products.sort(key=lambda x: x['policy_count'], reverse=True)
        
        # Simple pagination
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_products = products[start:end]
        
        # Get available categories for filters (use type_code as category)
        categories = list(InsuranceType.objects.filter(
            is_active=True
        ).values_list('type_code', flat=True).distinct())
        
        return Response({
            'count': len(products),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(products) + per_page - 1) // per_page,
            'filters': {
                'categories': categories,
                'companies': list(InsuranceCompany.objects.filter(
                    is_active=True
                ).values('id', 'company_name')),
            },
            'results': paginated_products
        })

