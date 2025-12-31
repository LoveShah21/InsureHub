# Customers Module Documentation

## Overview

The **Customers** module manages the detailed profiling of users. While the `Accounts` module handles login credentials, this module stores the domain-specific data required for insurance underwriting, risk operations, and policy issuance.

## Core Responsibilities

1. **KYC Data Management**: Storing sensitive identity information (PAN, Aadhaar) securely.
2. **Risk Profiling**: Aggregating data points (Health, Driving) to calculate risk scores.
3. **Asset Management**: Tracking insure-able assets like Vehicles (Fleets).

---

## 2. Models

### `CustomerProfile`
Extends the base User model (One-to-One).
- **Identity**: `pan_number`, `aadhar_number`.
- **Demographics**: `date_of_birth`, `gender`, `marital_status`, `occupation_type`, `annual_income`.
- **Contact**: `residential_address`, `city`, `state`.

### `CustomerRiskProfile`
A computed entity that represents the "riskiness" of the customer.
- **Fields**: `risk_score` (0-100), `risk_category` (LOW, MEDIUM, HIGH, CRITICAL).
- **Factors**:
  - `age_risk_factor`: Calculated from DOB.
  - `medical_risk_factor`: Derived from `CustomerMedicalDisclosure`.
  - `driving_risk_factor`: Derived from `CustomerDrivingHistory`.
  - `claim_history_risk_factor`: Derived from past claims.
- **Usage**: Used by `QuoteService` to apply premium loading (e.g., +20%).

### `CustomerMedicalDisclosure`
Stores health declarations for Health Insurance.
- **Fields**: `pre_existing_diseases` (JSON list), `is_smoker`, `is_drinker`, `surgeries_in_last_3_years`.

### `CustomerDrivingHistory`
Stores driving records for Motor Insurance.
- **Fields**: `license_number`, `license_valid_upto`, `years_of_experience`, `accident_count`.

### `Fleet`
For commercial customers managing multiple vehicles.
- Allows applying "Fleet Discounts" if the customer owns > 5 vehicles.

---

## 3. Business Logic

### Risk Calculation Service
A background service (or triggered on profile update) aggregates all factors:

```python
def calculate_overall_risk(customer):
    base_score = 50
    # Age adjustments
    if age < 25: base_score += 10
    if age > 60: base_score += 15
    
    # Medical adjustments
    if customer.medical_disclosure.is_smoker: base_score += 20
    
    # Driving adjustments
    base_score += (customer.driving_history.accident_count * 15)
    
    return min(100, base_score)
```

### Encryption & Privacy
Sensitive fields like `pan_number` and `aadhar_number` are candidates for field-level encryption (future scope), though currently stored with standard database security. Masking is applied in the frontend view (e.g., `XXXX-1234`).
