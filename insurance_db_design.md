# Intelligent Insurance Policy Management & Decision Support System
## BCNF-Normalized MySQL Database Design

**Version:** 1.0  
**Date:** December 2025  
**Normalization Level:** BCNF (Boyce-Codd Normal Form)  
**Database:** MySQL 8.0+

---

## Table of Contents
1. [Database Overview](#overview)
2. [Design Principles](#principles)
3. [Entity Relationship Diagram (ERD)](#erd)
4. [Core Tables](#tables)
5. [Implementation Notes](#notes)

---

## Database Overview {#overview}

This database supports an enterprise-grade insurance policy management system with:
- **14 Functional Modules** (Identity & Access, Product Catalog, Risk Assessment, Fleet Management, etc.)
- **BCNF Normalization** ensuring no functional dependency anomalies
- **Audit-Ready Logging** for compliance and security
- **State Machine Workflows** for claims processing
- **Role-Based Access Control (RBAC)** with granular permissions
- **Scalable Master Data Management** configuration tables

### Key Features
- **Immutable Audit Trails** for all critical operations
- **Temporal Tracking** for policy versions, claim status changes
- **Extensible Configuration** via master tables (no hardcoding)
- **Multi-Currency & Regional Support** for future expansion
- **Claim State Machine** with workflow enforcement
- **Fleet-Based Discount Logic** with business rule engine

---

## Design Principles {#principles}

### 1. BCNF Normalization
- **Every determinant is a candidate key** in its table
- **No partial or transitive dependencies** on non-prime attributes
- **Functional dependency X → Y implies X is a superkey**
- **Separate tables for independent concepts** (avoiding many-to-many issues in denormalization)

### 2. Audit & Security
- **All user actions logged** with timestamp, user_id, role, action, table_name, old_values, new_values
- **Immutable audit trails** (append-only)
- **Session tracking** for login/logout, account lockout on failures
- **IP address, browser tracking** for anomaly detection

### 3. Temporal Data
- **created_at, updated_at** on all transactional tables
- **created_by, updated_by** linking to users
- **Status workflow timestamps** for claims (submitted_at, reviewed_at, approved_at, settled_at)

### 4. Configuration-Driven
- **No hardcoded business logic** in database
- **Configuration tables** for discount rules, claim thresholds, weights
- **Master data tables** for insurance companies, coverage types, add-ons

### 5. Foreign Key Constraints
- **All FK relationships** explicitly enforced
- **ON DELETE RESTRICT** for immutability where needed
- **ON UPDATE CASCADE** for reference updates
- **Referential integrity** enforced at database level

---

## Core Tables (14 Modules) {#tables}

### Module 1: Identity & Access Control (IAM)

#### users
```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    last_login_at TIMESTAMP NULL,
    last_password_change_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
);
```

#### roles
```sql
CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    role_description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_role_name (role_name)
);

INSERT INTO roles (role_name, role_description, is_system_role) VALUES
('ADMIN', 'System Administrator - Full Access', TRUE),
('BACKOFFICE_OFFICER', 'Backoffice Staff - Policy & Claim Processing', TRUE),
('CUSTOMER', 'End User - Personal Dashboard Access', TRUE),
('SURVEYOR', 'Surveyor - Claim Assessment', TRUE),
('FINANCE_OFFICER', 'Finance - Payment & Settlement', TRUE);
```

#### user_roles (junction table for many-to-many)
```sql
CREATE TABLE user_roles (
    user_role_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_user_role (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
);
```

#### permissions
```sql
CREATE TABLE permissions (
    permission_id INT PRIMARY KEY AUTO_INCREMENT,
    permission_code VARCHAR(100) UNIQUE NOT NULL,
    permission_description VARCHAR(255),
    resource_name VARCHAR(100),
    action_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_permission_code (permission_code),
    INDEX idx_resource_action (resource_name, action_name)
);

-- Example permissions
INSERT INTO permissions (permission_code, permission_description, resource_name, action_name) VALUES
('POLICY_CREATE', 'Create new policy', 'POLICY', 'CREATE'),
('POLICY_VIEW', 'View policy details', 'POLICY', 'READ'),
('POLICY_EDIT', 'Edit policy', 'POLICY', 'UPDATE'),
('CLAIM_SUBMIT', 'Submit claim', 'CLAIM', 'CREATE'),
('CLAIM_REVIEW', 'Review and approve/reject claims', 'CLAIM', 'UPDATE'),
('USER_MANAGE', 'Manage users and roles', 'USER', 'MANAGE'),
('REPORT_VIEW', 'Access analytics reports', 'REPORT', 'READ'),
('AUDIT_VIEW', 'View audit logs', 'AUDIT', 'READ');
```

#### role_permissions (junction table)
```sql
CREATE TABLE role_permissions (
    role_permission_id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE,
    UNIQUE KEY unique_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id)
);
```

#### user_sessions
```sql
CREATE TABLE user_sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP NULL,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id_active (user_id, is_active),
    INDEX idx_session_token (session_token),
    INDEX idx_expires_at (expires_at)
);
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    audit_log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    user_role_id INT,
    table_name VARCHAR(100) NOT NULL,
    record_id INT,
    action_type ENUM('INSERT', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PERMISSION_DENIED') NOT NULL,
    description TEXT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (user_role_id) REFERENCES user_roles(user_role_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_table_name (table_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action_type (action_type),
    INDEX idx_record_lookup (table_name, record_id)
);
```

---

### Module 2: Insurance Product & Policy Catalog

#### insurance_companies
```sql
CREATE TABLE insurance_companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(255) UNIQUE NOT NULL,
    company_code VARCHAR(50) UNIQUE NOT NULL,
    registration_number VARCHAR(100),
    headquarters_address TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(15),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_code (company_code),
    INDEX idx_is_active (is_active)
);
```

#### insurance_types
```sql
CREATE TABLE insurance_types (
    insurance_type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(100) UNIQUE NOT NULL,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type_code (type_code)
);

INSERT INTO insurance_types (type_name, type_code, description) VALUES
('Motor Insurance', 'MOTOR', 'Vehicle/Auto Insurance'),
('Health Insurance', 'HEALTH', 'Medical and Health Coverage'),
('Travel Insurance', 'TRAVEL', 'Travel and Trip Insurance'),
('Workers Compensation', 'WC', 'Employee Injury/Compensation'),
('Commercial Property Management', 'CPM', 'Business Property Insurance');
```

#### coverage_types
```sql
CREATE TABLE coverage_types (
    coverage_type_id INT PRIMARY KEY AUTO_INCREMENT,
    coverage_name VARCHAR(255) NOT NULL,
    coverage_code VARCHAR(50) NOT NULL,
    insurance_type_id INT NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    base_premium_per_unit DECIMAL(12, 2),
    unit_of_measurement VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_coverage (insurance_type_id, coverage_code),
    INDEX idx_insurance_type_id (insurance_type_id),
    INDEX idx_coverage_code (coverage_code)
);

-- Example: Motor Insurance - Third Party Liability
INSERT INTO coverage_types (coverage_name, coverage_code, insurance_type_id, description, is_mandatory, base_premium_per_unit) 
VALUES ('Third Party Liability', 'TP_LIABILITY', 1, 'Third party bodily injury and property damage', TRUE, 500.00);
```

#### riders_addons
```sql
CREATE TABLE riders_addons (
    addon_id INT PRIMARY KEY AUTO_INCREMENT,
    addon_name VARCHAR(255) NOT NULL,
    addon_code VARCHAR(50) NOT NULL,
    insurance_type_id INT NOT NULL,
    description TEXT,
    premium_percentage DECIMAL(5, 2),
    is_optional BOOLEAN DEFAULT TRUE,
    max_coverage_limit DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_addon (insurance_type_id, addon_code),
    INDEX idx_insurance_type_id (insurance_type_id)
);

-- Example: Motor - Accidental Damage Waiver
INSERT INTO riders_addons (addon_name, addon_code, insurance_type_id, description, premium_percentage, is_optional, max_coverage_limit)
VALUES ('Accidental Damage Waiver', 'ADW', 1, 'Waiver of deductible for accidental damage', 5.00, TRUE, 500000.00);
```

#### policy_eligibility_rules
```sql
CREATE TABLE policy_eligibility_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_type_id INT NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_condition JSON NOT NULL,
    rule_priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    INDEX idx_insurance_type_id (insurance_type_id),
    INDEX idx_is_active (is_active)
);

-- Example condition (JSON): {"min_age": 18, "max_age": 75, "min_driving_exp": 2}
```

#### premium_slabs
```sql
CREATE TABLE premium_slabs (
    slab_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_type_id INT NOT NULL,
    slab_name VARCHAR(255) NOT NULL,
    min_coverage_amount DECIMAL(15, 2),
    max_coverage_amount DECIMAL(15, 2),
    base_premium DECIMAL(12, 2) NOT NULL,
    percentage_markup DECIMAL(5, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    UNIQUE KEY unique_slab (insurance_type_id, min_coverage_amount, max_coverage_amount),
    INDEX idx_insurance_type_id (insurance_type_id)
);
```

---

### Module 3: Customer Profiling & Risk Assessment

#### customers
```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    gender ENUM('MALE', 'FEMALE', 'OTHER'),
    marital_status VARCHAR(50),
    nationality VARCHAR(100),
    pan_number VARCHAR(50) UNIQUE,
    aadhar_number VARCHAR(50) UNIQUE,
    residential_address TEXT NOT NULL,
    residential_city VARCHAR(100),
    residential_state VARCHAR(100),
    residential_country VARCHAR(100),
    residential_pincode VARCHAR(10),
    professional_address TEXT,
    occupation_type VARCHAR(100),
    annual_income DECIMAL(15, 2),
    employment_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_pan_number (pan_number),
    INDEX idx_aadhar_number (aadhar_number)
);
```

#### customer_medical_disclosures
```sql
CREATE TABLE customer_medical_disclosures (
    disclosure_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    disclosure_date DATE NOT NULL,
    medical_condition VARCHAR(255),
    diagnosis_date DATE,
    is_chronic BOOLEAN,
    medication_list TEXT,
    hospital_visits_last_year INT,
    is_disclosed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_disclosure_date (disclosure_date)
);
```

#### customer_driving_history
```sql
CREATE TABLE customer_driving_history (
    driving_history_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    license_number VARCHAR(100),
    license_issue_date DATE,
    license_expiry_date DATE,
    license_status VARCHAR(50),
    total_years_experience INT,
    violations_count INT DEFAULT 0,
    accidents_count INT DEFAULT 0,
    suspension_status VARCHAR(50),
    last_updated DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    UNIQUE KEY unique_license (license_number),
    INDEX idx_customer_id (customer_id)
);
```

#### claim_history
```sql
CREATE TABLE claim_history (
    claim_history_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    claim_year YEAR,
    claim_count INT DEFAULT 0,
    claim_amount_total DECIMAL(15, 2),
    claim_approved_amount DECIMAL(15, 2),
    claim_rejection_rate DECIMAL(5, 2),
    last_claim_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    UNIQUE KEY unique_customer_year (customer_id, claim_year),
    INDEX idx_customer_id (customer_id),
    INDEX idx_claim_year (claim_year)
);
```

#### customer_risk_profiles
```sql
CREATE TABLE customer_risk_profiles (
    risk_profile_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL UNIQUE,
    risk_category ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    risk_score DECIMAL(5, 2),
    age_risk_factor DECIMAL(5, 2),
    medical_risk_factor DECIMAL(5, 2),
    driving_risk_factor DECIMAL(5, 2),
    claim_history_risk_factor DECIMAL(5, 2),
    employment_risk_factor DECIMAL(5, 2),
    overall_risk_percentage DECIMAL(5, 2),
    calculated_at TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_risk_category (risk_category),
    INDEX idx_valid_until (valid_until)
);
```

---

### Module 4: Fleet Management & Discount Engine

#### fleets
```sql
CREATE TABLE fleets (
    fleet_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    fleet_name VARCHAR(255) NOT NULL,
    fleet_code VARCHAR(100),
    fleet_type VARCHAR(100),
    total_vehicles INT,
    fleet_ownership_date DATE,
    fleet_purpose VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_customer_id (customer_id),
    INDEX idx_fleet_code (fleet_code),
    INDEX idx_is_active (is_active)
);
```

#### fleet_vehicles
```sql
CREATE TABLE fleet_vehicles (
    fleet_vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    fleet_id INT NOT NULL,
    vehicle_registration_number VARCHAR(50) UNIQUE NOT NULL,
    vehicle_make VARCHAR(100),
    vehicle_model VARCHAR(100),
    vehicle_year INT,
    vehicle_engine_number VARCHAR(100),
    vehicle_chassis_number VARCHAR(100),
    vehicle_type VARCHAR(50),
    vehicle_fuel_type VARCHAR(50),
    vehicle_seating_capacity INT,
    vehicle_current_value DECIMAL(15, 2),
    vehicle_status VARCHAR(50),
    added_at DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fleet_id) REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    UNIQUE KEY unique_registration (vehicle_registration_number),
    INDEX idx_fleet_id (fleet_id),
    INDEX idx_vehicle_status (vehicle_status)
);
```

#### fleet_claim_history
```sql
CREATE TABLE fleet_claim_history (
    fleet_claim_id INT PRIMARY KEY AUTO_INCREMENT,
    fleet_id INT NOT NULL,
    claim_year YEAR,
    total_claims INT DEFAULT 0,
    total_claim_amount DECIMAL(15, 2),
    approved_claim_amount DECIMAL(15, 2),
    claim_ratio DECIMAL(5, 4),
    settled_claims INT DEFAULT 0,
    rejected_claims INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fleet_id) REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    UNIQUE KEY unique_fleet_year (fleet_id, claim_year),
    INDEX idx_fleet_id (fleet_id),
    INDEX idx_claim_year (claim_year)
);
```

#### fleet_risk_scores
```sql
CREATE TABLE fleet_risk_scores (
    fleet_risk_id INT PRIMARY KEY AUTO_INCREMENT,
    fleet_id INT NOT NULL UNIQUE,
    fleet_risk_score DECIMAL(5, 2),
    vehicle_count_factor DECIMAL(5, 2),
    claim_ratio_factor DECIMAL(5, 2),
    vehicle_age_factor DECIMAL(5, 2),
    driver_safety_factor DECIMAL(5, 2),
    fleet_risk_category ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    discount_percentage DECIMAL(5, 2),
    calculated_at TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fleet_id) REFERENCES fleets(fleet_id) ON DELETE CASCADE,
    INDEX idx_fleet_id (fleet_id),
    INDEX idx_discount_percentage (discount_percentage)
);
```

---

### Module 5: Insurance Application & Data Capture

#### insurance_applications
```sql
CREATE TABLE insurance_applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    insurance_type_id INT NOT NULL,
    application_number VARCHAR(100) UNIQUE NOT NULL,
    application_status ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'APPROVED_WITH_CONDITIONS') NOT NULL,
    submission_date TIMESTAMP,
    review_start_date TIMESTAMP NULL,
    approval_date TIMESTAMP NULL,
    rejection_reason TEXT,
    data_completeness_score DECIMAL(5, 2),
    submitted_by INT,
    reviewed_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (submitted_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_application_number (application_number),
    INDEX idx_customer_id (customer_id),
    INDEX idx_insurance_type_id (insurance_type_id),
    INDEX idx_application_status (application_status),
    INDEX idx_submission_date (submission_date)
);
```

#### application_form_data
```sql
CREATE TABLE application_form_data (
    form_data_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_value LONGTEXT,
    field_type VARCHAR(50),
    is_validated BOOLEAN DEFAULT FALSE,
    validation_error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES insurance_applications(application_id) ON DELETE CASCADE,
    UNIQUE KEY unique_form_field (application_id, field_name),
    INDEX idx_application_id (application_id),
    INDEX idx_is_validated (is_validated)
);
```

#### application_documents
```sql
CREATE TABLE application_documents (
    document_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_url VARCHAR(500),
    file_size INT,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INT,
    verification_status ENUM('PENDING', 'VERIFIED', 'REJECTED') DEFAULT 'PENDING',
    verification_notes TEXT,
    verified_by INT,
    verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES insurance_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_application_id (application_id),
    INDEX idx_document_type (document_type),
    INDEX idx_verification_status (verification_status)
);
```

#### application_validation_rules
```sql
CREATE TABLE application_validation_rules (
    validation_rule_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_type_id INT NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    validation_rule JSON NOT NULL,
    required_documents JSON,
    rule_priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    UNIQUE KEY unique_type_field (insurance_type_id, field_name),
    INDEX idx_insurance_type_id (insurance_type_id)
);

-- Example: Motor Insurance requires RC, DL, PYP (Previous Year Policy)
```

---

### Module 6: Intelligent Quote Comparison & Decision Engine

#### quotes
```sql
CREATE TABLE quotes (
    quote_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT NOT NULL,
    customer_id INT NOT NULL,
    insurance_type_id INT NOT NULL,
    quote_number VARCHAR(100) UNIQUE NOT NULL,
    quote_status ENUM('GENERATED', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED') DEFAULT 'GENERATED',
    base_premium DECIMAL(15, 2) NOT NULL,
    risk_adjustment_percentage DECIMAL(5, 2),
    adjusted_premium DECIMAL(15, 2),
    fleet_discount_percentage DECIMAL(5, 2),
    fleet_discount_amount DECIMAL(15, 2),
    loyalty_discount_percentage DECIMAL(5, 2),
    loyalty_discount_amount DECIMAL(15, 2),
    other_discounts_amount DECIMAL(15, 2),
    final_premium DECIMAL(15, 2) NOT NULL,
    gst_amount DECIMAL(15, 2),
    total_premium_with_gst DECIMAL(15, 2) NOT NULL,
    quote_validity_days INT DEFAULT 30,
    quote_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quote_expiry_at TIMESTAMP,
    quote_generated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES insurance_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (quote_generated_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_quote_number (quote_number),
    INDEX idx_application_id (application_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_quote_status (quote_status),
    INDEX idx_quote_expiry_at (quote_expiry_at)
);
```

#### quote_scoring_details
```sql
CREATE TABLE quote_scoring_details (
    scoring_detail_id INT PRIMARY KEY AUTO_INCREMENT,
    quote_id INT NOT NULL,
    scoring_factor VARCHAR(255) NOT NULL,
    factor_value DECIMAL(10, 4),
    factor_weight DECIMAL(5, 2),
    factor_score DECIMAL(10, 4),
    factor_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE CASCADE,
    INDEX idx_quote_id (quote_id),
    INDEX idx_scoring_factor (scoring_factor)
);
```

#### quote_coverage_selection
```sql
CREATE TABLE quote_coverage_selection (
    coverage_selection_id INT PRIMARY KEY AUTO_INCREMENT,
    quote_id INT NOT NULL,
    coverage_type_id INT NOT NULL,
    coverage_limit DECIMAL(15, 2),
    coverage_premium DECIMAL(12, 2),
    is_selected BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE CASCADE,
    FOREIGN KEY (coverage_type_id) REFERENCES coverage_types(coverage_type_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_quote_coverage (quote_id, coverage_type_id),
    INDEX idx_quote_id (quote_id)
);
```

#### quote_addon_selection
```sql
CREATE TABLE quote_addon_selection (
    addon_selection_id INT PRIMARY KEY AUTO_INCREMENT,
    quote_id INT NOT NULL,
    addon_id INT NOT NULL,
    addon_premium DECIMAL(12, 2),
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id) REFERENCES riders_addons(addon_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_quote_addon (quote_id, addon_id),
    INDEX idx_quote_id (quote_id)
);
```

#### quote_recommendations
```sql
CREATE TABLE quote_recommendations (
    recommendation_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT NOT NULL,
    customer_id INT NOT NULL,
    insurance_type_id INT NOT NULL,
    recommendation_rank INT,
    recommended_quote_id INT,
    recommendation_reason TEXT,
    suitability_score DECIMAL(5, 2),
    budget_match_percentage DECIMAL(5, 2),
    coverage_match_percentage DECIMAL(5, 2),
    value_for_money_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES insurance_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (recommended_quote_id) REFERENCES quotes(quote_id) ON DELETE SET NULL,
    INDEX idx_application_id (application_id),
    INDEX idx_recommendation_rank (recommendation_rank)
);
```

---

### Module 7: Policy Issuance & Payment Processing

#### policies
```sql
CREATE TABLE policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_number VARCHAR(100) UNIQUE NOT NULL,
    quote_id INT NOT NULL,
    customer_id INT NOT NULL,
    insurance_type_id INT NOT NULL,
    insurance_company_id INT NOT NULL,
    policy_status ENUM('ACTIVE', 'INACTIVE', 'EXPIRED', 'CANCELLED', 'LAPSED') DEFAULT 'ACTIVE',
    policy_start_date DATE NOT NULL,
    policy_end_date DATE NOT NULL,
    policy_tenure_months INT,
    premium_amount DECIMAL(15, 2) NOT NULL,
    gst_amount DECIMAL(15, 2),
    total_premium_with_gst DECIMAL(15, 2) NOT NULL,
    sum_insured DECIMAL(15, 2),
    policy_version INT DEFAULT 1,
    issued_at TIMESTAMP,
    issued_by INT,
    last_renewal_date DATE,
    next_renewal_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE RESTRICT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE RESTRICT,
    FOREIGN KEY (issued_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_policy_number (policy_number),
    INDEX idx_customer_id (customer_id),
    INDEX idx_policy_status (policy_status),
    INDEX idx_policy_start_date (policy_start_date),
    INDEX idx_policy_end_date (policy_end_date),
    INDEX idx_next_renewal_date (next_renewal_date)
);
```

#### policy_coverage
```sql
CREATE TABLE policy_coverage (
    policy_coverage_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    coverage_type_id INT NOT NULL,
    coverage_limit DECIMAL(15, 2),
    coverage_premium DECIMAL(12, 2),
    deductible_amount DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (coverage_type_id) REFERENCES coverage_types(coverage_type_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_policy_coverage (policy_id, coverage_type_id),
    INDEX idx_policy_id (policy_id)
);
```

#### policy_addon
```sql
CREATE TABLE policy_addon (
    policy_addon_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    addon_id INT NOT NULL,
    addon_premium DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id) REFERENCES riders_addons(addon_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_policy_addon (policy_id, addon_id),
    INDEX idx_policy_id (policy_id)
);
```

#### policy_versions
```sql
CREATE TABLE policy_versions (
    policy_version_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    version_number INT NOT NULL,
    version_reason VARCHAR(255),
    old_premium DECIMAL(15, 2),
    new_premium DECIMAL(15, 2),
    version_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version_created_by INT,
    is_current BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (version_created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_policy_version (policy_id, version_number),
    INDEX idx_policy_id (policy_id),
    INDEX idx_is_current (is_current)
);
```

#### payments
```sql
CREATE TABLE payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    customer_id INT NOT NULL,
    payment_number VARCHAR(100) UNIQUE NOT NULL,
    payment_amount DECIMAL(15, 2) NOT NULL,
    payment_method ENUM('CREDIT_CARD', 'DEBIT_CARD', 'NET_BANKING', 'UPI', 'CHEQUE', 'BANK_TRANSFER') NOT NULL,
    payment_status ENUM('PENDING', 'INITIATED', 'SUCCESS', 'FAILED', 'CANCELLED', 'REFUNDED') DEFAULT 'PENDING',
    transaction_id VARCHAR(255),
    transaction_reference VARCHAR(255),
    gateway_response JSON,
    payment_date TIMESTAMP,
    retry_count INT DEFAULT 0,
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    UNIQUE KEY unique_payment_number (payment_number),
    INDEX idx_policy_id (policy_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_customer_id (customer_id),
    INDEX idx_payment_date (payment_date)
);
```

#### invoices
```sql
CREATE TABLE invoices (
    invoice_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    payment_id INT,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    invoice_date DATE,
    invoice_amount DECIMAL(15, 2) NOT NULL,
    gst_amount DECIMAL(15, 2),
    total_invoice_amount DECIMAL(15, 2),
    invoice_status ENUM('DRAFT', 'ISSUED', 'PAID', 'CANCELLED') DEFAULT 'DRAFT',
    invoice_url VARCHAR(500),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE CASCADE,
    FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE SET NULL,
    FOREIGN KEY (generated_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_invoice_number (invoice_number),
    INDEX idx_policy_id (policy_id),
    INDEX idx_invoice_status (invoice_status),
    INDEX idx_invoice_date (invoice_date)
);
```

---

### Module 8: Claim Lifecycle & Workflow Management

#### claims
```sql
CREATE TABLE claims (
    claim_id INT PRIMARY KEY AUTO_INCREMENT,
    policy_id INT NOT NULL,
    customer_id INT NOT NULL,
    claim_number VARCHAR(100) UNIQUE NOT NULL,
    claim_incident_date DATE NOT NULL,
    claim_incident_description TEXT NOT NULL,
    claim_reported_date TIMESTAMP,
    claim_status ENUM('SUBMITTED', 'IN_REVIEW', 'SURVEYOR_ASSIGNED', 'UNDER_INVESTIGATION', 'APPROVED', 'REJECTED', 'SETTLED', 'APPEAL_FILED', 'APPEAL_APPROVED', 'APPEAL_REJECTED') DEFAULT 'SUBMITTED',
    claim_amount_requested DECIMAL(15, 2) NOT NULL,
    claim_amount_approved DECIMAL(15, 2),
    claim_amount_settled DECIMAL(15, 2),
    rejection_reason TEXT,
    appeal_reason TEXT,
    reported_by INT NOT NULL,
    assigned_surveyor_id INT,
    assigned_at TIMESTAMP NULL,
    reviewed_by INT,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE RESTRICT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_surveyor_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    UNIQUE KEY unique_claim_number (claim_number),
    INDEX idx_policy_id (policy_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_claim_status (claim_status),
    INDEX idx_claim_reported_date (claim_reported_date),
    INDEX idx_assigned_surveyor_id (assigned_surveyor_id)
);
```

#### claim_status_history
```sql
CREATE TABLE claim_status_history (
    status_history_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_id INT NOT NULL,
    old_status VARCHAR(100),
    new_status VARCHAR(100) NOT NULL,
    status_change_reason TEXT,
    changed_by INT NOT NULL,
    status_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    INDEX idx_claim_id (claim_id),
    INDEX idx_status_changed_at (status_changed_at),
    INDEX idx_new_status (new_status)
);
```

#### claim_documents
```sql
CREATE TABLE claim_documents (
    claim_document_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_id INT NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_url VARCHAR(500),
    file_size INT,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INT NOT NULL,
    verification_status ENUM('PENDING', 'VERIFIED', 'REJECTED') DEFAULT 'PENDING',
    verification_notes TEXT,
    verified_by INT,
    verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_claim_id (claim_id),
    INDEX idx_document_type (document_type),
    INDEX idx_verification_status (verification_status)
);
```

#### claim_assessments
```sql
CREATE TABLE claim_assessments (
    assessment_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_id INT NOT NULL,
    surveyor_id INT NOT NULL,
    assessment_date DATE NOT NULL,
    assessment_report_url VARCHAR(500),
    damage_assessment TEXT,
    loss_amount_assessed DECIMAL(15, 2),
    deductible_applicable DECIMAL(15, 2),
    net_claim_amount DECIMAL(15, 2),
    assessment_status ENUM('PENDING', 'COMPLETED', 'UNDER_REVIEW') DEFAULT 'PENDING',
    assessment_findings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (surveyor_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_claim_assessment (claim_id, surveyor_id),
    INDEX idx_claim_id (claim_id),
    INDEX idx_assessment_status (assessment_status)
);
```

#### claim_settlement
```sql
CREATE TABLE claim_settlement (
    settlement_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_id INT NOT NULL,
    settlement_amount DECIMAL(15, 2) NOT NULL,
    settlement_date DATE,
    settlement_method ENUM('BANK_TRANSFER', 'CHEQUE', 'DIRECT_REPAIR') NOT NULL,
    bank_account_number VARCHAR(100),
    bank_name VARCHAR(100),
    bank_ifsc_code VARCHAR(50),
    settlement_status ENUM('PENDING', 'PROCESSED', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    settlement_reference_number VARCHAR(100),
    settlement_approved_by INT NOT NULL,
    settlement_approved_at TIMESTAMP,
    settlement_processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (settlement_approved_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_settlement_claim (claim_id),
    INDEX idx_claim_id (claim_id),
    INDEX idx_settlement_status (settlement_status)
);
```

---

### Module 9: Notification, Reminder & Communication

#### notifications
```sql
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    recipient_user_id INT NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    notification_title VARCHAR(255) NOT NULL,
    notification_body TEXT NOT NULL,
    related_entity_type VARCHAR(100),
    related_entity_id INT,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_recipient_user_id (recipient_user_id),
    INDEX idx_notification_type (notification_type),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);
```

#### notification_channels
```sql
CREATE TABLE notification_channels (
    channel_id INT PRIMARY KEY AUTO_INCREMENT,
    notification_id INT NOT NULL,
    channel_type ENUM('EMAIL', 'SMS', 'IN_APP', 'PUSH') NOT NULL,
    channel_recipient VARCHAR(255),
    send_status ENUM('PENDING', 'SENT', 'FAILED', 'BOUNCED') DEFAULT 'PENDING',
    sent_at TIMESTAMP NULL,
    failure_reason TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(notification_id) ON DELETE CASCADE,
    INDEX idx_notification_id (notification_id),
    INDEX idx_channel_type (channel_type),
    INDEX idx_send_status (send_status)
);
```

#### notification_templates
```sql
CREATE TABLE notification_templates (
    template_id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(255) NOT NULL,
    template_code VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(100),
    email_subject VARCHAR(255),
    email_body LONGTEXT,
    sms_body VARCHAR(160),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_code (template_code)
);

-- Examples
INSERT INTO notification_templates (template_name, template_code, template_type, email_subject, is_active) VALUES
('Policy Expiry Reminder', 'POLICY_EXPIRY_REMINDER', 'REMINDER', 'Your {{INSURANCE_TYPE}} Policy Expires Soon', TRUE),
('Claim Status Update', 'CLAIM_STATUS_UPDATE', 'ALERT', 'Update on Your Claim #{{CLAIM_NUMBER}}', TRUE),
('Renewal Notification', 'RENEWAL_NOTIFICATION', 'RENEWAL', 'Time to Renew Your {{INSURANCE_TYPE}} Policy', TRUE),
('Payment Pending', 'PAYMENT_PENDING', 'ALERT', 'Complete Your Premium Payment for Policy #{{POLICY_NUMBER}}', TRUE);
```

#### scheduled_reminders
```sql
CREATE TABLE scheduled_reminders (
    reminder_id INT PRIMARY KEY AUTO_INCREMENT,
    reminder_type VARCHAR(100) NOT NULL,
    related_entity_type VARCHAR(100) NOT NULL,
    related_entity_id INT NOT NULL,
    template_id INT NOT NULL,
    recipient_user_id INT,
    reminder_scheduled_for TIMESTAMP NOT NULL,
    reminder_sent_at TIMESTAMP NULL,
    reminder_status ENUM('PENDING', 'SENT', 'CANCELLED') DEFAULT 'PENDING',
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES notification_templates(template_id) ON DELETE RESTRICT,
    FOREIGN KEY (recipient_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_reminder_scheduled_for (reminder_scheduled_for),
    INDEX idx_reminder_status (reminder_status),
    INDEX idx_related_entity (related_entity_type, related_entity_id)
);
```

---

### Module 10: Customer Feedback & Service Quality Analysis

#### customer_feedback
```sql
CREATE TABLE customer_feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    policy_id INT,
    claim_id INT,
    insurance_company_id INT,
    feedback_category VARCHAR(100),
    feedback_title VARCHAR(255),
    feedback_description TEXT NOT NULL,
    rating_overall INT,
    rating_product DECIMAL(3, 1),
    rating_service DECIMAL(3, 1),
    rating_claims_process DECIMAL(3, 1),
    rating_customer_support DECIMAL(3, 1),
    feedback_status ENUM('SUBMITTED', 'REVIEWED', 'RESPONDED', 'CLOSED') DEFAULT 'SUBMITTED',
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_by INT,
    response_message TEXT,
    responded_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE SET NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE SET NULL,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE SET NULL,
    FOREIGN KEY (responded_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_customer_id (customer_id),
    INDEX idx_feedback_status (feedback_status),
    INDEX idx_feedback_date (feedback_date),
    INDEX idx_rating_overall (rating_overall)
);
```

#### feedback_sentiment
```sql
CREATE TABLE feedback_sentiment (
    sentiment_id INT PRIMARY KEY AUTO_INCREMENT,
    feedback_id INT NOT NULL UNIQUE,
    sentiment_score DECIMAL(5, 2),
    sentiment_category ENUM('VERY_NEGATIVE', 'NEGATIVE', 'NEUTRAL', 'POSITIVE', 'VERY_POSITIVE'),
    sentiment_keywords TEXT,
    sentiment_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feedback_id) REFERENCES customer_feedback(feedback_id) ON DELETE CASCADE,
    INDEX idx_feedback_id (feedback_id),
    INDEX idx_sentiment_category (sentiment_category)
);
```

#### service_quality_metrics
```sql
CREATE TABLE service_quality_metrics (
    metric_id INT PRIMARY KEY AUTO_INCREMENT,
    metric_period DATE,
    insurance_company_id INT,
    total_feedbacks INT,
    average_rating DECIMAL(3, 2),
    product_rating DECIMAL(3, 2),
    service_rating DECIMAL(3, 2),
    claims_process_rating DECIMAL(3, 2),
    support_rating DECIMAL(3, 2),
    sentiment_positive_count INT,
    sentiment_negative_count INT,
    sentiment_neutral_count INT,
    customer_satisfaction_percentage DECIMAL(5, 2),
    nps_score DECIMAL(5, 2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE CASCADE,
    UNIQUE KEY unique_metric_period (insurance_company_id, metric_period),
    INDEX idx_metric_period (metric_period)
);
```

---

### Module 11: Analytics, Reporting & Admin Dashboard

#### policy_analytics
```sql
CREATE TABLE policy_analytics (
    analytics_id INT PRIMARY KEY AUTO_INCREMENT,
    report_date DATE,
    insurance_type_id INT NOT NULL,
    insurance_company_id INT,
    total_policies_issued INT,
    total_premium_collected DECIMAL(15, 2),
    average_premium DECIMAL(15, 2),
    total_active_policies INT,
    total_expired_policies INT,
    total_cancelled_policies INT,
    policy_renewal_count INT,
    policy_renewal_rate DECIMAL(5, 2),
    customer_acquisition_count INT,
    customer_retention_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE SET NULL,
    INDEX idx_report_date (report_date),
    INDEX idx_insurance_type_id (insurance_type_id),
    INDEX idx_insurance_company_id (insurance_company_id)
);
```

#### claim_analytics
```sql
CREATE TABLE claim_analytics (
    analytics_id INT PRIMARY KEY AUTO_INCREMENT,
    report_date DATE,
    insurance_type_id INT NOT NULL,
    insurance_company_id INT,
    total_claims_received INT,
    total_claims_approved INT,
    total_claims_rejected INT,
    total_claims_pending INT,
    claims_approval_rate DECIMAL(5, 2),
    claims_rejection_rate DECIMAL(5, 2),
    average_claim_amount DECIMAL(15, 2),
    total_claim_payout DECIMAL(15, 2),
    average_settlement_days INT,
    claims_processed_within_sla INT,
    sla_compliance_percentage DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE SET NULL,
    INDEX idx_report_date (report_date),
    INDEX idx_insurance_type_id (insurance_type_id)
);
```

#### revenue_analytics
```sql
CREATE TABLE revenue_analytics (
    analytics_id INT PRIMARY KEY AUTO_INCREMENT,
    report_period DATE,
    insurance_type_id INT NOT NULL,
    total_premium_revenue DECIMAL(18, 2),
    total_gst_collected DECIMAL(15, 2),
    total_discount_given DECIMAL(15, 2),
    net_revenue DECIMAL(18, 2),
    claim_payouts DECIMAL(18, 2),
    claims_vs_revenue_ratio DECIMAL(5, 4),
    profitability_ratio DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    INDEX idx_report_period (report_period),
    INDEX idx_insurance_type_id (insurance_type_id)
);
```

#### customer_risk_analytics
```sql
CREATE TABLE customer_risk_analytics (
    analytics_id INT PRIMARY KEY AUTO_INCREMENT,
    report_date DATE,
    low_risk_customers INT,
    medium_risk_customers INT,
    high_risk_customers INT,
    critical_risk_customers INT,
    average_risk_score DECIMAL(5, 2),
    high_risk_policy_premium_percentage DECIMAL(5, 2),
    total_high_risk_premium DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_date (report_date)
);
```

---

### Module 12: Policy Renewal Prediction (ML-Based)

#### renewal_predictions
```sql
CREATE TABLE renewal_predictions (
    prediction_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    policy_id INT,
    current_policy_end_date DATE,
    predicted_renewal_probability DECIMAL(5, 2),
    predicted_churn_probability DECIMAL(5, 2),
    churn_risk_category ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    prediction_confidence_score DECIMAL(5, 2),
    contributing_factors JSON,
    recommended_action VARCHAR(255),
    prediction_model_version VARCHAR(50),
    prediction_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prediction_valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE SET NULL,
    INDEX idx_customer_id (customer_id),
    INDEX idx_churn_risk_category (churn_risk_category),
    INDEX idx_prediction_generated_at (prediction_generated_at)
);
```

#### renewal_strategy_recommendations
```sql
CREATE TABLE renewal_strategy_recommendations (
    recommendation_id INT PRIMARY KEY AUTO_INCREMENT,
    prediction_id INT NOT NULL,
    customer_id INT NOT NULL,
    recommendation_type VARCHAR(100),
    recommendation_description TEXT,
    expected_renewal_increase_percentage DECIMAL(5, 2),
    discount_offer_percentage DECIMAL(5, 2),
    retention_priority INT,
    action_owner VARCHAR(100),
    action_deadline DATE,
    is_implemented BOOLEAN DEFAULT FALSE,
    implementation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES renewal_predictions(prediction_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_prediction_id (prediction_id),
    INDEX idx_is_implemented (is_implemented)
);
```

---

### Module 13: System Monitoring & Audit Module

#### system_events
```sql
CREATE TABLE system_events (
    event_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_type VARCHAR(100) NOT NULL,
    event_severity ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
    module_name VARCHAR(100),
    event_description TEXT,
    event_data JSON,
    affected_user_id INT,
    affected_resource_type VARCHAR(100),
    affected_resource_id INT,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (affected_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_event_severity (event_severity),
    INDEX idx_module_name (module_name),
    INDEX idx_event_timestamp (event_timestamp),
    INDEX idx_affected_user_id (affected_user_id)
);
```

#### data_modification_history
```sql
CREATE TABLE data_modification_history (
    modification_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id INT NOT NULL,
    modification_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    modified_by INT,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    column_name VARCHAR(100),
    old_value LONGTEXT,
    new_value LONGTEXT,
    transaction_id VARCHAR(255),
    reason_for_modification VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (modified_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_table_name (table_name),
    INDEX idx_record_id (record_id),
    INDEX idx_modified_by (modified_by),
    INDEX idx_modified_at (modified_at),
    INDEX idx_transaction_id (transaction_id)
);
```

#### compliance_audit_trail
```sql
CREATE TABLE compliance_audit_trail (
    audit_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    audit_type VARCHAR(100) NOT NULL,
    audit_description TEXT,
    audited_entity_type VARCHAR(100),
    audited_entity_id INT,
    compliance_status VARCHAR(100),
    finding_severity ENUM('MINOR', 'MAJOR', 'CRITICAL') DEFAULT 'MINOR',
    audit_performed_by INT NOT NULL,
    audit_date DATE,
    remediation_required BOOLEAN DEFAULT FALSE,
    remediation_deadline DATE,
    remediation_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_performed_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    INDEX idx_audit_type (audit_type),
    INDEX idx_audit_date (audit_date),
    INDEX idx_compliance_status (compliance_status)
);
```

---

### Module 14: Configuration & Master Data Management

#### business_configuration
```sql
CREATE TABLE business_configuration (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value LONGTEXT NOT NULL,
    config_type VARCHAR(100),
    config_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    min_value VARCHAR(255),
    max_value VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT,
    FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_config_key (config_key),
    INDEX idx_config_type (config_type),
    INDEX idx_is_active (is_active)
);

-- Examples
INSERT INTO business_configuration (config_key, config_value, config_type, config_description) VALUES
('QUOTE_VALIDITY_DAYS', '30', 'QUOTE', 'Number of days a quote remains valid'),
('CLAIM_SLA_DAYS', '15', 'CLAIM', 'Service level agreement for claim settlement in days'),
('ACCOUNT_LOCK_THRESHOLD', '5', 'SECURITY', 'Number of failed login attempts before account lock'),
('ACCOUNT_LOCK_DURATION_MINUTES', '30', 'SECURITY', 'Duration account remains locked'),
('PASSWORD_EXPIRY_DAYS', '90', 'SECURITY', 'Number of days before password expires'),
('SESSION_TIMEOUT_MINUTES', '30', 'SECURITY', 'Session inactivity timeout in minutes'),
('MAX_RETRY_PAYMENT', '3', 'PAYMENT', 'Maximum payment retry attempts'),
('GST_RATE', '18', 'TAX', 'Goods and Services Tax rate percentage'),
('CLAIM_APPROVAL_THRESHOLD_AMOUNT', '100000', 'CLAIM', 'Claim amount above which requires manager approval');
```

#### discount_rules
```sql
CREATE TABLE discount_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    rule_name VARCHAR(255) NOT NULL,
    rule_code VARCHAR(100) UNIQUE NOT NULL,
    insurance_type_id INT,
    rule_condition JSON NOT NULL,
    discount_percentage DECIMAL(5, 2) NOT NULL,
    discount_max_amount DECIMAL(15, 2),
    rule_priority INT DEFAULT 0,
    is_combinable BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_rule_code (rule_code),
    INDEX idx_is_active (is_active),
    INDEX idx_rule_priority (rule_priority)
);

-- Example: Fleet discount rule
-- {"min_vehicles": 5, "fleet_claim_ratio_max": 0.2} -> 10% discount
```

#### quote_calculation_weights
```sql
CREATE TABLE quote_calculation_weights (
    weight_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_type_id INT NOT NULL,
    factor_name VARCHAR(255) NOT NULL,
    factor_weight DECIMAL(5, 2) NOT NULL,
    factor_calculation_formula TEXT,
    min_weight_value DECIMAL(10, 4),
    max_weight_value DECIMAL(10, 4),
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    UNIQUE KEY unique_type_factor (insurance_type_id, factor_name),
    INDEX idx_insurance_type_id (insurance_type_id)
);

-- Example weights for Motor Insurance quote calculation
-- age_risk_factor: 0.20, medical_risk_factor: 0.15, driving_risk_factor: 0.35, claim_history: 0.30
```

#### claim_approval_thresholds
```sql
CREATE TABLE claim_approval_thresholds (
    threshold_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_type_id INT NOT NULL,
    approval_level ENUM('AUTO_APPROVE', 'MANAGER_APPROVAL', 'DIRECTOR_APPROVAL', 'BOARD_APPROVAL') NOT NULL,
    min_claim_amount DECIMAL(15, 2),
    max_claim_amount DECIMAL(15, 2),
    required_approver_role_id INT NOT NULL,
    max_processing_days INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE CASCADE,
    FOREIGN KEY (required_approver_role_id) REFERENCES roles(role_id) ON DELETE RESTRICT,
    UNIQUE KEY unique_type_level (insurance_type_id, approval_level, min_claim_amount),
    INDEX idx_insurance_type_id (insurance_type_id)
);
```

#### company_configuration
```sql
CREATE TABLE company_configuration (
    company_config_id INT PRIMARY KEY AUTO_INCREMENT,
    insurance_company_id INT NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value LONGTEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE CASCADE,
    UNIQUE KEY unique_company_config (insurance_company_id, config_key),
    INDEX idx_insurance_company_id (insurance_company_id)
);
```

---

## Implementation Notes {#notes}

### 1. Indexing Strategy
- **Foreign Key Columns**: Always indexed
- **Search Columns** (email, username, policy_number): UNIQUE or indexed
- **Filter Columns** (status, is_active, dates): Indexed for query performance
- **Composite Indexes** for common query patterns (user_id, is_active)
- **Covering Indexes** for frequently joined queries

### 2. Partition Strategy (for Large Tables)
```sql
-- For audit_logs (large volume)
ALTER TABLE audit_logs PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- For claim_history (time-based)
ALTER TABLE claim_history PARTITION BY RANGE (YEAR(claim_year)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026)
);
```

### 3. BCNF Compliance Checklist
✅ **No Partial Dependencies**: All non-key attributes depend on the entire primary key  
✅ **No Transitive Dependencies**: No non-key attribute depends on another non-key attribute  
✅ **Every Determinant is a Superkey**: Functional dependencies X→Y only when X is a superkey  
✅ **Separate Tables for Independent Concepts**: User roles, permissions, sessions separate  
✅ **Junction Tables for Many-to-Many**: user_roles, role_permissions, quote_coverage_selection  
✅ **No Data Redundancy**: Information stored once with references elsewhere  

### 4. Temporal Queries
```sql
-- Find policies expiring in next 30 days
SELECT p.policy_id, p.policy_number, c.email
FROM policies p
JOIN customers c ON p.customer_id = c.customer_id
WHERE p.policy_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
AND p.policy_status = 'ACTIVE';

-- Claim resolution time
SELECT DATEDIFF(cs.settlement_approved_at, c.claim_reported_date) as resolution_days
FROM claims c
JOIN claim_settlement cs ON c.claim_id = cs.claim_id
ORDER BY resolution_days DESC;
```

### 5. Audit Trail Queries
```sql
-- Track all modifications to a specific policy
SELECT dl.*, u.username
FROM data_modification_history dl
JOIN users u ON dl.modified_by = u.user_id
WHERE dl.table_name = 'policies' AND dl.record_id = ?
ORDER BY dl.modified_at DESC;

-- Find who accessed claim details
SELECT al.*
FROM audit_logs al
WHERE al.table_name = 'claims' AND al.action_type = 'UPDATE'
ORDER BY al.timestamp DESC;
```

### 6. Risk Score Calculation
```sql
-- Update customer risk profile (Example calculation)
UPDATE customer_risk_profiles
SET 
    age_risk_factor = CASE 
        WHEN YEAR(CURDATE()) - YEAR(c.date_of_birth) < 25 THEN 0.35
        WHEN YEAR(CURDATE()) - YEAR(c.date_of_birth) > 65 THEN 0.30
        ELSE 0.15
    END,
    driving_risk_factor = CASE 
        WHEN cdh.violations_count > 3 THEN 0.45
        WHEN cdh.violations_count > 1 THEN 0.25
        ELSE 0.10
    END,
    overall_risk_percentage = (age_risk_factor + medical_risk_factor + driving_risk_factor + claim_history_risk_factor + employment_risk_factor) / 5,
    calculated_at = CURRENT_TIMESTAMP
FROM customers c
LEFT JOIN customer_driving_history cdh ON c.customer_id = cdh.customer_id
WHERE customer_risk_profiles.customer_id = c.customer_id;
```

### 7. Quote Calculation Logic
```sql
-- Example: Motor Insurance Premium = Base × (1 + Risk Adjustment) × (1 - Discounts) + Add-ons
SELECT 
    q.base_premium,
    q.base_premium * (1 + q.risk_adjustment_percentage / 100) as adjusted_premium,
    q.adjusted_premium * (1 - q.fleet_discount_percentage / 100) * (1 - q.loyalty_discount_percentage / 100) as discounted_premium,
    COALESCE(SUM(qa.addon_premium), 0) as addons_total,
    (q.adjusted_premium * (1 - q.fleet_discount_percentage / 100) * (1 - q.loyalty_discount_percentage / 100)) + COALESCE(SUM(qa.addon_premium), 0) as final_premium
FROM quotes q
LEFT JOIN quote_addon_selection qa ON q.quote_id = qa.quote_id
WHERE q.quote_id = ?
GROUP BY q.quote_id;
```

---

## Security Considerations

1. **Password Storage**: Always use bcrypt/argon2 with salt (not plain text)
2. **Sensitive Data**: Mask PAN, Aadhar, bank account numbers in logs
3. **Access Control**: Enforce permissions at database level via roles
4. **Encryption**: Encrypt sensitive columns (aadhar_number, pan_number) at rest
5. **SSL/TLS**: All connections should be encrypted in transit
6. **Audit Logging**: All DML operations logged with user context
7. **Session Management**: Implement token expiration and refresh logic
8. **Rate Limiting**: Apply at application layer to prevent brute force attacks

---

## Future Enhancements

- **Sharding**: For customer and policy data across regions
- **Time-Series DB**: Move analytics data to InfluxDB for performance
- **Event Sourcing**: Capture all state changes as immutable events
- **Data Warehouse**: Periodic ETL to separate analytics database
- **Document Storage**: Store PDF policies, invoices in S3/blob storage
- **API Rate Limiting Tables**: Track API usage by user/company
- **A/B Testing**: Configuration for different discount/quote algorithms

---

**End of Database Design Document**
