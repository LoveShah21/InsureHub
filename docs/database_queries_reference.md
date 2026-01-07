# Database Queries Reference

## Comprehensive Documentation for Viva & Technical Defense

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [ORM Query Categories Overview](#2-orm-query-categories-overview)
3. [Module-wise Query Documentation](#3-module-wise-query-documentation)
4. [Complex & Critical Queries (VIVA FOCUS)](#4-complex--critical-queries-viva-focus)
5. [Raw SQL Queries](#5-raw-sql-queries)
6. [Transactional Queries](#6-transactional-queries)
7. [Read vs Write Patterns](#7-read-vs-write-patterns)
8. [Query Performance & Scaling Considerations](#8-query-performance--scaling-considerations)
9. [Common Viva Questions & Answers](#9-common-viva-questions--answers)

---

## 1. Introduction

### Purpose of Documenting Queries

This document provides a comprehensive reference of all database queries used in the **Intelligent Insurance Policy Management & Decision Support System**. It is designed specifically for:

- **Viva preparation** — Understanding the rationale behind each query
- **Technical defense** — Explaining database design choices and optimizations
- **Performance discussion** — Demonstrating awareness of query efficiency

### Difference Between ORM-Generated SQL and Raw SQL

| Aspect | Django ORM | Raw SQL |
|--------|-----------|---------|
| **Abstraction** | High-level Python API | Direct SQL statements |
| **Security** | Automatic SQL injection protection | Manual parameterization required |
| **Portability** | Database-agnostic | Database-specific syntax |
| **Performance Control** | Limited (optimizer hints) | Full control |
| **Maintainability** | Easy to read/modify | Harder to maintain |

**This project uses exclusively Django ORM** — no raw SQL queries are present. This ensures:
- Consistent SQL injection protection
- Easier maintenance and code readability
- Seamless compatibility with MySQL backend

### Why Understanding Queries Matters for Scalability and Performance

1. **Query Optimization** — Poorly written queries can cause N+1 problems, full table scans, and slow response times
2. **Index Utilization** — Understanding how indexes work ensures efficient query execution
3. **Transaction Management** — Critical operations like payment processing require atomic transactions
4. **Scaling Preparation** — Identifying bottlenecks early helps prepare for production loads

---

## 2. ORM Query Categories Overview

Queries in this project are grouped by functional module:

| Category | Purpose | Key Tables |
|----------|---------|------------|
| **Authentication & IAM** | User login, registration, role management | `users`, `roles`, `user_roles`, `permissions` |
| **Catalog & Configuration** | Insurance products, companies, coverage types | `insurance_types`, `insurance_companies`, `coverage_types`, `riders_addons` |
| **Applications & Quotes** | Application CRUD, quote generation, scoring | `insurance_applications`, `application_documents`, `quotes`, `quote_recommendations` |
| **Policies & Payments** | Policy issuance, Razorpay payments, invoices | `policies`, `payments`, `invoices` |
| **Claims** | Claim submission, status workflow, settlement | `claims`, `claim_documents`, `claim_status_history`, `claim_assessments` |
| **Notifications** | User notifications, email triggers | `notifications`, `scheduled_reminders` |
| **Analytics & Reports** | Dashboard metrics, aggregations | Cross-table aggregations |
| **Audit & Logs** | Status history, IP tracking | `claim_status_history`, `audit_log` |

---

## 3. Module-wise Query Documentation

---

### 3.1 Accounts Module (Authentication & IAM)

#### 3.1.1 User Listing with Roles (Prefetch Optimization)

**Query Purpose:**
List all users with their assigned roles for admin management. Uses `prefetch_related` to avoid N+1 query problem when accessing user roles.

**Django ORM Code:**
```python
# apps/accounts/views.py - UserViewSet
queryset = User.objects.prefetch_related('user_roles__role').all()
```

**Generated SQL (Approximate):**
```sql
-- Query 1: Fetch users
SELECT * FROM users;

-- Query 2: Fetch related user_roles and roles (single query due to prefetch)
SELECT ur.*, r.* 
FROM user_roles ur
INNER JOIN roles r ON ur.role_id = r.id
WHERE ur.user_id IN (1, 2, 3, ...);
```

**Tables Involved:**
- `users`
- `user_roles`
- `roles`

**Query Type:** SELECT with JOIN (Prefetch)

**Index Usage:**
- `users.email` — Unique index for login lookup
- `user_roles.user_id` — Foreign key index for user→roles
- `user_roles.role_id` — Foreign key index for role lookup

**Optimization Notes:**
- `prefetch_related('user_roles__role')` prevents N+1 queries
- Without prefetch: 1 query for users + N queries for each user's roles
- With prefetch: 2 queries total regardless of user count

---

#### 3.1.2 User Search with Q Filters

**Query Purpose:**
Search users by email, name, or phone number using OR conditions.

**Django ORM Code:**
```python
# apps/accounts/views.py - UserViewSet.get_queryset()
from django.db.models import Q

queryset = queryset.filter(
    Q(email__icontains=search_query) |
    Q(first_name__icontains=search_query) |
    Q(last_name__icontains=search_query) |
    Q(phone_number__icontains=search_query)
)
```

**Generated SQL (Approximate):**
```sql
SELECT * FROM users
WHERE email LIKE '%search%'
   OR first_name LIKE '%search%'
   OR last_name LIKE '%search%'
   OR phone_number LIKE '%search%';
```

**Tables Involved:** `users`

**Query Type:** SELECT with OR conditions

**Index Usage:**
- `LIKE '%value%'` queries cannot use B-tree indexes effectively
- For production: Consider full-text search or Elasticsearch

**Optimization Notes:**
- Q objects enable complex OR/AND combinations
- `distinct()` applied to prevent duplicates from joins

---

#### 3.1.3 Role Assignment (get_or_create Pattern)

**Query Purpose:**
Assign a role to a user, avoiding duplicate assignments using `get_or_create`.

**Django ORM Code:**
```python
# apps/accounts/views.py - UserViewSet.assign_role()
role = Role.objects.get(id=role_id)

user_role, created = UserRole.objects.get_or_create(
    user=user,
    role=role,
    defaults={'assigned_by': request.user}
)
```

**Generated SQL (Approximate):**
```sql
-- Step 1: Fetch role
SELECT * FROM roles WHERE id = 1;

-- Step 2: Try to get existing user_role
SELECT * FROM user_roles WHERE user_id = 10 AND role_id = 1;

-- Step 3: If not found, INSERT (atomic operation)
INSERT INTO user_roles (user_id, role_id, assigned_by_id, created_at)
VALUES (10, 1, 5, NOW());
```

**Tables Involved:**
- `roles`
- `user_roles`

**Query Type:** SELECT + conditional INSERT

**Index Usage:**
- `user_roles.unique_together = ['user', 'role']` — Unique constraint prevents duplicates

**Optimization Notes:**
- `get_or_create` is atomic and handles race conditions
- Returns tuple `(instance, created_boolean)`

---

#### 3.1.4 Role-Based Permission Check

**Query Purpose:**
Check if user has Admin or Backoffice role for authorization.

**Django ORM Code:**
```python
# Used throughout views
if user.user_roles.filter(role__role_name__in=['ADMIN', 'BACKOFFICE']).exists():
    # Grant access
```

**Generated SQL (Approximate):**
```sql
SELECT 1 FROM user_roles ur
INNER JOIN roles r ON ur.role_id = r.id
WHERE ur.user_id = 10
  AND r.role_name IN ('ADMIN', 'BACKOFFICE')
LIMIT 1;
```

**Tables Involved:**
- `user_roles`
- `roles`

**Query Type:** SELECT with EXISTS optimization

**Index Usage:**
- `user_roles.user_id` — FK index
- `roles.role_name` — Should have index for frequent lookups

**Optimization Notes:**
- `exists()` returns boolean, not full queryset (more efficient)
- Stops at first match due to `LIMIT 1`

---

### 3.2 Quotes Module

#### 3.2.1 Quote Listing with Related Entities

**Query Purpose:**
List quotes with customer, insurance type, and company information in optimized queries.

**Django ORM Code:**
```python
# apps/quotes/views.py - QuoteViewSet.get_queryset()
queryset = Quote.objects.select_related(
    'customer__user', 'insurance_type', 'insurance_company'
).prefetch_related('coverages', 'addons').all()
```

**Generated SQL (Approximate):**
```sql
-- Main query with JOINs (select_related)
SELECT q.*, c.*, u.*, it.*, ic.*
FROM quotes q
INNER JOIN customers c ON q.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
INNER JOIN insurance_types it ON q.insurance_type_id = it.id
INNER JOIN insurance_companies ic ON q.insurance_company_id = ic.id;

-- Separate query for coverages (prefetch_related)
SELECT * FROM quote_coverage_selection
WHERE quote_id IN (1, 2, 3, ...);

-- Separate query for addons (prefetch_related)
SELECT * FROM quote_addon_selection
WHERE quote_id IN (1, 2, 3, ...);
```

**Tables Involved:**
- `quotes`
- `customers`
- `users`
- `insurance_types`
- `insurance_companies`
- `quote_coverage_selection`
- `quote_addon_selection`

**Query Type:** SELECT with JOINs + Prefetch

**Index Usage:**
- `quotes.customer_id` — FK index
- `quotes.insurance_type_id` — FK index
- `quotes.insurance_company_id` — FK index
- `quotes.status` — Index for filtering

**Optimization Notes:**
- `select_related` for ForeignKey (single query with JOINs)
- `prefetch_related` for reverse ForeignKey/ManyToMany (separate query with IN clause)
- Combining both minimizes total queries

---

#### 3.2.2 Quote Generation (Multiple Creates)

**Query Purpose:**
Generate quotes for approved application from all active companies.

**Django ORM Code:**
```python
# apps/quotes/views.py - QuoteViewSet.generate_for_application()

# Fetch active companies
companies = InsuranceCompany.objects.filter(is_active=True)

# Fetch coverages for insurance type
type_coverages = CoverageType.objects.filter(
    insurance_type=application.insurance_type
)

# Get mandatory coverage IDs
coverage_ids = list(type_coverages.filter(
    is_mandatory=True
).values_list('id', flat=True))

# Create quote for each company
for company in companies:
    quote = Quote.objects.create(
        application=application,
        customer=customer,
        insurance_type=application.insurance_type,
        insurance_company=company,
        base_premium=base_premium,
        # ... other fields
    )
    
    # Create quote coverages
    for cov_id in coverage_ids:
        coverage = type_coverages.get(id=cov_id)
        QuoteCoverage.objects.create(
            quote=quote,
            coverage_type=coverage,
            # ... other fields
        )
```

**Generated SQL (Approximate):**
```sql
-- Fetch active companies
SELECT * FROM insurance_companies WHERE is_active = 1;

-- Fetch coverages for insurance type
SELECT * FROM coverage_types WHERE insurance_type_id = 1;

-- Get mandatory coverage IDs
SELECT id FROM coverage_types 
WHERE insurance_type_id = 1 AND is_mandatory = 1;

-- For each company: INSERT quote
INSERT INTO quotes (application_id, customer_id, insurance_type_id, 
                    insurance_company_id, base_premium, ...)
VALUES (1, 1, 1, 1, 10000, ...);

-- For each coverage: INSERT quote_coverage
INSERT INTO quote_coverage_selection (quote_id, coverage_type_id, ...)
VALUES (1, 1, ...);
```

**Tables Involved:**
- `insurance_companies`
- `coverage_types`
- `quotes`
- `quote_coverage_selection`
- `quote_addon_selection`

**Query Type:** SELECT + Multiple INSERTs

**Index Usage:**
- `insurance_companies.is_active` — Filter index
- `coverage_types.insurance_type_id` — FK index

**Optimization Notes:**
- Multiple INSERTs in loop — could use `bulk_create` for performance
- Current implementation prioritizes clarity over micro-optimization

---

#### 3.2.3 Quote Recommendations (Delete + Create)

**Query Purpose:**
Clear old recommendations and create new ones based on score ranking.

**Django ORM Code:**
```python
# apps/quotes/views.py

# Clear old recommendations
QuoteRecommendation.objects.filter(application=application).delete()

# Create new recommendations (top 3)
for rank, (quote, scores) in enumerate(generated_quotes[:3], start=1):
    QuoteRecommendation.objects.create(
        application=application,
        customer=application.customer,
        recommended_quote=quote,
        recommendation_rank=rank,
        suitability_score=scores['overall_score'],
        # ... other fields
    )
```

**Generated SQL (Approximate):**
```sql
-- Delete existing recommendations
DELETE FROM quote_recommendations WHERE application_id = 1;

-- Insert new recommendations
INSERT INTO quote_recommendations 
    (application_id, customer_id, recommended_quote_id, recommendation_rank, ...)
VALUES (1, 1, 5, 1, ...);
-- Repeat for ranks 2 and 3
```

**Tables Involved:** `quote_recommendations`

**Query Type:** DELETE + INSERT

**Index Usage:**
- `quote_recommendations.application_id` — FK index for deletion

---

### 3.3 Policies & Payments Module

#### 3.3.1 Policy Listing with Filters

**Query Purpose:**
List policies with customer and company information, with optional status/type filters.

**Django ORM Code:**
```python
# apps/policies/views.py - PolicyViewSet.get_queryset()
queryset = Policy.objects.select_related(
    'customer__user', 'insurance_type', 'insurance_company'
).all()

# Filter by status
if status_filter:
    queryset = queryset.filter(status__iexact=status_filter)

# Filter by insurance type
if insurance_type:
    queryset = queryset.filter(insurance_type_id=insurance_type)
```

**Generated SQL (Approximate):**
```sql
SELECT p.*, c.*, u.*, it.*, ic.*
FROM policies p
INNER JOIN customers c ON p.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
INNER JOIN insurance_types it ON p.insurance_type_id = it.id
INNER JOIN insurance_companies ic ON p.insurance_company_id = ic.id
WHERE p.status = 'ACTIVE'
  AND p.insurance_type_id = 1;
```

**Tables Involved:**
- `policies`
- `customers`
- `users`
- `insurance_types`
- `insurance_companies`

**Query Type:** SELECT with JOINs and WHERE filters

**Index Usage:**
- `policies.status` — Index for status filtering
- `policies.customer_id` — FK index
- `policies.insurance_type_id` — FK index

---

#### 3.3.2 Payment Lookup for Razorpay Verification

**Query Purpose:**
Find payment record by Razorpay order ID with deep relation loading for policy creation.

**Django ORM Code:**
```python
# apps/policies/views.py - verify_razorpay_payment()
payment = Payment.objects.select_related(
    'quote__customer__user',
    'quote__insurance_type',
    'quote__insurance_company'
).get(razorpay_order_id=razorpay_order_id)
```

**Generated SQL (Approximate):**
```sql
SELECT p.*, q.*, c.*, u.*, it.*, ic.*
FROM payments p
INNER JOIN quotes q ON p.quote_id = q.id
INNER JOIN customers c ON q.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
INNER JOIN insurance_types it ON q.insurance_type_id = it.id
INNER JOIN insurance_companies ic ON q.insurance_company_id = ic.id
WHERE p.razorpay_order_id = 'order_xxx';
```

**Tables Involved:**
- `payments`
- `quotes`
- `customers`
- `users`
- `insurance_types`
- `insurance_companies`

**Query Type:** SELECT with deep JOINs

**Index Usage:**
- `payments.razorpay_order_id` — Index for Razorpay lookup (critical!)

**Optimization Notes:**
- Deep `select_related` chain loads all required data in single query
- Essential for atomic policy creation workflow

---

#### 3.3.3 Check for Existing Pending Payment

**Query Purpose:**
Prevent duplicate payment orders by checking for existing pending payments.

**Django ORM Code:**
```python
# apps/policies/views.py - create_razorpay_order()
existing_payment = Payment.objects.filter(
    quote=quote,
    status__in=['PENDING', 'INITIATED']
).first()
```

**Generated SQL (Approximate):**
```sql
SELECT * FROM payments
WHERE quote_id = 1
  AND status IN ('PENDING', 'INITIATED')
LIMIT 1;
```

**Tables Involved:** `payments`

**Query Type:** SELECT with IN filter

**Index Usage:**
- `payments.quote_id` — FK index
- `payments.status` — Index for status filtering

---

### 3.4 Claims Module

#### 3.4.1 Claim Listing with Documents (Prefetch)

**Query Purpose:**
List claims with related policy and documents for customer/backoffice view.

**Django ORM Code:**
```python
# apps/claims/views.py - ClaimViewSet.get_queryset()
queryset = Claim.objects.select_related(
    'customer__user', 'policy'
).prefetch_related('documents').all()
```

**Generated SQL (Approximate):**
```sql
-- Main query with JOINs
SELECT cl.*, c.*, u.*, p.*
FROM claims cl
INNER JOIN customers c ON cl.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
INNER JOIN policies p ON cl.policy_id = p.id;

-- Prefetch documents
SELECT * FROM claim_documents
WHERE claim_id IN (1, 2, 3, ...);
```

**Tables Involved:**
- `claims`
- `customers`
- `users`
- `policies`
- `claim_documents`

**Query Type:** SELECT with JOINs + Prefetch

**Index Usage:**
- `claims.customer_id` — FK index
- `claims.policy_id` — FK index
- `claims.status` — Index for filtering

---

#### 3.4.2 Claim Search with Q Filters

**Query Purpose:**
Search claims by claim number, policy number, or customer details.

**Django ORM Code:**
```python
# apps/claims/views.py
from django.db.models import Q

queryset = queryset.filter(
    Q(claim_number__icontains=search_query) |
    Q(policy__policy_number__icontains=search_query) |
    Q(customer__user__email__icontains=search_query) |
    Q(customer__user__first_name__icontains=search_query)
)
```

**Generated SQL (Approximate):**
```sql
SELECT cl.*
FROM claims cl
INNER JOIN policies p ON cl.policy_id = p.id
INNER JOIN customers c ON cl.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
WHERE cl.claim_number LIKE '%search%'
   OR p.policy_number LIKE '%search%'
   OR u.email LIKE '%search%'
   OR u.first_name LIKE '%search%';
```

**Tables Involved:**
- `claims`
- `policies`
- `customers`
- `users`

**Query Type:** SELECT with JOINs and OR conditions

---

#### 3.4.3 Surveyor Assignment (get_or_create)

**Query Purpose:**
Assign surveyor to claim, creating assessment record if not exists.

**Django ORM Code:**
```python
# apps/claims/views.py - ClaimViewSet.assign_surveyor()
assessment, created = ClaimAssessment.objects.get_or_create(
    claim=claim,
    surveyor=surveyor,
    defaults={'assessment_status': 'PENDING'}
)
```

**Generated SQL (Approximate):**
```sql
-- Try to get existing
SELECT * FROM claim_assessments 
WHERE claim_id = 1 AND surveyor_id = 5;

-- If not found, INSERT
INSERT INTO claim_assessments (claim_id, surveyor_id, assessment_status, ...)
VALUES (1, 5, 'PENDING', ...);
```

**Tables Involved:** `claim_assessments`

**Query Type:** SELECT + conditional INSERT

---

#### 3.4.4 Claim Approval Threshold Lookup

**Query Purpose:**
Find the approval threshold for a claim amount to determine who can approve.

**Django ORM Code:**
```python
# apps/claims/services.py - ClaimsWorkflowService.get_approval_threshold()
threshold = ClaimApprovalThreshold.objects.filter(
    insurance_type=insurance_type,
    min_claim_amount__lte=amount,
    max_claim_amount__gte=amount,
    is_active=True
).first()
```

**Generated SQL (Approximate):**
```sql
SELECT * FROM claim_approval_thresholds
WHERE insurance_type_id = 1
  AND min_claim_amount <= 50000
  AND max_claim_amount >= 50000
  AND is_active = 1
LIMIT 1;
```

**Tables Involved:** `claim_approval_thresholds`

**Query Type:** SELECT with range filter

**Index Usage:**
- Composite index on `(insurance_type_id, min_claim_amount, max_claim_amount)` would be optimal

---

### 3.5 Applications Module

#### 3.5.1 Application Listing with Documents

**Query Purpose:**
List applications with customer, insurance type, and documents.

**Django ORM Code:**
```python
# apps/applications/views.py
queryset = InsuranceApplication.objects.select_related(
    'customer__user', 'insurance_type'
).prefetch_related('documents').all()
```

**Generated SQL (Approximate):**
```sql
SELECT ia.*, c.*, u.*, it.*
FROM insurance_applications ia
INNER JOIN customers c ON ia.customer_id = c.id
INNER JOIN users u ON c.user_id = u.id
INNER JOIN insurance_types it ON ia.insurance_type_id = it.id;

SELECT * FROM application_documents
WHERE application_id IN (1, 2, 3, ...);
```

**Tables Involved:**
- `insurance_applications`
- `customers`
- `users`
- `insurance_types`
- `application_documents`

---

#### 3.5.2 Document Verification Lookup

**Query Purpose:**
Find specific document for verification by backoffice.

**Django ORM Code:**
```python
# apps/applications/views.py - ApplicationDocumentVerifyView
document = ApplicationDocument.objects.get(
    id=document_id,
    application_id=application_id
)
```

**Generated SQL (Approximate):**
```sql
SELECT * FROM application_documents
WHERE id = 5 AND application_id = 1;
```

**Tables Involved:** `application_documents`

**Query Type:** SELECT with compound WHERE

---

### 3.6 Customers Module

#### 3.6.1 Customer Profile Get or Create

**Query Purpose:**
Get existing customer profile or create new one for authenticated user.

**Django ORM Code:**
```python
# apps/customers/views.py - CustomerProfileView.get_object()
profile, created = CustomerProfile.objects.get_or_create(
    user=self.request.user
)
```

**Generated SQL (Approximate):**
```sql
SELECT * FROM customers WHERE user_id = 10;

-- If not found
INSERT INTO customers (user_id, ...) VALUES (10, ...);
```

**Tables Involved:** `customers`

**Query Type:** SELECT + conditional INSERT

---

#### 3.6.2 Customer Listing with Filters

**Query Purpose:**
List customers with optional city/state/occupation filters.

**Django ORM Code:**
```python
# apps/customers/views.py - CustomerListView.get_queryset()
queryset = CustomerProfile.objects.select_related('user').all()

if city:
    queryset = queryset.filter(residential_city__icontains=city)
if state:
    queryset = queryset.filter(residential_state__icontains=state)
if occupation:
    queryset = queryset.filter(occupation_type=occupation)
```

**Generated SQL (Approximate):**
```sql
SELECT c.*, u.*
FROM customers c
INNER JOIN users u ON c.user_id = u.id
WHERE c.residential_city LIKE '%Mumbai%'
  AND c.residential_state LIKE '%Maharashtra%';
```

**Tables Involved:**
- `customers`
- `users`

---

### 3.7 Notifications Module

#### 3.7.1 Unread Count Query

**Query Purpose:**
Count unread notifications for badge display.

**Django ORM Code:**
```python
# apps/notifications/views.py - NotificationViewSet.unread()
count = self.get_queryset().filter(is_read=False).count()
```

**Generated SQL (Approximate):**
```sql
SELECT COUNT(*) FROM notifications
WHERE user_id = 10 AND is_read = 0;
```

**Tables Involved:** `notifications`

**Query Type:** SELECT COUNT with filter

**Index Usage:**
- Composite index on `(user_id, is_read)` recommended

---

#### 3.7.2 Mark All as Read (Bulk Update)

**Query Purpose:**
Mark all unread notifications as read in single query.

**Django ORM Code:**
```python
# apps/notifications/views.py
updated = self.get_queryset().filter(is_read=False).update(
    is_read=True,
    read_at=timezone.now()
)
```

**Generated SQL (Approximate):**
```sql
UPDATE notifications
SET is_read = 1, read_at = NOW()
WHERE user_id = 10 AND is_read = 0;
```

**Tables Involved:** `notifications`

**Query Type:** UPDATE (bulk)

---

#### 3.7.3 Notification Summary by Type (Aggregation)

**Query Purpose:**
Group notifications by type for summary display.

**Django ORM Code:**
```python
# apps/notifications/views.py
by_type = queryset.values('notification_type').annotate(
    count=Count('id')
)
```

**Generated SQL (Approximate):**
```sql
SELECT notification_type, COUNT(id) as count
FROM notifications
WHERE user_id = 10
GROUP BY notification_type;
```

**Tables Involved:** `notifications`

**Query Type:** SELECT with GROUP BY

---

### 3.8 Analytics Module

#### 3.8.1 Dashboard Aggregations

**Query Purpose:**
Calculate live metrics for admin dashboard.

**Django ORM Code:**
```python
# apps/analytics/views.py - DashboardView.get()

# Application metrics
applications_total = InsuranceApplication.objects.count()
applications_pending = InsuranceApplication.objects.filter(
    status__in=['SUBMITTED', 'UNDER_REVIEW']
).count()
applications_last_30_days = InsuranceApplication.objects.filter(
    created_at__date__gte=thirty_days_ago
).count()

# Quote metrics
quotes_total = Quote.objects.count()
quotes_accepted = Quote.objects.filter(status='ACCEPTED').count()

# Policy metrics with SUM aggregation
total_premium_collected = Policy.objects.filter(
    status='ACTIVE'
).aggregate(total=Sum('total_premium_with_gst'))['total'] or 0

# Claim metrics with SUM aggregation
total_claims_amount = Claim.objects.filter(
    status='SETTLED'
).aggregate(total=Sum('amount_settled'))['total'] or 0
```

**Generated SQL (Approximate):**
```sql
-- Application counts
SELECT COUNT(*) FROM insurance_applications;
SELECT COUNT(*) FROM insurance_applications 
WHERE status IN ('SUBMITTED', 'UNDER_REVIEW');
SELECT COUNT(*) FROM insurance_applications 
WHERE DATE(created_at) >= '2025-12-08';

-- Quote counts
SELECT COUNT(*) FROM quotes;
SELECT COUNT(*) FROM quotes WHERE status = 'ACCEPTED';

-- Policy premium aggregation
SELECT SUM(total_premium_with_gst) FROM policies WHERE status = 'ACTIVE';

-- Claim amount aggregation
SELECT SUM(amount_settled) FROM claims WHERE status = 'SETTLED';
```

**Tables Involved:**
- `insurance_applications`
- `quotes`
- `policies`
- `claims`

**Query Type:** SELECT COUNT + SELECT SUM

**Optimization Notes:**
- Multiple COUNT queries — could be combined with CASE statements
- Aggregate functions are efficient with proper indexes

---

#### 3.8.2 Application Metrics by Status and Type

**Query Purpose:**
Group applications by status and insurance type for metrics.

**Django ORM Code:**
```python
# apps/analytics/views.py - ApplicationMetricsView
status_breakdown = InsuranceApplication.objects.values('status').annotate(
    count=Count('id')
)

type_breakdown = InsuranceApplication.objects.values(
    'insurance_type__type_name'
).annotate(count=Count('id'))
```

**Generated SQL (Approximate):**
```sql
-- By status
SELECT status, COUNT(id) as count
FROM insurance_applications
GROUP BY status;

-- By type (with JOIN)
SELECT it.type_name, COUNT(ia.id) as count
FROM insurance_applications ia
INNER JOIN insurance_types it ON ia.insurance_type_id = it.id
GROUP BY it.type_name;
```

**Tables Involved:**
- `insurance_applications`
- `insurance_types`

**Query Type:** SELECT with GROUP BY

---

#### 3.8.3 Claim Metrics with Multiple Aggregations

**Query Purpose:**
Calculate claim statistics by status and type.

**Django ORM Code:**
```python
# apps/analytics/views.py - ClaimMetricsView
status_breakdown = Claim.objects.values('status').annotate(
    count=Count('id'),
    total_requested=Sum('amount_requested'),
    total_approved=Sum('amount_approved')
)

type_breakdown = Claim.objects.values('claim_type').annotate(
    count=Count('id'),
    total_requested=Sum('amount_requested')
)
```

**Generated SQL (Approximate):**
```sql
-- By status with multiple aggregations
SELECT status, 
       COUNT(id) as count,
       SUM(amount_requested) as total_requested,
       SUM(amount_approved) as total_approved
FROM claims
GROUP BY status;

-- By type
SELECT claim_type,
       COUNT(id) as count,
       SUM(amount_requested) as total_requested
FROM claims
GROUP BY claim_type;
```

**Tables Involved:** `claims`

**Query Type:** SELECT with GROUP BY and multiple aggregations

---

## 4. Complex & Critical Queries (VIVA FOCUS)

---

### 4.1 Quote Ranking & Recommendation Queries

**Location:** `apps/quotes/views.py`

**Complexity:**
This is the most complex query flow in the project, involving:
1. Fetching application with related entities
2. Fetching all active insurance companies
3. Fetching coverages and addons for insurance type
4. Creating quotes for each company
5. Creating coverage/addon selections for each quote
6. Scoring and ranking quotes
7. Deleting old recommendations
8. Creating new recommendations (top 3)

**Key Queries:**
```python
# 1. Application with deep relations
application = InsuranceApplication.objects.select_related(
    'customer', 'insurance_type'
).get(id=application_id)

# 2. All active companies
companies = InsuranceCompany.objects.filter(is_active=True)

# 3. Coverages for insurance type
type_coverages = CoverageType.objects.filter(
    insurance_type=application.insurance_type
)

# 4. Mandatory coverage IDs (values_list optimization)
coverage_ids = list(type_coverages.filter(
    is_mandatory=True
).values_list('id', flat=True))

# 5. Clear old recommendations
QuoteRecommendation.objects.filter(application=application).delete()

# 6. Get recommendations with related data
recommendations = QuoteRecommendation.objects.filter(
    application=application
).select_related('recommended_quote__insurance_company')
```

**Time Complexity at Scale:**
- O(C × V) where C = companies, V = coverages per company
- For 5 companies with 10 coverages each = 50 coverage inserts
- Linear scaling — acceptable for current scope

**Potential Optimizations:**
1. Use `bulk_create` for QuoteCoverage/QuoteAddon objects
2. Pre-calculate company multipliers in database
3. Cache insurance type → coverage mappings

---

### 4.2 Analytics Aggregation Queries

**Location:** `apps/analytics/views.py`

**Complexity:**
Dashboard loads multiple aggregations in single request — 10+ separate queries.

**Key Queries:**
```python
# COUNT queries
applications_total = InsuranceApplication.objects.count()
applications_pending = InsuranceApplication.objects.filter(...).count()

# SUM aggregations
total_premium = Policy.objects.filter(status='ACTIVE').aggregate(
    total=Sum('total_premium_with_gst')
)['total']

# GROUP BY with annotations
status_breakdown = Claim.objects.values('status').annotate(
    count=Count('id'),
    total_requested=Sum('amount_requested'),
    total_approved=Sum('amount_approved')
)
```

**Time Complexity at Scale:**
- COUNT queries: O(n) full table scans without index
- With index: O(log n) for indexed columns
- GROUP BY: O(n) minimum for full scan

**Potential Optimizations:**
1. **Materialized views** — Pre-compute aggregations
2. **Caching** — Cache dashboard for 5-minute TTL
3. **Database indexes** — Add composite indexes
4. **Read replicas** — Route analytics to read replica

---

### 4.3 Claim Approval Threshold Evaluation

**Location:** `apps/claims/services.py`

**Complexity:**
Range-based lookup with multiple conditions.

**Query:**
```python
threshold = ClaimApprovalThreshold.objects.filter(
    insurance_type=insurance_type,
    min_claim_amount__lte=amount,
    max_claim_amount__gte=amount,
    is_active=True
).first()
```

**Generated SQL:**
```sql
SELECT * FROM claim_approval_thresholds
WHERE insurance_type_id = 1
  AND min_claim_amount <= 50000
  AND max_claim_amount >= 50000
  AND is_active = 1
ORDER BY id
LIMIT 1;
```

**Index Recommendation:**
```sql
CREATE INDEX idx_threshold_lookup ON claim_approval_thresholds 
(insurance_type_id, is_active, min_claim_amount, max_claim_amount);
```

---

### 4.4 Fleet Risk Score Calculations

**Location:** `apps/customers/fleet_models.py`

**Implementation:**
Fleet risk scoring is modeled but uses computed properties rather than complex queries.

```python
class FleetRiskScore(models.Model):
    fleet = models.OneToOneField(Fleet, on_delete=models.CASCADE)
    
    # Pre-calculated scores stored in database
    overall_risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    accident_rate_score = models.DecimalField(max_digits=5, decimal_places=2)
    claim_history_score = models.DecimalField(max_digits=5, decimal_places=2)
    fleet_age_score = models.DecimalField(max_digits=5, decimal_places=2)
    driver_experience_score = models.DecimalField(max_digits=5, decimal_places=2)
```

**Design Decision:**
Store calculated scores rather than compute on-the-fly. Recalculate on:
- New vehicle addition
- Claim submission
- Driver assignment change

---

## 5. Raw SQL Queries

### ✅ No Raw SQL Used in This Project

After comprehensive codebase analysis using grep search for:
- `raw(` method calls
- `execute(` cursor calls
- Direct SQL strings

**Finding:** No raw SQL queries exist in the codebase.

**Justification:**
1. Django ORM is sufficient for all business logic
2. ORM provides automatic SQL injection protection
3. Easier maintenance and code review
4. Database-agnostic (can switch from MySQL to PostgreSQL)

**Where Raw SQL Might Be Needed (Not Implemented):**
- Complex reporting with CTEs
- Recursive queries (org hierarchy)
- Database-specific features (MySQL full-text)

---

## 6. Transactional Queries

### 6.1 Payment → Policy Issuance (Critical Transaction)

**Location:** `apps/policies/views.py`

**Purpose:**
Ensure atomicity when creating policy after successful payment. Either all operations succeed or none do.

**Implementation:**
```python
# apps/policies/views.py - verify_razorpay_payment()

with transaction.atomic():
    quote = payment.quote
    
    # 1. Update payment to SUCCESS
    payment.status = 'SUCCESS'
    payment.razorpay_payment_id = razorpay_payment_id
    payment.payment_date = timezone.now()
    payment.save()
    
    # 2. Create policy
    policy = Policy.objects.create(
        quote=quote,
        customer=quote.customer,
        status='ACTIVE',
        # ... other fields
    )
    
    # 3. Link payment to policy
    payment.policy = policy
    payment.save()
    
    # 4. Create invoice
    invoice = Invoice.objects.create(
        policy=policy,
        payment=payment,
        status='PAID',
        # ... other fields
    )
```

**Rollback Scenarios:**
- Policy creation fails → Payment not marked SUCCESS
- Invoice creation fails → Policy and payment updates rolled back
- Any database error → Complete rollback

**Why Critical:**
- Prevents orphaned payments (money taken, no policy)
- Prevents duplicate policies
- Ensures data consistency

---

### 6.2 Claim Status Transitions

**Location:** `apps/claims/services.py`

**Purpose:**
Ensure claim status change and history recording happen atomically.

**Implementation:**
```python
# apps/claims/services.py - ClaimsWorkflowService

@transaction.atomic
def transition_status(
    self,
    new_status: str,
    user,
    reason: str = '',
    approved_amount: Decimal = None,
    request=None
):
    # 1. Validate transition
    if not self.can_transition_to(new_status):
        raise ValueError(...)
    
    old_status = self.claim.status
    
    # 2. Update claim fields based on status
    if new_status == 'APPROVED':
        self.claim.amount_approved = approved_amount
        self.claim.approved_at = timezone.now()
    
    # 3. Save claim
    self.claim.status = new_status
    self.claim.save()
    
    # 4. Record history
    self.record_status_change(old_status, new_status, user, reason, request)
    
    return self.claim
```

**Rollback Scenarios:**
- Status history creation fails → Claim status not changed
- Validation error mid-transaction → Complete rollback

---

### 6.3 Surveyor Assignment with Assessment Creation

**Location:** `apps/claims/services.py`

**Implementation:**
```python
@transaction.atomic
def assign_surveyor(self, surveyor_user, assessment_date: date = None):
    # 1. Create assessment record
    assessment = ClaimAssessment.objects.create(
        claim=self.claim,
        surveyor=surveyor_user,
        assessment_status='PENDING'
    )
    
    # 2. Update claim status
    old_status = self.claim.status
    self.claim.status = 'SURVEYOR_ASSIGNED'
    self.claim.save()
    
    # 3. Record history
    self.record_status_change(old_status, 'SURVEYOR_ASSIGNED', surveyor_user)
    
    return assessment
```

---

### 6.4 Settlement Creation

**Location:** `apps/claims/services.py`

**Implementation:**
```python
@transaction.atomic
def create_settlement(
    self,
    user,
    settlement_method: str = 'BANK_TRANSFER',
    bank_details: dict = None
) -> ClaimSettlement:
    # 1. Validate claim status
    if self.claim.status != 'APPROVED':
        raise ValueError("Settlement can only be created for approved claims.")
    
    # 2. Create settlement record
    settlement = ClaimSettlement.objects.create(
        claim=self.claim,
        settlement_amount=self.claim.amount_approved,
        settlement_method=settlement_method,
        settlement_status='PENDING'
    )
    
    return settlement
```

---

## 7. Read vs Write Patterns

### 7.1 High-Frequency Read Operations

| Operation | Frequency | Query Pattern | Optimization |
|-----------|-----------|---------------|--------------|
| Dashboard metrics | Every page load | Multiple COUNT/SUM | Add caching |
| Notification unread count | Every page | COUNT with filter | Index on (user_id, is_read) |
| Quote listing | Customer dashboard | SELECT with JOINs | select_related applied |
| Policy listing | Customer/Backoffice | SELECT with JOINs | select_related applied |
| Claim listing | Multiple views | SELECT with JOINs | select_related + prefetch |

### 7.2 Write-Heavy Operations

| Operation | Frequency | Write Type | Safety Measures |
|-----------|-----------|------------|-----------------|
| Quote generation | Per application | Batch INSERT | None (acceptable) |
| Payment verification | Per transaction | UPDATE + INSERT | transaction.atomic |
| Claim status update | Per action | UPDATE + INSERT | transaction.atomic |
| Mark notifications read | User action | Bulk UPDATE | Single query |
| Document upload | Per document | INSERT | File validation |

### 7.3 Performance-Critical Queries

1. **Payment Verification** — Must complete quickly for user experience
2. **Dashboard Load** — Multiple aggregations affect page load time
3. **Quote Generation** — Multiple inserts, may take 2-3 seconds
4. **Search Queries** — LIKE queries can be slow on large datasets

---

## 8. Query Performance & Scaling Considerations

### 8.1 Index Strategy

**Existing Indexes (from Model Meta):**

```python
# users table
indexes = [
    models.Index(fields=['email']),
    models.Index(fields=['username']),
    models.Index(fields=['is_active']),
]

# quotes table
indexes = [
    models.Index(fields=['application']),
    models.Index(fields=['customer']),
    models.Index(fields=['status']),
    models.Index(fields=['expiry_at']),
    models.Index(fields=['overall_score']),
]

# policies table
indexes = [
    models.Index(fields=['customer']),
    models.Index(fields=['status']),
    models.Index(fields=['policy_start_date']),
    models.Index(fields=['policy_end_date']),
]

# claims table
indexes = [
    models.Index(fields=['policy']),
    models.Index(fields=['customer']),
    models.Index(fields=['status']),
    models.Index(fields=['submitted_at']),
]

# notifications table
indexes = [
    models.Index(fields=['user', 'is_read']),
    models.Index(fields=['notification_type']),
    models.Index(fields=['created_at']),
]
```

### 8.2 Where Caching Could Be Introduced

| Data | Cache Duration | Invalidation |
|------|----------------|--------------|
| Dashboard metrics | 5 minutes | On any write |
| Insurance types list | 1 hour | On catalog update |
| Insurance companies | 1 hour | On catalog update |
| Coverage types | 1 hour | On catalog update |
| Quote recommendations | 10 minutes | On quote generation |

**Implementation:**
```python
from django.core.cache import cache

def get_dashboard_metrics():
    cache_key = 'dashboard_metrics_v1'
    data = cache.get(cache_key)
    
    if data is None:
        data = calculate_metrics()  # Expensive queries
        cache.set(cache_key, data, timeout=300)  # 5 minutes
    
    return data
```

### 8.3 Read Replicas / Sharding (Conceptual)

**Read Replica Strategy:**
```python
# settings.py
DATABASES = {
    'default': {
        # Primary for writes
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'insurance_db',
        'HOST': 'primary.db.host',
    },
    'replica': {
        # Replica for reads
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'insurance_db',
        'HOST': 'replica.db.host',
    }
}

# Database router
class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        return 'replica'
    
    def db_for_write(self, model, **hints):
        return 'default'
```

**Sharding Considerations:**
- Shard by customer_id for horizontal scaling
- Analytics queries become complex with sharding
- Not needed at current scale (<100K users)

### 8.4 Expected Bottlenecks at Scale

| Scale | Bottleneck | Solution |
|-------|------------|----------|
| 10K users | Dashboard queries | Add caching |
| 50K policies | Search queries | Add full-text search (Elasticsearch) |
| 100K claims | Status history table size | Archive old data |
| 1M notifications | Unread count queries | Pre-computed counters |

---

## 9. Common Viva Questions & Answers

### Q1: How does Django ORM generate SQL?

**Answer:**
Django ORM uses a lazy evaluation pattern:

1. **QuerySet Creation** — No SQL executed yet
   ```python
   qs = User.objects.filter(is_active=True)  # No query
   ```

2. **Query Execution** — SQL generated when iterating/evaluating
   ```python
   list(qs)  # NOW the query executes
   ```

3. **SQL Generation** — ORM inspects model metadata, applies filters, generates parameterized SQL

**From This Project:**
```python
# This line doesn't execute anything
queryset = Quote.objects.select_related('customer__user')

# This triggers the actual query
quote = queryset.get(id=1)
```

---

### Q2: What is the N+1 query problem?

**Answer:**
N+1 occurs when accessing related objects in a loop without prefetching.

**Bad Example:**
```python
quotes = Quote.objects.all()  # 1 query
for quote in quotes:
    print(quote.customer.user.email)  # N queries (1 per quote)
```

**From This Project (Correct Approach):**
```python
# apps/quotes/views.py
quotes = Quote.objects.select_related(
    'customer__user'
).all()  # 1 query with JOINs

for quote in quotes:
    print(quote.customer.user.email)  # No additional queries
```

---

### Q3: Why use select_related vs prefetch_related?

**Answer:**

| Aspect | select_related | prefetch_related |
|--------|---------------|------------------|
| **Relationship** | ForeignKey, OneToOne | ManyToMany, Reverse FK |
| **SQL** | Single JOIN query | Separate IN query |
| **Best For** | Single related object | Multiple related objects |

**From This Project:**
```python
# apps/claims/views.py
queryset = Claim.objects.select_related(
    'customer__user',  # ForeignKey chain - use select_related
    'policy'           # ForeignKey - use select_related
).prefetch_related(
    'documents'        # Reverse FK (one claim → many docs) - use prefetch_related
)
```

---

### Q4: How do you ensure transactional integrity?

**Answer:**
Using `transaction.atomic()` context manager or decorator.

**From This Project (Payment Flow):**
```python
# apps/policies/views.py
with transaction.atomic():
    # All these operations succeed or fail together
    payment.status = 'SUCCESS'
    payment.save()
    
    policy = Policy.objects.create(...)
    
    payment.policy = policy
    payment.save()
    
    invoice = Invoice.objects.create(...)
```

**Why Important:**
- Prevents partial updates (money taken, no policy)
- Database rolls back on any error
- ACID compliance guaranteed

---

### Q5: How do aggregations work in Django ORM?

**Answer:**
Using `aggregate()` for single value, `annotate()` for per-row values.

**From This Project (Analytics):**
```python
# apps/analytics/views.py

# aggregate() - returns single dictionary
total = Policy.objects.aggregate(total=Sum('total_premium_with_gst'))
# Result: {'total': 150000.00}

# annotate() - adds value to each row in GROUP BY
breakdown = Claim.objects.values('status').annotate(count=Count('id'))
# Result: [{'status': 'APPROVED', 'count': 10}, ...]
```

---

### Q6: What indexes exist and why?

**Answer:**
From model Meta classes:

```python
# Quotes table - for filtering and ordering
indexes = [
    models.Index(fields=['status']),       # Filter by status
    models.Index(fields=['overall_score']), # Sort by score
]

# Payments table - for Razorpay lookup
indexes = [
    models.Index(fields=['razorpay_order_id']),  # Critical for verification
]

# Notifications - for unread count
indexes = [
    models.Index(fields=['user', 'is_read']),  # Composite for common query
]
```

**Why Important:**
Without indexes, MySQL performs full table scans (O(n)).
With indexes, lookup is O(log n) using B-tree.

---

### Q7: How is data integrity maintained?

**Answer:**

1. **Foreign Key Constraints:**
   ```python
   customer = models.ForeignKey(
       'customers.CustomerProfile',
       on_delete=models.CASCADE  # Delete related on parent delete
   )
   
   insurance_type = models.ForeignKey(
       'catalog.InsuranceType',
       on_delete=models.RESTRICT  # Prevent deletion if referenced
   )
   ```

2. **Unique Constraints:**
   ```python
   class Meta:
       unique_together = ['user', 'role']  # No duplicate user-role pairs
   ```

3. **Validation in Model:**
   ```python
   def approve(self, user, approved_amount):
       if approved_amount > self.amount_requested:
           raise ValueError("Cannot exceed requested amount")
   ```

---

### Q8: How would you optimize slow queries?

**Answer:**

1. **Add Missing Indexes:**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['status', 'created_at']),
       ]
   ```

2. **Use select_related/prefetch_related:**
   ```python
   Quote.objects.select_related('customer__user')
   ```

3. **Avoid .count() in loops:**
   ```python
   # Bad
   for user in users:
       user.notifications.count()
   
   # Good - use annotate
   users = User.objects.annotate(notif_count=Count('notifications'))
   ```

4. **Cache expensive queries:**
   ```python
   cache.get_or_set('dashboard_metrics', calculate_metrics, 300)
   ```

---

### Q9: How are complex OR conditions handled?

**Answer:**
Using Django Q objects:

**From This Project:**
```python
# apps/accounts/views.py
from django.db.models import Q

queryset = queryset.filter(
    Q(email__icontains=search) |      # OR
    Q(first_name__icontains=search) | # OR
    Q(last_name__icontains=search)
)

# Generated SQL:
# WHERE email LIKE '%search%' 
#    OR first_name LIKE '%search%' 
#    OR last_name LIKE '%search%'
```

Q objects can be combined with `|` (OR) and `&` (AND).

---

### Q10: What is the difference between .get() and .filter().first()?

**Answer:**

| Method | Returns | On Not Found | Multiple Matches |
|--------|---------|--------------|------------------|
| `.get()` | Single object | `DoesNotExist` exception | `MultipleObjectsReturned` exception |
| `.filter().first()` | Single object | `None` | Returns first |

**From This Project:**
```python
# Using .get() when exactly one expected
quote = Quote.objects.get(id=quote_id)  # Raises if not found

# Using .first() when might not exist
existing_payment = Payment.objects.filter(
    quote=quote, status='PENDING'
).first()  # Returns None if not found
```

---

## Appendix: Complete Query Reference by File

### apps/accounts/views.py
- `User.objects.prefetch_related('user_roles__role').all()` — User listing
- `Role.objects.get(id=role_id)` — Role lookup
- `UserRole.objects.get_or_create(user, role)` — Role assignment
- `UserRole.objects.get(user=user, role_id=role_id).delete()` — Role removal

### apps/quotes/views.py
- `Quote.objects.select_related(...).prefetch_related(...)` — Quote listing
- `InsuranceCompany.objects.filter(is_active=True)` — Active companies
- `CoverageType.objects.filter(insurance_type=...)` — Type coverages
- `Quote.objects.create(...)` — Quote creation
- `QuoteCoverage.objects.create(...)` — Coverage selection
- `QuoteRecommendation.objects.filter(...).delete()` — Clear recommendations

### apps/policies/views.py
- `Policy.objects.select_related(...).filter(...)` — Policy listing
- `Payment.objects.filter(quote=..., status__in=[...]).first()` — Pending payment check
- `Payment.objects.create(...)` — Payment record creation
- `Policy.objects.create(...)` — Policy creation (in transaction)
- `Invoice.objects.create(...)` — Invoice creation (in transaction)

### apps/claims/views.py
- `Claim.objects.select_related(...).prefetch_related('documents')` — Claim listing
- `ClaimDocument.objects.create(...)` — Document upload
- `ClaimAssessment.objects.get_or_create(...)` — Surveyor assignment

### apps/claims/services.py
- `ClaimApprovalThreshold.objects.filter(...).first()` — Threshold lookup
- `ClaimStatusHistory.objects.create(...)` — Status history
- `ClaimAssessment.objects.create(...)` — Assessment creation
- `ClaimSettlement.objects.create(...)` — Settlement creation

### apps/analytics/views.py
- `InsuranceApplication.objects.count()` — Total count
- `Policy.objects.aggregate(Sum(...))` — Premium aggregation
- `Claim.objects.values('status').annotate(Count, Sum)` — Claim breakdown

### apps/notifications/views.py
- `Notification.objects.filter(user=..., is_read=False).count()` — Unread count
- `queryset.filter(is_read=False).update(is_read=True)` — Bulk update
- `queryset.values('notification_type').annotate(Count)` — Type breakdown

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Prepared For:** Viva & Technical Defense
