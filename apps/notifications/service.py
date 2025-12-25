"""
Notification Service

Provides functions to create and send notifications.
In production, this would integrate with:
- Email service (SendGrid, AWS SES)
- SMS gateway
- Push notification service

For this academic project, notifications are logged to console.
"""

import logging
from django.utils import timezone
from django.conf import settings

from .models import Notification, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for creating and sending notifications.
    
    Usage:
        from apps.notifications.service import notification_service
        
        notification_service.notify_policy_issued(policy)
        notification_service.notify_claim_status_change(claim)
    """
    
    def create_notification(
        self,
        user,
        notification_type: str,
        title: str,
        message: str,
        related_entity_type: str = '',
        related_entity_id: int = None,
        channel: str = 'IN_APP',
        send_email: bool = True
    ) -> Notification:
        """
        Create a notification for a user.
        
        Args:
            user: User instance
            notification_type: Type of notification
            title: Notification title
            message: Notification message body
            related_entity_type: Type of related entity (e.g., 'policy')
            related_entity_id: ID of related entity
            channel: Notification channel
            send_email: Whether to send email
        
        Returns:
            Notification instance
        """
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            channel=channel
        )
        
        # Log notification (console output for academic demo)
        logger.info(
            f"[NOTIFICATION] To: {user.email} | Type: {notification_type} | "
            f"Title: {title}"
        )
        
        # Send email (mock - just log for now)
        if send_email and channel in ['EMAIL', 'IN_APP']:
            self._send_email_notification(notification)
        
        return notification
    
    def _send_email_notification(self, notification: Notification):
        """
        Send email notification (mock implementation).
        
        In production, this would use Django's email backend
        or a third-party service.
        """
        try:
            # Mock email sending - just log
            logger.info(
                f"[EMAIL] Sending to: {notification.user.email}\n"
                f"  Subject: {notification.title}\n"
                f"  Body: {notification.message[:100]}..."
            )
            
            # Mark as sent
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
            
            return True
        except Exception as e:
            logger.error(f"[EMAIL ERROR] {str(e)}")
            notification.email_error = str(e)
            notification.save(update_fields=['email_error'])
            return False
    
    # ========== Policy Events ==========
    
    def notify_policy_issued(self, policy):
        """Send notification when policy is issued."""
        user = policy.customer.user
        
        message = (
            f"Your insurance policy {policy.policy_number} has been issued.\n\n"
            f"Policy Details:\n"
            f"- Type: {policy.insurance_type.type_name}\n"
            f"- Company: {policy.insurance_company.company_name}\n"
            f"- Start Date: {policy.policy_start_date}\n"
            f"- End Date: {policy.policy_end_date}\n"
            f"- Sum Insured: ₹{policy.sum_insured:,.2f}"
        )
        
        return self.create_notification(
            user=user,
            notification_type='POLICY_ISSUED',
            title=f'Policy {policy.policy_number} Issued',
            message=message,
            related_entity_type='policy',
            related_entity_id=policy.id
        )
    
    def notify_policy_expiring(self, policy, days_until_expiry: int):
        """Send reminder for expiring policy."""
        user = policy.customer.user
        
        message = (
            f"Your policy {policy.policy_number} will expire on "
            f"{policy.policy_end_date}.\n\n"
            f"Days remaining: {days_until_expiry}\n\n"
            f"Please renew your policy to continue coverage."
        )
        
        return self.create_notification(
            user=user,
            notification_type='POLICY_EXPIRING',
            title=f'Policy Expiring in {days_until_expiry} Days',
            message=message,
            related_entity_type='policy',
            related_entity_id=policy.id
        )
    
    # ========== Claim Events ==========
    
    def notify_claim_submitted(self, claim):
        """Send notification when claim is submitted."""
        user = claim.customer.user
        
        message = (
            f"Your claim {claim.claim_number} has been submitted.\n\n"
            f"Claim Amount: ₹{claim.amount_requested:,.2f}\n"
            f"Status: Submitted\n\n"
            f"Our team will review your claim shortly."
        )
        
        return self.create_notification(
            user=user,
            notification_type='CLAIM_SUBMITTED',
            title=f'Claim {claim.claim_number} Submitted',
            message=message,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    def notify_claim_approved(self, claim):
        """Send notification when claim is approved."""
        user = claim.customer.user
        
        message = (
            f"Great news! Your claim {claim.claim_number} has been approved.\n\n"
            f"Requested Amount: ₹{claim.amount_requested:,.2f}\n"
            f"Approved Amount: ₹{claim.amount_approved:,.2f}\n\n"
            f"The approved amount will be settled shortly."
        )
        
        return self.create_notification(
            user=user,
            notification_type='CLAIM_APPROVED',
            title=f'Claim {claim.claim_number} Approved',
            message=message,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    def notify_claim_rejected(self, claim):
        """Send notification when claim is rejected."""
        user = claim.customer.user
        
        message = (
            f"We regret to inform you that your claim {claim.claim_number} "
            f"has been rejected.\n\n"
            f"Reason: {claim.rejection_reason}\n\n"
            f"If you have questions, please contact our support team."
        )
        
        return self.create_notification(
            user=user,
            notification_type='CLAIM_REJECTED',
            title=f'Claim {claim.claim_number} Rejected',
            message=message,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    def notify_claim_settled(self, claim):
        """Send notification when claim is settled."""
        user = claim.customer.user
        
        message = (
            f"Your claim {claim.claim_number} has been settled.\n\n"
            f"Settled Amount: ₹{claim.amount_settled:,.2f}\n\n"
            f"Thank you for your patience."
        )
        
        return self.create_notification(
            user=user,
            notification_type='CLAIM_SETTLED',
            title=f'Claim {claim.claim_number} Settled',
            message=message,
            related_entity_type='claim',
            related_entity_id=claim.id
        )
    
    # ========== Application Events ==========
    
    def notify_application_approved(self, application):
        """Send notification when application is approved."""
        user = application.customer.user
        
        message = (
            f"Your application {application.application_number} has been approved!\n\n"
            f"You can now generate quotes and proceed with policy issuance."
        )
        
        return self.create_notification(
            user=user,
            notification_type='APPLICATION_APPROVED',
            title=f'Application {application.application_number} Approved',
            message=message,
            related_entity_type='application',
            related_entity_id=application.id
        )
    
    def notify_application_rejected(self, application):
        """Send notification when application is rejected."""
        user = application.customer.user
        
        message = (
            f"Your application {application.application_number} has been rejected.\n\n"
            f"Reason: {application.rejection_reason}\n\n"
            f"You may submit a new application with the required corrections."
        )
        
        return self.create_notification(
            user=user,
            notification_type='APPLICATION_REJECTED',
            title=f'Application {application.application_number} Rejected',
            message=message,
            related_entity_type='application',
            related_entity_id=application.id
        )
    
    # ========== Payment Events ==========
    
    def notify_payment_success(self, payment):
        """Send notification on successful payment."""
        user = payment.customer.user
        
        message = (
            f"Payment of ₹{payment.payment_amount:,.2f} was successful.\n\n"
            f"Transaction ID: {payment.transaction_id}\n"
            f"Payment Reference: {payment.payment_number}"
        )
        
        return self.create_notification(
            user=user,
            notification_type='PAYMENT_SUCCESS',
            title='Payment Successful',
            message=message,
            related_entity_type='payment',
            related_entity_id=payment.id
        )
    
    def notify_payment_failed(self, payment):
        """Send notification on failed payment."""
        user = payment.customer.user
        
        message = (
            f"Payment of ₹{payment.payment_amount:,.2f} failed.\n\n"
            f"Reason: {payment.failed_reason}\n\n"
            f"Please try again or use a different payment method."
        )
        
        return self.create_notification(
            user=user,
            notification_type='PAYMENT_FAILED',
            title='Payment Failed',
            message=message,
            related_entity_type='payment',
            related_entity_id=payment.id
        )


# Singleton instance
notification_service = NotificationService()
