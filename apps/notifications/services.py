"""
Notification Service

This module provides business logic for notifications:
- Event-triggered notifications
- Scheduled reminder processing
- Template rendering
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction

from apps.notifications.models import (
    Notification, NotificationTemplate, ScheduledReminder
)
from apps.policies.models import Policy


class NotificationService:
    """
    Service for creating and managing notifications.
    
    Provides:
    - Event-based notification creation
    - Template-based rendering
    - Scheduled reminder management
    """
    
    @classmethod
    def create_notification(
        cls,
        user,
        notification_type: str,
        title: str,
        message: str,
        channel: str = 'IN_APP',
        related_entity_type: str = '',
        related_entity_id: int = None
    ) -> Notification:
        """
        Create a notification for a user.
        """
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            channel=channel,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
    
    @classmethod
    def notify_from_template(
        cls,
        user,
        template_code: str,
        context: dict,
        related_entity_type: str = '',
        related_entity_id: int = None
    ) -> Notification:
        """
        Create notification using a template.
        """
        try:
            template = NotificationTemplate.objects.get(
                template_code=template_code,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            # Fallback to generic notification
            return cls.create_notification(
                user=user,
                notification_type='GENERAL',
                title=f'Notification: {template_code}',
                message=str(context),
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )
        
        rendered = template.render(context)
        
        return cls.create_notification(
            user=user,
            notification_type=template.notification_type,
            title=rendered['subject'],
            message=rendered['body'],
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
    
    # === Event-based notifications ===
    
    @classmethod
    def notify_policy_issued(cls, policy: Policy):
        """Notify customer when policy is issued."""
        user = policy.customer.user
        context = {
            'customer_name': user.get_full_name() or user.email,
            'policy_number': policy.policy_number,
            'insurance_type': policy.quote.application.insurance_type.type_name,
            'start_date': policy.start_date.strftime('%d %b %Y'),
            'end_date': policy.end_date.strftime('%d %b %Y'),
            'sum_insured': str(policy.quote.sum_assured),
        }
        
        return cls.notify_from_template(
            user=user,
            template_code='POLICY_ISSUED',
            context=context,
            related_entity_type='policy',
            related_entity_id=policy.id
        )
    
    @classmethod
    def notify_claim_approved(cls, claim):
        """Notify customer when claim is approved."""
        user = claim.customer.user
        context = {
            'customer_name': user.get_full_name() or user.email,
            'claim_number': claim.claim_number,
            'approved_amount': str(claim.amount_approved),
        }
        
        return cls.notify_from_template(
            user=user,
            template_code='CLAIM_APPROVED',
            context=context,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    @classmethod
    def notify_claim_rejected(cls, claim):
        """Notify customer when claim is rejected."""
        user = claim.customer.user
        context = {
            'customer_name': user.get_full_name() or user.email,
            'claim_number': claim.claim_number,
            'rejection_reason': claim.rejection_reason,
        }
        
        return cls.notify_from_template(
            user=user,
            template_code='CLAIM_REJECTED',
            context=context,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    @classmethod
    def notify_claim_settled(cls, claim):
        """Notify customer when claim is settled."""
        user = claim.customer.user
        
        return cls.create_notification(
            user=user,
            notification_type='CLAIM_SETTLED',
            title=f'Claim {claim.claim_number} Settled',
            message=f'Your claim has been settled. Amount: ₹{claim.amount_settled}',
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    @classmethod
    def notify_application_approved(cls, application):
        """Notify customer when application is approved."""
        user = application.customer.user
        
        return cls.create_notification(
            user=user,
            notification_type='APPLICATION_APPROVED',
            title='Application Approved',
            message=f'Your {application.insurance_type.type_name} application has been approved. Quotes are now available.',
            related_entity_type='application',
            related_entity_id=application.id
        )
    
    @classmethod
    def notify_quote_generated(cls, quote):
        """Notify customer when quotes are generated."""
        user = quote.customer.user
        
        return cls.create_notification(
            user=user,
            notification_type='QUOTE_GENERATED',
            title='New Insurance Quote Available',
            message=f'A new quote is available from {quote.insurance_company.company_name}. Total premium: ₹{quote.total_premium}',
            related_entity_type='quote',
            related_entity_id=quote.id
        )
    
    @classmethod
    def notify_payment_success(cls, payment):
        """Notify customer of successful payment."""
        user = payment.quote.customer.user
        
        return cls.create_notification(
            user=user,
            notification_type='PAYMENT_SUCCESS',
            title='Payment Successful',
            message=f'Payment of ₹{payment.amount} received. Your policy will be issued shortly.',
            related_entity_type='payment',
            related_entity_id=payment.id
        )
    
    @classmethod
    def notify_payment_failed(cls, payment):
        """Notify customer of failed payment."""
        user = payment.quote.customer.user
        
        return cls.create_notification(
            user=user,
            notification_type='PAYMENT_FAILED',
            title='Payment Failed',
            message=f'Your payment of ₹{payment.amount} could not be processed. Please try again.',
            related_entity_type='payment',
            related_entity_id=payment.id
        )
    
    # === Scheduled Reminders ===
    
    @classmethod
    def schedule_policy_expiry_reminder(
        cls,
        policy: Policy,
        days_before: int = 30
    ) -> ScheduledReminder:
        """
        Schedule a policy expiry reminder.
        
        Creates a reminder to be sent N days before expiry.
        """
        try:
            template = NotificationTemplate.objects.get(
                template_code='POLICY_EXPIRING',
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
        
        reminder_date = policy.end_date - timedelta(days=days_before)
        reminder_datetime = datetime.combine(
            reminder_date,
            datetime.min.time()
        ).replace(tzinfo=timezone.get_current_timezone())
        
        # Don't schedule if already past
        if reminder_datetime <= timezone.now():
            return None
        
        return ScheduledReminder.objects.create(
            reminder_type='POLICY_EXPIRY',
            related_entity_type='policy',
            related_entity_id=policy.id,
            template=template,
            recipient_user=policy.customer.user,
            reminder_scheduled_for=reminder_datetime,
            recurrence_pattern=f'{days_before}_days_before'
        )
    
    @classmethod
    def process_due_reminders(cls):
        """
        Process all reminders that are due.
        
        Should be run periodically (e.g., via cron/celery).
        Returns count of processed reminders.
        """
        now = timezone.now()
        due_reminders = ScheduledReminder.objects.filter(
            reminder_status='PENDING',
            reminder_scheduled_for__lte=now
        ).select_related('template', 'recipient_user')
        
        processed = 0
        for reminder in due_reminders:
            try:
                cls._send_reminder(reminder)
                reminder.mark_sent()
                processed += 1
            except Exception as e:
                reminder.mark_failed(str(e))
        
        return processed
    
    @classmethod
    def _send_reminder(cls, reminder: ScheduledReminder):
        """Send a single reminder notification."""
        # Build context based on entity type
        context = {}
        
        if reminder.related_entity_type == 'policy':
            try:
                policy = Policy.objects.get(id=reminder.related_entity_id)
                context = {
                    'customer_name': reminder.recipient_user.get_full_name() or reminder.recipient_user.email,
                    'policy_number': policy.policy_number,
                    'expiry_date': policy.end_date.strftime('%d %b %Y'),
                }
            except Policy.DoesNotExist:
                reminder.cancel()
                return
        
        # Create notification
        cls.notify_from_template(
            user=reminder.recipient_user,
            template_code=reminder.template.template_code,
            context=context,
            related_entity_type=reminder.related_entity_type,
            related_entity_id=reminder.related_entity_id
        )
    
    @classmethod
    def get_unread_count(cls, user) -> int:
        """Get count of unread notifications for user."""
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
    
    @classmethod
    def mark_all_read(cls, user) -> int:
        """Mark all notifications as read for user."""
        count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return count
