"""
Views for Quote Generation & Decision Engine module.

Provides API endpoints for:
- Quote generation from approved applications
- Quote listing and details
- Quote comparison with scoring
- Quote acceptance
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from decimal import Decimal

from apps.accounts.permissions import IsAdminOrBackoffice
from apps.applications.models import InsuranceApplication
from apps.catalog.models import InsuranceCompany, CoverageType, RiderAddon

from .models import Quote, QuoteCoverage, QuoteAddon, QuoteRecommendation
from .serializers import (
    QuoteSerializer,
    QuoteListSerializer,
    QuoteGenerateSerializer,
    QuoteRecommendationSerializer,
    QuoteComparisonSerializer,
)
from .scoring import calculate_quote_score, generate_recommendation_reason


class QuoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for quotes.
    
    GET /api/v1/quotes/          - List customer's quotes
    GET /api/v1/quotes/{id}/     - Get quote details
    POST /api/v1/quotes/generate/ - Generate quotes for application
    GET /api/v1/quotes/compare/   - Compare top 3 recommendations
    POST /api/v1/quotes/{id}/accept/ - Accept a quote
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Backoffice sees all
        if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
            return Quote.objects.select_related(
                'customer__user', 'insurance_type', 'insurance_company'
            ).prefetch_related('coverages', 'addons').all()
        
        # Customers see only their own
        return Quote.objects.select_related(
            'customer__user', 'insurance_type', 'insurance_company'
        ).prefetch_related('coverages', 'addons').filter(customer__user=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        return QuoteSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate quotes for an approved application.
        
        This creates quotes from all active insurance companies,
        calculates scores, and returns top 3 recommendations.
        """
        serializer = QuoteGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        application_id = serializer.validated_data['application_id']
        coverage_ids = serializer.validated_data.get('coverage_ids', [])
        addon_ids = serializer.validated_data.get('addon_ids', [])
        
        try:
            application = InsuranceApplication.objects.select_related(
                'customer', 'insurance_type'
            ).get(id=application_id)
        except InsuranceApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if application.customer.user != request.user:
            return Response(
                {'error': 'You can only generate quotes for your own applications.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check status
        if application.status != 'APPROVED':
            return Response(
                {'error': 'Quotes can only be generated for approved applications.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active companies
        companies = InsuranceCompany.objects.filter(is_active=True)
        
        if not companies.exists():
            return Response(
                {'error': 'No insurance companies available.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get coverages and addons for this insurance type
        type_coverages = CoverageType.objects.filter(
            insurance_type=application.insurance_type
        )
        type_addons = RiderAddon.objects.filter(
            insurance_type=application.insurance_type
        )
        
        # Use provided IDs or default to mandatory coverages
        if not coverage_ids:
            coverage_ids = list(type_coverages.filter(
                is_mandatory=True
            ).values_list('id', flat=True))
        
        generated_quotes = []
        
        for company in companies:
            # Calculate base premium (simplified calculation)
            base_premium = self._calculate_base_premium(
                application, company, coverage_ids
            )
            
            # Calculate addon premium
            addon_premium = self._calculate_addon_premium(
                base_premium, addon_ids
            )
            
            # Risk adjustment (simplified)
            risk_adjustment = Decimal('5.00')  # Default 5%
            adjusted_premium = base_premium * (1 + risk_adjustment / 100)
            
            # Discounts (simplified)
            final_premium = adjusted_premium + addon_premium
            
            # GST
            gst_pct = Decimal('18.00')
            gst_amount = final_premium * (gst_pct / 100)
            total_premium = final_premium + gst_amount
            
            # Calculate score
            customer = application.customer
            scores = calculate_quote_score(
                premium=total_premium,
                company=company,
                selected_coverages=coverage_ids,
                insurance_type_id=application.insurance_type.id,
                annual_income=customer.annual_income,
                budget_min=application.budget_min,
                budget_max=application.budget_max
            )
            
            # Create quote
            quote = Quote.objects.create(
                application=application,
                customer=customer,
                insurance_type=application.insurance_type,
                insurance_company=company,
                base_premium=base_premium,
                risk_adjustment_percentage=risk_adjustment,
                adjusted_premium=adjusted_premium,
                final_premium=final_premium,
                gst_percentage=gst_pct,
                gst_amount=gst_amount,
                total_premium_with_gst=total_premium,
                sum_insured=application.requested_coverage_amount or Decimal('500000'),
                policy_tenure_months=application.policy_tenure_months,
                overall_score=scores['overall_score'],
                generated_by=request.user
            )
            
            # Create quote coverages
            for cov_id in coverage_ids:
                try:
                    coverage = type_coverages.get(id=cov_id)
                    QuoteCoverage.objects.create(
                        quote=quote,
                        coverage_type=coverage,
                        coverage_limit=application.requested_coverage_amount or Decimal('500000'),
                        coverage_premium=coverage.base_premium_per_unit,
                        is_selected=True
                    )
                except CoverageType.DoesNotExist:
                    pass
            
            # Create quote addons
            for addon_id in addon_ids:
                try:
                    addon = type_addons.get(id=addon_id)
                    QuoteAddon.objects.create(
                        quote=quote,
                        addon=addon,
                        addon_premium=base_premium * (addon.premium_percentage / 100),
                        is_selected=True
                    )
                except RiderAddon.DoesNotExist:
                    pass
            
            generated_quotes.append((quote, scores))
        
        # Sort by score and create recommendations (top 3)
        generated_quotes.sort(key=lambda x: x[1]['overall_score'], reverse=True)
        
        # Clear old recommendations
        QuoteRecommendation.objects.filter(application=application).delete()
        
        for rank, (quote, scores) in enumerate(generated_quotes[:3], start=1):
            QuoteRecommendation.objects.create(
                application=application,
                customer=application.customer,
                insurance_type=application.insurance_type,
                recommended_quote=quote,
                recommendation_rank=rank,
                recommendation_reason=generate_recommendation_reason(
                    scores, quote.insurance_company.company_name
                ),
                suitability_score=scores['overall_score'],
                affordability_score=scores['affordability_score'],
                coverage_match_score=scores['coverage_score'],
                company_rating_score=scores['claim_ratio_score']
            )
        
        # Return comparison
        recommendations = QuoteRecommendation.objects.filter(
            application=application
        ).select_related('recommended_quote__insurance_company')
        
        all_quotes = [q for q, _ in generated_quotes]
        
        return Response({
            'message': f'Generated {len(generated_quotes)} quotes.',
            'application_id': application.id,
            'total_quotes': len(generated_quotes),
            'recommendations': QuoteRecommendationSerializer(recommendations, many=True).data,
            'all_quotes': QuoteListSerializer(all_quotes, many=True).data
        }, status=status.HTTP_201_CREATED)
    
    def _calculate_base_premium(self, application, company, coverage_ids):
        """Calculate base premium from coverages."""
        coverages = CoverageType.objects.filter(id__in=coverage_ids)
        base = sum(c.base_premium_per_unit for c in coverages)
        
        # Apply company-specific multiplier (simplified)
        multiplier = Decimal('1.0')
        if company.service_rating >= Decimal('4.5'):
            multiplier = Decimal('1.15')  # Premium for top-rated
        elif company.service_rating >= Decimal('4.0'):
            multiplier = Decimal('1.05')
        
        return base * multiplier if base > 0 else Decimal('10000')
    
    def _calculate_addon_premium(self, base_premium, addon_ids):
        """Calculate addon premium."""
        addons = RiderAddon.objects.filter(id__in=addon_ids)
        total = Decimal('0')
        for addon in addons:
            total += base_premium * (addon.premium_percentage / 100)
        return total
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Get quote comparison for an application.
        
        Query params:
        - application_id: Required application ID
        """
        application_id = request.query_params.get('application_id')
        
        if not application_id:
            return Response(
                {'error': 'application_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            application = InsuranceApplication.objects.get(id=application_id)
        except InsuranceApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if application.customer.user != request.user:
            if not request.user.user_roles.filter(
                role__role_name__in=['ADMIN', 'BACKOFFICE']
            ).exists():
                return Response(
                    {'error': 'Access denied.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        recommendations = QuoteRecommendation.objects.filter(
            application=application
        ).select_related('recommended_quote__insurance_company')
        
        all_quotes = Quote.objects.filter(
            application=application
        ).select_related('insurance_company').order_by('-overall_score')
        
        return Response({
            'application_id': application.id,
            'total_quotes': all_quotes.count(),
            'recommendations': QuoteRecommendationSerializer(recommendations, many=True).data,
            'all_quotes': QuoteListSerializer(all_quotes, many=True).data
        })
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a quote."""
        quote = self.get_object()
        
        # Check ownership
        if quote.customer.user != request.user:
            return Response(
                {'error': 'You can only accept your own quotes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            quote.accept()
            return Response({
                'message': 'Quote accepted successfully.',
                'quote': QuoteSerializer(quote).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
