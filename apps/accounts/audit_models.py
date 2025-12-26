"""
Data Modification History Model

This module contains the DataModificationHistory model for tracking
field-level changes to critical data.

Note: AuditLog is defined in accounts/models.py (existing table).
This file provides supplementary data tracking.
"""

from django.db import models
from django.conf import settings


class DataModificationHistory(models.Model):
    """
    Change tracking for critical tables.
    
    Stores before/after values for important data changes.
    """
    # User who made the change
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='data_modifications'
    )
    
    # Target entity
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    
    # Change details
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # Modification type
    modification_type = models.CharField(
        max_length=20,
        choices=[
            ('INSERT', 'Insert'),
            ('UPDATE', 'Update'),
            ('DELETE', 'Delete'),
        ],
        db_index=True
    )
    
    # Reason (optional)
    modification_reason = models.TextField(blank=True)
    
    # Timestamp
    modified_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'data_modification_history'
        ordering = ['-modified_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id', 'modified_at']),
        ]
    
    def __str__(self):
        return f"{self.entity_type}.{self.field_name}: {self.old_value} → {self.new_value}"
    
    @classmethod
    def track_changes(cls, user, entity, old_data, new_data, reason=''):
        """
        Track field-level changes between old and new data.
        
        Args:
            user: User making the change
            entity: Model instance being modified
            old_data: Dict of old field values
            new_data: Dict of new field values
            reason: Optional reason for the change
        
        Returns:
            List of created DataModificationHistory records
        """
        entity_type = entity.__class__.__name__
        entity_id = str(entity.pk)
        records = []
        
        for field_name in new_data:
            old_val = str(old_data.get(field_name, ''))
            new_val = str(new_data.get(field_name, ''))
            
            if old_val != new_val:
                record = cls.objects.create(
                    modified_by=user,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    old_value=old_val[:500],
                    new_value=new_val[:500],
                    modification_type='UPDATE',
                    modification_reason=reason
                )
                records.append(record)
        
        return records
