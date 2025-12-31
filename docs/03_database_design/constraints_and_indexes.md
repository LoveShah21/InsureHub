# Constraints and Indexes

## Overview

This document describes all database constraints (primary keys, foreign keys, unique constraints, check constraints) and indexes implemented in the Insurance Policy Management System.

---

## 1. Primary Key Constraints

All tables use surrogate primary keys (auto-incrementing integers) for:
- Stable references unaffected by business data changes
- Efficient JOIN operations
- Consistent foreign key patterns

| Table | Primary Key | Type |
|-------|-------------|------|
| users | user_id | INT AUTO_INCREMENT |
| roles | role_id | INT AUTO_INCREMENT |
| user_roles | user_role_id | INT AUTO_INCREMENT |
| permissions | permission_id | INT AUTO_INCREMENT |
| customers | customer_id | INT AUTO_INCREMENT |
| insurance_applications | application_id | INT AUTO_INCREMENT |
| quotes | quote_id | INT AUTO_INCREMENT |
| policies | policy_id | INT AUTO_INCREMENT |
| payments | payment_id | INT AUTO_INCREMENT |
| claims | claim_id | INT AUTO_INCREMENT |
| insurance_types | insurance_type_id | INT AUTO_INCREMENT |
| insurance_companies | company_id | INT AUTO_INCREMENT |

---

## 2. Foreign Key Constraints

### IAM Module

```sql
-- user_roles
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
FOREIGN KEY (assigned_by) REFERENCES users(user_id) ON DELETE RESTRICT

-- role_permissions
FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE

-- audit_logs
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
```

### Customer Module

```sql
-- customers (1:1 with users)
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT

-- customer_risk_profiles (1:1 with customers)
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE

-- customer_medical_disclosures
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE

-- customer_driving_history (1:1)
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
```

### Application & Quote Module

```sql
-- insurance_applications
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT
FOREIGN KEY (submitted_by) REFERENCES users(user_id) ON DELETE SET NULL
FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL

-- quotes
FOREIGN KEY (application_id) REFERENCES insurance_applications(application_id) ON DELETE CASCADE
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT
FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE RESTRICT

-- quote_coverage_selection
FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE CASCADE
FOREIGN KEY (coverage_type_id) REFERENCES coverage_types(coverage_type_id) ON DELETE RESTRICT
```

### Policy & Payment Module

```sql
-- policies (1:1 with quotes)
FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE RESTRICT
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
FOREIGN KEY (insurance_type_id) REFERENCES insurance_types(insurance_type_id) ON DELETE RESTRICT
FOREIGN KEY (insurance_company_id) REFERENCES insurance_companies(company_id) ON DELETE RESTRICT

-- payments
FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE RESTRICT
FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE SET NULL
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
```

### Claims Module

```sql
-- claims
FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ON DELETE RESTRICT
FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
FOREIGN KEY (settled_by) REFERENCES users(user_id) ON DELETE SET NULL

-- claim_documents
FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE SET NULL
FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL

-- claim_status_history
FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE RESTRICT

-- claim_settlement (1:1)
FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
FOREIGN KEY (settlement_approved_by) REFERENCES users(user_id) ON DELETE RESTRICT
```

---

## 3. Unique Constraints

### Business Keys (Natural Keys)

```sql
-- users
UNIQUE (email)
UNIQUE (username)

-- roles
UNIQUE (role_name)

-- permissions
UNIQUE (permission_code)

-- customers
UNIQUE (user_id)  -- 1:1 with users
UNIQUE (pan_number)
UNIQUE (aadhar_number)

-- insurance_types
UNIQUE (type_name)
UNIQUE (type_code)

-- insurance_companies
UNIQUE (company_name)
UNIQUE (company_code)

-- Reference numbers
UNIQUE (application_number) ON insurance_applications
UNIQUE (quote_number) ON quotes
UNIQUE (policy_number) ON policies
UNIQUE (payment_number) ON payments
UNIQUE (claim_number) ON claims
UNIQUE (invoice_number) ON invoices

-- Razorpay
UNIQUE (razorpay_order_id) ON payments
```

### Composite Unique Constraints

```sql
-- Prevent duplicate role assignments
UNIQUE (user_id, role_id) ON user_roles

-- Prevent duplicate permission grants
UNIQUE (role_id, permission_id) ON role_permissions

-- Prevent duplicate coverage codes per insurance type
UNIQUE (insurance_type_id, coverage_code) ON coverage_types

-- Prevent duplicate addon codes per insurance type
UNIQUE (insurance_type_id, addon_code) ON riders_addons

-- Prevent duplicate quote-coverage associations
UNIQUE (quote_id, coverage_type_id) ON quote_coverage_selection

-- Prevent duplicate claim history per customer per year
UNIQUE (customer_id, claim_year) ON claim_history
```

