"""
Quote Scoring Engine

This module implements the rule-based scoring algorithm for quote comparison.

SCORING FORMULA:
score = (0.4 * affordability) + (0.3 * claim_ratio) + 
        (0.2 * coverage_score) + (0.1 * service_rating)

Each component is normalized to a 0-100 scale before applying weights.

Components:
- Affordability: How well the premium fits the customer's budget
- Claim Ratio: Insurance company's historical claim settlement ratio
- Coverage Score: Completeness of selected coverages
- Service Rating: Company's service quality rating

This is a RULE-BASED system, not ML-based (as per project requirements).
"""

from decimal import Decimal
from typing import Optional

from apps.catalog.models import InsuranceCompany, CoverageType
from apps.customers.models import CustomerProfile


# Scoring weights
WEIGHT_AFFORDABILITY = Decimal('0.40')
WEIGHT_CLAIM_RATIO = Decimal('0.30')
WEIGHT_COVERAGE = Decimal('0.20')
WEIGHT_SERVICE_RATING = Decimal('0.10')


def calculate_affordability_score(
    premium: Decimal,
    annual_income: Optional[Decimal],
    budget_min: Optional[Decimal] = None,
    budget_max: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate affordability score (0-100).
    
    Logic:
    - If premium is within budget range: high score (80-100)
    - If premium < 5% of annual income: excellent (90-100)
    - If premium > 15% of annual income: poor (0-40)
    
    Args:
        premium: Annual premium amount
        annual_income: Customer's annual income
        budget_min: Customer's minimum budget preference
        budget_max: Customer's maximum budget preference
    
    Returns:
        Decimal: Score between 0-100
    """
    # Check budget fit
    if budget_min is not None and budget_max is not None:
        if budget_min <= premium <= budget_max:
            # Perfect fit - within budget
            # Score based on position in range (lower is better)
            range_size = budget_max - budget_min
            if range_size > 0:
                position = (premium - budget_min) / range_size
                return Decimal('100') - (position * Decimal('20'))  # 80-100
            return Decimal('90')
        elif premium < budget_min:
            # Below budget - suspicious (might lack coverage)
            return Decimal('70')
        else:
            # Over budget
            overage_pct = ((premium - budget_max) / budget_max) * 100
            if overage_pct <= 10:
                return Decimal('60')
            elif overage_pct <= 25:
                return Decimal('40')
            else:
                return Decimal('20')
    
    # Fallback to income-based calculation
    if annual_income and annual_income > 0:
        premium_pct = (premium / annual_income) * 100
        
        if premium_pct <= 3:
            return Decimal('100')  # Very affordable
        elif premium_pct <= 5:
            return Decimal('90')
        elif premium_pct <= 8:
            return Decimal('75')
        elif premium_pct <= 12:
            return Decimal('55')
        elif premium_pct <= 15:
            return Decimal('35')
        else:
            return Decimal('15')  # Too expensive
    
    # No income data - neutral score
    return Decimal('50')


def calculate_claim_ratio_score(company: InsuranceCompany) -> Decimal:
    """
    Calculate score based on company's claim settlement ratio.
    
    Logic:
    - 95%+ settlement ratio: 100 points
    - 90-95%: 85 points
    - 85-90%: 70 points
    - 80-85%: 55 points
    - Below 80%: 40 points or less
    
    Args:
        company: InsuranceCompany instance
    
    Returns:
        Decimal: Score between 0-100
    """
    ratio = company.claim_settlement_ratio
    
    if ratio >= Decimal('0.95'):
        return Decimal('100')
    elif ratio >= Decimal('0.92'):
        return Decimal('90')
    elif ratio >= Decimal('0.90'):
        return Decimal('85')
    elif ratio >= Decimal('0.85'):
        return Decimal('70')
    elif ratio >= Decimal('0.80'):
        return Decimal('55')
    elif ratio >= Decimal('0.75'):
        return Decimal('40')
    else:
        return Decimal('25')


def calculate_coverage_score(
    selected_coverages: list,
    insurance_type_id: int
) -> Decimal:
    """
    Calculate score based on coverage completeness.
    
    Logic:
    - All mandatory coverages selected: base 60 points
    - Each optional coverage adds points
    - More comprehensive coverage = higher score
    
    Args:
        selected_coverages: List of selected coverage IDs
        insurance_type_id: Insurance type ID
    
    Returns:
        Decimal: Score between 0-100
    """
    all_coverages = CoverageType.objects.filter(insurance_type_id=insurance_type_id)
    mandatory = all_coverages.filter(is_mandatory=True)
    optional = all_coverages.filter(is_mandatory=False)
    
    total_mandatory = mandatory.count()
    total_optional = optional.count()
    
    if total_mandatory == 0:
        mandatory_score = Decimal('60')
    else:
        selected_mandatory = mandatory.filter(id__in=selected_coverages).count()
        mandatory_score = (Decimal(selected_mandatory) / Decimal(total_mandatory)) * Decimal('60')
    
    if total_optional == 0:
        optional_score = Decimal('40')
    else:
        selected_optional = optional.filter(id__in=selected_coverages).count()
        optional_score = (Decimal(selected_optional) / Decimal(total_optional)) * Decimal('40')
    
    return mandatory_score + optional_score


def calculate_service_rating_score(company: InsuranceCompany) -> Decimal:
    """
    Calculate score based on company's service rating.
    
    Service rating is on a 5-point scale, normalized to 0-100.
    
    Args:
        company: InsuranceCompany instance
    
    Returns:
        Decimal: Score between 0-100
    """
    rating = company.service_rating
    # Normalize to 0-100 (rating is 0-5)
    return (rating / Decimal('5')) * Decimal('100')


def calculate_quote_score(
    premium: Decimal,
    company: InsuranceCompany,
    selected_coverages: list,
    insurance_type_id: int,
    annual_income: Optional[Decimal] = None,
    budget_min: Optional[Decimal] = None,
    budget_max: Optional[Decimal] = None
) -> dict:
    """
    Calculate overall quote score using weighted formula.
    
    FORMULA:
    score = (0.4 * affordability) + (0.3 * claim_ratio) + 
            (0.2 * coverage_score) + (0.1 * service_rating)
    
    Args:
        premium: Quote's final premium
        company: Insurance company
        selected_coverages: List of selected coverage IDs
        insurance_type_id: Insurance type ID
        annual_income: Customer's annual income (optional)
        budget_min: Customer's minimum budget (optional)
        budget_max: Customer's maximum budget (optional)
    
    Returns:
        dict: Contains overall_score and component breakdown
    """
    # Calculate individual scores
    affordability = calculate_affordability_score(
        premium, annual_income, budget_min, budget_max
    )
    claim_ratio = calculate_claim_ratio_score(company)
    coverage = calculate_coverage_score(selected_coverages, insurance_type_id)
    service_rating = calculate_service_rating_score(company)
    
    # Apply weights and calculate overall score
    overall_score = (
        (WEIGHT_AFFORDABILITY * affordability) +
        (WEIGHT_CLAIM_RATIO * claim_ratio) +
        (WEIGHT_COVERAGE * coverage) +
        (WEIGHT_SERVICE_RATING * service_rating)
    )
    
    return {
        'overall_score': round(overall_score, 2),
        'affordability_score': round(affordability, 2),
        'claim_ratio_score': round(claim_ratio, 2),
        'coverage_score': round(coverage, 2),
        'service_rating_score': round(service_rating, 2),
        'weights': {
            'affordability': float(WEIGHT_AFFORDABILITY),
            'claim_ratio': float(WEIGHT_CLAIM_RATIO),
            'coverage': float(WEIGHT_COVERAGE),
            'service_rating': float(WEIGHT_SERVICE_RATING),
        }
    }


def generate_recommendation_reason(scores: dict, company_name: str) -> str:
    """
    Generate human-readable recommendation reason.
    
    Args:
        scores: Score breakdown from calculate_quote_score
        company_name: Name of the insurance company
    
    Returns:
        str: Recommendation reason text
    """
    reasons = []
    
    if scores['affordability_score'] >= 80:
        reasons.append("fits well within your budget")
    elif scores['affordability_score'] >= 60:
        reasons.append("reasonably priced")
    
    if scores['claim_ratio_score'] >= 85:
        reasons.append(f"{company_name} has an excellent claim settlement record")
    elif scores['claim_ratio_score'] >= 70:
        reasons.append(f"{company_name} has a good claim settlement ratio")
    
    if scores['coverage_score'] >= 80:
        reasons.append("provides comprehensive coverage")
    elif scores['coverage_score'] >= 60:
        reasons.append("covers all essential needs")
    
    if scores['service_rating_score'] >= 80:
        reasons.append("highly rated for customer service")
    
    if not reasons:
        reasons.append("balanced option for your requirements")
    
    return "This quote " + ", ".join(reasons) + "."
