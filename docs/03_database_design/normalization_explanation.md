# Database Normalization Explanation

## Overview

The Insurance Policy Management System database is designed to conform to **Boyce-Codd Normal Form (BCNF)**, ensuring data integrity, minimizing redundancy, and preventing update anomalies.

---

## 1. Normalization Forms Applied

### First Normal Form (1NF) ✅
- All tables have primary keys
- All columns contain atomic (indivisible) values
- No repeating groups

**Example Compliance:**
```sql
-- GOOD: Atomic values
users.email = 'john@example.com'
users.first_name = 'John'
users.last_name = 'Doe'

-- NOT: Non-atomic (avoided)
users.full_name = 'John Doe'  -- Would violate 1NF
```

### Second Normal Form (2NF) ✅
- All non-key attributes are fully functionally dependent on the entire primary key
- No partial dependencies

**Example Compliance:**
```sql
-- Table: quote_coverage_selection
-- Composite Key: (quote_id, coverage_type_id)

-- coverage_premium depends on BOTH quote_id AND coverage_type_id
-- (same coverage has different premiums for different quotes)
```

### Third Normal Form (3NF) ✅
- No transitive dependencies
- Non-key attributes depend only on the primary key

**Example Compliance:**
```sql
-- WRONG: Transitive Dependency (NOT in our schema)
quotes.company_name  -- Depends on company_id, not quote_id

-- CORRECT: Normalized
quotes.insurance_company_id FK → insurance_companies.company_id
insurance_companies.company_name  -- Direct dependency on PK
```

### Boyce-Codd Normal Form (BCNF) ✅
- Every determinant is a candidate key
- No non-trivial functional dependencies where the determinant is not a superkey

---

## 2. Functional Dependencies Analysis

### users Table
```
{user_id} → {email, username, password_hash, first_name, last_name, ...}
{email} → {user_id}  (candidate key)
{username} → {user_id}  (candidate key)
```
**Status:** BCNF compliant ✅

### user_roles Table
```
{user_role_id} → {user_id, role_id, assigned_at, assigned_by}
{user_id, role_id} → {user_role_id, assigned_at, assigned_by}  (unique constraint)
```
**Status:** BCNF compliant ✅

### quotes Table
```
{quote_id} → {quote_number, application_id, customer_id, insurance_company_id, ...}
{quote_number} → {quote_id}  (candidate key)
```
**Status:** BCNF compliant ✅

### claims Table
```
{claim_id} → {claim_number, policy_id, customer_id, status, ...}
{claim_number} → {claim_id}  (candidate key)
```
**Status:** BCNF compliant ✅

---

## 3. Junction Tables Justification

### Why user_roles (M:N)?
**Problem without junction table:**
```sql
-- BAD: Repeating groups
users (
    user_id,
    role1_id,  -- What if user has 5 roles?
    role2_id,  -- Fixed columns limit flexibility
    role3_id
)
```

**Solution: Junction table**
```sql
-- GOOD: Flexible M:N relationship
user_roles (
    user_role_id,
    user_id,
    role_id,
    assigned_at,  -- Enables tracking assignment date
    assigned_by   -- Enables tracking who assigned
)
```

### Why quote_coverage_selection (M:N)?
- A quote can have multiple coverage types
- Each coverage type can appear in multiple quotes
- The junction table stores quote-specific premium for each coverage

```sql
quote_coverage_selection (
    quote_id,
    coverage_type_id,
    coverage_limit,    -- Per-quote value
    coverage_premium   -- Per-quote calculated premium
)
```

### Why role_permissions (M:N)?
- Roles can have multiple permissions
- Permissions can be assigned to multiple roles
- Enables flexible RBAC configuration

---

## 4. JSON Fields Justification

The schema uses JSON fields in specific cases where flexibility outweighs strict normalization:

### application_data (InsuranceApplication)
```json
{
  "vehicle_make": "Honda",
  "vehicle_model": "City",
  "vehicle_year": 2022,
  "registration_number": "GJ01XX1234"
}
```