---

## 4. Check Constraints

### Django-Enforced Validations
Django model validators enforce these at application level:

```python
# Claim approval cannot exceed requested amount
amount_approved <= amount_requested

# Ratings must be in valid range
claim_settlement_ratio BETWEEN 0 AND 1
service_rating BETWEEN 0 AND 5

# Discount percentage must be positive
discount_percentage BETWEEN 0 AND 100

# Weight factors must sum to valid range
factor_weight BETWEEN 0 AND 1
```

---

## 5. Indexing Strategy

### Primary Key Indexes (Automatic)
All primary keys are automatically indexed by MySQL.

### Foreign Key Indexes
Django automatically creates indexes on ForeignKey fields.

### Explicit Performance Indexes

```sql
-- Users: Frequently queried for authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);

-- User Roles: Role lookups
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- Audit Logs: Filtering and searching
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);

-- Applications: Status filtering
CREATE INDEX idx_applications_status ON insurance_applications(status);
CREATE INDEX idx_applications_customer ON insurance_applications(customer_id);
CREATE INDEX idx_applications_submission ON insurance_applications(submission_date);

-- Quotes: Expiry and score sorting
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quotes_expiry ON quotes(expiry_at);
CREATE INDEX idx_quotes_score ON quotes(overall_score);
CREATE INDEX idx_quotes_customer ON quotes(customer_id);

-- Policies: Status and date filtering
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_start ON policies(policy_start_date);
CREATE INDEX idx_policies_end ON policies(policy_end_date);
CREATE INDEX idx_policies_customer ON policies(customer_id);

-- Payments: Status and Razorpay lookup
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_razorpay ON payments(razorpay_order_id);
CREATE INDEX idx_payments_customer ON payments(customer_id);

-- Claims: Status and date filtering
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_submitted ON claims(submitted_at);
CREATE INDEX idx_claims_policy ON claims(policy_id);
CREATE INDEX idx_claims_customer ON claims(customer_id);

-- Notifications: User inbox queries
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- Business Configuration: Key lookups
CREATE INDEX idx_config_key ON business_configuration(config_key);
CREATE INDEX idx_config_active ON business_configuration(is_active);
```

---

## 6. Index Justification

### High-Frequency Query Patterns

| Query Pattern | Index Used | Reason |
|--------------|------------|--------|
| Login by email | idx_users_email | Every login request |
| Get user roles | idx_user_roles_user | Authorization check |
| Customer applications | idx_applications_customer | Dashboard loading |
| Active quotes | idx_quotes_status, idx_quotes_expiry | Quote listing |
| Customer policies | idx_policies_customer | Dashboard |
| Claim by status | idx_claims_status | Backoffice workflows |
| Unread notifications | idx_notifications_user_read | Header badge count |
| Config lookup | idx_config_key | Every business rule evaluation |

### Composite Index Considerations

```sql
-- Optimal for: WHERE user_id = ? AND is_read = ?
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);

-- Optimal for: WHERE table_name = ? AND record_id = ?
CREATE INDEX idx_audit_table_record ON audit_logs(table_name, record_id);
```

---

## 7. Cascade Behavior Summary

| Relationship | ON DELETE | Reason |
|-------------|-----------|--------|
| User → UserRoles | CASCADE | Remove role assignments when user deleted |
| Customer → Applications | CASCADE | Remove applications when customer deleted |
| Application → Quotes | CASCADE | Remove quotes when application deleted |
| Quote → Policy | RESTRICT | Cannot delete quoted data if policy exists |
| Policy → Claims | RESTRICT | Cannot delete policy if claims exist |
| Claim → Documents | CASCADE | Remove documents when claim deleted |
| Claim → StatusHistory | CASCADE | Remove history when claim deleted |
| FK to User (actors) | SET NULL | Preserve records, nullify actor reference |
| FK to InsuranceType | RESTRICT | Protect referential integrity of master data |

---

## 8. Viva Defense Points

**Q: Why use surrogate keys instead of natural keys?**
A: Natural keys like email or policy_number can change. Surrogate keys (auto-increment IDs) provide stable references for foreign keys and better JOIN performance.

**Q: Why CASCADE on some relationships and RESTRICT on others?**
A: CASCADE for dependent data that has no meaning without parent (documents, history). RESTRICT for critical business data where deletion could cause data loss (policies with claims).

**Q: How do indexes improve performance?**
A: Indexes create B-tree structures that reduce lookup from O(n) to O(log n). For example, finding a user by email without index scans all rows; with index, it directly locates the record.

**Q: Why index both (user_id, is_read) together?**
A: This composite index optimizes the specific query pattern "get unread notifications for user X" which is executed on every page load for the notification badge.
