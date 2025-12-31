# Table Definitions

## Complete Table Reference

This document provides detailed definitions for all database tables in the Insurance Policy Management System.

---

## 1. Identity & Access Management (IAM)

### users
Primary user authentication table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Display username |
| password | VARCHAR(255) | NOT NULL | Hashed password (Django) |
| first_name | VARCHAR(100) | NOT NULL | First name |
| last_name | VARCHAR(100) | NOT NULL | Last name |
| phone_number | VARCHAR(15) | NULL | Contact phone |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| failed_login_attempts | INT | DEFAULT 0 | Lockout counter |
| account_locked_until | TIMESTAMP | NULL | Lockout expiry |
| last_login | TIMESTAMP | NULL | Last login time |
| last_password_change_at | TIMESTAMP | NULL | Password change tracking |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

### roles
System roles for RBAC.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| role_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| role_name | VARCHAR(100) | UNIQUE, NOT NULL | Role name (ADMIN, BACKOFFICE, CUSTOMER) |
| role_description | TEXT | NULL | Role description |
| is_system_role | BOOLEAN | DEFAULT FALSE | System-defined role flag |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

### user_roles
Junction table for User-Role assignment.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_role_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| user_id | INT | FK → users, NOT NULL | User reference |
| role_id | INT | FK → roles, NOT NULL | Role reference |
| assigned_at | TIMESTAMP | DEFAULT NOW | Assignment timestamp |
| assigned_by | INT | FK → users | Assigner user |
| **UNIQUE** | | (user_id, role_id) | Prevent duplicate assignments |

### permissions
Granular permissions (future extensibility).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| permission_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| permission_code | VARCHAR(100) | UNIQUE, NOT NULL | Permission key (e.g., POLICY_CREATE) |
| permission_description | VARCHAR(255) | NULL | Human-readable description |
| resource_name | VARCHAR(100) | NOT NULL | Resource (POLICY, CLAIM, USER) |
| action_name | VARCHAR(50) | NOT NULL | Action (CREATE, READ, UPDATE, DELETE) |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |

### audit_logs
Immutable audit trail.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| audit_log_id | BIGINT | PK, AUTO_INCREMENT | Unique identifier |
| user_id | INT | FK → users, NULL | Acting user |
| table_name | VARCHAR(100) | NOT NULL | Affected table |
| record_id | INT | NULL | Affected record ID |
| action_type | ENUM | NOT NULL | INSERT, UPDATE, DELETE, LOGIN, LOGOUT |
| description | TEXT | NULL | Action description |
| old_values | JSON | NULL | Previous state |
| new_values | JSON | NULL | New state |
| ip_address | VARCHAR(45) | NULL | Client IP |
| timestamp | TIMESTAMP | DEFAULT NOW | Action timestamp |

---

## 2. Insurance Catalog

### insurance_types
Types of insurance products.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| insurance_type_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| type_name | VARCHAR(100) | UNIQUE, NOT NULL | Display name |
| type_code | VARCHAR(50) | UNIQUE, NOT NULL | Short code (MOTOR, HEALTH) |
| description | TEXT | NULL | Type description |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

### insurance_companies
Insurance providers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| company_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| company_name | VARCHAR(255) | UNIQUE, NOT NULL | Company name |
| company_code | VARCHAR(50) | UNIQUE, NOT NULL | Short code |
| registration_number | VARCHAR(100) | NULL | Regulatory registration |
| headquarters_address | TEXT | NULL | Address |
| contact_email | VARCHAR(255) | NULL | Contact email |
| contact_phone | VARCHAR(15) | NULL | Contact phone |
| website | VARCHAR(255) | NULL | Website URL |
| claim_settlement_ratio | DECIMAL(5,2) | DEFAULT 0.90 | CSR (0-1) |
| service_rating | DECIMAL(3,2) | DEFAULT 4.00 | Rating (0-5) |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

### coverage_types
Coverage options per insurance type.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| coverage_type_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| coverage_name | VARCHAR(255) | NOT NULL | Coverage name |
| coverage_code | VARCHAR(50) | NOT NULL | Short code |
| insurance_type_id | INT | FK → insurance_types | Parent type |
| description | TEXT | NULL | Description |
| is_mandatory | BOOLEAN | DEFAULT FALSE | Required coverage |
| base_premium_per_unit | DECIMAL(12,2) | DEFAULT 0.00 | Base premium |
| unit_of_measurement | VARCHAR(50) | NULL | Measurement unit |
| **UNIQUE** | | (insurance_type_id, coverage_code) | Prevent duplicates |

