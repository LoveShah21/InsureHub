"""
URL configuration for applications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InsuranceApplicationViewSet, ApplicationDocumentVerifyView

router = DefaultRouter()
router.register(r'applications', InsuranceApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'applications/<int:application_id>/documents/<int:document_id>/verify/',
        ApplicationDocumentVerifyView.as_view(),
        name='document_verify'
    ),
]
