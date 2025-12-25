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
    path('', include(router.urls)),
    
    # Razorpay payment endpoints
    path('payments/create-order/', create_razorpay_order, name='create_razorpay_order'),
    path('payments/verify/', verify_razorpay_payment, name='verify_razorpay_payment'),
]
