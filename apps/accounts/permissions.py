"""
Custom permission classes for role-based access control.

Note: Current MVP enforces role-based access only.
Granular permissions are included for future extensibility.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class for Admin-only access.
    """
    message = "Admin access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(role__role_name='ADMIN').exists()


class IsBackoffice(BasePermission):
    """
    Permission class for Backoffice staff access.
    Includes Admin users.
    """
    message = "Backoffice access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(
            role__role_name__in=['ADMIN', 'BACKOFFICE']
        ).exists()


class IsCustomer(BasePermission):
    """
    Permission class for Customer access.
    """
    message = "Customer access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(role__role_name='CUSTOMER').exists()


class IsAdminOrBackoffice(BasePermission):
    """
    Permission class for Admin or Backoffice access.
    """
    message = "Admin or Backoffice access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(
            role__role_name__in=['ADMIN', 'BACKOFFICE']
        ).exists()


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission to allow owners or admins to access objects.
    Assumes the model has a `user` or `customer__user` field.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can access anything
        if request.user.user_roles.filter(role__role_name='ADMIN').exists():
            return True
        
        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer') and hasattr(obj.customer, 'user'):
            return obj.customer.user == request.user
        
        return False


def get_user_roles(user):
    """
    Helper function to get a user's role names.
    
    Returns:
        list: List of role names for the user
    """
    if not user or not user.is_authenticated:
        return []
    return list(user.user_roles.values_list('role__role_name', flat=True))


def has_role(user, role_name):
    """
    Helper function to check if user has a specific role.
    
    Args:
        user: User instance
        role_name: Role name string (e.g., 'ADMIN', 'BACKOFFICE', 'CUSTOMER')
    
    Returns:
        bool: True if user has the role
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_roles.filter(role__role_name=role_name).exists()


def is_admin(user):
    """Check if user is an admin."""
    return has_role(user, 'ADMIN')


def is_backoffice(user):
    """Check if user is backoffice staff."""
    return has_role(user, 'BACKOFFICE') or has_role(user, 'ADMIN')


def is_customer(user):
    """Check if user is a customer."""
    return has_role(user, 'CUSTOMER')
