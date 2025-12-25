"""
Role-Based Access Control Mixins

These mixins enforce server-side authorization for template views.
Every protected view must use the appropriate mixin.

Security:
- AdminRequiredMixin → /panel/* routes
- BackofficeRequiredMixin → /backoffice/* routes  
- CustomerRequiredMixin → /customer/* routes

Unauthorized access returns 403 Forbidden, NOT just menu hiding.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleCheckMixin(UserPassesTestMixin):
    """Base mixin for role checking."""
    required_roles = []
    
    def test_func(self):
        """Check if user has any of the required roles."""
        if not self.request.user.is_authenticated:
            return False
        
        return self.request.user.user_roles.filter(
            role__role_name__in=self.required_roles
        ).exists()
    
    def handle_no_permission(self):
        """Return 403 Forbidden for unauthorized users."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this page.")
        return super().handle_no_permission()


class AdminRequiredMixin(LoginRequiredMixin, RoleCheckMixin):
    """
    Mixin for Admin-only views.
    
    Use for: /panel/* routes (custom admin panel)
    
    Example:
        class UserListView(AdminRequiredMixin, ListView):
            model = User
    """
    required_roles = ['ADMIN']
    login_url = '/auth/login/'


class BackofficeRequiredMixin(LoginRequiredMixin, RoleCheckMixin):
    """
    Mixin for Backoffice views (includes Admin).
    
    Use for: /backoffice/* routes
    
    Example:
        class ApplicationReviewView(BackofficeRequiredMixin, DetailView):
            model = InsuranceApplication
    """
    required_roles = ['ADMIN', 'BACKOFFICE']
    login_url = '/auth/login/'


class CustomerRequiredMixin(LoginRequiredMixin, RoleCheckMixin):
    """
    Mixin for Customer views.
    
    Use for: /customer/* routes
    
    Example:
        class CustomerDashboardView(CustomerRequiredMixin, TemplateView):
            template_name = 'customer/dashboard.html'
    """
    required_roles = ['CUSTOMER']
    login_url = '/auth/login/'


class AnyAuthenticatedMixin(LoginRequiredMixin):
    """
    Mixin for any authenticated user.
    
    Use for: Profile, common pages accessible by all roles.
    """
    login_url = '/auth/login/'


def get_user_role(user):
    """
    Get the primary role of a user.
    
    Returns: 'ADMIN', 'BACKOFFICE', 'CUSTOMER', or None
    """
    if not user.is_authenticated:
        return None
    
    # Priority: ADMIN > BACKOFFICE > CUSTOMER
    for role in ['ADMIN', 'BACKOFFICE', 'CUSTOMER']:
        if user.user_roles.filter(role__role_name=role).exists():
            return role
    
    return None


def get_dashboard_url(user):
    """
    Get the appropriate dashboard URL for a user based on role.
    """
    role = get_user_role(user)
    
    if role == 'ADMIN':
        return '/panel/dashboard/'
    elif role == 'BACKOFFICE':
        return '/backoffice/dashboard/'
    elif role == 'CUSTOMER':
        return '/customer/dashboard/'
    
    return '/auth/login/'
