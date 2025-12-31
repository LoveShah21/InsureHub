# Configuration and Risk Module Documentation

## Overview

This module is the "Control Center" of the application. It decouples business logic from code, allowing the system to be **Configuration-Driven**. It also encapsulates the **Risk Engine**, which uses these configurations to assess customer risk.

## Core Responsibilities

1. **System Configuration**: Global variables (Tax rates, Timeouts).
2. **Rule Management**: Defining eligibility and discount logic dynamically.
3. **Risk Engine**: The logic that computes risk scores.

---

## 2. Configuration Models

### `BusinessConfiguration`
A Key-Value store for system constants.
- `GST_RATE`: 18.00
- `QUOTE_VALIDITY_DAYS`: 30
- `CLAIM_SLA_DAYS`: 15
- `ACCOUNT_LOCK_THRESHOLD`: 5

### `PremiumSlab`
Defines base rates.
- Structure: `InsuranceType | Min_Sum_Insured | Max_Sum_Insured | Rate_Percentage`
- Example: Motor | 5,00,000 | 10,00,000 | 2.5%

### `ClaimApprovalThreshold`
Defines RBAC for claim amounts.
- `Role: BACKOFFICE` -> `Limit: 50,000`
- `Role: ADMIN` -> `Limit: 5,00,000`

---

## 3. The Rules Engine (`DiscountRule`)

We utilize a JSON-based rule evaluator.

**Rule Storage (`rule_condition` JSONField):**
```json
{
  "min_age": 25,
  "max_claim_ratio": 0.1,
  "min_fleet_size": 5
}
```

**Evaluation Logic:**
The engine fetches the context (User data, Application data) and compares it against the JSON keys.
- If `user.age >= min_age` AND `user.fleet >= min_fleet_size` -> **APPLY DISCOUNT**.

---

## 4. The Risk Engine

The Risk Engine is a service that aggregates data from the **Customers** module and outputs a `RiskProfile`.

### Weighting Algorithm
The risk score is a weighted average of multiple factors:

`Score = (AgeRisk * 0.2) + (MedicalRisk * 0.3) + (DrivingRisk * 0.3) + (HistoryRisk * 0.2)`

### Integration
- **Input**: Customer Profile, Medical Disclosure, Driving History.
- **Output**: `CustomerRiskProfile` (persisted in DB).
- **Consumer**: The `Quotes` module reads this profile to determine the `risk_adjustment_percentage`.

**Risk Categories**:
- 0-20: **LOW** (Discount eligible)
- 21-50: **MEDIUM** (Standard rate)
- 51-80: **HIGH** (Loading applied)
- 81-100: **CRITICAL** (May be declined)
