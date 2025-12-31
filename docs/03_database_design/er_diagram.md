# Entity-Relationship Diagram

## Complete ER Diagram

The following diagram represents the complete database schema of the Insurance Policy Management System.

---

## 1. High-Level Entity Relationship Overview
0.
```mermaid
erDiagram
    %% IAM MODULE
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    ROLES ||--o{ ROLE_PERMISSIONS : has
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : granted
    USERS ||--o{ AUDIT_LOGS : generates

    %% CUSTOMER MODULE
    USERS ||--|| CUSTOMERS : profile
    CUSTOMERS ||--|| MEDICAL_DISCLOSURE : has
    CUSTOMERS ||--|| DRIVING_HISTORY : has
    CUSTOMERS ||--o{ CLAIM_HISTORY : has
    CUSTOMERS ||--|| RISK_PROFILE : has
    CUSTOMERS ||--o{ FLEETS : owns
    FLEETS ||--o{ FLEET_VEHICLES : contains

    %% APPLICATION MODULE
    CUSTOMERS ||--o{ APPLICATIONS : submits
    APPLICATIONS ||--o{ APP_DOCUMENTS : includes

    %% QUOTE MODULE
    APPLICATIONS ||--o{ QUOTES : generates
    QUOTES ||--o{ QUOTE_COVERAGES : includes
    QUOTES ||--o{ QUOTE_ADDONS : includes
    QUOTES ||--|| QUOTE_RECOMMENDATIONS : has

    %% POLICY MODULE
    QUOTES ||--|| POLICIES : converts_to
    POLICIES ||--o{ PAYMENTS : requires
    PAYMENTS ||--|| INVOICES : generates

    %% CLAIMS MODULE
    POLICIES ||--o{ CLAIMS : against
    CLAIMS ||--o{ CLAIM_DOCS : includes
    CLAIMS ||--o{ CLAIM_STATUS : history
    CLAIMS ||--|| CLAIM_ASSESSMENT : evaluation
    CLAIMS ||--|| CLAIM_SETTLEMENT : result

    %% CATALOG MODULE
    INSURANCE_TYPES ||--o{ APPLICATIONS : defined_by
    INSURANCE_COMPANIES ||--o{ QUOTES : provided_by
    INSURANCE_TYPES ||--o{ COVERAGE_TYPES : has
    INSURANCE_TYPES ||--o{ RIDER_ADDONS : has
    INSURANCE_TYPES ||--o{ PREMIUM_SLABS : uses
    INSURANCE_TYPES ||--o{ DISCOUNT_RULES : uses
```

---

## 2. Detailed ER Diagram (Mermaid Syntax)

