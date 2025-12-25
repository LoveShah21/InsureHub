"""
URL configuration for insurance_project.

API endpoints are versioned under /api/v1/
Frontend routes use Django Templates with session auth.

NOTE: Django Admin is NOT used in this project.
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request):
    """API root endpoint with welcome message and available endpoints."""
    return Response({
        'message': 'Insurance Policy Management & Decision Support System API',
        'version': 'v1',
        'endpoints': {
            'auth': {
                'register': '/api/v1/auth/register/',
                'login': '/api/v1/auth/login/',
                'logout': '/api/v1/auth/logout/',
                'refresh': '/api/v1/auth/refresh/',
                'change_password': '/api/v1/auth/change-password/',
            },
            'users': {
                'me': '/api/v1/users/me/',
                'list': '/api/v1/users/',
            },
            'roles': '/api/v1/roles/',
            'catalog': {
                'insurance_types': '/api/v1/insurance-types/',
                'companies': '/api/v1/companies/',
                'coverages': '/api/v1/coverages/',
                'addons': '/api/v1/addons/',
            },
            'customers': '/api/v1/profile/',
            'applications': '/api/v1/applications/',
            'quotes': '/api/v1/quotes/',
            'policies': '/api/v1/policies/',
            'payments': '/api/v1/payments/',
            'claims': '/api/v1/claims/',
            'analytics': '/api/v1/analytics/dashboard/',
        }
    })


urlpatterns = [
    # API root
    path('api/v1/', api_root, name='api_root'),
    
    # REST API endpoints
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.catalog.urls')),
    path('api/v1/', include('apps.customers.urls')),
    path('api/v1/', include('apps.applications.urls')),
    path('api/v1/', include('apps.quotes.urls')),
    path('api/v1/', include('apps.policies.urls')),
    path('api/v1/', include('apps.claims.urls')),
    path('api/v1/', include('apps.notifications.urls')),
    path('api/v1/', include('apps.analytics.urls')),
    
    # Frontend Template Routes
    path('', include('apps.frontend.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
