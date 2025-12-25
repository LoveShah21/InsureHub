"""
Analytics Dashboard Views

Provides live aggregation endpoints for metrics.
Uses ORM aggregation, no pre-computed tables.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from apps.accounts.permissions import IsAdminOrBackoffice
from apps.applications.models import InsuranceApplication
from apps.policies.models import Policy, Payment
from apps.claims.models import Claim
from apps.quotes.models import Quote


class DashboardView(APIView):
    """
    Analytics dashboard with live metrics.
    
    GET /api/v1/analytics/dashboard/
    
    Returns aggregated metrics for Admin/Backoffice.
    """
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
    
    def get(self, request):
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Application metrics
        applications_total = InsuranceApplication.objects.count()
        applications_pending = InsuranceApplication.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        applications_last_30_days = InsuranceApplication.objects.filter(
            created_at__date__gte=thirty_days_ago
        ).count()
        
        # Quote metrics
        quotes_total = Quote.objects.count()
        quotes_accepted = Quote.objects.filter(status='ACCEPTED').count()
        
        # Policy metrics
        policies_total = Policy.objects.count()
        policies_active = Policy.objects.filter(status='ACTIVE').count()
        total_premium_collected = Policy.objects.filter(
            status='ACTIVE'
        ).aggregate(total=Sum('total_premium_with_gst'))['total'] or 0
        
        # Claim metrics
        claims_total = Claim.objects.count()
        claims_pending = Claim.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        claims_approved = Claim.objects.filter(status='APPROVED').count()
        claims_settled = Claim.objects.filter(status='SETTLED').count()
        total_claims_amount = Claim.objects.filter(
            status='SETTLED'
        ).aggregate(total=Sum('amount_settled'))['total'] or 0
        
        # Payment metrics
        payment_success_rate = 0
        payments_total = Payment.objects.count()
        if payments_total > 0:
            payments_successful = Payment.objects.filter(status='SUCCESS').count()
            payment_success_rate = round((payments_successful / payments_total) * 100, 2)
        
        return Response({
            'generated_at': timezone.now().isoformat(),
            'period': {
                'from': thirty_days_ago.isoformat(),
                'to': today.isoformat()
            },
            'applications': {
                'total': applications_total,
                'pending_review': applications_pending,
                'last_30_days': applications_last_30_days
            },
            'quotes': {
                'total': quotes_total,
                'accepted': quotes_accepted,
                'acceptance_rate': round((quotes_accepted / quotes_total * 100), 2) if quotes_total > 0 else 0
            },
            'policies': {
                'total': policies_total,
                'active': policies_active,
                'total_premium_collected': float(total_premium_collected)
            },
            'claims': {
                'total': claims_total,
                'pending': claims_pending,
                'approved': claims_approved,
                'settled': claims_settled,
                'total_amount_settled': float(total_claims_amount)
            },
            'payments': {
                'total': payments_total,
                'success_rate_percent': payment_success_rate
            }
        })


class ApplicationMetricsView(APIView):
    """Application-specific analytics."""
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
    
    def get(self, request):
        # Group by status
        status_breakdown = InsuranceApplication.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Group by insurance type
        type_breakdown = InsuranceApplication.objects.values(
            'insurance_type__type_name'
        ).annotate(count=Count('id'))
        
        return Response({
            'by_status': list(status_breakdown),
            'by_type': list(type_breakdown)
        })


class ClaimMetricsView(APIView):
    """Claim-specific analytics."""
    permission_classes = [IsAuthenticated, IsAdminOrBackoffice]
    
    def get(self, request):
        # Group by status
        status_breakdown = Claim.objects.values('status').annotate(
            count=Count('id'),
            total_requested=Sum('amount_requested'),
            total_approved=Sum('amount_approved')
        )
        
        # Group by type
        type_breakdown = Claim.objects.values('claim_type').annotate(
            count=Count('id'),
            total_requested=Sum('amount_requested')
        )
        
        return Response({
            'by_status': list(status_breakdown),
            'by_type': list(type_breakdown)
        })
