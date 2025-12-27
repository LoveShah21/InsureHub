"""
Email Service for InsureHub

Provides email notification functions for:
- Quote generation and sending
- Policy issuance
- Claim status updates
- Application status updates
- Payment confirmations

Uses Gmail SMTP configured in settings.py
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(subject, template_name, context, recipient_email, plain_message=None):
    """
    Core email sending function.
    
    Args:
        subject: Email subject line
        template_name: Path to HTML template (relative to templates/emails/)
        context: Context dict for template rendering
        recipient_email: Recipient email address
        plain_message: Optional plain text fallback
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Check if email is configured
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Skipping email send.")
            return False
        
        # Render HTML template
        html_message = render_to_string(f'emails/{template_name}', context)
        
        # Create plain text version if not provided
        if not plain_message:
            plain_message = strip_tags(html_message)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=settings.EMAIL_FAIL_SILENTLY)
        
        logger.info(f"Email sent successfully to {recipient_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        if not settings.EMAIL_FAIL_SILENTLY:
            raise
        return False


def send_quote_generated_email(quote):
    """
    Notify customer when quotes are generated for their application.
    
    Args:
        quote: Quote model instance (first quote of the batch)
    """
    customer = quote.customer
    user = customer.user
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'application_number': quote.application.application_number,
        'insurance_type': quote.insurance_type.type_name,
        'quote_count': quote.application.quotes.count(),
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Quotes Ready for Your Application {quote.application.application_number}",
        template_name='quote_generated.html',
        context=context,
        recipient_email=user.email
    )


def send_quote_sent_email(quote):
    """
    Notify customer when a specific quote is sent to them for review.
    
    Args:
        quote: Quote model instance
    """
    customer = quote.customer
    user = customer.user
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'quote_number': quote.quote_number,
        'company_name': quote.insurance_company.company_name,
        'insurance_type': quote.insurance_type.type_name,
        'sum_insured': f"₹{quote.sum_insured:,.0f}",
        'total_premium': f"₹{quote.total_premium_with_gst:,.0f}",
        'validity_date': quote.expiry_at.strftime('%B %d, %Y'),
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Quote {quote.quote_number} - Review Your Insurance Offer",
        template_name='quote_sent.html',
        context=context,
        recipient_email=user.email
    )


def send_policy_issued_email(policy):
    """
    Notify customer when their policy is issued successfully.
    
    Args:
        policy: Policy model instance
    """
    customer = policy.customer
    user = customer.user
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'policy_number': policy.policy_number,
        'company_name': policy.insurance_company.company_name,
        'insurance_type': policy.insurance_type.type_name,
        'sum_insured': f"₹{policy.sum_insured:,.0f}",
        'total_premium': f"₹{policy.total_premium_with_gst:,.0f}",
        'start_date': policy.start_date.strftime('%B %d, %Y'),
        'end_date': policy.end_date.strftime('%B %d, %Y'),
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Policy Issued! Your Policy Number: {policy.policy_number}",
        template_name='policy_issued.html',
        context=context,
        recipient_email=user.email
    )


def send_payment_success_email(payment, policy=None):
    """
    Notify customer of successful payment.
    
    Args:
        payment: Payment model instance
        policy: Optional Policy model instance if policy was created
    """
    user = payment.customer.user
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'payment_id': payment.razorpay_payment_id or payment.id,
        'amount': f"₹{payment.amount:,.0f}",
        'payment_date': payment.payment_date.strftime('%B %d, %Y at %I:%M %p') if payment.payment_date else 'Just now',
        'policy_number': policy.policy_number if policy else None,
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Payment Successful - ₹{payment.amount:,.0f}",
        template_name='payment_success.html',
        context=context,
        recipient_email=user.email
    )


def send_claim_status_email(claim, old_status=None):
    """
    Notify customer when their claim status changes.
    
    Args:
        claim: Claim model instance
        old_status: Previous status (optional)
    """
    customer = claim.customer
    user = customer.user
    
    status_messages = {
        'SUBMITTED': 'Your claim has been submitted successfully.',
        'UNDER_REVIEW': 'Your claim is now under review by our team.',
        'APPROVED': f'Great news! Your claim has been approved for ₹{claim.amount_approved:,.0f}.',
        'REJECTED': 'We regret to inform you that your claim has been rejected.',
        'SETTLED': f'Your claim has been settled. Amount of ₹{claim.amount_settled:,.0f} will be credited to your account.',
        'CLOSED': 'Your claim has been closed.',
    }
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'claim_number': claim.claim_number,
        'policy_number': claim.policy.policy_number,
        'status': claim.status,
        'status_message': status_messages.get(claim.status, f'Your claim status is now: {claim.status}'),
        'amount_requested': f"₹{claim.amount_requested:,.0f}",
        'amount_approved': f"₹{claim.amount_approved:,.0f}" if claim.amount_approved else None,
        'rejection_reason': claim.rejection_reason if claim.status == 'REJECTED' else None,
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Claim {claim.claim_number} - Status Update: {claim.status}",
        template_name='claim_status.html',
        context=context,
        recipient_email=user.email
    )


def send_application_status_email(application, old_status=None):
    """
    Notify customer when their application status changes.
    
    Args:
        application: InsuranceApplication model instance
        old_status: Previous status (optional)
    """
    customer = application.customer
    user = customer.user
    
    status_messages = {
        'SUBMITTED': 'Your application has been submitted successfully and is pending review.',
        'UNDER_REVIEW': 'Your application is now being reviewed by our team.',
        'APPROVED': 'Congratulations! Your application has been approved. You can now view and compare quotes.',
        'REJECTED': 'We regret to inform you that your application has been rejected.',
    }
    
    context = {
        'customer_name': user.get_full_name() or user.email,
        'application_number': application.application_number,
        'insurance_type': application.insurance_type.type_name,
        'status': application.status,
        'status_message': status_messages.get(application.status, f'Your application status is now: {application.status}'),
        'rejection_reason': application.rejection_reason if application.status == 'REJECTED' else None,
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject=f"Application {application.application_number} - Status: {application.status}",
        template_name='application_status.html',
        context=context,
        recipient_email=user.email
    )


def send_welcome_email(user):
    """
    Send welcome email to newly registered users.
    
    Args:
        user: User model instance
    """
    context = {
        'customer_name': user.get_full_name() or user.email,
        'email': user.email,
        'login_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    return send_email(
        subject="Welcome to InsureHub - Your Insurance Journey Starts Here!",
        template_name='welcome.html',
        context=context,
        recipient_email=user.email
    )
