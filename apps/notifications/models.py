"""
Notification Models

This module contains models for user notifications:
- Notification: User notification records
- NotificationTemplate: Email/notification templates (conceptual)

Notifications are triggered by:
- Policy issuance
- Claim status changes
- Policy expiry reminders
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    User notification record.
    
    Stores notifications for:
    - Policy events (issued, expiring)
    - Claim events (submitted, approved, rejected, settled)
    - Application events (approved, rejected)
    - Payment events (success, failed)
    """
    TYPE_CHOICES = [
        ('POLICY_ISSUED', 'Policy Issued'),
        ('POLICY_EXPIRING', 'Policy Expiring Soon'),
        ('POLICY_EXPIRED', 'Policy Expired'),
        ('CLAIM_SUBMITTED', 'Claim Submitted'),
        ('CLAIM_UPDATED', 'Claim Status Updated'),
        ('CLAIM_APPROVED', 'Claim Approved'),
        ('CLAIM_REJECTED', 'Claim Rejected'),
        ('CLAIM_SETTLED', 'Claim Settled'),
        ('APPLICATION_SUBMITTED', 'Application Submitted'),
        ('APPLICATION_APPROVED', 'Application Approved'),
        ('APPLICATION_REJECTED', 'Application Rejected'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('QUOTE_GENERATED', 'Quote Generated'),
        ('RENEWAL_REMINDER', 'Renewal Reminder'),
        ('GENERAL', 'General Notification'),
    ]
    
    CHANNEL_CHOICES = [
        ('IN_APP', 'In-App'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, db_index=True
    )
    channel = models.CharField(
        max_length=10, choices=CHANNEL_CHOICES, default='IN_APP'
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Reference to related entity
    related_entity_type = models.CharField(
        max_length=50, blank=True,
        help_text="E.g., 'policy', 'claim', 'application'"
    )
    related_entity_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Email status
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationTemplate(models.Model):
    """
    Email/notification templates.
    
    Templates use placeholders like {policy_number}, {customer_name}, etc.
    This is conceptual - in production, use a proper template engine.
    """
    template_code = models.CharField(max_length=50, unique=True, db_index=True)
    notification_type = models.CharField(max_length=30)
    
    # Template content
    subject_template = models.CharField(max_length=255)
    body_template = models.TextField()
    html_template = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
    
    def __str__(self):
        return f"{self.template_code} ({self.notification_type})"
    
    def render(self, context: dict) -> dict:
        """
        Render template with context variables.
        
        Args:
            context: Dictionary of placeholder values
        
        Returns:
            dict: Rendered subject and body
        """
        subject = self.subject_template
        body = self.body_template
        
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'body': body
        }
    
    @classmethod
    def get_default_templates(cls):
        """Return default notification templates for seeding."""
        return [
            {
                'template_code': 'POLICY_ISSUED',
                'notification_type': 'POLICY_ISSUED',
                'subject_template': 'Your Policy {policy_number} Has Been Issued',
                'body_template': 'Dear {customer_name},\n\nYour insurance policy {policy_number} has been successfully issued.\n\nPolicy Details:\n- Insurance Type: {insurance_type}\n- Start Date: {start_date}\n- End Date: {end_date}\n- Sum Insured: ₹{sum_insured}\n\nThank you for choosing our services.'
            },
            {
                'template_code': 'CLAIM_APPROVED',
                'notification_type': 'CLAIM_APPROVED',
                'subject_template': 'Your Claim {claim_number} Has Been Approved',
                'body_template': 'Dear {customer_name},\n\nYour claim {claim_number} has been approved.\n\nApproved Amount: ₹{approved_amount}\n\nThe amount will be settled shortly.\n\nThank you.'
            },
            {
                'template_code': 'CLAIM_REJECTED',
                'notification_type': 'CLAIM_REJECTED',
                'subject_template': 'Update on Your Claim {claim_number}',
                'body_template': 'Dear {customer_name},\n\nWe regret to inform you that your claim {claim_number} has been rejected.\n\nReason: {rejection_reason}\n\nIf you have questions, please contact our support team.'
            },
            {
                'template_code': 'POLICY_EXPIRING',
                'notification_type': 'POLICY_EXPIRING',
                'subject_template': 'Your Policy {policy_number} is Expiring Soon',
                'body_template': 'Dear {customer_name},\n\nYour policy {policy_number} will expire on {expiry_date}.\n\nPlease renew your policy to continue enjoying coverage.\n\nThank you for being a valued customer.'
            }
        ]


class ScheduledReminder(models.Model):
    """
    Scheduled reminders for automated notifications.
    
    Used for:
    - Policy expiry reminders
    - Renewal reminders
    - Payment due reminders
    """
    REMINDER_TYPE_CHOICES = [
        ('POLICY_EXPIRY', 'Policy Expiry'),
        ('RENEWAL_DUE', 'Renewal Due'),
        ('PAYMENT_DUE', 'Payment Due'),
        ('DOCUMENT_EXPIRY', 'Document Expiry'),
        ('CUSTOM', 'Custom Reminder'),
    ]
    
    REMINDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    reminder_type = models.CharField(
        max_length=20, choices=REMINDER_TYPE_CHOICES, db_index=True
    )
    
    # Related entity
    related_entity_type = models.CharField(
        max_length=50,
        help_text="E.g., 'policy', 'payment'"
    )
    related_entity_id = models.PositiveIntegerField()
    
    # Template
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.RESTRICT,
        related_name='scheduled_reminders'
    )
    
    # Recipient
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='scheduled_reminders'
    )
    
    # Schedule
    reminder_scheduled_for = models.DateTimeField(db_index=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_status = models.CharField(
        max_length=20, choices=REMINDER_STATUS_CHOICES, default='PENDING'
    )
    
    # Recurrence (optional)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=100, blank=True,
        help_text="E.g., 'daily', 'weekly', '30_days_before'"
    )
    
    # Failure tracking
    failure_reason = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_reminders'
        ordering = ['reminder_scheduled_for']
        indexes = [
            models.Index(fields=['reminder_status', 'reminder_scheduled_for']),
            models.Index(fields=['related_entity_type', 'related_entity_id']),
        ]
    
    def __str__(self):
        return f"{self.reminder_type}: {self.reminder_scheduled_for}"
    
    def mark_sent(self):
        """Mark reminder as sent."""
        self.reminder_status = 'SENT'
        self.reminder_sent_at = timezone.now()
        self.save(update_fields=['reminder_status', 'reminder_sent_at'])
    
    def mark_failed(self, reason):
        """Mark reminder as failed."""
        self.reminder_status = 'FAILED'
        self.failure_reason = reason
        self.retry_count += 1
        self.save(update_fields=['reminder_status', 'failure_reason', 'retry_count'])
    
    def cancel(self):
        """Cancel the reminder."""
        if self.reminder_status == 'PENDING':
            self.reminder_status = 'CANCELLED'
            self.save(update_fields=['reminder_status'])