```mermaid
erDiagram
    %% IAM MODULE
    users {
        int user_id PK
        varchar email UK
        varchar username UK
        varchar password_hash
        varchar first_name
        varchar last_name
        varchar phone_number
        boolean is_active
        int failed_login_attempts
        timestamp account_locked_until
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }
    
    roles {
        int role_id PK
        varchar role_name UK
        text role_description
        boolean is_system_role
        timestamp created_at
    }
    
    user_roles {
        int user_role_id PK
        int user_id FK
        int role_id FK
        timestamp assigned_at
        int assigned_by FK
    }
    
    permissions {
        int permission_id PK
        varchar permission_code UK
        varchar permission_description
        varchar resource_name
        varchar action_name
    }
    
    role_permissions {
        int role_permission_id PK
        int role_id FK
        int permission_id FK
        timestamp granted_at
    }
    
    audit_logs {
        bigint audit_log_id PK
        int user_id FK
        varchar table_name
        int record_id
        varchar action_type
        text description
        json old_values
        json new_values
        varchar ip_address
        timestamp timestamp
    }
    
    %% CUSTOMER MODULE
    customers {
        int customer_id PK
        int user_id FK
        date date_of_birth
        varchar gender
        varchar marital_status
        varchar pan_number UK
        varchar aadhar_number UK
        text residential_address
        varchar occupation_type
        decimal annual_income
    }
    
    customer_risk_profiles {
        int risk_profile_id PK
        int customer_id FK
        varchar risk_category
        decimal risk_score
        decimal age_risk_factor
        decimal medical_risk_factor
        decimal driving_risk_factor
        decimal claim_history_risk_factor
        decimal overall_risk_percentage
    }
    
    %% APPLICATION MODULE
    insurance_applications {
        int application_id PK
        varchar application_number UK
        int customer_id FK
        int insurance_type_id FK
        varchar status
        json application_data
        decimal requested_coverage_amount
        int policy_tenure_months
        timestamp submission_date
        timestamp approval_date
    }
    
    %% QUOTE MODULE
    quotes {
        int quote_id PK
        varchar quote_number UK
        int application_id FK
        int customer_id FK
        int insurance_company_id FK
        varchar status
        decimal base_premium
        decimal risk_adjustment_percentage
        decimal final_premium
        decimal gst_amount
        decimal total_premium_with_gst
        decimal sum_insured
        decimal overall_score
        timestamp expiry_at
    }
    
    %% POLICY MODULE
    policies {
        int policy_id PK
        varchar policy_number UK
        int quote_id FK
        int customer_id FK
        varchar status
        date policy_start_date
        date policy_end_date
        decimal premium_amount
        decimal total_premium_with_gst
        decimal sum_insured
    }
    
    payments {
        int payment_id PK
        varchar payment_number UK
        int quote_id FK
        int policy_id FK
        decimal payment_amount
        varchar payment_method
        varchar status
        varchar razorpay_order_id UK
        varchar razorpay_payment_id
        varchar razorpay_signature
        timestamp payment_date
    }
    
    %% CLAIMS MODULE
    claims {
        int claim_id PK
        varchar claim_number UK
        int policy_id FK
        int customer_id FK
        varchar claim_type
        text claim_description
        date incident_date
        decimal amount_requested
        decimal amount_approved
        decimal amount_settled
        varchar status
        timestamp submitted_at
        timestamp approved_at
        timestamp settled_at
    }
    
    %% CATALOG MODULE
    insurance_types {
        int insurance_type_id PK
        varchar type_name UK
        varchar type_code UK
        text description
        boolean is_active
    }
    
    insurance_companies {
        int company_id PK
        varchar company_name UK
        varchar company_code UK
        decimal claim_settlement_ratio
        decimal service_rating
        boolean is_active
    }
    
    coverage_types {
        int coverage_type_id PK
        varchar coverage_name
        varchar coverage_code
        int insurance_type_id FK
        boolean is_mandatory
        decimal base_premium_per_unit
    }
    
    discount_rules {
        int discount_rule_id PK
        varchar rule_name
        varchar rule_code UK
        int insurance_type_id FK
        json rule_condition
        decimal discount_percentage
        decimal discount_max_amount
        boolean is_combinable
        boolean is_active
    }
    
    %% RELATIONSHIPS
    users ||--o{ user_roles : "has"
    roles ||--o{ user_roles : "assigned_to"
    roles ||--o{ role_permissions : "has"
    permissions ||--o{ role_permissions : "granted_to"
    users ||--o| customers : "has_profile"
    users ||--o{ audit_logs : "performs"
    
    customers ||--o{ insurance_applications : "submits"
    customers ||--o| customer_risk_profiles : "has"
    customers ||--o{ quotes : "receives"
    customers ||--o{ policies : "owns"
    customers ||--o{ claims : "files"
    
    insurance_types ||--o{ insurance_applications : "type_of"
    insurance_types ||--o{ coverage_types : "has"
    insurance_types ||--o{ discount_rules : "applies_to"
    
    insurance_applications ||--o{ quotes : "generates"
    
    insurance_companies ||--o{ quotes : "provides"
    
    quotes ||--o| policies : "converts_to"
    quotes ||--o{ payments : "paid_by"
    
    policies ||--o{ claims : "claimed_against"
    policies ||--o{ payments : "has"
    
    claims ||--o{ claim_documents : "has"
    claims ||--o{ claim_status_history : "tracks"
    claims ||--o| claim_settlement : "settles_to"
```

---

## 3. Junction Tables (Many-to-Many Relationships)

### 3.1 user_roles
Links Users ↔ Roles (M:N)

```mermaid
erDiagram
    user_roles {
        int user_role_id PK
        int user_id FK
        int role_id FK
        int assigned_by FK
        unique user_id_role_id
    }
```

### 3.2 role_permissions
Links Roles ↔ Permissions (M:N)

```mermaid
erDiagram
    role_permissions {
        int role_permission_id PK
        int role_id FK
        int permission_id FK
        unique role_id_permission_id
    }
```

### 3.3 quote_coverage_selection
Links Quotes ↔ CoverageTypes (M:N)

```mermaid
erDiagram
    quote_coverage_selection {
        int coverage_selection_id PK
        int quote_id FK
        int coverage_type_id FK
        decimal coverage_limit
        decimal coverage_premium
        unique quote_id_coverage_type_id
    }
```

---

## 4. Cardinality Summary

| Relationship | Type | Description |
|-------------|------|-------------|
| User → CustomerProfile | 1:1 | Each user has at most one customer profile |
| User → UserRoles | 1:M | Users can have multiple roles |
| Role → UserRoles | 1:M | Roles can be assigned to multiple users |
| Customer → Applications | 1:M | Customers can submit many applications |
| Application → Quotes | 1:M | Applications generate multiple quotes |
| Quote → Policy | 1:1 | One accepted quote becomes one policy |
| Policy → Claims | 1:M | Policies can have multiple claims |
| Claim → Settlement | 1:1 | Each claim has one settlement record |
| InsuranceType → CoverageTypes | 1:M | Types have multiple coverage options |

---

## 5. Key Foreign Key Relationships

### Cascading Deletes
- `UserRoles` → CASCADE from User (user deletion removes roles)
- `InsuranceApplication` → CASCADE from Customer
- `Quote` → CASCADE from Application
- `ClaimDocument` → CASCADE from Claim

### Restrict Deletes
- `Policy` → RESTRICT from Quote (cannot delete quoted data)
- `Claim` → RESTRICT from Policy (cannot delete claimed policy)
- `CoverageType` → RESTRICT from InsuranceType

### Set Null
- `submitted_by`, `reviewed_by` → SET NULL (preserve records if user deleted)
