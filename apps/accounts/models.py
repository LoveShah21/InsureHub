"""
Identity & Access Control (IAM) Models

This module contains the core authentication and authorization models:
- User: Custom user model extending AbstractUser
- Role: System roles (Admin, Backoffice, Customer)
- UserRole: Many-to-many junction for user-role assignment
- Permission: Granular permissions (future-ready, MVP uses role-based only)
- RolePermission: Role-permission mapping

Note: Current MVP enforces role-based access only. Granular permissions
are included for extensibility and demonstrate RBAC understanding.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Adds fields for:
    - Phone number
    - Login tracking
    - Account lockout handling
    """
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Login tracking
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_users'
    )
    updated_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_users'
    )
    
    # Use email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock the account for specified duration."""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock the account and reset failed attempts."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def record_failed_login(self, max_attempts=5, lockout_minutes=30):
        """
        Record a failed login attempt.
        Locks account after max_attempts failures.
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account(lockout_minutes)
        else:
            self.save(update_fields=['failed_login_attempts'])
    
    def record_successful_login(self):
        """Reset failed attempts on successful login."""
        self.failed_login_attempts = 0
        self.last_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_login'])


class Role(models.Model):
    """
    System roles for role-based access control.
    
    Default roles:
    - ADMIN: Full system access
    - BACKOFFICE: Policy & claim processing
    - CUSTOMER: Personal dashboard access
    """
    ROLE_ADMIN = 'ADMIN'
    ROLE_BACKOFFICE = 'BACKOFFICE'
    ROLE_CUSTOMER = 'CUSTOMER'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'System Administrator'),
        (ROLE_BACKOFFICE, 'Backoffice Officer'),
        (ROLE_CUSTOMER, 'Customer'),
    ]
    
    role_name = models.CharField(max_length=100, unique=True, db_index=True)
    role_description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.role_name
    
    @classmethod
    def get_default_roles(cls):
        """Return list of default system roles to seed."""
        return [
            {'role_name': cls.ROLE_ADMIN, 'role_description': 'System Administrator - Full Access', 'is_system_role': True},
            {'role_name': cls.ROLE_BACKOFFICE, 'role_description': 'Backoffice Staff - Policy & Claim Processing', 'is_system_role': True},
            {'role_name': cls.ROLE_CUSTOMER, 'role_description': 'End User - Personal Dashboard Access', 'is_system_role': True},
        ]


class UserRole(models.Model):
    """
    Junction table for many-to-many relationship between User and Role.
    Tracks who assigned the role and when.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name='assigned_roles',
        null=True, blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role.role_name}"


class Permission(models.Model):
    """
    Granular permissions for future extensibility.
    
    Note: Current MVP uses role-based access only.
    Permissions are included for extensibility and demonstrate RBAC understanding.
    
    Example permissions:
    - POLICY_CREATE, POLICY_VIEW, POLICY_EDIT
    - CLAIM_SUBMIT, CLAIM_REVIEW
    - USER_MANAGE, REPORT_VIEW
    """
    permission_code = models.CharField(max_length=100, unique=True, db_index=True)
    permission_description = models.CharField(max_length=255, blank=True)
    resource_name = models.CharField(max_length=100, db_index=True)
    action_name = models.CharField(max_length=50)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'permissions'
        indexes = [
            models.Index(fields=['resource_name', 'action_name']),
        ]
    
    def __str__(self):
        return f"{self.permission_code} ({self.resource_name}.{self.action_name})"
    
    @classmethod
    def get_default_permissions(cls):
        """Return list of default permissions to seed."""
        return [
            {'permission_code': 'POLICY_CREATE', 'permission_description': 'Create new policy', 'resource_name': 'POLICY', 'action_name': 'CREATE'},
            {'permission_code': 'POLICY_VIEW', 'permission_description': 'View policy details', 'resource_name': 'POLICY', 'action_name': 'READ'},
            {'permission_code': 'POLICY_EDIT', 'permission_description': 'Edit policy', 'resource_name': 'POLICY', 'action_name': 'UPDATE'},
            {'permission_code': 'CLAIM_SUBMIT', 'permission_description': 'Submit claim', 'resource_name': 'CLAIM', 'action_name': 'CREATE'},
            {'permission_code': 'CLAIM_REVIEW', 'permission_description': 'Review and approve/reject claims', 'resource_name': 'CLAIM', 'action_name': 'UPDATE'},
            {'permission_code': 'USER_MANAGE', 'permission_description': 'Manage users and roles', 'resource_name': 'USER', 'action_name': 'MANAGE'},
            {'permission_code': 'REPORT_VIEW', 'permission_description': 'Access analytics reports', 'resource_name': 'REPORT', 'action_name': 'READ'},
            {'permission_code': 'AUDIT_VIEW', 'permission_description': 'View audit logs', 'resource_name': 'AUDIT', 'action_name': 'READ'},
        ]


class RolePermission(models.Model):
    """
    Junction table for many-to-many relationship between Role and Permission.
    
    Note: Current MVP uses role-based access only.
    This table is included for future extensibility.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.role.role_name} - {self.permission.permission_code}"


class AuditLog(models.Model):
    """
    Immutable audit trail for all critical operations.
    
    Tracks:
    - User actions (INSERT, UPDATE, DELETE, LOGIN, LOGOUT)
    - Permission denials
    - IP addresses and timestamps
    """
    ACTION_CHOICES = [
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PERMISSION_DENIED', 'Permission Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    user_role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)
    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.IntegerField(null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['table_name', 'record_id']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action_type} on {self.table_name} by {self.user} at {self.timestamp}"
