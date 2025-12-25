"""
Razorpay Payment Gateway Integration

This module provides real Razorpay Sandbox integration for payments.
NOT a mock - uses actual Razorpay test credentials.

Features:
- Order creation
- Signature verification (HMAC-SHA256)
- Idempotent payment verification

Security:
- Keys loaded from environment variables
- Signature verification prevents tampering
"""

import razorpay
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)


class RazorpayGateway:
    """
    Razorpay Sandbox Payment Gateway.
    
    Usage:
        from apps.policies.payment_gateway import razorpay_gateway
        
        # Create order
        order = razorpay_gateway.create_order(amount=15000, receipt_id='QT-123')
        
        # Verify payment
        is_valid = razorpay_gateway.verify_payment(
            order_id='order_xxx',
            payment_id='pay_xxx',
            signature='xxx'
        )
    """
    
    def __init__(self):
        """Initialize Razorpay client with test credentials."""
        self.key_id = config('RAZORPAY_KEY_ID', default='')
        self.key_secret = config('RAZORPAY_KEY_SECRET', default='')
        
        if not self.key_id or not self.key_secret:
            logger.warning("Razorpay credentials not configured!")
        
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    def create_order(self, amount: float, receipt_id: str, currency: str = 'INR') -> dict:
        """
        Create a Razorpay order.
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            receipt_id: Unique receipt/reference ID (e.g., quote number)
            currency: Currency code (default: INR)
        
        Returns:
            dict: Razorpay order object with 'id', 'amount', 'currency', etc.
        
        Raises:
            razorpay.errors.BadRequestError: If order creation fails
        """
        try:
            order_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': currency,
                'receipt': receipt_id,
                'payment_capture': 1  # Auto-capture payment
            }
            
            order = self.client.order.create(data=order_data)
            
            logger.info(
                f"[RAZORPAY] Order created: {order['id']} | "
                f"Amount: ₹{amount} | Receipt: {receipt_id}"
            )
            
            return order
        
        except razorpay.errors.BadRequestError as e:
            logger.error(f"[RAZORPAY] Order creation failed: {str(e)}")
            raise
    
    def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify Razorpay payment signature.
        
        This is CRITICAL for security - ensures the payment callback
        is genuinely from Razorpay and not tampered with.
        
        Args:
            order_id: Razorpay order ID (order_xxx)
            payment_id: Razorpay payment ID (pay_xxx)
            signature: Razorpay signature
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            params = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params)
            
            logger.info(
                f"[RAZORPAY] Payment verified: {payment_id} | Order: {order_id}"
            )
            
            return True
        
        except razorpay.errors.SignatureVerificationError:
            logger.warning(
                f"[RAZORPAY] Signature verification FAILED: {payment_id}"
            )
            return False
    
    def fetch_payment(self, payment_id: str) -> dict:
        """
        Fetch payment details from Razorpay.
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            dict: Payment details
        """
        try:
            return self.client.payment.fetch(payment_id)
        except Exception as e:
            logger.error(f"[RAZORPAY] Fetch payment failed: {str(e)}")
            raise
    
    def fetch_order(self, order_id: str) -> dict:
        """
        Fetch order details from Razorpay.
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            dict: Order details
        """
        try:
            return self.client.order.fetch(order_id)
        except Exception as e:
            logger.error(f"[RAZORPAY] Fetch order failed: {str(e)}")
            raise
    
    def get_key_id(self) -> str:
        """
        Get the Razorpay Key ID (for frontend).
        
        This is safe to expose to frontend - it's the public key.
        """
        return self.key_id


# Singleton instance
razorpay_gateway = RazorpayGateway()
