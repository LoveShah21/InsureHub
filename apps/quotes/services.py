"""
Quote Calculation Service

This module provides business logic for quote generation:
- Premium calculation using slabs
- Risk adjustment application
- Discount rule evaluation
- Fleet discount calculation
"""

from decimal import Decimal
from datetime import date
from typing import List, Optional, Tuple
from django.db.models import Q

from apps.catalog.models import (
    InsuranceType, InsuranceCompany, CoverageType, RiderAddon,
    PremiumSlab, DiscountRule, QuoteCalculationWeight
)
from apps.customers.models import CustomerProfile, CustomerRiskProfile
from apps.applications.models import InsuranceApplication


class QuoteCalculationService:
    """
    Service for calculating insurance quotes.
    
    Implements configuration-driven premium calculation with:
    - Base premium from slabs
    - Coverage and addon additions
    - Risk adjustments from customer profile
    - Discount rules evaluation
    """
    
    def __init__(self, application: InsuranceApplication):
        self.application = application
        self.customer = application.customer
        self.insurance_type = application.insurance_type
        self.sum_assured = application.sum_assured
    
    def calculate_base_premium(self) -> Decimal:
        """
        Calculate base premium using premium slabs.
        
        Finds the matching slab for the coverage amount and applies
        base premium + percentage markup.
        """
        slab = PremiumSlab.objects.filter(
            insurance_type=self.insurance_type,
            min_coverage_amount__lte=self.sum_assured,
            max_coverage_amount__gte=self.sum_assured,
            is_active=True
        ).first()
        
        if slab:
            return slab.calculate_premium(self.sum_assured)
        
        # Fallback: Calculate using default rate
        default_rate = Decimal('0.02')  # 2% of sum assured
        return self.sum_assured * default_rate
    
    def calculate_coverage_premium(self, coverages: List[CoverageType]) -> Decimal:
        """Calculate additional premium for selected coverages."""
        total = Decimal('0.00')
        for coverage in coverages:
            total += coverage.base_premium_per_unit
        return total
    
    def calculate_addon_premium(self, addons: List[RiderAddon], base_premium: Decimal) -> Decimal:
        """Calculate additional premium for selected add-ons."""
        total = Decimal('0.00')
        for addon in addons:
            addon_premium = base_premium * (addon.premium_percentage / 100)
            if addon.max_coverage_limit and addon_premium > addon.max_coverage_limit:
                addon_premium = addon.max_coverage_limit
            total += addon_premium
        return total
    
    def get_risk_adjustment(self) -> Tuple[Decimal, str]:
        """
        Get risk adjustment percentage from customer's risk profile.
        
        Returns:
            Tuple of (adjustment_percentage, risk_category)
        """
        try:
            risk_profile = self.customer.risk_profile
            return (risk_profile.overall_risk_percentage, risk_profile.risk_category)
        except CustomerRiskProfile.DoesNotExist:
            return (Decimal('0.00'), 'MEDIUM')
    
    def evaluate_discount_rules(self, base_premium: Decimal) -> List[dict]:
        """
        Evaluate all applicable discount rules.
        
        Returns list of applicable discounts with amounts.
        """
        applicable_discounts = []
        today = date.today()
        
        # Get active discount rules for this insurance type
        rules = DiscountRule.objects.filter(
            Q(insurance_type=self.insurance_type) | Q(insurance_type__isnull=True),
            is_active=True
        ).order_by('-rule_priority')
        
        for rule in rules:
            # Check date validity
            if not rule.is_valid_for_date(today):
                continue
            
            # Evaluate rule conditions
            if self._evaluate_discount_condition(rule):
                discount_amount = base_premium * (rule.discount_percentage / 100)
                
                # Apply max cap if set
                if rule.discount_max_amount and discount_amount > rule.discount_max_amount:
                    discount_amount = rule.discount_max_amount
                
                applicable_discounts.append({
                    'rule_code': rule.rule_code,
                    'rule_name': rule.rule_name,
                    'percentage': rule.discount_percentage,
                    'amount': discount_amount,
                    'is_combinable': rule.is_combinable
                })
        
        return applicable_discounts
    
    def _evaluate_discount_condition(self, rule: DiscountRule) -> bool:
        """
        Evaluate if a discount rule's conditions are met.
        
        Supports conditions like:
        - min_fleet_size: Minimum vehicles in fleet
        - max_claim_ratio: Maximum claim ratio
        - min_years_no_claim: Years without claims
        - age_range: [min_age, max_age]
        """
        conditions = rule.rule_condition
        if not conditions:
            return True
        
        # Check fleet size condition
        if 'min_fleet_size' in conditions:
            fleet_count = self.customer.fleets.filter(is_active=True).count()
            if fleet_count < conditions['min_fleet_size']:
                return False
        
        # Check claim ratio condition
        if 'max_claim_ratio' in conditions:
            claim_history = self.customer.claim_histories.order_by('-claim_year').first()
            if claim_history:
                ratio = claim_history.claim_rejection_rate / 100
                if ratio > conditions['max_claim_ratio']:
                    return False
        
        # Check no-claim years condition
        if 'min_years_no_claim' in conditions:
            years_required = conditions['min_years_no_claim']
            recent_histories = self.customer.claim_histories.filter(
                claim_year__gte=date.today().year - years_required
            )
            if recent_histories.filter(claim_count__gt=0).exists():
                return False
        
        # Check age condition
        if 'age_range' in conditions:
            min_age, max_age = conditions['age_range']
            customer_age = self.customer.age
            if customer_age and (customer_age < min_age or customer_age > max_age):
                return False
        
        return True
    
    def calculate_fleet_discount(self, base_premium: Decimal) -> Decimal:
        """
        Calculate fleet discount if applicable.
        
        Uses FleetRiskScore for discount percentage.
        """
        from apps.customers.models import Fleet, FleetRiskScore
        
        active_fleet = self.customer.fleets.filter(is_active=True).first()
        if not active_fleet:
            return Decimal('0.00')
        
        try:
            fleet_score = active_fleet.risk_score
            return base_premium * (fleet_score.discount_percentage / 100)
        except FleetRiskScore.DoesNotExist:
            return Decimal('0.00')
    
    def calculate_gst(self, premium: Decimal) -> Decimal:
        """Calculate GST on premium."""
        from apps.catalog.models import BusinessConfiguration
        gst_rate = BusinessConfiguration.get_decimal('GST_RATE', Decimal('18'))
        return premium * (gst_rate / 100)
    
    def generate_quote(
        self,
        insurance_company: InsuranceCompany,
        coverages: List[CoverageType] = None,
        addons: List[RiderAddon] = None
    ) -> dict:
        """
        Generate a complete quote calculation.
        
        Returns dict with all premium components.
        """
        coverages = coverages or []
        addons = addons or []
        
        # Calculate components
        base_premium = self.calculate_base_premium()
        coverage_premium = self.calculate_coverage_premium(coverages)
        addon_premium = self.calculate_addon_premium(addons, base_premium)
        
        # Subtotal before adjustments
        subtotal = base_premium + coverage_premium + addon_premium
        
        # Risk adjustment
        risk_percentage, risk_category = self.get_risk_adjustment()
        risk_adjustment = subtotal * (risk_percentage / 100)
        
        # Discounts
        discounts = self.evaluate_discount_rules(subtotal)
        total_discount = sum(d['amount'] for d in discounts if d['is_combinable'])
        
        # If non-combinable discounts exist, take the best one
        non_combinable = [d for d in discounts if not d['is_combinable']]
        if non_combinable:
            best_discount = max(non_combinable, key=lambda x: x['amount'])
            if best_discount['amount'] > total_discount:
                total_discount = best_discount['amount']
                discounts = [best_discount]
        
        # Fleet discount
        fleet_discount = self.calculate_fleet_discount(subtotal)
        
        # Net premium
        net_premium = subtotal + risk_adjustment - total_discount - fleet_discount
        if net_premium < 0:
            net_premium = Decimal('0.00')
        
        # GST
        gst_amount = self.calculate_gst(net_premium)
        
        # Total
        total_premium = net_premium + gst_amount
        
        return {
            'insurance_company': insurance_company,
            'base_premium': base_premium,
            'coverage_premium': coverage_premium,
            'addon_premium': addon_premium,
            'subtotal': subtotal,
            'risk_adjustment': risk_adjustment,
            'risk_category': risk_category,
            'discounts': discounts,
            'total_discount': total_discount,
            'fleet_discount': fleet_discount,
            'net_premium': net_premium,
            'gst_amount': gst_amount,
            'total_premium': total_premium,
            'coverages': coverages,
            'addons': addons,
        }
    
    def calculate_quote_score(self, quote_data: dict) -> Decimal:
        """
        Calculate quote score based on weighted factors.
        
        Higher score = better value quote.
        """
        weights = QuoteCalculationWeight.objects.filter(
            insurance_type=self.insurance_type,
            is_active=True
        )
        
        score = Decimal('50.00')  # Base score
        
        company = quote_data['insurance_company']
        
        # Company rating factor
        weight = weights.filter(factor_name='company_rating').first()
        if weight:
            score += company.service_rating * weight.factor_weight * 10
        
        # Claim settlement ratio factor
        weight = weights.filter(factor_name='claim_settlement_ratio').first()
        if weight:
            score += company.claim_settlement_ratio * weight.factor_weight * 30
        
        # Premium competitiveness factor (lower is better)
        weight = weights.filter(factor_name='premium_factor').first()
        if weight:
            # Inverse relationship - lower premium = higher score
            premium_ratio = quote_data['total_premium'] / (self.sum_assured or 1)
            score += (1 - min(premium_ratio, 1)) * weight.factor_weight * 20
        
        return min(max(score, Decimal('0.00')), Decimal('100.00'))
