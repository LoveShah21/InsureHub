"""
Serializers for Identity & Access Control (IAM) module.

Handles:
- User registration and profile management
- Login/authentication
- Role management
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Role, UserRole, Permission


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates password strength and creates user with hashed password.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Ensure email is unique (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        """Ensure username is unique."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and strength."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })
        
        # Validate password strength using Django validators
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password and assign Customer role."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Assign default Customer role
        customer_role = Role.objects.filter(role_name=Role.ROLE_CUSTOMER).first()
        if customer_role:
            UserRole.objects.create(user=user, role=customer_role)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates credentials and checks account status.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'No account found with this email address.'
            })
        
        # Check if account is locked
        if user.is_account_locked:
            raise serializers.ValidationError({
                'email': 'Account is temporarily locked due to multiple failed login attempts. Please try again later.'
            })
        
        # Check if account is active
        if not user.is_active:
            raise serializers.ValidationError({
                'email': 'This account has been deactivated.'
            })
        
        # Authenticate
        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not authenticated_user:
            # Record failed login attempt
            user.record_failed_login()
            raise serializers.ValidationError({
                'password': 'Invalid password. Please try again.'
            })
        
        # Record successful login
        authenticated_user.record_successful_login()
        
        attrs['user'] = authenticated_user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read/update).
    Excludes sensitive fields.
    """
    roles = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'is_active', 'last_login',
            'date_joined', 'roles'
        ]
        read_only_fields = ['id', 'email', 'is_active', 'last_login', 'date_joined', 'roles']
    
    def get_roles(self, obj):
        """Get user's role names."""
        return list(obj.user_roles.values_list('role__role_name', flat=True))
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (limited fields)."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "New passwords do not match."
            })
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = ['id', 'role_name', 'role_description', 'is_system_role', 'created_at']
        read_only_fields = ['is_system_role', 'created_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole assignment."""
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'user_email', 'assigned_at', 'assigned_by']
        read_only_fields = ['assigned_at', 'assigned_by']


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users (Admin view)."""
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'is_active', 'date_joined', 'last_login', 'roles']
    
    def get_roles(self, obj):
        return list(obj.user_roles.values_list('role__role_name', flat=True))
