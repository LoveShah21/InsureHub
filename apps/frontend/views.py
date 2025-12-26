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


class CustomerProfileView(CustomerRequiredMixin, TemplateView):
    """View/edit customer profile."""
    template_name = 'customer/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = CustomerProfile.objects.get(user=self.request.user)
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
    """Review application details."""
    template_name = 'backoffice/applications/detail.html'
    context_object_name = 'application'
    model = InsuranceApplication


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
    """Review claim details."""
    template_name = 'backoffice/claims/detail.html'
    context_object_name = 'claim'
    model = Claim


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


# ============== Payment Callbacks ==============

def payment_success(request):
    """Payment success callback page."""
    return render(request, 'customer/payment_success.html')


def payment_failure(request):
    """Payment failure callback page."""
    return render(request, 'customer/payment_failure.html')
