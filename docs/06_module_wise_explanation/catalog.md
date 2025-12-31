# Catalog Module Documentation

## Overview

The **Catalog** module represents the "Product Definition" layer of the system. It uses a **Configuration-Driven Architecture**, meaning insurance products, pricing, and rules are defined in the database rather than hardcoded in Python files. This allows Administrators to modify business offerings without code deployment.

## Core Responsibilities

1. **Product Masters**: Defining Insurance Types, Companies, Coverages, and Add-ons.
2. **Pricing Configuration**: Managing Premium Slabs and GST rates.
3. **Business Rules**: Defining Discount Rules and Eligibility Criteria.
4. **System Configuration**: Global settings (SLA days, Lockout thresholds).

---

## 2. Models

### Product Hierarchy
1. **`InsuranceType`**: The root category (e.g., "Motor Insurance", "Health Insurance").
2. **`InsuranceCompany`**: The provider (e.g., "Tata AIG", "HDFC Ergo"). Contains quality metrics like `claim_settlement_ratio` used in scoring.
3. **`CoverageType`**: Specific coverages linked to an Insurance Type (e.g., "Third Party Liability", "Own Damage"). Can be Mandatory or Optional.
4. **`RiderAddon`**: Extra enhancements (e.g., "Zero Depreciation", "Roadside Assistance").

### Configuration Models
1. **`PremiumSlab`**: Defines base premium rates based on sum insured ranges.
   - Example: Range 5L-10L → Rate 2.5%.
2. **`BusinessConfiguration`**: Key-value store for system settings.
   - `GST_RATE`: 18.0
   - `CLAIM_SLA_DAYS`: 15
3. **`DiscountRule`**: JSON-based rule engine.
   - Stores conditions like `{"min_fleet_size": 5}`.
   - Evaluated dynamically during quote generation.

---

## 3. Business Logic

### Dynamic Form Generation
The frontend uses the `InsuranceType` configuration to render appropriate application forms. For example, selecting "Motor Insurance" renders vehicle-related fields, while "Health" renders medical history fields.

### Rule Evaluation
The module provides utility functions to evaluate JSON logic against customer data.

```python
def evaluate_rule(rule_condition, context):
    # Simplified logic
    for key, required_value in rule_condition.items():
        if context.get(key) < required_value:
            return False
    return True
```

---

## 4. Usage in System

- **Applications Module**: Uses `InsuranceType` to validate submissions.
- **Quotes Module**: Uses `PremiumSlab` for base calculation and `DiscountRule` for adjustments.
- **Policies Module**: Links issued policies to specific entries in the catalog.
