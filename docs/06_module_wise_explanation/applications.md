# Applications Module Documentation

## Overview

The **Applications** module handles the intake of insurance requests. It acts as the digital "Proposal Form" where customers submit their intent to purchase insurance, along with necessary data and documents. This module bridges the gap between a `Customer` and a `Quote`.

## Core Responsibilities

1. **Data Ingestion**: Capturing dynamic data based on insurance types.
2. **Document Management**: Handling uploads of proof documents (RC, ID, Medical Reports).
3. **Workflow Management**: Managing the lifecycle from `DRAFT` to `APPROVED`.

---

## 2. Models

### `InsuranceApplication`
The central record for a new insurance request.
- **Fields**: `customer`, `insurance_type`, `status`.
- **`application_data` (JSONField)**: The key design feature. It stores variable schema data.
  - *Motor Application*: `{"vehicle_no": "MH12AB1234", "make": "Honda", "year": 2022}`
  - *Health Application*: `{"patient_name": "John Doe", "hospital_preference": "Apollo"}`
  - *Travel Application*: `{"passport_no": "P123456", "destination": "USA", "dates": "..."}`
- **Constraint**: A customer can have multiple applications in different states.

### `ApplicationDocument`
Stores files supporting the application.
- **Fields**: `application`, `document_type`, `file`, `verification_status` (PENDING/VERIFIED).
- **Types**: `IDENTITY_PROOF`, `ADDRESS_PROOF`, `VEHICLE_RC`, `MEDICAL_REPORT`.

---

## 3. Workflow Logic

### 1. Draft & Submission
- Customers create an application in `DRAFT` state. They can save progress and return later.
- On submission, the system validates that all mandatory fields (for that specific `InsuranceType`) are present in `application_data`.
- Status moves to `SUBMITTED`.

### 2. Backoffice Review
- **Document Verification**: Staff members view uploaded files and mark them as `VERIFIED`.
- **Approval**: Once all docs are verified, staff marks the application as `APPROVED`.
- **Rejection**: If data is invalid, application is `REJECTED` with a reason. Customer can edit and resubmit (creates a new version or updates status).

---

## 4. Integration

- **Catalog**: The `InsuranceType` determines the frontend form fields and validation rules.
- **Quotes**: An `APPROVED` application is the prerequisite for generating a `Quote`. The Quote Engine reads the `application_data` to calculate premiums (e.g., car model year determines IDV).
- **Notifications**: Alerts sent on submission and status changes.
