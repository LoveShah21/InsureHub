# Claims Lifecycle Sequence Diagram

## Overview

This document details the claims processing workflow, covering submission, review, approval, and settlement steps, emphasizing the state machine transitions and role-based thresholds.

---

## 1. Claim Submission Flow

```mermaid
sequenceDiagram
    participant Cust as Customer View
    participant Serv as Claims Service
    participant Model as Claim Model
    participant DB as Database

    Cust->>Serv: Submit Claim {policy_id, amount, docs}
    Serv->>Model: Validate Policy (Is Active?)
    Model-->>Serv: Active
    Serv->>DB: Create Claim (SUBMITTED)
    Serv->>DB: Save Documents
    Serv->>DB: Log History (SUBMITTED)
    Serv-->>Cust: Success
```

---

## 2. Claim Review and Approval Flow

```mermaid
sequenceDiagram
    participant Officer as Backoffice Officer
    participant Serv as Claims Service
    participant Check as Threshold Check
    participant Notif as Notification
    participant Email as Email Service

    Officer->>Serv: Post Review (Approve: ₹45,000)
    Serv->>Check: Check Approval Authority
    Check-->>Serv: Authority OK (Limit: ₹50k)
    Serv->>Serv: Update Status (APPROVED)
    Serv->>Notif: Create Notif
    Serv->>Email: Send Email
    Serv-->>Officer: Success
```

---

## 3. Threshold check logic (Detailed)

```mermaid
flowchart TD
    subgraph S1["Scenario 1: Claim ₹45,000 | Limit ₹50k"]
        direction TB
        C1[Claim: ₹45,000] --> D1{Is Claim < Limit?}
        L1[Limit: ₹50,000] --> D1
        D1 -- Yes --> A1[ALLOW APPROVAL]
    end

    subgraph S2["Scenario 2: Claim ₹80,000 | Limit ₹50k"]
        direction TB
        C2[Claim: ₹80,000] --> D2{Is Claim < Limit?}
        L2[Limit: ₹50,000] --> D2
        D2 -- No --> A2[DENY APPROVAL<br/>Error: Exceeds Limit]
    end
```

---

## 4. Settlement Process

```mermaid
sequenceDiagram
    participant Officer
    participant Service as Claims Service
    participant Model as Claim Model

    Officer->>Service: Create Settlement (Bank Transfer)
    Service->>Service: Verify Status (Must be APPROVED)
    Service->>Service: Create Settlement Rec
    Service->>Model: Update Status (SETTLED)
    Service->>Model: Close Claim (CLOSED)
```

---

## 5. State Machine Transitions

| Current State | Valid Next States | Trigger Action |
|---------------|-------------------|----------------|
| SUBMITTED | UNDER_REVIEW | start_review() |
| UNDER_REVIEW | APPROVED | approve() |
| UNDER_REVIEW | REJECTED | reject() |
| APPROVED | SETTLED | settle() |
| SETTLED | CLOSED | close() |
| REJECTED | CLOSED | close() |

**Invalid Transitions (Prevented by Logic):**
- SUBMITTED → APPROVED (Must review first)
- REJECTED → APPROVED (Final state)
- CLOSED → APPROVED (Final state)
