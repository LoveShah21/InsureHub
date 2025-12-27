"""
Frontend URL Configuration

Routes:
- /               → Landing page
- /auth/*         → Authentication (login, register, logout)
- /customer/*     → Customer portal
- /backoffice/*   → Backoffice dashboard
- /panel/*        → Custom admin panel
"""

from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),
    
    # Authentication
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Customer Portal
    path('customer/dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('customer/applications/', views.CustomerApplicationListView.as_view(), name='customer_applications'),
    path('customer/applications/new/', views.CustomerApplicationCreateView.as_view(), name='customer_application_create'),
    path('customer/applications/<int:pk>/', views.CustomerApplicationDetailView.as_view(), name='customer_application_detail'),
    path('customer/quotes/', views.CustomerQuoteListView.as_view(), name='customer_quotes'),
    path('customer/quotes/<int:pk>/', views.CustomerQuoteDetailView.as_view(), name='customer_quote_detail'),
    path('customer/quotes/<int:pk>/pay/', views.CustomerPaymentView.as_view(), name='customer_payment'),
    path('customer/policies/', views.CustomerPolicyListView.as_view(), name='customer_policies'),
    path('customer/policies/<int:pk>/', views.CustomerPolicyDetailView.as_view(), name='customer_policy_detail'),
    path('customer/claims/', views.CustomerClaimListView.as_view(), name='customer_claims'),
    path('customer/claims/new/', views.CustomerClaimCreateView.as_view(), name='customer_claim_create'),
    path('customer/claims/<int:pk>/', views.CustomerClaimDetailView.as_view(), name='customer_claim_detail'),
    path('customer/profile/', views.CustomerProfileView.as_view(), name='customer_profile'),
    path('customer/notifications/', views.CustomerNotificationsView.as_view(), name='customer_notifications'),
    path('customer/explore/', views.PolicyExploreView.as_view(), name='policy_explore'),
    path('customer/insurance/<int:pk>/', views.InsuranceTypeDetailView.as_view(), name='insurance_type_detail'),
    
    # Backoffice Dashboard
    path('backoffice/dashboard/', views.BackofficeDashboardView.as_view(), name='backoffice_dashboard'),
    path('backoffice/applications/', views.BackofficeApplicationListView.as_view(), name='backoffice_applications'),
    path('backoffice/applications/<int:pk>/', views.BackofficeApplicationDetailView.as_view(), name='backoffice_application_detail'),
    path('backoffice/quotes/', views.BackofficeQuoteListView.as_view(), name='backoffice_quotes'),
    path('backoffice/quotes/create/', views.BackofficeQuoteCreateView.as_view(), name='backoffice_quote_create'),
    path('backoffice/quotes/<int:pk>/', views.BackofficeQuoteDetailView.as_view(), name='backoffice_quote_detail'),
    path('backoffice/claims/', views.BackofficeClaimListView.as_view(), name='backoffice_claims'),
    path('backoffice/claims/<int:pk>/', views.BackofficeClaimDetailView.as_view(), name='backoffice_claim_detail'),
    
    # Custom Admin Panel
    path('panel/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('panel/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('panel/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('panel/catalog/types/', views.AdminInsuranceTypeListView.as_view(), name='admin_insurance_types'),
    path('panel/catalog/coverages/', views.AdminCoverageTypeListView.as_view(), name='admin_coverage_types'),
    path('panel/catalog/addons/', views.AdminRiderAddonListView.as_view(), name='admin_rider_addons'),
    path('panel/catalog/companies/', views.AdminCompanyListView.as_view(), name='admin_companies'),
    path('panel/quotes/', views.AdminQuoteListView.as_view(), name='admin_quotes'),
    path('panel/policies/', views.AdminPolicyListView.as_view(), name='admin_policies'),
    path('panel/payments/', views.AdminPaymentListView.as_view(), name='admin_payments'),
    path('panel/customers/', views.AdminCustomerListView.as_view(), name='admin_customers'),
    
    # Configuration Management
    path('panel/config/premium-slabs/', views.AdminPremiumSlabListView.as_view(), name='admin_premium_slabs'),
    path('panel/config/discount-rules/', views.AdminDiscountRuleListView.as_view(), name='admin_discount_rules'),
    path('panel/config/business/', views.AdminBusinessConfigListView.as_view(), name='admin_business_config'),
    path('panel/config/eligibility/', views.AdminEligibilityRuleListView.as_view(), name='admin_eligibility_rules'),
    path('panel/config/claim-thresholds/', views.AdminClaimThresholdListView.as_view(), name='admin_claim_thresholds'),
    path('panel/analytics/', views.AdminAnalyticsDashboardView.as_view(), name='admin_analytics'),
    
    # Payment callbacks
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
]
