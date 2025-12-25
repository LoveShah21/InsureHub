"""
URL configuration for customers app.
"""

from django.urls import path

from .views import CustomerProfileView, CustomerListView, CustomerDetailView

urlpatterns = [
    path('profile/', CustomerProfileView.as_view(), name='customer_profile'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
]