### riders_addons
Optional add-ons/riders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| addon_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| addon_name | VARCHAR(255) | NOT NULL | Add-on name |
| addon_code | VARCHAR(50) | NOT NULL | Short code |
| insurance_type_id | INT | FK → insurance_types | Parent type |
| description | TEXT | NULL | Description |
| premium_percentage | DECIMAL(5,2) | DEFAULT 0.00 | % of base premium |
| is_optional | BOOLEAN | DEFAULT TRUE | Optional flag |
| max_coverage_limit | DECIMAL(15,2) | NULL | Maximum coverage |
| **UNIQUE** | | (insurance_type_id, addon_code) | Prevent duplicates |

---

## 3. Customer Profiling

### customers
Customer profile extending users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| customer_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| user_id | INT | FK → users, UNIQUE | User reference (1:1) |
| date_of_birth | DATE | NULL | Birth date |
| gender | ENUM | NULL | MALE, FEMALE, OTHER |
| marital_status | VARCHAR(50) | NULL | Marital status |
| nationality | VARCHAR(100) | DEFAULT 'Indian' | Nationality |
| pan_number | VARCHAR(50) | UNIQUE, NULL | PAN card number |
| aadhar_number | VARCHAR(50) | UNIQUE, NULL | Aadhaar number |
| residential_address | TEXT | NULL | Full address |
| residential_city | VARCHAR(100) | NULL | City |
| residential_state | VARCHAR(100) | NULL | State |
| residential_pincode | VARCHAR(10) | NULL | PIN code |
| occupation_type | VARCHAR(50) | NULL | Occupation category |
| annual_income | DECIMAL(15,2) | NULL | Yearly income |
| created_at | TIMESTAMP | DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

### customer_risk_profiles
Computed risk assessment.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| risk_profile_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| customer_id | INT | FK → customers, UNIQUE | Customer (1:1) |
| risk_category | ENUM | NOT NULL | LOW, MEDIUM, HIGH, CRITICAL |
| risk_score | DECIMAL(5,2) | DEFAULT 50.00 | Score 0-100 |
| age_risk_factor | DECIMAL(5,2) | DEFAULT 0 | Age component |
| medical_risk_factor | DECIMAL(5,2) | DEFAULT 0 | Medical component |
| driving_risk_factor | DECIMAL(5,2) | DEFAULT 0 | Driving component |
| claim_history_risk_factor | DECIMAL(5,2) | DEFAULT 0 | Claims component |
| overall_risk_percentage | DECIMAL(5,2) | DEFAULT 0 | Premium adjustment % |
| calculated_at | TIMESTAMP | ON UPDATE NOW | Last calculation |
| valid_until | TIMESTAMP | NULL | Profile expiry |

---

## 4. Applications

### insurance_applications
Insurance application submissions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| application_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| application_number | VARCHAR(100) | UNIQUE, NOT NULL | Reference number |
| customer_id | INT | FK → customers | Applicant |
| insurance_type_id | INT | FK → insurance_types | Insurance type |
| status | ENUM | DEFAULT 'DRAFT' | DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED |
| rejection_reason | TEXT | NULL | Rejection reason |
| application_data | JSON | DEFAULT {} | Dynamic form data |
| requested_coverage_amount | DECIMAL(15,2) | NULL | Desired coverage |
| policy_tenure_months | INT | DEFAULT 12 | Policy duration |
| budget_min | DECIMAL(15,2) | NULL | Budget minimum |
| budget_max | DECIMAL(15,2) | NULL | Budget maximum |
| submission_date | TIMESTAMP | NULL | Submission time |
| review_start_date | TIMESTAMP | NULL | Review start |
| approval_date | TIMESTAMP | NULL | Approval time |
| submitted_by | INT | FK → users | Submitter |
| reviewed_by | INT | FK → users | Reviewer |

---

## 5. Quotes

### quotes
Generated insurance quotes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| quote_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| quote_number | VARCHAR(100) | UNIQUE, NOT NULL | Reference number |
| application_id | INT | FK → insurance_applications | Source application |
| customer_id | INT | FK → customers | Customer |
| insurance_type_id | INT | FK → insurance_types | Insurance type |
| insurance_company_id | INT | FK → insurance_companies | Provider |
| status | ENUM | DEFAULT 'GENERATED' | GENERATED, SENT, ACCEPTED, REJECTED, EXPIRED |
| base_premium | DECIMAL(15,2) | NOT NULL | Base premium |
| risk_adjustment_percentage | DECIMAL(5,2) | DEFAULT 0.00 | Risk adjustment % |
| adjusted_premium | DECIMAL(15,2) | NOT NULL | After risk adjustment |
| fleet_discount_percentage | DECIMAL(5,2) | DEFAULT 0.00 | Fleet discount % |
| fleet_discount_amount | DECIMAL(15,2) | DEFAULT 0.00 | Fleet discount ₹ |
| final_premium | DECIMAL(15,2) | NOT NULL | After discounts |
| gst_amount | DECIMAL(15,2) | NOT NULL | GST |
| total_premium_with_gst | DECIMAL(15,2) | NOT NULL | Grand total |
| sum_insured | DECIMAL(15,2) | NOT NULL | Coverage amount |
| overall_score | DECIMAL(5,2) | DEFAULT 0.00 | Suitability score |
| validity_days | INT | DEFAULT 30 | Valid for days |
| expiry_at | TIMESTAMP | NOT NULL | Expiry timestamp |
| generated_by | INT | FK → users | Generator |
| accepted_at | TIMESTAMP | NULL | Acceptance time |

