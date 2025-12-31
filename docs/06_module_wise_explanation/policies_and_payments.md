# Policies and Payments Module Documentation

## Overview

The **Policies** and **Payments** module manages the revenue generation and contract issuance phase. It integrates with **Razorpay** for handling monetary transactions securely and manages the lifecycle of the insurance contract (Policy).

## Core Responsibilities

1. **Payment Processing**: Secure integration with Payment Gateway.
2. **Policy Issuance**: Converting an accepted Quote into a legal Policy.
3. **Contract Management**: Tracking policy validity, renewals, and cancellations.
4. **Invoice Generation**: Creating fiscal records for transactions.

---

## 2. Models

### `Policy`
The legal contract.
- Fields: `policy_number`, `start_date`, `end_date`, `sum_insured`.
- Status: `ACTIVE`, `EXPIRED`, `CANCELLED`.
- Constraint: One-to-One with `Quote`.

### `Payment`
Transaction record.
- **Gateway Fields**: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`.
- Status: `PENDING`, `SUCCESS`, `FAILED`.

### `Invoice`
Immutable record of the financial transaction, generated post-payment.

---

## 3. Razorpay Integration

The system uses the **Razorpay Sandbox** environment to simulate real-world payments.

### Security: Signature Verification
The most critical aspect is **HMAC-SHA256 Signature Verification**.
1. Razorpay sends `payment_id` and `signature` to the frontend callback.
2. Frontend sends these to the Backend.
3. Backend reconstructs the payload: `order_id + "|" + payment_id`.
4. Backend hashes this payload with the **Razorpay Secret Key**.
5. The generated hash MUST match the received signature.
   - **Match**: Payment is valid. Issue Policy.
   - **Mismatch**: Tampering detected. Reject transaction.

### Singleton Pattern
The integration is implemented as a singleton service `RazorpayGateway` to maintain a single initialized client instance across the application.

---

## 4. Policy Issuance Workflow

The issuance is an atomic operation triggered by a successful payment verification:

1. **Verify Payment**: Ensure signature is valid.
2. **Mark Quote Accepted**: Lock the quote to prevent reuse.
3. **Create Policy**:
   - `start_date` = Today.
   - `end_date` = Today + 1 year (or tenure).
4. **Generate Invoice**: Capture financial snapshot.
5. **Notify**: Send "Policy Issued" email with details.

---

## 5. Integration

- **Quotes**: The source triggering the flow.
- **Claims**: Policies act as the parent for claims (validation of active status).
- **Notifications**: Triggers issuance and renewal alerts.
