# Analytics Module Documentation

## Overview

The **Analytics** module provides business intelligence and reporting capabilities. It aggregates data from all other modules (Policies, Claims, Quotes) to provide actionable insights for Administrators and Backoffice staff.

## Core Responsibilities

1. **Dashboard Metrics**: Real-time stats for the admin panel.
2. **Performance Reporting**: Tracking revenue, claim ratios, and conversion rates.
3. **Audit Visualization**: Making sense of system logs.

---

## 2. Key Metrics & Logic

### Revenue Metrics
- **Total Premium Collected**: Sum of `payment_amount` where status is `SUCCESS`.
- **Revenue by Insurance Type**: Grouping payments by the associated Policy's `InsuranceType`.
  - SQL: `SELECT type_name, SUM(amount) FROM payments JOIN policies ... GROUP BY type_name`

### Operational Metrics
- **Claim Settlement Ratio (CSR)**:
  `CSR = (Total Settled Claims / Total Closed Claims) * 100`
- **Average Claim Processing Time**:
  `AVG(settled_at - submitted_at)`
- **Quote-to-Policy Conversion Rate**:
  `Conversion % = (Total Policies / Total Quotes Generated) * 100`

### Risk Metrics
- **Risk Distribution**: Percentage of customers in LOW, MEDIUM, HIGH risk categories.
- **Loss Ratio**: `Total Claim Payouts / Total Premium Collected`. (Critical for insurance profitability).

---

## 3. Implementation

### Dashboard Views
The analytics are not stored in a separate "Analytics Table" but are computed on-the-fly (or cached) using Django's Aggregation API (`Annotate`, `Aggregate`).

```python
from django.db.models import Sum, Count

def get_dashboard_stats():
    return {
        'total_revenue': Payment.objects.filter(status='SUCCESS').aggregate(Sum('amount')),
        'active_policies': Policy.objects.filter(status='ACTIVE').count(),
        'pending_claims': Claim.objects.filter(status='SUBMITTED').count()
    }
```

### Reporting
- **PDF/CSV Utils**: The module includes utilities to export these reports (e.g., "Monthly Revenue Report") for offline analysis.

---

## 4. Future Scope

- **Predictive Analytics**: Using ML to forecast next month's claims based on historical trends.
- **Customer Churn Analysis**: Identifying customers likely to not renew their policies.