---

## 6. Policies & Payments

### policies
Issued insurance policies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| policy_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| policy_number | VARCHAR(100) | UNIQUE, NOT NULL | Policy reference |
| quote_id | INT | FK → quotes, UNIQUE | Source quote (1:1) |
| customer_id | INT | FK → customers | Policy holder |
| insurance_type_id | INT | FK → insurance_types | Insurance type |
| insurance_company_id | INT | FK → insurance_companies | Provider |
| status | ENUM | DEFAULT 'ACTIVE' | ACTIVE, INACTIVE, EXPIRED, CANCELLED |
| policy_start_date | DATE | NOT NULL | Start date |
| policy_end_date | DATE | NOT NULL | End date |
| policy_tenure_months | INT | NOT NULL | Duration |
| premium_amount | DECIMAL(15,2) | NOT NULL | Premium |
| gst_amount | DECIMAL(15,2) | NOT NULL | GST |
| total_premium_with_gst | DECIMAL(15,2) | NOT NULL | Total |
| sum_insured | DECIMAL(15,2) | NOT NULL | Coverage |
| issued_at | TIMESTAMP | NULL | Issue time |
| issued_by | INT | FK → users | Issuer |

### payments
Payment records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| payment_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| payment_number | VARCHAR(100) | UNIQUE, NOT NULL | Payment reference |
| quote_id | INT | FK → quotes | Quote being paid |
| policy_id | INT | FK → policies, NULL | Resulting policy |
| customer_id | INT | FK → customers | Payer |
| payment_amount | DECIMAL(15,2) | NOT NULL | Amount |
| payment_method | VARCHAR(20) | DEFAULT 'RAZORPAY' | Method |
| status | ENUM | DEFAULT 'PENDING' | PENDING, INITIATED, SUCCESS, FAILED |
| razorpay_order_id | VARCHAR(100) | UNIQUE | Razorpay order |
| razorpay_payment_id | VARCHAR(100) | NULL | Razorpay payment |
| razorpay_signature | VARCHAR(255) | NULL | Signature for verification |
| gateway_response | JSON | NULL | Full response |
| failure_reason | TEXT | NULL | Failure details |
| payment_date | TIMESTAMP | NULL | Payment completion |

---

## 7. Claims

### claims
Insurance claims.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| claim_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| claim_number | VARCHAR(100) | UNIQUE, NOT NULL | Claim reference |
| policy_id | INT | FK → policies | Claimed policy |
| customer_id | INT | FK → customers | Claimant |
| claim_type | ENUM | NOT NULL | ACCIDENT, THEFT, MEDICAL, etc. |
| claim_description | TEXT | NOT NULL | Incident details |
| incident_date | DATE | NOT NULL | When incident occurred |
| incident_location | TEXT | NULL | Where incident occurred |
| amount_requested | DECIMAL(15,2) | NOT NULL | Claimed amount |
| amount_approved | DECIMAL(15,2) | NULL | Approved amount |
| amount_settled | DECIMAL(15,2) | NULL | Paid amount |
| status | ENUM | DEFAULT 'SUBMITTED' | Status workflow |
| rejection_reason | TEXT | NULL | Rejection reason |
| submitted_at | TIMESTAMP | DEFAULT NOW | Submission time |
| review_started_at | TIMESTAMP | NULL | Review start |
| approved_at | TIMESTAMP | NULL | Approval time |
| settled_at | TIMESTAMP | NULL | Settlement time |
| closed_at | TIMESTAMP | NULL | Closure time |
| reviewed_by | INT | FK → users | Reviewer |
| settled_by | INT | FK → users | Settler |

---

## 8. Configuration Tables

### business_configuration
System-wide settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| config_id | INT | PK, AUTO_INCREMENT | Unique identifier |
| config_key | VARCHAR(255) | UNIQUE, NOT NULL | Setting key |
| config_value | TEXT | NOT NULL | Setting value |
| config_type | ENUM | DEFAULT 'GENERAL' | Category |
| config_description | TEXT | NULL | Description |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |

**Default configurations:**
- `GST_RATE`: 18 (Tax percentage)
- `QUOTE_VALIDITY_DAYS`: 30
- `CLAIM_SLA_DAYS`: 15
- `ACCOUNT_LOCK_THRESHOLD`: 5
