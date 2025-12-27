"""
Frontend Views

All views use server-side role-guard mixins for authorization.
Unauthorized access returns 403 Forbidden, NOT just menu hiding.

Template Auth: Django session authentication
API Auth: JWT (for AJAX calls)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q
from django.utils import timezone

from apps.accounts.mixins import (
    AdminRequiredMixin,
    BackofficeRequiredMixin,
    CustomerRequiredMixin,
    get_dashboard_url
)
from apps.accounts.models import User, Role, UserRole
from apps.customers.models import CustomerProfile
from apps.catalog.models import InsuranceType, InsuranceCompany, CoverageType, RiderAddon
from apps.applications.models import InsuranceApplication, ApplicationDocument
from apps.quotes.models import Quote, QuoteRecommendation
from apps.policies.models import Policy, Payment, Invoice
from apps.claims.models import Claim


# ============== Public Views ==============

def landing_page(request):
    """Landing page - redirect to dashboard if logged in."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))
    return render(request, 'landing.html')


def login_view(request):
    """Login page with session authentication."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            return redirect(get_dashboard_url(user))
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'auth/login.html')


def register_view(request):
    """Registration page."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'auth/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=email,  # Email is used as username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Assign CUSTOMER role
        customer_role = Role.objects.filter(role_name='CUSTOMER').first()
        if customer_role:
            UserRole.objects.create(user=user, role=customer_role)
        
        # Create customer profile
        CustomerProfile.objects.create(user=user)
        
        # Login user
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('customer_dashboard')
    
    return render(request, 'auth/register.html')


@login_required
def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ============== Customer Portal ==============

