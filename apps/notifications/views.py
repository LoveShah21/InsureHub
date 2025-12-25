"""
Views for Notifications module.

Provides API endpoints for:
- Listing user notifications
- Marking notifications as read
- Notification preferences (future)
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count

from .models import Notification
from .serializers import NotificationSerializer, NotificationListSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user notifications.
    
    GET /api/v1/notifications/           - List user's notifications
    GET /api/v1/notifications/{id}/      - Get notification details
    GET /api/v1/notifications/unread/    - Get unread count
    POST /api/v1/notifications/{id}/read/ - Mark as read
    POST /api/v1/notifications/read-all/ - Mark all as read
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notification count."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'message': 'Notification marked as read.',
            'notification': NotificationSerializer(notification).data
        })
    
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """Mark all notifications as read."""
        from django.utils import timezone
        
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated} notifications marked as read.'
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get notification summary by type."""
        queryset = self.get_queryset()
        
        total = queryset.count()
        unread = queryset.filter(is_read=False).count()
        
        by_type = queryset.values('notification_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'unread': unread,
            'by_type': list(by_type)
        })
