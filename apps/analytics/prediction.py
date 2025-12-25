"""
Renewal Prediction Module (Phase 4 - Conceptual)

This module demonstrates the schema and concept for renewal prediction.
In a production system, this would use ML models trained on:
- Customer behavior data
- Payment history
- Policy usage patterns
- Claim frequency

For this academic project, this is a placeholder with dummy logic.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal
import random


class RenewalPrediction(models.Model):
    """
    Renewal prediction for a policy.
    
    Schema for future ML-based prediction system.
    Currently uses dummy prediction logic.
    
    FUTURE SCOPE:
    - Train ML model on historical renewal data
    - Features: customer age, claim count, payment timeliness, policy type
    - Output: probability of renewal (0-1)
    """
    PREDICTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CALCULATED', 'Calculated'),
        ('EXPIRED', 'Expired'),
    ]
    
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.CASCADE,
        related_name='renewal_predictions'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='renewal_predictions'
    )
    
    # Prediction output
    renewal_probability = models.DecimalField(
        max_digits=5, decimal_places=4,
        help_text="Probability of renewal (0.0000 to 1.0000)"
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=4,
        help_text="Model confidence (0.0000 to 1.0000)"
    )
    
    # Feature values used in prediction (for explainability)
    feature_values = models.JSONField(
        default=dict,
        help_text="Feature values used for this prediction"
    )
    
    # Status
    status = models.CharField(
        max_length=20, choices=PREDICTION_STATUS_CHOICES, default='PENDING'
    )
    
    # Timestamps
    predicted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'renewal_predictions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prediction for {self.policy.policy_number}: {self.renewal_probability:.2%}"


def dummy_renewal_prediction(policy) -> dict:
    """
    Dummy prediction function for demonstration.
    
    In production, this would call an ML model.
    
    Args:
        policy: Policy instance
    
    Returns:
        dict: Prediction result with probability and features
    
    FUTURE IMPLEMENTATION:
    - Load trained model
    - Extract features from policy/customer data
    - Run prediction
    - Return probability with confidence interval
    """
    # Dummy feature extraction
    features = {
        'policy_tenure_months': policy.policy_tenure_months,
        'days_until_expiry': policy.days_until_expiry,
        'claim_count': policy.claims.count(),
        'premium_amount': float(policy.premium_amount),
        'is_first_policy': policy.customer.policies.count() == 1,
    }
    
    # Dummy prediction logic (NOT ML-based)
    # Higher renewal probability if:
    # - No claims filed
    # - Reasonable premium
    # - Not first-time customer
    
    base_probability = 0.75
    
    # Adjust based on claim count (more claims = lower renewal)
    if features['claim_count'] > 0:
        base_probability -= 0.1 * features['claim_count']
    
    # Adjust for returning customers
    if not features['is_first_policy']:
        base_probability += 0.1
    
    # Add some randomness for demo
    base_probability += random.uniform(-0.1, 0.1)
    
    # Clamp to valid range
    probability = max(0.1, min(0.95, base_probability))
    
    return {
        'renewal_probability': round(probability, 4),
        'confidence_score': round(random.uniform(0.7, 0.9), 4),
        'features': features,
        'model_version': 'DUMMY_V1',
        'note': 'This is a placeholder prediction for academic demonstration. '
                'Production system would use a trained ML model.'
    }


# Sample output for documentation
SAMPLE_PREDICTION_OUTPUT = {
    'policy_number': 'POL-20251225-ABC12345',
    'customer_email': 'customer@example.com',
    'prediction': {
        'renewal_probability': 0.8234,
        'confidence_score': 0.8567,
        'interpretation': 'High likelihood of renewal',
        'recommended_action': 'Send renewal reminder 30 days before expiry'
    },
    'features_used': {
        'policy_tenure_months': 12,
        'days_until_expiry': 45,
        'claim_count': 0,
        'premium_amount': 15000.00,
        'is_first_policy': False,
        'payment_timeliness_score': 0.95
    },
    'model_info': {
        'model_type': 'Random Forest Classifier',
        'training_date': '2025-01-01',
        'accuracy': 0.87,
        'note': 'CONCEPTUAL - Not implemented in MVP'
    }
}
