"""
Serializers for Notifications module.
"""

from rest_framework import serializers
from .models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'channel', 'title', 'message',
            'related_entity_type', 'related_entity_id',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'is_read', 'created_at'
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_code', 'notification_type',
            'subject_template', 'body_template', 'is_active',
            'created_at', 'updated_at'
        ]
