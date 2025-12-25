"""
URL configuration for analytics app.
"""

from django.urls import path

from .views import DashboardView, ApplicationMetricsView, ClaimMetricsView

urlpatterns = [
    path('analytics/dashboard/', DashboardView.as_view(), name='analytics_dashboard'),
    path('analytics/applications/', ApplicationMetricsView.as_view(), name='analytics_applications'),
    path('analytics/claims/', ClaimMetricsView.as_view(), name='analytics_claims'),
]