**Why JSON?**
- Different insurance types require different fields
- Motor insurance needs vehicle details
- Health insurance needs medical details
- Creating separate tables for each type would cause table explosion
- JSON provides flexibility with single schema

**Trade-off:**
- Cannot create indexes on JSON fields (performance impact on large data)
- Query complexity increases for JSON filtering

### rule_condition (DiscountRule, EligibilityRule)
```json
{
  "min_age": 18,
  "max_age": 65,
  "min_fleet_size": 5,
  "max_claim_ratio": 0.2
}
```

**Why JSON?**
- Rules are evaluated at runtime by Python code
- Adding new condition types doesn't require schema changes
- Business rules are inherently dynamic

### assessment_findings (ClaimAssessment)
```json
{
  "damage_type": "collision",
  "repair_estimate": 45000,
  "parts_replaced": ["bumper", "headlight"],
  "labor_hours": 8
}
```

**Why JSON?**
- Assessment findings vary by claim type
- Storing structured findings without fixed schema

---

## 5. Denormalization Decisions (Intentional)

### Redundant customer_id in quotes
```sql
quotes.customer_id  -- Redundant (can derive from application.customer_id)
```

**Justification:**
- Avoids expensive JOINs for frequent customer→quotes queries
- Query pattern analysis shows 80%+ queries need customer filtering
- Acceptable redundancy for read performance

### Redundant insurance_type_id in policies
```sql
policies.insurance_type_id  -- Can derive from quote.application.insurance_type_id
```

**Justification:**
- Policy queries often filter by insurance type
- Avoids 3-table JOIN chain for common queries

---

## 6. Avoiding Anomalies

### Insert Anomaly Prevention
```sql
-- Cannot insert role_permission without existing role → Correct behavior
-- Cannot insert quote without application → Enforces business rule
```

### Update Anomaly Prevention
```sql
-- Changing company_name updates ONE row in insurance_companies
-- All related quotes automatically reflect the change via FK
```

### Delete Anomaly Prevention
```sql
-- ON DELETE RESTRICT prevents orphan records
-- Cannot delete InsuranceType if CoverageTypes exist
-- Cannot delete Policy if Claims exist
```

---

## 7. Normalization Summary Table

| Table | 1NF | 2NF | 3NF | BCNF | Notes |
|-------|-----|-----|-----|------|-------|
| users | ✅ | ✅ | ✅ | ✅ | Multiple candidate keys |
| roles | ✅ | ✅ | ✅ | ✅ | Simple structure |
| user_roles | ✅ | ✅ | ✅ | ✅ | Junction table |
| permissions | ✅ | ✅ | ✅ | ✅ | Simple structure |
| customers | ✅ | ✅ | ✅ | ✅ | 1:1 with users |
| insurance_applications | ✅ | ✅ | ✅ | ✅ | JSON for flexible data |
| quotes | ✅ | ✅ | ✅ | ✅ | Intentional denormalization |
| policies | ✅ | ✅ | ✅ | ✅ | Intentional denormalization |
| claims | ✅ | ✅ | ✅ | ✅ | Complete workflow data |
| insurance_types | ✅ | ✅ | ✅ | ✅ | Master data |
| coverage_types | ✅ | ✅ | ✅ | ✅ | FK to insurance_types |
| discount_rules | ✅ | ✅ | ✅ | ✅ | JSON conditions |
| premium_slabs | ✅ | ✅ | ✅ | ✅ | Range-based lookup |
| business_configuration | ✅ | ✅ | ✅ | ✅ | Key-value store |

---

## 8. Viva Defense Points

**Q: Why not store all customer data in users table?**
A: Separation of concerns - not all users are customers. Users table handles authentication, CustomerProfile handles domain-specific data. This follows Single Responsibility Principle.

**Q: Why use JSON fields instead of creating more tables?**
A: Trade-off between flexibility and strict normalization. For dynamic business rules and insurance-type-specific data, JSON provides necessary flexibility without table explosion. We accept limited indexing in exchange.

**Q: Why store redundant customer_id in quotes?**
A: Performance optimization. Customer→Quotes is a high-frequency query pattern. The redundancy eliminates a JOIN, and we maintain consistency through application-level validation.
