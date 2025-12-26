"""
Views for Identity & Access Control (IAM) module.

Provides API endpoints for:
- User registration (public)
- Login with JWT tokens (public)
- User profile management (authenticated)
- Role management (admin only)
"""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, Role, UserRole
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    RoleSerializer,
    UserRoleSerializer,
    UserListSerializer,
)
from .permissions import IsAdmin, IsAdminOrBackoffice


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    POST /api/v1/auth/register/
    
    Creates a new user account and assigns the Customer role.
    Returns the user data and JWT tokens.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    API endpoint for user login.
    
    POST /api/v1/auth/login/
    
    Validates credentials and returns JWT tokens.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/v1/auth/logout/
    
    Blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current user's profile.
    
    GET /api/v1/users/me/
    PUT/PATCH /api/v1/users/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer


class PasswordChangeView(APIView):
    """
    API endpoint for changing password.
    
    POST /api/v1/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing users (Admin only).
    
    GET /api/v1/users/           - List all users
    GET /api/v1/users/{id}/      - Retrieve user details
    
    Search params: ?q= (email, name), ?role=, ?is_active=
    """
    queryset = User.objects.prefetch_related('user_roles__role').all()
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(user_roles__role__role_name__iexact=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)
        
        return queryset.distinct()
    
    @action(detail=True, methods=['post'], url_path='assign-role')
    def assign_role(self, request, pk=None):
        """Assign a role to a user."""
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response({
                'error': 'role_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({
                'error': 'Role not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={'assigned_by': request.user}
        )
        
        if created:
            return Response({
                'message': f'Role {role.role_name} assigned to {user.email}.'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': f'User already has role {role.role_name}.'
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='remove-role')
    def remove_role(self, request, pk=None):
        """Remove a role from a user."""
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response({
                'error': 'role_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_role = UserRole.objects.get(user=user, role_id=role_id)
            role_name = user_role.role.role_name
            user_role.delete()
            return Response({
                'message': f'Role {role_name} removed from {user.email}.'
            }, status=status.HTTP_200_OK)
        except UserRole.DoesNotExist:
            return Response({
                'error': 'User does not have this role.'
            }, status=status.HTTP_404_NOT_FOUND)


class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for role management (Admin only).
    
    GET /api/v1/roles/           - List all roles
    POST /api/v1/roles/          - Create role
    GET /api/v1/roles/{id}/      - Retrieve role
    PUT/PATCH /api/v1/roles/{id}/ - Update role
    DELETE /api/v1/roles/{id}/   - Delete role (non-system only)
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system_role:
            return Response({
                'error': 'System roles cannot be deleted.'
            }, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)
