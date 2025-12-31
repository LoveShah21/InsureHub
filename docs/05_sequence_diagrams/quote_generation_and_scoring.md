# Quote Generation and Scoring Sequence Diagram

## Overview

This document describes the quote generation workflow, premium calculation, and the rule-based scoring algorithm.

---

## 1. Quote Generation Flow

```mermaid
sequenceDiagram
    participant Backoffice as Backoffice View
    participant QuoteService as Quote Service
    participant QuoteModel as Quote Model
    participant PremiumSlab as Premium Slab
    participant DiscountRules as Discount Rules
    participant ScoringEngine as Scoring Engine

    Backoffice->>QuoteService: Generate Quote Request
    QuoteService->>PremiumSlab: Get Application & Customer Data
    PremiumSlab-->>QuoteService: Application + Customer
    
    QuoteService->>DiscountRules: Calculate Base Premium
    Note right of DiscountRules: Find slab by coverage
    DiscountRules-->>QuoteService: Base Premium = ₹25,000
    
    QuoteService->>PremiumSlab: Get Risk Profile
    PremiumSlab-->>QuoteService: Risk Adjustment: +15%
    
    QuoteService->>DiscountRules: Evaluate Discount Rules
    Note right of DiscountRules: Check conditions
    DiscountRules-->>QuoteService: Discounts: Fleet(10%), Loyalty(5%)
    
    QuoteService->>QuoteService: Calculate Final Premium
    QuoteService->>QuoteService: Calculate GST (18%)
    
    QuoteService->>ScoringEngine: Calculate Score
    Note right of ScoringEngine: Apply scoring formula
    ScoringEngine-->>QuoteService: Score: 78.5
    
    QuoteService->>QuoteModel: Create Quote
    QuoteModel-->>QuoteService: Quote Created
    QuoteService-->>Backoffice: Quote Result (QT-2025...)
```

---

## 2. Premium Calculation Formula

```mermaid
flowchart TD
    Step1[Step 1: Base Premium<br/>Sum Insured: ₹10,00,000<br/>Rate: 2.5% -> ₹25,000]
    Step2[Step 2: Add Coverage Premiums<br/>Total: ₹4,500 -> ₹29,500]
    Step3[Step 3: Add Addon Premiums<br/>Total: ₹3,300 -> ₹32,800]
    Step4[Step 4: Risk Adjustment<br/>High Risk +15% -> ₹37,720]
    Step5[Step 5: Apply Discounts<br/>Total -₹5,658 -> ₹32,062]
    Step6[Step 6: Calculate GST<br/>18% -> ₹5,771]
    Result[TOTAL PREMIUM<br/>₹37,833]
    
    Step1 --> Step2 --> Step3 --> Step4 --> Step5 --> Step6 --> Result
```

---

## 3. Quote Scoring Algorithm

```python
# From apps/quotes/scoring.py

def calculate_quote_score(quote, customer, application):
    """
    Calculate overall quote suitability score.
    
    Formula:
    score = (0.4 × affordability) + (0.3 × claim_ratio) + 
            (0.2 × coverage_score) + (0.1 × service_rating)
    """
    
    # Component 1: Affordability (40% weight)
    # How affordable is the premium relative to customer income?
    affordability = calculate_affordability_score(
        premium=quote.total_premium_with_gst,
        annual_income=customer.annual_income
    )
    
    # Component 2: Claim Settlement Ratio (30% weight)
    # How reliable is the insurance company?
    claim_ratio = calculate_claim_ratio_score(
        company=quote.insurance_company
    )
    
    # Component 3: Coverage Completeness (20% weight)
    # Does the quote cover what was requested?
    coverage = calculate_coverage_score(
        quote=quote,
        application=application
    )
    
    # Component 4: Service Rating (10% weight)
    # Company's customer service quality
    service = calculate_service_rating_score(
        company=quote.insurance_company
    )
    
    # Weighted sum
    final_score = (
        (0.4 * affordability) +
        (0.3 * claim_ratio) +
        (0.2 * coverage) +
        (0.1 * service)
    )
    
    return round(final_score, 2)
```

### Scoring Components Detail

```mermaid
classDiagram
    class Score {
        +calculate_quote_score()
        +Final Score
    }
    class Affordability {
        Weight: 40%
        Score: Based on premium/income
    }
    class ClaimRatio {
        Weight: 30%
        Score: CSR * 100
    }
    class Coverage {
        Weight: 20%
        Score: (Sum Insured / Requested) * 100
    }
    class Service {
        Weight: 10%
        Score: (Rating / 5) * 100
    }
    
    Score *-- Affordability
    Score *-- ClaimRatio
    Score *-- Coverage
    Score *-- Service
```

---

## 4. Example Score Calculation

> [!NOTE]
> **Example: Quote Score Calculation**
>
> **Customer**: Annual Income = ₹12,00,000
> **Quote**: Total Premium = ₹37,833, Sum Insured = ₹10,00,000
> **Company**: CSR = 0.92, Service Rating = 4.5/5
>
> | Component | Calculation | Score | Weighted |
> |-----------|-------------|-------|----------|
> | **Affordability** | 37,833 / 12,00,000 = 3.15% | 75 | 30 |
> | **Claim Ratio** | 0.92 × 100 | 92 | 27.6 |
> | **Coverage** | 10L / 10L = 1.0 | 100 | 20 |
> | **Service** | (4.5/5) × 100 | 90 | 9 |
> | **Total** | | | **86.6** |
>
> *Recommendation: "Highly Recommended - Excellent balance of affordability and coverage"*

---

## 5. Discount Rule Evaluation

```mermaid
sequenceDiagram
    participant QuoteService
    participant DiscountRule as Discount Rule Table
    participant Customer as Customer Data

    QuoteService->>DiscountRule: Get active rules for insurance type
    DiscountRule-->>QuoteService: List of rules
    
    loop For each rule
        QuoteService->>Customer: Get customer data (fleet, count, age)
        Customer-->>QuoteService: Data
        QuoteService->>QuoteService: Evaluate JSON condition
    end
```