class CustomerDashboardView(CustomerRequiredMixin, TemplateView):
    """Customer dashboard with summary stats."""
    template_name = 'customer/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = CustomerProfile.objects.get(user=self.request.user)
        
        context['customer'] = customer
        context['applications_count'] = InsuranceApplication.objects.filter(customer=customer).count()
        context['active_policies_count'] = Policy.objects.filter(customer=customer, status='ACTIVE').count()
        context['pending_claims_count'] = Claim.objects.filter(
            customer=customer, status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        context['recent_applications'] = InsuranceApplication.objects.filter(
            customer=customer
        ).order_by('-created_at')[:5]
        
        return context


class CustomerApplicationListView(CustomerRequiredMixin, ListView):
    """List customer's applications with search support."""
    template_name = 'customer/applications/list.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        from django.db.models import Q
        customer = CustomerProfile.objects.get(user=self.request.user)
        queryset = InsuranceApplication.objects.filter(
            customer=customer
        ).select_related('insurance_type').order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(application_number__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class CustomerApplicationCreateView(CustomerRequiredMixin, TemplateView):
    """Create new application."""
    template_name = 'customer/applications/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context


class CustomerApplicationDetailView(CustomerRequiredMixin, DetailView):
    """View application details."""
    template_name = 'customer/applications/detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return InsuranceApplication.objects.filter(customer=customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all().order_by('-uploaded_at')
        return context


class CustomerQuoteListView(CustomerRequiredMixin, ListView):
    """List customer's quotes."""
    template_name = 'customer/quotes/list.html'
    context_object_name = 'quotes'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Quote.objects.filter(customer=customer).order_by('-created_at')


class CustomerQuoteDetailView(CustomerRequiredMixin, DetailView):
    """View quote details with comparison."""
    template_name = 'customer/quotes/detail.html'
    context_object_name = 'quote'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Quote.objects.filter(customer=customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote = self.get_object()
        context['recommendations'] = QuoteRecommendation.objects.filter(
            application=quote.application
        ).select_related('recommended_quote')[:3]
        return context


class CustomerPaymentView(CustomerRequiredMixin, DetailView):
    """Payment page with Razorpay integration."""
    template_name = 'customer/payment.html'
    context_object_name = 'quote'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Quote.objects.filter(customer=customer, status='ACCEPTED')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.policies.payment_gateway import razorpay_gateway
        context['razorpay_key_id'] = razorpay_gateway.get_key_id()
        return context


class CustomerPolicyListView(CustomerRequiredMixin, ListView):
    """List customer's policies."""
    template_name = 'customer/policies/list.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Policy.objects.filter(customer=customer).order_by('-created_at')


class CustomerPolicyDetailView(CustomerRequiredMixin, DetailView):
    """View policy details."""
    template_name = 'customer/policies/detail.html'
    context_object_name = 'policy'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Policy.objects.filter(customer=customer)


class CustomerClaimListView(CustomerRequiredMixin, ListView):
    """List customer's claims."""
    template_name = 'customer/claims/list.html'
    context_object_name = 'claims'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Claim.objects.filter(customer=customer).order_by('-created_at')


class CustomerClaimCreateView(CustomerRequiredMixin, TemplateView):
    """Create new claim."""
    template_name = 'customer/claims/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = CustomerProfile.objects.get(user=self.request.user)
        context['policies'] = Policy.objects.filter(customer=customer, status='ACTIVE')
        return context


class CustomerClaimDetailView(CustomerRequiredMixin, DetailView):
    """View claim details."""
    template_name = 'customer/claims/detail.html'
    context_object_name = 'claim'
    
    def get_queryset(self):
        customer = CustomerProfile.objects.get(user=self.request.user)
        return Claim.objects.filter(customer=customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all().order_by('-uploaded_at')
        return context


class CustomerNotificationsView(CustomerRequiredMixin, TemplateView):
    """View all notifications for customer."""
    template_name = 'customer/notifications.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.notifications.models import Notification
        
        notifications = Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:100]
        
        context['notifications'] = notifications
        context['unread_count'] = notifications.filter(is_read=False).count()
        return context


class CustomerProfileView(CustomerRequiredMixin, TemplateView):
    """View/edit customer profile with risk data."""
    template_name = 'customer/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = CustomerProfile.objects.get(user=self.request.user)
        context['profile'] = profile
        
        # Medical disclosure for health insurance
        from apps.customers.models import CustomerMedicalDisclosure, CustomerDrivingHistory, CustomerRiskProfile
        context['medical_disclosures'] = CustomerMedicalDisclosure.objects.filter(
            customer=profile
        ).order_by('-disclosure_date')
        
        # Driving history for motor insurance
        try:
            context['driving_history'] = profile.driving_history
        except CustomerDrivingHistory.DoesNotExist:
            context['driving_history'] = None
        
        # Risk profile
        try:
            context['risk_profile'] = profile.risk_profile
        except CustomerRiskProfile.DoesNotExist:
            context['risk_profile'] = None
        
        return context


class PolicyExploreView(CustomerRequiredMixin, TemplateView):
    """Policy marketplace/discovery page."""
    template_name = 'customer/explore.html'


class InsuranceTypeDetailView(CustomerRequiredMixin, TemplateView):
    """Insurance type detail page with full info."""
    template_name = 'customer/insurance_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        insurance_type = InsuranceType.objects.prefetch_related(
            'coverage_types', 'addons'
        ).get(pk=self.kwargs['pk'])
        
        context['insurance_type'] = insurance_type
        context['coverages'] = insurance_type.coverage_types.all()
        context['addons'] = insurance_type.addons.all()
        
        # Get premium range from coverages
        premiums = [c.base_premium_per_unit for c in context['coverages'] if c.base_premium_per_unit]
        context['premium_range'] = {
            'min': min(premiums) if premiums else 0,
            'max': max(premiums) if premiums else 0,
        }
        
        # Get active companies
        context['companies'] = InsuranceCompany.objects.filter(is_active=True)
        
        # Icon mapping
        icon_map = {
            'MOTOR': 'car-front',
            'HEALTH': 'heart-pulse',
            'TRAVEL': 'airplane',
            'WC': 'briefcase',
            'CPM': 'building',
        }
        context['icon_name'] = icon_map.get(insurance_type.type_code, 'shield')
        
        return context


# ============== Backoffice Dashboard ==============

class BackofficeDashboardView(BackofficeRequiredMixin, TemplateView):
    """Backoffice dashboard with pending items."""
    template_name = 'backoffice/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['pending_applications'] = InsuranceApplication.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        context['pending_claims'] = Claim.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        context['recent_applications'] = InsuranceApplication.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).order_by('-created_at')[:10]
        context['recent_claims'] = Claim.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).order_by('-created_at')[:10]
        
        return context


class BackofficeApplicationListView(BackofficeRequiredMixin, ListView):
    """List all applications for review with search support."""
    template_name = 'backoffice/applications/list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = InsuranceApplication.objects.select_related(
            'customer__user', 'insurance_type'
        ).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(application_number__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.distinct()


class BackofficeApplicationDetailView(BackofficeRequiredMixin, DetailView):
    """Review application details with documents, quotes, and risk info."""
    template_name = 'backoffice/applications/detail.html'
    context_object_name = 'application'
    model = InsuranceApplication
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.object
        
        # Documents
        context['documents'] = ApplicationDocument.objects.filter(
            application=application
        ).order_by('-uploaded_at')
        
        # Quotes generated for this application
        context['quotes'] = Quote.objects.filter(
            application=application
        ).select_related('insurance_company').order_by('-created_at')
        
        # Customer risk profile if available
        try:
            context['risk_profile'] = application.customer.risk_profile
        except:
            context['risk_profile'] = None
        
        # Form data (from application fields)
        context['form_data'] = application.form_data or {}
        
        # Insurance companies for quote generation
        context['insurance_companies'] = InsuranceCompany.objects.filter(is_active=True)
        
        return context


class BackofficeClaimListView(BackofficeRequiredMixin, ListView):
    """List all claims for review."""
    template_name = 'backoffice/claims/list.html'
    context_object_name = 'claims'
    paginate_by = 20
    
    def get_queryset(self):
        status_filter = self.request.GET.get('status')
        queryset = Claim.objects.all().order_by('-created_at')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class BackofficeClaimDetailView(BackofficeRequiredMixin, DetailView):
    """Review claim details with assessments, history, and settlement."""
    template_name = 'backoffice/claims/detail.html'
    context_object_name = 'claim'
    model = Claim
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claim = self.object
        
        # Status history
        from apps.claims.models import ClaimStatusHistory, ClaimAssessment, ClaimSettlement
        context['status_history'] = ClaimStatusHistory.objects.filter(
            claim=claim
        ).order_by('-status_changed_at')
        
        # Assessments
        context['assessments'] = ClaimAssessment.objects.filter(
            claim=claim
        ).select_related('surveyor').order_by('-created_at')
        
        # Settlement
        try:
            context['settlement'] = claim.settlement
        except ClaimSettlement.DoesNotExist:
            context['settlement'] = None
        
        # Available surveyors (users with SURVEYOR role)
        context['surveyors'] = User.objects.filter(
            user_roles__role__role_name='SURVEYOR',
            is_active=True
        ).distinct()
        
        # SLA status using service
        from apps.claims.services import ClaimsWorkflowService
        service = ClaimsWorkflowService(claim)
        context['sla_status'] = service.get_sla_status()
        
        return context


class BackofficeQuoteListView(BackofficeRequiredMixin, ListView):
    """List all quotes for management."""
    template_name = 'backoffice/quotes/list.html'
    context_object_name = 'quotes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Quote.objects.select_related(
            'customer__user', 'insurance_type', 'insurance_company', 'application'
        ).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(quote_number__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query) |
                Q(insurance_company__company_name__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by insurance type
        type_filter = self.request.GET.get('insurance_type')
        if type_filter:
            queryset = queryset.filter(insurance_type_id=type_filter)
        
        # Filter by company
        company_filter = self.request.GET.get('company')
        if company_filter:
            queryset = queryset.filter(insurance_company_id=company_filter)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        context['companies'] = InsuranceCompany.objects.filter(is_active=True)
        return context


class BackofficeQuoteCreateView(BackofficeRequiredMixin, TemplateView):
    """Generate new quotes for approved applications."""
    template_name = 'backoffice/quotes/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        
        # Get approved applications that don't have quotes yet or allow regeneration
        context['approved_applications'] = InsuranceApplication.objects.filter(
            status='APPROVED'
        ).select_related('customer__user', 'insurance_type').order_by('-created_at')
        
        # Pre-select application from query param
        context['preselected_app'] = self.request.GET.get('application')
        if context['preselected_app']:
            try:
                context['preselected_app'] = int(context['preselected_app'])
            except ValueError:
                context['preselected_app'] = None
        
        # Companies for selection
        context['companies'] = InsuranceCompany.objects.filter(is_active=True)
        
        # Coverages and addons as JSON for JavaScript
        coverages = list(CoverageType.objects.filter(
            insurance_type__is_active=True
        ).values('id', 'coverage_name', 'coverage_code', 'insurance_type', 'base_premium_per_unit', 'is_mandatory'))
        context['coverages_json'] = json.dumps(coverages, default=str)
        
        addons = list(RiderAddon.objects.filter(
            insurance_type__is_active=True
        ).values('id', 'addon_name', 'addon_code', 'insurance_type', 'premium_percentage'))
        context['addons_json'] = json.dumps(addons, default=str)
        
        return context


class BackofficeQuoteDetailView(BackofficeRequiredMixin, DetailView):
    """View and manage quote details."""
    template_name = 'backoffice/quotes/detail.html'
    context_object_name = 'quote'
    model = Quote
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote = self.object
        
        # Get coverages and addons
        context['coverages'] = quote.coverages.select_related('coverage_type').all()
        context['addons'] = quote.addons.select_related('addon').all()
        
        # Get related quotes for same application
        context['related_quotes'] = Quote.objects.filter(
            application=quote.application
        ).select_related('insurance_company').order_by('-overall_score')
        
        return context


# ============== Custom Admin Panel ==============

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard with system stats."""
    template_name = 'panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['total_policies'] = Policy.objects.count()
        context['total_premium'] = Policy.objects.filter(
            status='ACTIVE'
        ).aggregate(total=Sum('total_premium_with_gst'))['total'] or 0
        context['total_claims'] = Claim.objects.count()
        context['pending_claims'] = Claim.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        
        return context


class AdminUserListView(AdminRequiredMixin, ListView):
    """List all users with search support."""
    template_name = 'panel/users/list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = User.objects.prefetch_related('user_roles__role').order_by('-date_joined')
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Filter by role
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(user_roles__role__role_name__iexact=role)
        
        # Filter by status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.distinct()


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """View/edit user details."""
    template_name = 'panel/users/detail.html'
    context_object_name = 'user_obj'
    model = User
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Role.objects.all()
        context['user_roles'] = self.object.user_roles.all()
        return context


class AdminInsuranceTypeListView(AdminRequiredMixin, ListView):
    """Manage insurance types with search."""
    template_name = 'panel/catalog/types.html'
    context_object_name = 'types'
    
    def get_queryset(self):
        queryset = InsuranceType.objects.prefetch_related('coverage_types').all()
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(type_name__icontains=search_query) |
                Q(type_code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Status filter
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Annotate with coverage count and premium range
        types_with_data = []
        for ins_type in queryset:
            premiums = [c.base_premium_per_unit for c in ins_type.coverage_types.all() if c.base_premium_per_unit]
            ins_type.min_premium = min(premiums) if premiums else 0
            ins_type.max_premium = max(premiums) if premiums else 0
            ins_type.coverage_count = ins_type.coverage_types.count()
            types_with_data.append(ins_type)
        
        return types_with_data


class AdminCoverageTypeListView(AdminRequiredMixin, ListView):
    """Manage coverage types with base premium."""
    template_name = 'panel/catalog/coverages.html'
    context_object_name = 'coverages'
    
    def get_queryset(self):
        from apps.catalog.models import CoverageType
        queryset = CoverageType.objects.select_related('insurance_type').order_by(
            'insurance_type', 'coverage_name'
        )
        
        # Filter by insurance type
        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(insurance_type_id=type_id)
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(coverage_name__icontains=search_query) |
                Q(coverage_code__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for coverage types."""
        from apps.catalog.models import CoverageType
        from decimal import Decimal
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        coverage_id = request.POST.get('coverage_id')
        
        try:
            if action == 'create':
                CoverageType.objects.create(
                    coverage_name=request.POST.get('coverage_name'),
                    coverage_code=request.POST.get('coverage_code'),
                    insurance_type_id=request.POST.get('insurance_type'),
                    description=request.POST.get('description', ''),
                    base_premium_per_unit=Decimal(request.POST.get('base_premium_per_unit', '0')),
                    unit_of_measurement=request.POST.get('unit_of_measurement', 'per policy'),
                    is_mandatory=request.POST.get('is_mandatory') == 'on'
                )
                messages.success(request, 'Coverage type created successfully.')
            
            elif action == 'update' and coverage_id:
                coverage = CoverageType.objects.get(id=coverage_id)
                coverage.coverage_name = request.POST.get('coverage_name', coverage.coverage_name)
                coverage.base_premium_per_unit = Decimal(request.POST.get('base_premium_per_unit', coverage.base_premium_per_unit))
                coverage.description = request.POST.get('description', coverage.description)
                coverage.is_mandatory = request.POST.get('is_mandatory') == 'on'
                coverage.save()
                messages.success(request, 'Coverage type updated successfully.')
            
            elif action == 'delete' and coverage_id:
                CoverageType.objects.filter(id=coverage_id).delete()
                messages.success(request, 'Coverage type deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_coverage_types')


class AdminCompanyListView(AdminRequiredMixin, ListView):
    """Manage insurance companies with search."""
    template_name = 'panel/catalog/companies.html'
    context_object_name = 'companies'
    
    def get_queryset(self):
        queryset = InsuranceCompany.objects.all()
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(company_code__icontains=search_query) |
                Q(registration_number__icontains=search_query)
            )
        
        # Status filter
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Rating filter
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            queryset = queryset.filter(service_rating__gte=float(min_rating))
        
        return queryset


