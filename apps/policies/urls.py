"""
URL configuration for policies app.

Includes:
- Policy CRUD
- Razorpay payment endpoints (create-order, verify)
- Invoice viewing
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PolicyViewSet,
    PaymentViewSet,
    InvoiceViewSet,
    create_razorpay_order,
    verify_razorpay_payment,
)

router = DefaultRouter()
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    # Razorpay payment endpoints (MUST be BEFORE router URLs to take precedence)
    path('payments/create-order/', create_razorpay_order, name='create_razorpay_order'),
    path('payments/verify/', verify_razorpay_payment, name='verify_razorpay_payment'),
    
    # Router URLs (policies, payments list, invoices)
    path('', include(router.urls)),
]
