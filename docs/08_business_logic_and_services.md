# Business Logic and Services

## Overview

In the **Service Layer** architecture, business logic is abstracted away from Views (Controllers) and Models (Data). This document details the core services that drive the application's intelligence.

---

## 1. QuoteCalculationService
**Location**: `apps/quotes/services.py`

This is the most complex service in the system.

### Logic Flow
1. **Initialize**: Accepts `InsuranceApplication` and `Customer`.
2. **Base Calculation**:
   - Queries `PremiumSlab` based on requested Sum Insured.
   - `Base = Sum_Insured * Slab_Rate`.
3. **Coverage Loading**:
   - Iterates through selected `CoverageTypes`.
   - Adds fixed costs or percentage costs to Base.
4. **Add-on Loading**:
   - Iterates through `RiderAddons`.
   - Adds costs (e.g., "Zero Dep" = 15% of Base).
5. **Risk Adjustment**:
   - Calls `CustomerRiskProfile`.
   - `Adjusted_Premium = Premium * (1 + Risk_Score/100)`.
6. **Discount Application**:
   - Fetches active `DiscountRules`.
   - Evaluates JSON conditions against customer context.
   - Subtracts eligible discount amounts (capped at max limit).
7. **Taxation**:
   - Applies `GST_RATE` from `BusinessConfiguration`.
8. **Final Output**: Returns a dictionary with detailed line items and the final total.

---

## 2. ClaimsWorkflowService
**Location**: `apps/claims/services.py`

Manages the state transitions of a Claim.

### Logic Flow
- **Submit**: Validates policy status.
- **Approve(user, claim, amount)**:
  - Fetches `ClaimApprovalThreshold` for `user.roles`.
  - If `amount > threshold.limit`: Trace Error "Authorization Limit Exceeded".
  - Else: Update status to `APPROVED`, record `amount_approved`.
- **Settle**:
  - Validates claim is `APPROVED`.
  - Trigger mock bank transfer logic.
  - Update status to `SETTLED`.

---

## 3. NotificationService
**Location**: `apps/notifications/services.py`

Handles multi-channel alerting.

### Logic Flow
- **Send(user, template_code, context)**:
  - Fetches `NotificationTemplate` by code.
  - Performs String Interpolation: `template.body.format(**context)`.
  - **DB**: Creates `Notification` record (for In-App bell icon).
  - **Email**: Dispatches async email task (simulated in MVP).

---

## 4. RiskAssessmentService
**Location**: `apps/customers/services.py`

Background service for scoring customers.

### Logic Flow
- **Calculate**:
  - Normalizes metrics (Age, Accidents) to a 0-100 scale.
  - Applies weighted average formula.
  - Updates `CustomerRiskProfile` table.
  - This runs asynchronously or on-demand when a customer updates their profile.

---

## 5. RazorpayGateway Service
**Location**: `apps/policies/payment_gateway.py`

Singleton wrapper for Razorpay API.

### Logic Flow
- **Create Order**: Interfaces with `razorpay_client.order.create`.
- **Verify Signature**: Implements the HMAC-SHA256 comparison logic detailed in security docs.
- **Fail-safe**: Logs all raw API responses for debugging payment failures.