class AdminPolicyListView(AdminRequiredMixin, ListView):
    """View all policies with search."""
    template_name = 'panel/policies/list.html'
    context_object_name = 'policies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Policy.objects.select_related('customer__user', 'insurance_type', 'insurance_company').all()
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(policy_number__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query) |
                Q(insurance_company__company_name__icontains=search_query)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


class AdminPaymentListView(AdminRequiredMixin, ListView):
    """View all payments with search."""
    template_name = 'panel/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Payment.objects.select_related('quote__application__customer__user').all()
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(razorpay_order_id__icontains=search_query) |
                Q(razorpay_payment_id__icontains=search_query) |
                Q(quote__quote_number__icontains=search_query) |
                Q(quote__application__customer__user__email__icontains=search_query)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


class AdminQuoteListView(AdminRequiredMixin, ListView):
    """View all quotes with search and filters."""
    template_name = 'panel/quotes/list.html'
    context_object_name = 'quotes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Quote.objects.select_related(
            'customer__user', 'insurance_type', 'insurance_company'
        ).all()
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(quote_number__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(insurance_type__type_name__icontains=search_query) |
                Q(insurance_company__company_name__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Insurance type filter
        type_filter = self.request.GET.get('insurance_type')
        if type_filter:
            queryset = queryset.filter(insurance_type_id=type_filter)
        
        # Company filter
        company_filter = self.request.GET.get('company')
        if company_filter:
            queryset = queryset.filter(insurance_company_id=company_filter)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        context['companies'] = InsuranceCompany.objects.filter(is_active=True)
        
        # Stats
        context['stats'] = {
            'total': Quote.objects.count(),
            'generated': Quote.objects.filter(status='GENERATED').count(),
            'sent': Quote.objects.filter(status='SENT').count(),
            'accepted': Quote.objects.filter(status='ACCEPTED').count(),
        }
        return context


class AdminCustomerListView(AdminRequiredMixin, ListView):
    """View all customers with search and filters."""
    template_name = 'panel/customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CustomerProfile.objects.select_related('user').annotate(
            applications_count=Count('applications'),
            policies_count=Count('policies'),
            claims_count=Count('claims')
        )
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )
        
        # KYC status filter
        kyc_status = self.request.GET.get('kyc_status')
        if kyc_status:
            queryset = queryset.filter(kyc_status=kyc_status)
        
        # Has policies filter
        has_policies = self.request.GET.get('has_policies')
        if has_policies == 'yes':
            queryset = queryset.filter(policies_count__gt=0)
        elif has_policies == 'no':
            queryset = queryset.filter(policies_count=0)
        
        return queryset.order_by('-user__date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats
        total = CustomerProfile.objects.count()
        with_policies = CustomerProfile.objects.filter(policies__isnull=False).distinct().count()
        kyc_verified = CustomerProfile.objects.filter(kyc_status='VERIFIED').count()
        
        context['stats'] = {
            'total': total,
            'with_policies': with_policies,
            'kyc_verified': kyc_verified
        }
        return context


class AdminRiderAddonListView(AdminRequiredMixin, ListView):
    """Manage rider add-ons."""
    template_name = 'panel/catalog/addons.html'
    context_object_name = 'addons'
    
    def get_queryset(self):
        queryset = RiderAddon.objects.select_related('insurance_type').order_by(
            'insurance_type', 'addon_name'
        )
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(addon_name__icontains=search_query) |
                Q(addon_code__icontains=search_query)
            )
        
        # Insurance type filter
        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(insurance_type_id=type_id)
        
        # Status filter
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for rider add-ons."""
        from decimal import Decimal
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        addon_id = request.POST.get('addon_id')
        
        try:
            if action == 'create':
                RiderAddon.objects.create(
                    addon_name=request.POST.get('addon_name'),
                    addon_code=request.POST.get('addon_code'),
                    insurance_type_id=request.POST.get('insurance_type'),
                    description=request.POST.get('description', ''),
                    premium_percentage=Decimal(request.POST.get('premium_percentage', '0')),
                    is_active=request.POST.get('is_active') == 'on'
                )
                messages.success(request, 'Rider add-on created successfully.')
            
            elif action == 'update' and addon_id:
                addon = RiderAddon.objects.get(id=addon_id)
                addon.addon_name = request.POST.get('addon_name', addon.addon_name)
                addon.premium_percentage = Decimal(request.POST.get('premium_percentage', addon.premium_percentage))
                addon.description = request.POST.get('description', addon.description)
                addon.is_active = request.POST.get('is_active') == 'on'
                addon.save()
                messages.success(request, 'Rider add-on updated successfully.')
            
            elif action == 'delete' and addon_id:
                RiderAddon.objects.filter(id=addon_id).delete()
                messages.success(request, 'Rider add-on deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_rider_addons')


# ============== Admin Configuration Management ==============

class AdminPremiumSlabListView(AdminRequiredMixin, ListView):
    """Manage premium slabs by insurance type."""
    template_name = 'panel/config/premium_slabs.html'
    context_object_name = 'slabs'
    
    def get_queryset(self):
        from apps.catalog.config_models import PremiumSlab
        queryset = PremiumSlab.objects.select_related('insurance_type').order_by(
            'insurance_type', 'min_coverage_amount'
        )
        
        # Filter by insurance type
        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(insurance_type_id=type_id)
        
        # Filter by status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations via POST."""
        from apps.catalog.config_models import PremiumSlab
        from decimal import Decimal
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        slab_id = request.POST.get('slab_id')
        
        try:
            if action == 'create':
                PremiumSlab.objects.create(
                    insurance_type_id=request.POST.get('insurance_type'),
                    slab_name=request.POST.get('slab_name'),
                    min_coverage_amount=Decimal(request.POST.get('min_coverage_amount', '0')),
                    max_coverage_amount=Decimal(request.POST.get('max_coverage_amount', '0')),
                    base_premium=Decimal(request.POST.get('base_premium', '0')),
                    percentage_markup=Decimal(request.POST.get('percentage_markup', '0')),
                    is_active=True
                )
                messages.success(request, 'Premium slab created successfully.')
            
            elif action == 'update' and slab_id:
                slab = PremiumSlab.objects.get(id=slab_id)
                slab.slab_name = request.POST.get('slab_name', slab.slab_name)
                slab.base_premium = Decimal(request.POST.get('base_premium', slab.base_premium))
                slab.percentage_markup = Decimal(request.POST.get('percentage_markup', slab.percentage_markup))
                slab.save()
                messages.success(request, 'Premium slab updated successfully.')
            
            elif action == 'toggle' and slab_id:
                slab = PremiumSlab.objects.get(id=slab_id)
                slab.is_active = not slab.is_active
                slab.save()
                messages.success(request, f'Premium slab {"activated" if slab.is_active else "deactivated"}.')
            
            elif action == 'delete' and slab_id:
                PremiumSlab.objects.filter(id=slab_id).delete()
                messages.success(request, 'Premium slab deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_premium_slabs')


