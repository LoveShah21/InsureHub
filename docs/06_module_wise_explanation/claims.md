# Claims Module Documentation

## Overview

The **Claims** module is the post-issuance operational core. It implements a **State Machine Workflow** to manage the lifecycle of a claim from submission to settlement. It is designed to ensure compliance, enforce authority limits, and track SLAs.

## Core Responsibilities

1. **Lifecycle Management**: Enforcing valid status transitions.
2. **Validation**: Ensuring claims are valid against active policies.
3. **Approval Hierarchy**: Enforcing role-based approval limits.
4. **Settlement**: Managing payout processing.

---

## 2. Models

### `Claim`
The central entity.
- **Statuses**: `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `SETTLED`, `CLOSED`.
- **Financials**: `amount_requested`, `amount_approved`, `amount_settled`.
- **Timestamps**: `submitted_at`, `approved_at`, `settled_at` (for SLA tracking).

### `ClaimDocument`
Supporting evidence uploaded by the customer (Photos, FIR, Medical Reports).
- Includes verification status (`PENDING`, `VERIFIED`).

### `ClaimStatusHistory`
Audit trail of workflow transitions.
- Records *who* changed the status, *when*, and from *what* to *what*.

### `ClaimApprovalThreshold`
Configuration model defining authority limits.
- Example: "BACKOFFICE can approve up to ₹50,000. ADMIN must approve above ₹50,000."

---

## 3. Workflow Logic (State Machine)

The `ClaimsWorkflowService` enforces transitions:

1. **Submission**: Validates policy is active and covers the incident date. Sets status to `SUBMITTED`.
2. **Review**: Backoffice verifies documents. Status → `UNDER_REVIEW`.
3. **Decision**:
   - **Approve**: Checks `ClaimApprovalThreshold` for the user. If amount > limit, approval is blocked. Status → `APPROVED`.
   - **Reject**: Requires mandatory `rejection_reason`. Status → `REJECTED`.
4. **Settlement**: Processing of payment. Status → `SETTLED`.
5. **Closure**: Final state. Status → `CLOSED`.

### SLA Tracking
The system calculates `elapsed_days = current_date - submitted_date`. If `elapsed_days > configured_sla`, the claim is flagged as "Overdue" in dashboards.

---

## 4. Integration

- **Notifications**: Status changes trigger automatic email/in-app alerts to customers.
- **Policies**: Claims are linked to Policies; the sum of approved claims cannot exceed the Policy's Sum Insured.
- **Accounts**: Permissions determine who can perform transitions (e.g., only Admin can settle).
