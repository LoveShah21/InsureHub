# Quotes Module Documentation

## Overview

The **Quotes** module allows customers to discover pricing. It contains the system's "Brain": the **Quote Engine**. This engine performs complex calculations involving base rates, risk factors, and discounts, and then scores the resulting quotes to recommend the best options.

## Core Responsibilities

1. **Premium Calculation**: Mathematical computation of insurance costs.
2. **Risk Assessment**: Adjusting premiums based on customer profile risk.
3. **Scoring Engine**: evaluating "value for money" and ranking quotes.
4. **Recommendation**: Suggesting the best product for the user.

---

## 2. Models

### `Quote`
Represents a generated pricing offer.
- **Relationships**: Customer, Application, Insurance Company.
- **Financials**: `base_premium`, `risk_adjustment`, `tax_amount`, `final_premium`.
- **Status**: `GENERATED`, `SENT`, `ACCEPTED` (converts to Policy), `EXPIRED`.
- **Validity**: Auto-expires after X days (config).

### `QuoteCoverage` & `QuoteAddon`
Junction tables storing the specific coverage configuration for a particular quote.

### `QuoteRecommendation`
Stores the ranked results (Rank 1, Rank 2, Rank 3) for an application, along with the computed scores.

---

## 3. The Quote Engine (`services.py`)

### Calculation Pipeline
1. **Base Premium**: Lookup `PremiumSlab` matching the Sum Insured.
2. **Loadings**: Add premiums for optional Coverages and Add-ons.
3. **Risk Loading**: Fetch `CustomerRiskProfile`. Apply +% or -% loading.
   - *Example*: High risk driver (+15%), Low risk (+0% or discount).
4. **Discounts**: Evaluate `DiscountRule`s (Fleet, Loyalty, etc.). Subtract eligible amounts.
5. **Tax**: Apply GST (18%).

### Scoring Logic (`scoring.py`)
This is a USP of the system. It doesn't just show price; it scores quality.

**Formula**:
```python
Score = (0.4 * Affordability) + 
        (0.3 * Claim_Settlement_Ratio) + 
        (0.2 * Coverage_Match) + 
        (0.1 * Service_Rating)
```
- **Affordability**: Ratio of premium to customer income.
- **Reliability**: Uses company's historic settlement data.
- **Coverage**: How well the quote matches user needs.

---

## 4. Integration

- **Applications**: Input source for the quote engine.
- **Catalog**: Source of rates and rules.
- **Customers**: Source of risk profile data.
- **Policies**: Destination - an accepted quote becomes a policy.