class AdminDiscountRuleListView(AdminRequiredMixin, ListView):
    """Manage discount rules."""
    template_name = 'panel/config/discount_rules.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        from apps.catalog.config_models import DiscountRule
        queryset = DiscountRule.objects.select_related('insurance_type').order_by(
            '-rule_priority', 'rule_name'
        )
        
        # Filter by insurance type
        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(insurance_type_id=type_id)
        
        # Search
        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(rule_name__icontains=search) |
                Q(rule_code__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for discount rules."""
        from apps.catalog.config_models import DiscountRule
        from decimal import Decimal
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        rule_id = request.POST.get('rule_id')
        
        try:
            if action == 'create':
                DiscountRule.objects.create(
                    rule_name=request.POST.get('rule_name'),
                    rule_code=request.POST.get('rule_code'),
                    insurance_type_id=request.POST.get('insurance_type') or None,
                    discount_percentage=Decimal(request.POST.get('discount_percentage', '0')),
                    rule_priority=int(request.POST.get('rule_priority', '0')),
                    is_combinable=request.POST.get('is_combinable') == 'on',
                    is_active=True
                )
                messages.success(request, 'Discount rule created successfully.')
            
            elif action == 'update' and rule_id:
                rule = DiscountRule.objects.get(id=rule_id)
                rule.rule_name = request.POST.get('rule_name', rule.rule_name)
                rule.discount_percentage = Decimal(request.POST.get('discount_percentage', rule.discount_percentage))
                rule.save()
                messages.success(request, 'Discount rule updated successfully.')
            
            elif action == 'toggle' and rule_id:
                rule = DiscountRule.objects.get(id=rule_id)
                rule.is_active = not rule.is_active
                rule.save()
                messages.success(request, f'Discount rule {"activated" if rule.is_active else "deactivated"}.')
            
            elif action == 'delete' and rule_id:
                DiscountRule.objects.filter(id=rule_id).delete()
                messages.success(request, 'Discount rule deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_discount_rules')


class AdminBusinessConfigListView(AdminRequiredMixin, ListView):
    """Manage system-wide configuration."""
    template_name = 'panel/config/business_config.html'
    context_object_name = 'configs'
    
    def get_queryset(self):
        from apps.catalog.config_models import BusinessConfiguration
        queryset = BusinessConfiguration.objects.order_by('config_type', 'config_key')
        
        # Filter by type
        config_type = self.request.GET.get('type')
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        
        # Search
        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(config_key__icontains=search) |
                Q(config_description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.catalog.config_models import BusinessConfiguration
        context['config_types'] = BusinessConfiguration.CONFIG_TYPE_CHOICES
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for business configuration."""
        from apps.catalog.config_models import BusinessConfiguration
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        config_id = request.POST.get('config_id')
        
        try:
            if action == 'create':
                BusinessConfiguration.objects.create(
                    config_key=request.POST.get('config_key'),
                    config_value=request.POST.get('config_value'),
                    config_type=request.POST.get('config_type', 'GENERAL'),
                    config_description=request.POST.get('config_description', ''),
                    is_active=True
                )
                messages.success(request, 'Configuration created successfully.')
            
            elif action == 'update' and config_id:
                config = BusinessConfiguration.objects.get(id=config_id)
                config.config_value = request.POST.get('config_value', config.config_value)
                config.config_description = request.POST.get('config_description', config.config_description)
                config.save()
                messages.success(request, 'Configuration updated successfully.')
            
            elif action == 'toggle' and config_id:
                config = BusinessConfiguration.objects.get(id=config_id)
                config.is_active = not config.is_active
                config.save()
                messages.success(request, f'Configuration {"activated" if config.is_active else "deactivated"}.')
            
            elif action == 'delete' and config_id:
                BusinessConfiguration.objects.filter(id=config_id).delete()
                messages.success(request, 'Configuration deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_business_config')


class AdminEligibilityRuleListView(AdminRequiredMixin, ListView):
    """Manage policy eligibility rules."""
    template_name = 'panel/config/eligibility_rules.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        from apps.catalog.config_models import PolicyEligibilityRule
        queryset = PolicyEligibilityRule.objects.select_related('insurance_type').order_by(
            'insurance_type', '-rule_priority'
        )
        
        # Filter by insurance type
        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(insurance_type_id=type_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for eligibility rules."""
        from apps.catalog.config_models import PolicyEligibilityRule
        from django.contrib import messages
        import json
        
        action = request.POST.get('action', 'create')
        rule_id = request.POST.get('rule_id')
        
        try:
            if action == 'create':
                # Parse JSON condition if provided
                condition = request.POST.get('rule_condition', '{}')
                try:
                    condition_json = json.loads(condition) if condition else {}
                except json.JSONDecodeError:
                    condition_json = {'raw': condition}
                
                PolicyEligibilityRule.objects.create(
                    insurance_type_id=request.POST.get('insurance_type'),
                    rule_name=request.POST.get('rule_name'),
                    rule_condition=condition_json,
                    rule_priority=int(request.POST.get('rule_priority', 0)),
                    error_message=request.POST.get('error_message', ''),
                    is_active=True
                )
                messages.success(request, 'Eligibility rule created successfully.')
            
            elif action == 'toggle' and rule_id:
                rule = PolicyEligibilityRule.objects.get(id=rule_id)
                rule.is_active = not rule.is_active
                rule.save()
                messages.success(request, f'Eligibility rule {"activated" if rule.is_active else "deactivated"}.')
            
            elif action == 'delete' and rule_id:
                PolicyEligibilityRule.objects.filter(id=rule_id).delete()
                messages.success(request, 'Eligibility rule deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_eligibility_rules')


class AdminClaimThresholdListView(AdminRequiredMixin, ListView):
    """Manage claim approval thresholds."""
    template_name = 'panel/config/claim_thresholds.html'
    context_object_name = 'thresholds'
    
    def get_queryset(self):
        from apps.catalog.config_models import ClaimApprovalThreshold
        return ClaimApprovalThreshold.objects.select_related(
            'insurance_type', 'required_approver_role'
        ).order_by('insurance_type', 'min_claim_amount')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.catalog.config_models import ClaimApprovalThreshold
        context['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        context['roles'] = Role.objects.all()
        context['approval_levels'] = ClaimApprovalThreshold.APPROVAL_LEVEL_CHOICES
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle CRUD operations for claim thresholds."""
        from apps.catalog.config_models import ClaimApprovalThreshold
        from decimal import Decimal
        from django.contrib import messages
        
        action = request.POST.get('action', 'create')
        threshold_id = request.POST.get('threshold_id')
        
        try:
            if action == 'create':
                ClaimApprovalThreshold.objects.create(
                    insurance_type_id=request.POST.get('insurance_type'),
                    approval_level=request.POST.get('approval_level'),
                    min_claim_amount=Decimal(request.POST.get('min_claim_amount', '0')),
                    max_claim_amount=Decimal(request.POST.get('max_claim_amount', '9999999999.99')),
                    required_approver_role_id=request.POST.get('required_approver_role'),
                    max_processing_days=int(request.POST.get('max_processing_days', 15)),
                    is_active=True
                )
                messages.success(request, 'Claim threshold created successfully.')
            
            elif action == 'toggle' and threshold_id:
                threshold = ClaimApprovalThreshold.objects.get(id=threshold_id)
                threshold.is_active = not threshold.is_active
                threshold.save()
                messages.success(request, f'Claim threshold {"activated" if threshold.is_active else "deactivated"}.')
            
            elif action == 'delete' and threshold_id:
                ClaimApprovalThreshold.objects.filter(id=threshold_id).delete()
                messages.success(request, 'Claim threshold deleted successfully.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_claim_thresholds')


class AdminAnalyticsDashboardView(AdminRequiredMixin, TemplateView):
    """Analytics dashboard with charts and metrics."""
    template_name = 'panel/analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date, timedelta
        
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Policy stats
        context['total_policies'] = Policy.objects.count()
        context['active_policies'] = Policy.objects.filter(status='ACTIVE').count()
        context['policies_this_month'] = Policy.objects.filter(
            created_at__date__gte=thirty_days_ago
        ).count()
        
        # Claim stats
        context['total_claims'] = Claim.objects.count()
        context['pending_claims'] = Claim.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count()
        context['approved_claims'] = Claim.objects.filter(status='APPROVED').count()
        context['settled_claims'] = Claim.objects.filter(status='SETTLED').count()
        
        # Financial
        context['total_premium'] = Policy.objects.filter(
            status='ACTIVE'
        ).aggregate(total=Sum('total_premium_with_gst'))['total'] or 0
        
        context['total_claims_paid'] = Claim.objects.filter(
            status='SETTLED'
        ).aggregate(total=Sum('amount_settled'))['total'] or 0
        
        # Recent activity
        context['recent_policies'] = Policy.objects.order_by('-created_at')[:5]
        context['recent_claims'] = Claim.objects.order_by('-created_at')[:5]
        
        # By insurance type
        context['policies_by_type'] = Policy.objects.values(
            'insurance_type__type_name'
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        return context


# ============== Payment Callbacks ==============

def payment_success(request):
    """Payment success callback page."""
    return render(request, 'customer/payment_success.html')


def payment_failure(request):
    """Payment failure callback page."""
    return render(request, 'customer/payment_failure.html')
