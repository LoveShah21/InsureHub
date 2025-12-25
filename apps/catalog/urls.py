"""
URL configuration for catalog app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InsuranceTypeViewSet,
    InsuranceCompanyViewSet,
    CoverageTypeViewSet,
    RiderAddonViewSet,
)

router = DefaultRouter()
router.register(r'insurance-types', InsuranceTypeViewSet, basename='insurance-type')
router.register(r'companies', InsuranceCompanyViewSet, basename='company')
router.register(r'coverages', CoverageTypeViewSet, basename='coverage')
router.register(r'addons', RiderAddonViewSet, basename='addon')

urlpatterns = [
    path('', include(router.urls)),
]
